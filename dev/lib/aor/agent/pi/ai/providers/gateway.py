"""Eng AI Model Gateway provider (OpenAI `/chat/completions`-compatible).

Python port of the subset of
vendor/pi-mono-upstream/packages/ai/src/providers/openai-completions.ts that
targets a Completions-compatible HTTP endpoint using SSE streaming.

Wire-format notes
-----------------
Chunks arrive as `data: {JSON}\\n\\n`, terminated by `data: [DONE]`:

    {"choices": [{"index": 0, "delta": {"content": "hi"}, "finish_reason": null}]}
    {"choices": [{"index": 0, "delta": {}, "finish_reason": "stop"}]}
    {"usage": {"prompt_tokens": 10, "completion_tokens": 3, "total_tokens": 13}}

Tool-call deltas look like:

    "delta": {"tool_calls": [{"index": 0, "id": "call_1",
                                "function": {"name": "f", "arguments": "{\"a\":"}}]}

The `arguments` field streams as string fragments that concatenate into a
JSON object. We assemble them and emit `toolcall_delta` / `toolcall_end`
events.

The ANTHROPIC-like thinking-as-text and reasoning-effort code paths from
pi-ai are deliberately not ported here; the Gateway doesn't expose them.
"""

from __future__ import annotations

import asyncio
import json
import os
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
    ToolCall,
    ToolCallDeltaEvent,
    ToolCallEndEvent,
    ToolCallStartEvent,
    Usage,
)
from ..utils.json_parse import parse_streaming_json
from ._sse import iter_sse

_API = "openai-completions"
_PROVIDER = "salesforce-gateway"
_DEFAULT_TIMEOUT_S = 120.0


async def stream(
    model: Model,
    context: Context,
    options: StreamOptions | None = None,
) -> AssistantMessageEventStream:
    """Start a streaming call; returns an AssistantMessageEventStream.

    The background task that pumps events is scheduled on the running loop; the
    stream is returned synchronously (from the caller's perspective, once
    awaited) so iteration can begin immediately.
    """
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
    partial = _new_assistant_message(model)
    try:
        api_key = _resolve_api_key(options)
        payload = _build_payload(model, context, options)
        headers = _build_headers(api_key, options)

        # Respect SSL_CERT_FILE for corporate proxies that use a custom CA bundle.
        ssl_cert_file = os.environ.get("SSL_CERT_FILE")
        if ssl_cert_file:
            import ssl as _ssl
            _ssl_ctx = _ssl.create_default_context(cafile=ssl_cert_file)
            verify: bool | _ssl.SSLContext = _ssl_ctx
        else:
            verify = True
        events.push(StartEvent(partial=partial))
        async with httpx.AsyncClient(timeout=_DEFAULT_TIMEOUT_S, verify=verify) as client:
            async with client.stream(
                "POST",
                f"{model.base_url}/v1/chat/completions",
                headers=headers,
                json=payload,
            ) as response:
                response.raise_for_status()
                await _consume(response, partial, events, model)
    except asyncio.CancelledError:
        partial.stop_reason = "aborted"
        events.push(ErrorEvent(reason="aborted", error=partial))
        raise
    except Exception as exc:  # noqa: BLE001 - surface any failure as error event
        partial.stop_reason = "error"
        partial.error_message = str(exc)
        events.push(ErrorEvent(reason="error", error=partial))


def _new_assistant_message(model: Model) -> AssistantMessage:
    return AssistantMessage(
        api=model.api,
        provider=model.provider,
        model=model.id,
        stop_reason="stop",
        timestamp=int(time.time() * 1000),
    )


def _resolve_api_key(options: StreamOptions | SimpleStreamOptions | None) -> str:
    if options and options.api_key:
        return options.api_key
    env = get_env_api_key(_PROVIDER)
    if env:
        return env
    raise RuntimeError(
        "No API key for Salesforce Gateway. Set ENG_AI_MODEL_GW_KEY or pass api_key."
    )


def _build_headers(
    api_key: str, options: StreamOptions | SimpleStreamOptions | None
) -> dict[str, str]:
    headers: dict[str, str] = {
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
        "messages": _context_to_openai_messages(context),
        "stream": True,
        "stream_options": {"include_usage": True},
    }
    if options:
        if options.temperature is not None:
            payload["temperature"] = options.temperature
        if options.max_tokens is not None:
            payload["max_tokens"] = options.max_tokens
    if context.tools:
        payload["tools"] = [_tool_to_openai(tool) for tool in context.tools]
    return payload


def _context_to_openai_messages(context: Context) -> list[dict[str, Any]]:
    messages: list[dict[str, Any]] = []
    if context.system_prompt:
        messages.append({"role": "system", "content": context.system_prompt})
    for msg in context.messages:
        messages.extend(_message_to_openai(msg))
    return messages


def _message_to_openai(msg: Message) -> list[dict[str, Any]]:
    if msg.role == "user":
        content = msg.content if isinstance(msg.content, str) else _text_blocks(msg.content)
        return [{"role": "user", "content": content}]
    if msg.role == "assistant":
        out: dict[str, Any] = {"role": "assistant"}
        text_parts: list[str] = []
        tool_calls: list[dict[str, Any]] = []
        for block in msg.content:
            if block.type == "text":
                text_parts.append(block.text)
            elif block.type == "toolCall":
                tool_calls.append(
                    {
                        "id": block.id,
                        "type": "function",
                        "function": {
                            "name": block.name,
                            "arguments": json.dumps(block.arguments),
                        },
                    }
                )
        if text_parts:
            out["content"] = "".join(text_parts)
        if tool_calls:
            out["tool_calls"] = tool_calls
        if "content" not in out and not tool_calls:
            out["content"] = ""
        return [out]
    if msg.role == "toolResult":
        text = "".join(
            block.text for block in msg.content if getattr(block, "type", None) == "text"
        )
        return [
            {
                "role": "tool",
                "tool_call_id": msg.tool_call_id,
                "content": text,
            }
        ]
    return []


def _text_blocks(blocks: list[Any]) -> str:
    return "".join(b.text for b in blocks if getattr(b, "type", None) == "text")


def _tool_to_openai(tool: Any) -> dict[str, Any]:
    return {
        "type": "function",
        "function": {
            "name": tool.name,
            "description": tool.description,
            "parameters": tool.parameters or {"type": "object", "properties": {}},
        },
    }


async def _consume(
    response: httpx.Response,
    partial: AssistantMessage,
    events: AssistantMessageEventStream,
    model: Model,
) -> None:
    text_index: int | None = None
    text_buffer: list[str] = []
    tool_call_state: dict[int, _ToolCallAccum] = {}
    finish_reason: str | None = None
    usage_raw: dict[str, Any] | None = None
    saw_terminal = False

    async for sse in iter_sse(response):
        data = sse.data.strip()
        if not data:
            continue
        if data == "[DONE]":
            saw_terminal = True
            break
        try:
            chunk = json.loads(data)
        except json.JSONDecodeError:
            continue

        if "usage" in chunk and chunk["usage"]:
            usage_raw = chunk["usage"]

        for choice in chunk.get("choices", []):
            delta = choice.get("delta", {}) or {}
            if "content" in delta and delta["content"]:
                if text_index is None:
                    text_index = len(partial.content)
                    partial.content.append(TextContent(text=""))
                    events.push(TextStartEvent(content_index=text_index, partial=partial))
                piece = delta["content"]
                text_buffer.append(piece)
                text_block = partial.content[text_index]
                if isinstance(text_block, TextContent):
                    text_block.text += piece
                events.push(
                    TextDeltaEvent(
                        content_index=text_index, delta=piece, partial=partial
                    )
                )

            for tc in delta.get("tool_calls", []) or []:
                idx = tc.get("index", 0)
                accum = tool_call_state.get(idx)
                if accum is None:
                    accum = _ToolCallAccum(
                        content_index=len(partial.content),
                        id=tc.get("id") or f"call_{idx}",
                        name="",
                        arguments_raw="",
                    )
                    tool_call_state[idx] = accum
                    partial.content.append(
                        ToolCall(id=accum.id, name="", arguments={})
                    )
                    events.push(
                        ToolCallStartEvent(
                            content_index=accum.content_index, partial=partial
                        )
                    )
                if tc.get("id"):
                    accum.id = tc["id"]
                fn = tc.get("function", {}) or {}
                if fn.get("name"):
                    accum.name += fn["name"]
                if "arguments" in fn and fn["arguments"] is not None:
                    delta_args = fn["arguments"]
                    accum.arguments_raw += delta_args
                    events.push(
                        ToolCallDeltaEvent(
                            content_index=accum.content_index,
                            delta=delta_args,
                            partial=partial,
                        )
                    )

            if choice.get("finish_reason"):
                finish_reason = choice["finish_reason"]
                saw_terminal = True

    # Finalize text block
    if text_index is not None:
        text_block = partial.content[text_index]
        if isinstance(text_block, TextContent):
            events.push(
                TextEndEvent(
                    content_index=text_index, content=text_block.text, partial=partial
                )
            )

    # Finalize tool calls
    for accum in tool_call_state.values():
        try:
            args = json.loads(accum.arguments_raw) if accum.arguments_raw else {}
        except json.JSONDecodeError:
            args = parse_streaming_json(accum.arguments_raw)
        partial.content[accum.content_index] = ToolCall(
            id=accum.id, name=accum.name, arguments=args
        )
        events.push(
            ToolCallEndEvent(
                content_index=accum.content_index,
                tool_call=ToolCall(id=accum.id, name=accum.name, arguments=args),
                partial=partial,
            )
        )

    # Usage + cost
    if usage_raw:
        partial.usage = _usage_from_openai(usage_raw)
        calculate_cost(model, partial.usage)

    partial.stop_reason = _map_stop_reason(finish_reason, saw_terminal=saw_terminal)
    reason = partial.stop_reason
    if reason in ("stop", "length", "toolUse"):
        events.push(DoneEvent(reason=reason, message=partial))  # type: ignore[arg-type]
    else:
        if partial.error_message is None:
            partial.error_message = "Stream ended without a terminal marker"
        events.push(ErrorEvent(reason="error", error=partial))


def _map_stop_reason(finish: str | None, *, saw_terminal: bool) -> StopReason:
    if finish == "stop":
        return "stop"
    if finish == "length":
        return "length"
    if finish in ("tool_calls", "function_call"):
        return "toolUse"
    # finish_reason may legitimately be None when the upstream only emits
    # `[DONE]` without a prior finish_reason chunk. Treat that as "stop".
    # Missing both (saw_terminal is False) means the connection was
    # truncated before any terminal signal — surface as error so callers
    # can distinguish it from a clean stop.
    if finish is None:
        return "stop" if saw_terminal else "error"
    return "error"


def _usage_from_openai(usage: dict[str, Any]) -> Usage:
    prompt = int(usage.get("prompt_tokens", 0))
    completion = int(usage.get("completion_tokens", 0))
    total = int(usage.get("total_tokens", prompt + completion))
    cache_read = 0
    details = usage.get("prompt_tokens_details") or {}
    if isinstance(details, dict):
        cache_read = int(details.get("cached_tokens", 0) or 0)
    # Most APIs report cache_read as a subset of prompt_tokens, so we subtract
    # to avoid double-counting. Clamp to 0 in case an upstream ever reports
    # cache_read > prompt (defensive; not currently observed in practice).
    return Usage(
        input=max(0, prompt - cache_read),
        output=completion,
        cache_read=cache_read,
        cache_write=0,
        total_tokens=total,
    )


class _ToolCallAccum:
    __slots__ = ("content_index", "id", "name", "arguments_raw")

    def __init__(
        self, *, content_index: int, id: str, name: str, arguments_raw: str
    ) -> None:
        self.content_index = content_index
        self.id = id
        self.name = name
        self.arguments_raw = arguments_raw


register_api_provider(_API, stream, stream_simple, source_id="builtin:gateway")


__all__ = ["stream", "stream_simple"]
