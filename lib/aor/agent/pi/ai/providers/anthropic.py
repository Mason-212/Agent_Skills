"""Anthropic Messages API provider (streaming).

Python port of the subset of
vendor/pi-mono-upstream/packages/ai/src/providers/anthropic.ts targeting
the public `/v1/messages` endpoint with SSE streaming.

Event types on the wire
-----------------------
- `message_start` - envelope with usage/input tokens
- `content_block_start` - {index, content_block: {type: "text"|"thinking"|"tool_use", ...}}
- `content_block_delta` - {index, delta: {type: "text_delta"|"thinking_delta"|"input_json_delta"}}
- `content_block_stop` - {index}
- `message_delta` - {delta: {stop_reason, stop_sequence}, usage: {output_tokens}}
- `message_stop`

Tool-use arguments stream as `input_json_delta.partial_json` fragments.
Thinking blocks stream as `thinking_delta.thinking` fragments and optionally
carry a `signature_delta` for multi-turn replay.
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
from ._transforms import (
    build_tool_name_map,
    normalize_tool_name,
    resolve_original_tool_name,
)

_API = "anthropic-messages"
_PROVIDER = "anthropic"
_DEFAULT_TIMEOUT_S = 180.0
_ANTHROPIC_VERSION = "2023-06-01"


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
        wire_to_original = build_tool_name_map(context.tools or [])
        payload = _build_payload(model, context, options, wire_to_original)
        headers = _build_headers(api_key, options)

        events.push(StartEvent(partial=partial))
        async with httpx.AsyncClient(timeout=_DEFAULT_TIMEOUT_S) as client:
            async with client.stream(
                "POST",
                f"{model.base_url}/messages",
                headers=headers,
                json=payload,
            ) as response:
                response.raise_for_status()
                await _consume(response, partial, events, model, wire_to_original)
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
        "No Anthropic API key. Set ANTHROPIC_API_KEY (or ANTHROPIC_OAUTH_TOKEN) "
        "or pass api_key in StreamOptions."
    )


def _build_headers(
    api_key: str, options: StreamOptions | SimpleStreamOptions | None
) -> dict[str, str]:
    headers = {
        "x-api-key": api_key,
        "anthropic-version": _ANTHROPIC_VERSION,
        "content-type": "application/json",
        "accept": "text/event-stream",
    }
    if options and options.headers:
        headers.update(options.headers)
    return headers


def _build_payload(
    model: Model,
    context: Context,
    options: StreamOptions | SimpleStreamOptions | None,
    wire_to_original: dict[str, str],
) -> dict[str, Any]:
    max_tokens = (
        options.max_tokens
        if options and options.max_tokens is not None
        else min(model.max_tokens, 4096)
    )
    payload: dict[str, Any] = {
        "model": model.id,
        "max_tokens": max_tokens,
        "messages": _context_to_anthropic_messages(context),
        "stream": True,
    }
    if context.system_prompt:
        payload["system"] = context.system_prompt
    if options and options.temperature is not None:
        payload["temperature"] = options.temperature
    if context.tools:
        original_to_wire = {v: k for k, v in wire_to_original.items()}
        payload["tools"] = [
            _tool_to_anthropic(tool, original_to_wire) for tool in context.tools
        ]
    if isinstance(options, SimpleStreamOptions) and options.reasoning:
        payload["thinking"] = _map_reasoning_to_thinking(
            options.reasoning, options.thinking_budgets
        )
    return payload


def _tool_to_anthropic(tool: Tool, original_to_wire: dict[str, str]) -> dict[str, Any]:
    wire_name = original_to_wire.get(tool.name, normalize_tool_name(tool.name))
    return {
        "name": wire_name,
        "description": tool.description,
        "input_schema": tool.parameters or {"type": "object", "properties": {}},
    }


_ANTHROPIC_DEFAULT_THINKING_BUDGETS: dict[str, int] = {
    "minimal": 1024,
    "low": 2048,
    "medium": 8192,
    "high": 16384,
    "xhigh": 32768,
}


def _map_reasoning_to_thinking(
    level: str,
    overrides: dict[str, int] | None = None,
) -> dict[str, Any]:
    """Translate a SimpleStreamOptions reasoning level to Anthropic's thinking block.

    When `overrides` (the caller's `SimpleStreamOptions.thinking_budgets`)
    contains an entry for this level, it wins over the built-in default.
    """
    budget = (overrides or {}).get(level)
    if budget is None:
        budget = _ANTHROPIC_DEFAULT_THINKING_BUDGETS.get(level, 2048)
    return {"type": "enabled", "budget_tokens": budget}


def _context_to_anthropic_messages(context: Context) -> list[dict[str, Any]]:
    messages: list[dict[str, Any]] = []
    for msg in context.messages:
        messages.extend(_message_to_anthropic(msg))
    return _merge_adjacent_tool_results(messages)


def _message_to_anthropic(msg: Message) -> list[dict[str, Any]]:
    if msg.role == "user":
        if isinstance(msg.content, str):
            return [{"role": "user", "content": msg.content}]
        content = [{"type": "text", "text": b.text} for b in msg.content]
        return [{"role": "user", "content": content}]
    if msg.role == "assistant":
        blocks: list[dict[str, Any]] = []
        for block in msg.content:
            if block.type == "text":
                blocks.append({"type": "text", "text": block.text})
            elif block.type == "thinking":
                thinking_block: dict[str, Any] = {
                    "type": "thinking",
                    "thinking": block.thinking,
                }
                if block.thinking_signature:
                    thinking_block["signature"] = block.thinking_signature
                blocks.append(thinking_block)
            elif block.type == "toolCall":
                blocks.append(
                    {
                        "type": "tool_use",
                        "id": block.id,
                        "name": block.name,
                        "input": block.arguments,
                    }
                )
        return [{"role": "assistant", "content": blocks}]
    if msg.role == "toolResult":
        text = "".join(
            b.text for b in msg.content if getattr(b, "type", None) == "text"
        )
        return [
            {
                "role": "user",
                "content": [
                    {
                        "type": "tool_result",
                        "tool_use_id": msg.tool_call_id,
                        "content": text,
                        "is_error": msg.is_error,
                    }
                ],
            }
        ]
    return []


def _merge_adjacent_tool_results(messages: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Anthropic requires consecutive tool_result blocks in one user message."""
    merged: list[dict[str, Any]] = []
    for msg in messages:
        if (
            merged
            and merged[-1]["role"] == "user"
            and msg["role"] == "user"
            and isinstance(merged[-1].get("content"), list)
            and isinstance(msg.get("content"), list)
            and _all_tool_results(merged[-1]["content"])
            and _all_tool_results(msg["content"])
        ):
            merged[-1]["content"].extend(msg["content"])
        else:
            merged.append(msg)
    return merged


def _all_tool_results(blocks: list[Any]) -> bool:
    return all(
        isinstance(b, dict) and b.get("type") == "tool_result" for b in blocks
    )


async def _consume(
    response: httpx.Response,
    partial: AssistantMessage,
    events: AssistantMessageEventStream,
    model: Model,
    wire_to_original: dict[str, str],
) -> None:
    content_index_to_partial_index: dict[int, int] = {}
    tool_call_state: dict[int, _ToolAccum] = {}
    text_state: dict[int, _TextAccum] = {}
    thinking_state: dict[int, _ThinkingAccum] = {}
    stop_reason: str | None = None
    usage_input = 0
    usage_cache_read = 0
    usage_cache_write = 0
    usage_output = 0
    saw_terminal = False

    async for sse in iter_sse(response):
        if sse.event in (None, "ping"):
            continue
        if not sse.data:
            continue
        try:
            data = json.loads(sse.data)
        except json.JSONDecodeError:
            continue

        kind = sse.event or data.get("type", "")

        if kind == "message_start":
            usage = data.get("message", {}).get("usage", {}) or {}
            usage_input = int(usage.get("input_tokens", 0))
            usage_cache_read = int(usage.get("cache_read_input_tokens", 0) or 0)
            usage_cache_write = int(usage.get("cache_creation_input_tokens", 0) or 0)

        elif kind == "content_block_start":
            wire_index = int(data.get("index", 0))
            block = data.get("content_block", {}) or {}
            btype = block.get("type")
            partial_index = len(partial.content)
            content_index_to_partial_index[wire_index] = partial_index
            if btype == "text":
                partial.content.append(TextContent(text=""))
                text_state[wire_index] = _TextAccum(partial_index=partial_index, buffer=[])
                events.push(
                    TextStartEvent(content_index=partial_index, partial=partial)
                )
            elif btype == "thinking":
                partial.content.append(ThinkingContent(thinking=""))
                thinking_state[wire_index] = _ThinkingAccum(
                    partial_index=partial_index, buffer=[], signature=None
                )
                events.push(
                    ThinkingStartEvent(content_index=partial_index, partial=partial)
                )
            elif btype == "tool_use":
                wire_name = block.get("name", "")
                original_name = resolve_original_tool_name(wire_name, wire_to_original)
                tool_id = block.get("id", f"call_{wire_index}")
                partial.content.append(
                    ToolCall(id=tool_id, name=original_name, arguments={})
                )
                tool_call_state[wire_index] = _ToolAccum(
                    partial_index=partial_index,
                    id=tool_id,
                    name=original_name,
                    arguments_raw="",
                )
                events.push(
                    ToolCallStartEvent(content_index=partial_index, partial=partial)
                )

        elif kind == "content_block_delta":
            wire_index = int(data.get("index", 0))
            delta = data.get("delta", {}) or {}
            dtype = delta.get("type")
            partial_index = content_index_to_partial_index.get(wire_index)
            if partial_index is None:
                continue
            if dtype == "text_delta":
                text = delta.get("text", "")
                state = text_state.get(wire_index)
                if state is None:
                    continue
                state.buffer.append(text)
                tb = partial.content[state.partial_index]
                if isinstance(tb, TextContent):
                    tb.text += text
                events.push(
                    TextDeltaEvent(
                        content_index=state.partial_index, delta=text, partial=partial
                    )
                )
            elif dtype == "thinking_delta":
                piece = delta.get("thinking", "")
                state_t = thinking_state.get(wire_index)
                if state_t is None:
                    continue
                state_t.buffer.append(piece)
                tb2 = partial.content[state_t.partial_index]
                if isinstance(tb2, ThinkingContent):
                    tb2.thinking += piece
                events.push(
                    ThinkingDeltaEvent(
                        content_index=state_t.partial_index,
                        delta=piece,
                        partial=partial,
                    )
                )
            elif dtype == "signature_delta":
                state_t = thinking_state.get(wire_index)
                if state_t:
                    state_t.signature = delta.get("signature")
            elif dtype == "input_json_delta":
                frag = delta.get("partial_json", "")
                tc = tool_call_state.get(wire_index)
                if tc is None:
                    continue
                tc.arguments_raw += frag
                events.push(
                    ToolCallDeltaEvent(
                        content_index=tc.partial_index,
                        delta=frag,
                        partial=partial,
                    )
                )

        elif kind == "content_block_stop":
            wire_index = int(data.get("index", 0))
            if wire_index in text_state:
                state = text_state[wire_index]
                tb = partial.content[state.partial_index]
                text = tb.text if isinstance(tb, TextContent) else ""
                events.push(
                    TextEndEvent(
                        content_index=state.partial_index,
                        content=text,
                        partial=partial,
                    )
                )
            elif wire_index in thinking_state:
                state_t = thinking_state[wire_index]
                tb2 = partial.content[state_t.partial_index]
                if isinstance(tb2, ThinkingContent):
                    tb2.thinking_signature = state_t.signature
                    text = tb2.thinking
                else:
                    text = ""
                events.push(
                    ThinkingEndEvent(
                        content_index=state_t.partial_index,
                        content=text,
                        partial=partial,
                    )
                )
            elif wire_index in tool_call_state:
                tc = tool_call_state[wire_index]
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

        elif kind == "message_delta":
            delta = data.get("delta", {}) or {}
            if delta.get("stop_reason"):
                stop_reason = delta["stop_reason"]
                saw_terminal = True
            usage_m = data.get("usage", {}) or {}
            if "output_tokens" in usage_m:
                usage_output = int(usage_m["output_tokens"])

        elif kind == "message_stop":
            saw_terminal = True
            break

        elif kind == "error":
            err = data.get("error", {}) or {}
            raise RuntimeError(
                f"Anthropic API error: {err.get('type')}: {err.get('message')}"
            )

    partial.usage = Usage(
        input=usage_input,
        output=usage_output,
        cache_read=usage_cache_read,
        cache_write=usage_cache_write,
        total_tokens=usage_input + usage_output + usage_cache_read + usage_cache_write,
    )
    calculate_cost(model, partial.usage)

    partial.stop_reason = _map_stop_reason(stop_reason, saw_terminal=saw_terminal)
    if partial.stop_reason in ("stop", "length", "toolUse"):
        events.push(DoneEvent(reason=partial.stop_reason, message=partial))  # type: ignore[arg-type]
    else:
        if partial.error_message is None:
            partial.error_message = "Stream ended without a terminal marker"
        events.push(ErrorEvent(reason="error", error=partial))


def _map_stop_reason(raw: str | None, *, saw_terminal: bool) -> StopReason:
    if raw == "end_turn":
        return "stop"
    if raw == "max_tokens":
        return "length"
    if raw == "tool_use":
        return "toolUse"
    if raw == "stop_sequence":
        return "stop"
    # raw is None and no terminal marker observed => truncated stream.
    if raw is None:
        return "stop" if saw_terminal else "error"
    return "error"


class _TextAccum:
    __slots__ = ("partial_index", "buffer")

    def __init__(self, *, partial_index: int, buffer: list[str]) -> None:
        self.partial_index = partial_index
        self.buffer = buffer


class _ThinkingAccum:
    __slots__ = ("partial_index", "buffer", "signature")

    def __init__(
        self, *, partial_index: int, buffer: list[str], signature: str | None
    ) -> None:
        self.partial_index = partial_index
        self.buffer = buffer
        self.signature = signature


class _ToolAccum:
    __slots__ = ("partial_index", "id", "name", "arguments_raw")

    def __init__(
        self, *, partial_index: int, id: str, name: str, arguments_raw: str
    ) -> None:
        self.partial_index = partial_index
        self.id = id
        self.name = name
        self.arguments_raw = arguments_raw


register_api_provider(_API, stream, stream_simple, source_id="builtin:anthropic")


__all__ = ["stream", "stream_simple"]
