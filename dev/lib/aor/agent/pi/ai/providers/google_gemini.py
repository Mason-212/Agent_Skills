"""Google Gemini `generateContent` streaming provider.

Python port of the subset of
vendor/pi-mono-upstream/packages/ai/src/providers/google.ts and
google-shared.ts targeting public Gemini API.

Wire format
-----------
Gemini streams as a line-delimited JSON array over HTTP. Each element is a
`GenerateContentResponse` with `candidates[].content.parts` containing text,
thought, or functionCall parts. We parse the incremental stream by buffering
bytes and splitting on line boundaries, matching what
google-shared-gemini3-unsigned-tool-call.test.ts exercises.

Thinking parts surface as text blocks with `thought: true`. We emit them as
`thinking_*` events; their `thought_signature` (when present) is carried
over into Gemini's tool-call replay semantics (different from OpenAI's
reasoning replay - Gemini's signature is attached to the tool call itself,
via the ToolCall.thought_signature field).
"""

from __future__ import annotations

import asyncio
import json
import time
from typing import Any

import httpx

from ..env_keys import get_env_api_key
from ..event_stream import AssistantMessageEventStream
from ..models_catalog import calculate_cost
from ..registry import register_api_provider
from ..types import (
    AssistantMessage,
    Context,
    DoneEvent,
    ErrorEvent,
    Message,
    Model,
    SimpleStreamOptions,
    StartEvent,
    StopReason,
    StreamOptions,
    TextContent,
    TextDeltaEvent,
    TextEndEvent,
    TextStartEvent,
    ThinkingContent,
    ThinkingDeltaEvent,
    ThinkingEndEvent,
    ThinkingStartEvent,
    Tool,
    ToolCall,
    ToolCallEndEvent,
    ToolCallStartEvent,
    Usage,
)
from ._transforms import normalize_tool_call_id

_API = "google-generative-ai"
_PROVIDER = "google"
_DEFAULT_TIMEOUT_S = 180.0


async def stream(
    model: Model,
    context: Context,
    options: StreamOptions | None = None,
) -> AssistantMessageEventStream:
    events = AssistantMessageEventStream()
    events.set_task(asyncio.create_task(_run(model, context, options, events)))
    return events


async def stream_simple(
    model: Model,
    context: Context,
    options: SimpleStreamOptions | None = None,
) -> AssistantMessageEventStream:
    return await stream(model, context, options)


async def _run(
    model: Model,
    context: Context,
    options: StreamOptions | SimpleStreamOptions | None,
    events: AssistantMessageEventStream,
) -> None:
    partial = AssistantMessage(
        api=model.api,
        provider=model.provider,
        model=model.id,
        stop_reason="stop",
        timestamp=int(time.time() * 1000),
    )
    try:
        api_key = _resolve_api_key(options)
        payload = _build_payload(model, context, options)
        # Pass the key via header (x-goog-api-key) rather than the URL so it
        # cannot leak into httpx.HTTPStatusError messages or client logs.
        url = f"{model.base_url}/models/{model.id}:streamGenerateContent?alt=sse"
        headers = {
            "Content-Type": "application/json",
            "Accept": "text/event-stream",
            "x-goog-api-key": api_key,
        }
        if options and options.headers:
            headers.update(options.headers)

        events.push(StartEvent(partial=partial))
        async with httpx.AsyncClient(timeout=_DEFAULT_TIMEOUT_S) as client:
            async with client.stream("POST", url, headers=headers, json=payload) as response:
                response.raise_for_status()
                await _consume(response, partial, events, model)
    except asyncio.CancelledError:
        partial.stop_reason = "aborted"
        events.push(ErrorEvent(reason="aborted", error=partial))
        raise
    except Exception as exc:  # noqa: BLE001
        partial.stop_reason = "error"
        partial.error_message = str(exc)
        events.push(ErrorEvent(reason="error", error=partial))


def _resolve_api_key(options: StreamOptions | SimpleStreamOptions | None) -> str:
    if options and options.api_key:
        return options.api_key
    env = get_env_api_key(_PROVIDER)
    if env:
        return env
    raise RuntimeError(
        "No Gemini API key. Set GEMINI_API_KEY or pass api_key in StreamOptions."
    )


def _build_payload(
    model: Model,
    context: Context,
    options: StreamOptions | SimpleStreamOptions | None,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "contents": _context_to_gemini_contents(context),
    }
    generation_config: dict[str, Any] = {}
    if options and options.temperature is not None:
        generation_config["temperature"] = options.temperature
    if options and options.max_tokens is not None:
        generation_config["maxOutputTokens"] = options.max_tokens
    if isinstance(options, SimpleStreamOptions) and options.reasoning:
        generation_config["thinkingConfig"] = {
            "thinkingBudget": _map_reasoning_budget(
                options.reasoning, options.thinking_budgets
            ),
            "includeThoughts": True,
        }
    if generation_config:
        payload["generationConfig"] = generation_config
    if context.system_prompt:
        payload["systemInstruction"] = {
            "role": "user",
            "parts": [{"text": context.system_prompt}],
        }
    if context.tools:
        payload["tools"] = [
            {
                "functionDeclarations": [_tool_to_gemini(t) for t in context.tools],
            }
        ]
    return payload


_GEMINI_DEFAULT_THINKING_BUDGETS: dict[str, int] = {
    "minimal": 1024,
    "low": 4096,
    "medium": 8192,
    "high": 16384,
    "xhigh": 32768,
}


def _map_reasoning_budget(
    level: str,
    overrides: dict[str, int] | None = None,
) -> int:
    """Translate a SimpleStreamOptions reasoning level to a Gemini thinkingBudget.

    When `overrides` (the caller's `SimpleStreamOptions.thinking_budgets`)
    contains an entry for this level, it wins over the built-in default.
    """
    override = (overrides or {}).get(level)
    if override is not None:
        return override
    return _GEMINI_DEFAULT_THINKING_BUDGETS.get(level, 4096)


def _tool_to_gemini(tool: Tool) -> dict[str, Any]:
    return {
        "name": tool.name,
        "description": tool.description,
        "parameters": tool.parameters or {"type": "object", "properties": {}},
    }


def _context_to_gemini_contents(context: Context) -> list[dict[str, Any]]:
    contents: list[dict[str, Any]] = []
    for msg in context.messages:
        contents.extend(_message_to_gemini(msg))
    return contents


def _message_to_gemini(msg: Message) -> list[dict[str, Any]]:
    if msg.role == "user":
        text = msg.content if isinstance(msg.content, str) else "".join(
            b.text for b in msg.content if getattr(b, "type", None) == "text"
        )
        return [{"role": "user", "parts": [{"text": text}]}]
    if msg.role == "assistant":
        parts: list[dict[str, Any]] = []
        for block in msg.content:
            if block.type == "text":
                parts.append({"text": block.text})
            elif block.type == "thinking":
                parts.append({"text": block.thinking, "thought": True})
            elif block.type == "toolCall":
                fc_part: dict[str, Any] = {
                    "functionCall": {
                        "name": block.name,
                        "args": block.arguments,
                    }
                }
                if block.thought_signature:
                    fc_part["thoughtSignature"] = block.thought_signature
                parts.append(fc_part)
        if not parts:
            parts.append({"text": ""})
        return [{"role": "model", "parts": parts}]
    if msg.role == "toolResult":
        text = "".join(
            b.text for b in msg.content if getattr(b, "type", None) == "text"
        )
        return [
            {
                "role": "user",
                "parts": [
                    {
                        "functionResponse": {
                            "name": msg.tool_name,
                            "response": {"content": text},
                        }
                    }
                ],
            }
        ]
    return []


async def _consume(
    response: httpx.Response,
    partial: AssistantMessage,
    events: AssistantMessageEventStream,
    model: Model,
) -> None:
    text_index: int | None = None
    thinking_index: int | None = None
    finish: str | None = None
    usage_raw: dict[str, Any] | None = None
    saw_terminal = False

    async for line in response.aiter_lines():
        if not line:
            continue
        if line.startswith("data: "):
            line = line[6:]
        if line == "[DONE]":
            saw_terminal = True
            break
        try:
            chunk = json.loads(line)
        except json.JSONDecodeError:
            continue

        for candidate in chunk.get("candidates", []) or []:
            content = candidate.get("content", {}) or {}
            for part in content.get("parts", []) or []:
                if "text" in part and part["text"] is not None:
                    if part.get("thought"):
                        if thinking_index is None:
                            thinking_index = len(partial.content)
                            partial.content.append(ThinkingContent(thinking=""))
                            events.push(
                                ThinkingStartEvent(
                                    content_index=thinking_index, partial=partial
                                )
                            )
                        piece = part["text"]
                        tb = partial.content[thinking_index]
                        if isinstance(tb, ThinkingContent):
                            tb.thinking += piece
                        events.push(
                            ThinkingDeltaEvent(
                                content_index=thinking_index,
                                delta=piece,
                                partial=partial,
                            )
                        )
                    else:
                        if text_index is None:
                            text_index = len(partial.content)
                            partial.content.append(TextContent(text=""))
                            events.push(
                                TextStartEvent(
                                    content_index=text_index, partial=partial
                                )
                            )
                        piece = part["text"]
                        tbt = partial.content[text_index]
                        if isinstance(tbt, TextContent):
                            tbt.text += piece
                        events.push(
                            TextDeltaEvent(
                                content_index=text_index,
                                delta=piece,
                                partial=partial,
                            )
                        )
                elif "functionCall" in part:
                    fc = part["functionCall"] or {}
                    call_index = len(partial.content)
                    call_id = normalize_tool_call_id(
                        fc.get("id"), fallback_index=call_index
                    )
                    tool_call = ToolCall(
                        id=call_id,
                        name=fc.get("name", ""),
                        arguments=fc.get("args", {}) or {},
                        thought_signature=part.get("thoughtSignature"),
                    )
                    partial.content.append(tool_call)
                    # Gemini delivers each functionCall as a single, complete
                    # part rather than streaming JSON fragments like the
                    # OpenAI / Anthropic APIs do. We therefore do not emit a
                    # ToolCallDeltaEvent; start and end fire back-to-back with
                    # the finalized arguments already present on tool_call.
                    events.push(
                        ToolCallStartEvent(content_index=call_index, partial=partial)
                    )
                    events.push(
                        ToolCallEndEvent(
                            content_index=call_index,
                            tool_call=tool_call,
                            partial=partial,
                        )
                    )

            if candidate.get("finishReason"):
                finish = candidate["finishReason"]
                saw_terminal = True

        if "usageMetadata" in chunk and chunk["usageMetadata"]:
            usage_raw = chunk["usageMetadata"]

    if text_index is not None:
        tb = partial.content[text_index]
        if isinstance(tb, TextContent):
            events.push(
                TextEndEvent(
                    content_index=text_index, content=tb.text, partial=partial
                )
            )
    if thinking_index is not None:
        tb2 = partial.content[thinking_index]
        if isinstance(tb2, ThinkingContent):
            events.push(
                ThinkingEndEvent(
                    content_index=thinking_index,
                    content=tb2.thinking,
                    partial=partial,
                )
            )

    if usage_raw:
        partial.usage = _usage_from_gemini(usage_raw)
        calculate_cost(model, partial.usage)

    partial.stop_reason = _map_stop_reason(finish, partial, saw_terminal=saw_terminal)
    if partial.stop_reason in ("stop", "length", "toolUse"):
        events.push(DoneEvent(reason=partial.stop_reason, message=partial))  # type: ignore[arg-type]
    else:
        if partial.error_message is None:
            partial.error_message = "Stream ended without a terminal marker"
        events.push(ErrorEvent(reason="error", error=partial))


def _usage_from_gemini(raw: dict[str, Any]) -> Usage:
    prompt = int(raw.get("promptTokenCount", 0))
    output = int(raw.get("candidatesTokenCount", 0))
    cached = int(raw.get("cachedContentTokenCount", 0) or 0)
    total = int(raw.get("totalTokenCount", prompt + output))
    # See gateway._usage_from_openai for the cache/input subtraction rationale
    # and the max(0, ...) clamp.
    return Usage(
        input=max(0, prompt - cached),
        output=output,
        cache_read=cached,
        cache_write=0,
        total_tokens=total,
    )


def _map_stop_reason(
    finish: str | None, partial: AssistantMessage, *, saw_terminal: bool
) -> StopReason:
    if finish == "STOP":
        if any(getattr(b, "type", None) == "toolCall" for b in partial.content):
            return "toolUse"
        return "stop"
    if finish is None:
        # No finishReason observed -> connection was truncated.
        if not saw_terminal:
            return "error"
        if any(getattr(b, "type", None) == "toolCall" for b in partial.content):
            return "toolUse"
        return "stop"
    if finish == "MAX_TOKENS":
        return "length"
    if finish in ("TOOL_CALLS",):
        return "toolUse"
    return "error"


register_api_provider(_API, stream, stream_simple, source_id="builtin:gemini")


__all__ = ["stream", "stream_simple"]
