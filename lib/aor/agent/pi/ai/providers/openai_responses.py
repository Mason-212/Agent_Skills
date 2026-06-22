"""OpenAI `/v1/responses` provider (streaming, with reasoning replay).

Python port of the subset of
vendor/pi-mono-upstream/packages/ai/src/providers/openai-responses.ts and
openai-responses-shared.ts targeting text, function tool calls, and reasoning.

Responses API differs from Completions in several ways relevant to the port:

- The streaming event model is structured: events like
  `response.created`, `response.output_item.added`,
  `response.output_text.delta`, `response.output_text.done`,
  `response.reasoning_summary_text.delta`, `response.output_item.done`,
  `response.completed` replace the Completions chunk-delta shape.
- Assistant output is a list of *items* (message, reasoning, function_call).
  Messages contain text parts; reasoning items contain summary parts and,
  when encrypted, an opaque `encrypted_content` blob that must be replayed
  on subsequent turns to preserve the reasoning context.
- Tool calls are `function_call` items with `arguments` streaming as a
  string that ultimately parses as JSON.

Reasoning replay
----------------
When the caller includes previous `thinking` content blocks whose
`thinking_signature` carries an encrypted reasoning id/content, we replay
those items in the request payload so OpenAI can continue the prior chain of
thought. See notebook section 8 for the demo, and
vendor/pi-mono-upstream/packages/ai/test/openai-responses-reasoning-replay-e2e.test.ts.
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
    ToolCallDeltaEvent,
    ToolCallEndEvent,
    ToolCallStartEvent,
    Usage,
)
from ..utils.json_parse import parse_streaming_json
from ._sse import iter_sse

_API = "openai-responses"
_PROVIDER = "openai"
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
        headers = _build_headers(api_key, options)

        events.push(StartEvent(partial=partial))
        async with httpx.AsyncClient(timeout=_DEFAULT_TIMEOUT_S) as client:
            async with client.stream(
                "POST",
                f"{model.base_url}/responses",
                headers=headers,
                json=payload,
            ) as response:
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
        "No OpenAI API key. Set OPENAI_API_KEY or pass api_key in StreamOptions."
    )


def _build_headers(
    api_key: str, options: StreamOptions | SimpleStreamOptions | None
) -> dict[str, str]:
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "Accept": "text/event-stream",
    }
    if options and options.headers:
        headers.update(options.headers)
    return headers


def _build_payload(
    model: Model,
    context: Context,
    options: StreamOptions | SimpleStreamOptions | None,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "model": model.id,
        "input": _context_to_responses_input(context),
        "stream": True,
    }
    if context.system_prompt:
        payload["instructions"] = context.system_prompt
    if options:
        if options.temperature is not None:
            payload["temperature"] = options.temperature
        if options.max_tokens is not None:
            payload["max_output_tokens"] = options.max_tokens
    if context.tools:
        payload["tools"] = [_tool_to_responses(tool) for tool in context.tools]
    if isinstance(options, SimpleStreamOptions) and options.reasoning:
        payload["reasoning"] = {"effort": _map_reasoning_effort(options.reasoning)}
    return payload


def _map_reasoning_effort(level: str) -> str:
    if level == "xhigh":
        return "high"
    return level


def _tool_to_responses(tool: Tool) -> dict[str, Any]:
    return {
        "type": "function",
        "name": tool.name,
        "description": tool.description,
        "parameters": tool.parameters or {"type": "object", "properties": {}},
    }


def _context_to_responses_input(context: Context) -> list[dict[str, Any]]:
    """Convert the agent Context to the Responses `input` item list.

    Reasoning items (with `encrypted_content` in `thinking_signature`) are
    replayed here so OpenAI can continue the prior chain of thought across
    turns (see openai-responses-reasoning-replay-e2e).
    """
    items: list[dict[str, Any]] = []
    for msg in context.messages:
        items.extend(_message_to_responses_items(msg))
    return items


def _message_to_responses_items(msg: Message) -> list[dict[str, Any]]:
    if msg.role == "user":
        text = msg.content if isinstance(msg.content, str) else "".join(
            b.text for b in msg.content if getattr(b, "type", None) == "text"
        )
        return [
            {
                "type": "message",
                "role": "user",
                "content": [{"type": "input_text", "text": text}],
            }
        ]
    if msg.role == "assistant":
        items: list[dict[str, Any]] = []
        text_parts: list[dict[str, Any]] = []
        for block in msg.content:
            if block.type == "text":
                text_parts.append({"type": "output_text", "text": block.text})
            elif block.type == "thinking":
                signature = block.thinking_signature or ""
                try:
                    parsed = json.loads(signature) if signature else {}
                except json.JSONDecodeError:
                    parsed = {}
                encrypted = parsed.get("encrypted_content") if isinstance(parsed, dict) else None
                reasoning_id = parsed.get("id") if isinstance(parsed, dict) else None
                reasoning_item: dict[str, Any] = {"type": "reasoning"}
                if reasoning_id:
                    reasoning_item["id"] = reasoning_id
                if encrypted:
                    reasoning_item["encrypted_content"] = encrypted
                reasoning_item["summary"] = (
                    [{"type": "summary_text", "text": block.thinking}]
                    if block.thinking
                    else []
                )
                items.append(reasoning_item)
            elif block.type == "toolCall":
                items.append(
                    {
                        "type": "function_call",
                        "call_id": block.id,
                        "name": block.name,
                        "arguments": json.dumps(block.arguments),
                    }
                )
        if text_parts:
            items.append(
                {"type": "message", "role": "assistant", "content": text_parts}
            )
        return items
    if msg.role == "toolResult":
        text = "".join(
            b.text for b in msg.content if getattr(b, "type", None) == "text"
        )
        return [
            {
                "type": "function_call_output",
                "call_id": msg.tool_call_id,
                "output": text,
            }
        ]
    return []


async def _consume(
    response: httpx.Response,
    partial: AssistantMessage,
    events: AssistantMessageEventStream,
    model: Model,
) -> None:
    wire_to_partial: dict[int, int] = {}
    text_state: dict[int, _TextAccum] = {}
    reasoning_state: dict[int, _ReasonAccum] = {}
    tool_state: dict[int, _ToolAccum] = {}
    stop_reason: str | None = None
    usage: Usage | None = None
    saw_terminal = False

    async for sse in iter_sse(response):
        if not sse.data:
            continue
        try:
            data = json.loads(sse.data)
        except json.JSONDecodeError:
            continue
        kind = sse.event or data.get("type", "")

        if kind == "response.output_item.added":
            item = data.get("item", {}) or {}
            wire_idx = int(data.get("output_index", 0))
            partial_idx = len(partial.content)
            wire_to_partial[wire_idx] = partial_idx
            itype = item.get("type")
            if itype == "message":
                partial.content.append(TextContent(text=""))
                text_state[wire_idx] = _TextAccum(partial_index=partial_idx)
                events.push(
                    TextStartEvent(content_index=partial_idx, partial=partial)
                )
            elif itype == "reasoning":
                partial.content.append(ThinkingContent(thinking=""))
                reasoning_state[wire_idx] = _ReasonAccum(
                    partial_index=partial_idx,
                    reasoning_id=item.get("id"),
                    encrypted_content=item.get("encrypted_content"),
                )
                events.push(
                    ThinkingStartEvent(content_index=partial_idx, partial=partial)
                )
            elif itype == "function_call":
                call_id = item.get("call_id", f"call_{wire_idx}")
                name = item.get("name", "")
                partial.content.append(
                    ToolCall(id=call_id, name=name, arguments={})
                )
                tool_state[wire_idx] = _ToolAccum(
                    partial_index=partial_idx,
                    id=call_id,
                    name=name,
                    arguments_raw=item.get("arguments", "") or "",
                )
                events.push(
                    ToolCallStartEvent(content_index=partial_idx, partial=partial)
                )

        elif kind == "response.output_text.delta":
            wire_idx = int(data.get("output_index", 0))
            state = text_state.get(wire_idx)
            if state is None:
                continue
            delta_text = data.get("delta", "")
            tb = partial.content[state.partial_index]
            if isinstance(tb, TextContent):
                tb.text += delta_text
            events.push(
                TextDeltaEvent(
                    content_index=state.partial_index, delta=delta_text, partial=partial
                )
            )

        elif kind == "response.output_text.done":
            wire_idx = int(data.get("output_index", 0))
            state = text_state.get(wire_idx)
            if state is None:
                continue
            tb = partial.content[state.partial_index]
            text = tb.text if isinstance(tb, TextContent) else ""
            events.push(
                TextEndEvent(
                    content_index=state.partial_index, content=text, partial=partial
                )
            )

        elif kind == "response.reasoning_summary_text.delta":
            wire_idx = int(data.get("output_index", 0))
            state_r = reasoning_state.get(wire_idx)
            if state_r is None:
                continue
            piece = data.get("delta", "")
            tb2 = partial.content[state_r.partial_index]
            if isinstance(tb2, ThinkingContent):
                tb2.thinking += piece
            events.push(
                ThinkingDeltaEvent(
                    content_index=state_r.partial_index,
                    delta=piece,
                    partial=partial,
                )
            )

        elif kind == "response.function_call_arguments.delta":
            wire_idx = int(data.get("output_index", 0))
            tc = tool_state.get(wire_idx)
            if tc is None:
                continue
            frag = data.get("delta", "")
            tc.arguments_raw += frag
            events.push(
                ToolCallDeltaEvent(
                    content_index=tc.partial_index,
                    delta=frag,
                    partial=partial,
                )
            )

        elif kind == "response.output_item.done":
            wire_idx = int(data.get("output_index", 0))
            if wire_idx in reasoning_state:
                state_r = reasoning_state[wire_idx]
                tb2 = partial.content[state_r.partial_index]
                item = data.get("item", {}) or {}
                enc = item.get("encrypted_content") or state_r.encrypted_content
                rid = item.get("id") or state_r.reasoning_id
                if isinstance(tb2, ThinkingContent):
                    sig = {k: v for k, v in (("id", rid), ("encrypted_content", enc)) if v}
                    if sig:
                        tb2.thinking_signature = json.dumps(sig)
                    text = tb2.thinking
                else:
                    text = ""
                events.push(
                    ThinkingEndEvent(
                        content_index=state_r.partial_index,
                        content=text,
                        partial=partial,
                    )
                )
            elif wire_idx in tool_state:
                tc = tool_state[wire_idx]
                args = parse_streaming_json(tc.arguments_raw) if tc.arguments_raw else {}
                finalized = ToolCall(id=tc.id, name=tc.name, arguments=args)
                partial.content[tc.partial_index] = finalized
                events.push(
                    ToolCallEndEvent(
                        content_index=tc.partial_index,
                        tool_call=finalized,
                        partial=partial,
                    )
                )

        elif kind == "response.completed":
            resp = data.get("response", {}) or {}
            stop_reason = resp.get("status") or "completed"
            usage = _parse_usage(resp.get("usage"))
            saw_terminal = True

        elif kind == "response.failed" or kind == "response.error":
            resp = data.get("response", {}) or {}
            err = resp.get("error") or data.get("error") or {}
            raise RuntimeError(
                f"OpenAI Responses error: {err.get('code')}: {err.get('message')}"
            )

    if usage is not None:
        partial.usage = usage
        calculate_cost(model, partial.usage)

    partial.stop_reason = _map_stop_reason(
        stop_reason, partial, saw_terminal=saw_terminal
    )
    if partial.stop_reason in ("stop", "length", "toolUse"):
        events.push(DoneEvent(reason=partial.stop_reason, message=partial))  # type: ignore[arg-type]
    else:
        if partial.error_message is None:
            partial.error_message = "Stream ended without a terminal marker"
        events.push(ErrorEvent(reason="error", error=partial))


def _parse_usage(raw: dict[str, Any] | None) -> Usage | None:
    if not raw:
        return None
    input_tokens = int(raw.get("input_tokens", 0))
    output_tokens = int(raw.get("output_tokens", 0))
    cache_read = 0
    details = raw.get("input_tokens_details") or {}
    if isinstance(details, dict):
        cache_read = int(details.get("cached_tokens", 0) or 0)
    total = int(raw.get("total_tokens", input_tokens + output_tokens))
    # See gateway._usage_from_openai for the cache_read/input subtraction
    # rationale and the max(0, ...) clamp.
    return Usage(
        input=max(0, input_tokens - cache_read),
        output=output_tokens,
        cache_read=cache_read,
        cache_write=0,
        total_tokens=total,
    )


def _map_stop_reason(
    raw: str | None, partial: AssistantMessage, *, saw_terminal: bool
) -> StopReason:
    if raw in ("completed", "stop"):
        if any(getattr(b, "type", None) == "toolCall" for b in partial.content):
            return "toolUse"
        return "stop"
    if raw is None:
        # No response.completed seen -> connection was truncated. (raw is only
        # set inside the response.completed branch alongside saw_terminal=True,
        # so raw is None implies saw_terminal is False; we surface as error.)
        return "error"
    if raw in ("incomplete", "length"):
        return "length"
    return "error"


class _TextAccum:
    __slots__ = ("partial_index",)

    def __init__(self, *, partial_index: int) -> None:
        self.partial_index = partial_index


class _ReasonAccum:
    __slots__ = ("partial_index", "reasoning_id", "encrypted_content")

    def __init__(
        self,
        *,
        partial_index: int,
        reasoning_id: str | None,
        encrypted_content: str | None,
    ) -> None:
        self.partial_index = partial_index
        self.reasoning_id = reasoning_id
        self.encrypted_content = encrypted_content


class _ToolAccum:
    __slots__ = ("partial_index", "id", "name", "arguments_raw")

    def __init__(
        self, *, partial_index: int, id: str, name: str, arguments_raw: str
    ) -> None:
        self.partial_index = partial_index
        self.id = id
        self.name = name
        self.arguments_raw = arguments_raw


register_api_provider(_API, stream, stream_simple, source_id="builtin:openai-responses")


__all__ = ["stream", "stream_simple"]
