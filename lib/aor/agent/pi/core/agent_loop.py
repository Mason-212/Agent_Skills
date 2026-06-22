"""Stateless agent-loop engine.

Python port of `vendor/pi-mono-upstream/packages/agent/src/agent-loop.ts`.

Public surface
--------------
- `agent_loop(prompts, context, config, signal=None, stream_fn=None)`
- `agent_loop_continue(context, config, signal=None, stream_fn=None)`

Both are synchronous factory functions that return an
`EventStream[AgentEvent, list[AgentMessage]]` and spawn an `asyncio.Task`
that drives the loop. They must be called from inside a running event loop
(same constraint as the upstream TS version, which relies on promises).

Semantics preserved verbatim from the TS source:
- Outer `while True` / inner `while (hasMoreToolCalls or pending)` structure.
- `firstTurn` suppression to avoid emitting a second `turn_start` after the
  entry-point helpers already emitted one.
- Initial steering poll before the first assistant call.
- Steering preemption mid-tool-execution: remaining tool calls are replaced
  with skipped-result messages and steering is returned to the outer loop as
  `pendingMessages`.
- Tool-result message construction matches upstream exactly (including the
  synthetic "Skipped due to queued user message." text on preempted tools).
"""

from __future__ import annotations

import asyncio
import inspect
from typing import Any

from agent.pi.ai.event_stream import EventStream
from agent.pi.ai.stream import stream_simple
from agent.pi.ai.types import (
    AssistantMessage,
    Context,
    TextContent,
    ToolCall,
    ToolResultMessage,
)
from agent.pi.ai.validation import validate_tool_arguments
from agent.pi.core._internal import now_ms
from agent.pi.core.types import (
    AbortSignal,
    AgentContext,
    AgentEvent,
    AgentLoopConfig,
    AgentMessage,
    AgentTool,
    AgentToolResult,
    StreamFn,
)

AgentEventStream = EventStream[AgentEvent, list[AgentMessage]]


STEERING_SKIP_TEXT = "Skipped due to queued user message."
"""Sentinel text written into preempted tool-call results.

Verbatim from upstream `pi-agent-core`. Preserved for bug-for-bug
compatibility with any client that string-matches on it; treat as a
stable wire constant rather than a user-facing message.
"""


# ---------------------------------------------------------------------------
# Public entry points
# ---------------------------------------------------------------------------


def agent_loop(
    prompts: list[AgentMessage],
    context: AgentContext,
    config: AgentLoopConfig,
    signal: AbortSignal | None = None,
    stream_fn: StreamFn | None = None,
) -> AgentEventStream:
    """Start an agent loop with new prompt message(s).

    Each prompt is appended to the context, `agent_start` + `turn_start` are
    emitted, and `message_start`/`message_end` pairs are emitted for every
    prompt before the first assistant call (so UIs can render user input
    immediately).
    """

    stream = _create_agent_stream()

    async def _driver() -> None:
        new_messages: list[AgentMessage] = list(prompts)
        current_context = context.model_copy(
            update={"messages": [*context.messages, *prompts]}
        )

        stream.push(_mk("agent_start"))
        stream.push(_mk("turn_start"))
        for prompt in prompts:
            stream.push(_mk("message_start", message=prompt))
            stream.push(_mk("message_end", message=prompt))

        try:
            await _run_loop(current_context, new_messages, config, signal, stream, stream_fn)
        except asyncio.CancelledError:
            # Always terminate the stream before re-raising so any consumer
            # that isn't itself being cancelled (e.g. a direct `agent_loop()`
            # caller using stream.cancel()) unblocks promptly instead of
            # waiting on an empty queue forever.
            stream.fail(asyncio.CancelledError())
            raise
        except Exception as exc:  # noqa: BLE001 — match upstream's catch-all behaviour
            stream.fail(exc)

    # Retain a strong reference to the driver task on the stream so it
    # cannot be garbage-collected mid-flight (asyncio only keeps weak
    # refs to scheduled tasks; see asyncio.create_task docs).
    stream.set_task(asyncio.create_task(_driver()))
    return stream


def agent_loop_continue(
    context: AgentContext,
    config: AgentLoopConfig,
    signal: AbortSignal | None = None,
    stream_fn: StreamFn | None = None,
) -> AgentEventStream:
    """Continue the loop from existing context without adding a new message.

    The last message in `context` must not be an assistant message — providers
    reject requests where the assistant would "speak" two turns in a row.
    """

    if not context.messages:
        raise ValueError("Cannot continue: no messages in context")
    if context.messages[-1].role == "assistant":
        raise ValueError("Cannot continue from message role: assistant")

    stream = _create_agent_stream()

    async def _driver() -> None:
        new_messages: list[AgentMessage] = []
        current_context = context.model_copy(update={"messages": list(context.messages)})

        stream.push(_mk("agent_start"))
        stream.push(_mk("turn_start"))

        try:
            await _run_loop(current_context, new_messages, config, signal, stream, stream_fn)
        except asyncio.CancelledError:
            stream.fail(asyncio.CancelledError())
            raise
        except Exception as exc:  # noqa: BLE001
            stream.fail(exc)

    stream.set_task(asyncio.create_task(_driver()))
    return stream


# ---------------------------------------------------------------------------
# Internals
# ---------------------------------------------------------------------------


def _create_agent_stream() -> AgentEventStream:
    return EventStream[AgentEvent, list[AgentMessage]](
        is_complete=lambda e: e.type == "agent_end",
        extract_result=lambda e: e.messages if e.type == "agent_end" else [],
    )


def _mk(event_type: str, **fields: Any) -> AgentEvent:
    """Construct an `AgentEvent` by discriminator.

    Lazily imported to avoid circular typing cost; the map is tiny.
    """
    from agent.pi.core.types import (
        AgentEnd,
        AgentStart,
        MessageEnd,
        MessageStart,
        MessageUpdate,
        ToolExecutionEnd,
        ToolExecutionStart,
        ToolExecutionUpdate,
        TurnEnd,
        TurnStart,
    )

    cls_map: dict[str, type] = {
        "agent_start": AgentStart,
        "agent_end": AgentEnd,
        "turn_start": TurnStart,
        "turn_end": TurnEnd,
        "message_start": MessageStart,
        "message_update": MessageUpdate,
        "message_end": MessageEnd,
        "tool_execution_start": ToolExecutionStart,
        "tool_execution_update": ToolExecutionUpdate,
        "tool_execution_end": ToolExecutionEnd,
    }
    return cls_map[event_type](**fields)  # type: ignore[return-value]


async def _maybe_await(value: Any) -> Any:
    """Treat values as awaitable-or-not (mirrors TS `await` being a no-op on non-promises)."""
    if inspect.isawaitable(value):
        return await value
    return value


async def _run_loop(
    current_context: AgentContext,
    new_messages: list[AgentMessage],
    config: AgentLoopConfig,
    signal: AbortSignal | None,
    stream: AgentEventStream,
    stream_fn: StreamFn | None,
) -> None:
    """Core loop logic shared by `agent_loop` and `agent_loop_continue`."""

    first_turn = True
    pending_messages: list[AgentMessage] = []
    if config.get_steering_messages is not None:
        pending_messages = list(await config.get_steering_messages())

    while True:  # outer loop — re-enters when follow-up messages arrive
        has_more_tool_calls = True
        steering_after_tools: list[AgentMessage] | None = None

        while has_more_tool_calls or pending_messages:
            if not first_turn:
                stream.push(_mk("turn_start"))
            else:
                first_turn = False

            # Inject pending messages (steering / follow-up) before the assistant call.
            if pending_messages:
                for message in pending_messages:
                    stream.push(_mk("message_start", message=message))
                    stream.push(_mk("message_end", message=message))
                    current_context.messages.append(message)
                    new_messages.append(message)
                pending_messages = []

            assistant_message = await _stream_assistant_response(
                current_context, config, signal, stream, stream_fn
            )
            new_messages.append(assistant_message)

            if assistant_message.stop_reason in ("error", "aborted"):
                stream.push(_mk("turn_end", message=assistant_message, toolResults=[]))
                stream.push(_mk("agent_end", messages=new_messages))
                stream.end(new_messages)
                return

            tool_calls = [c for c in assistant_message.content if c.type == "toolCall"]
            has_more_tool_calls = len(tool_calls) > 0

            tool_results: list[ToolResultMessage] = []
            if has_more_tool_calls:
                tool_results, steering_after_tools = await _execute_tool_calls(
                    current_context.tools,
                    assistant_message,
                    signal,
                    stream,
                    config.get_steering_messages,
                )
                for result in tool_results:
                    current_context.messages.append(result)
                    new_messages.append(result)

            stream.push(
                _mk("turn_end", message=assistant_message, toolResults=tool_results)
            )

            if steering_after_tools:
                pending_messages = steering_after_tools
                steering_after_tools = None
            elif config.get_steering_messages is not None:
                pending_messages = list(await config.get_steering_messages())
            else:
                pending_messages = []

        # Inner loop drained. Check for follow-up.
        follow_ups: list[AgentMessage] = []
        if config.get_follow_up_messages is not None:
            follow_ups = list(await config.get_follow_up_messages())

        if follow_ups:
            pending_messages = follow_ups
            continue
        break

    stream.push(_mk("agent_end", messages=new_messages))
    stream.end(new_messages)


async def _stream_assistant_response(
    context: AgentContext,
    config: AgentLoopConfig,
    signal: AbortSignal | None,
    stream: AgentEventStream,
    stream_fn: StreamFn | None,
) -> AssistantMessage:
    """Stream one assistant response and return its final `AssistantMessage`.

    Matches the TS helper: applies optional `transform_context`, converts the
    `AgentMessage[]` to the LLM's `Message[]` via `convert_to_llm`, builds a
    `Context`, resolves the API key, and drives `stream_fn` (defaulting to
    `stream_simple`). Emits `message_start` on the `start` event, `message_update`
    for streaming deltas, and `message_end` on terminal `done`/`error` events.
    """

    messages: list[AgentMessage] = list(context.messages)
    if config.transform_context is not None:
        messages = list(await config.transform_context(messages, signal))

    llm_messages = await _maybe_await(config.convert_to_llm(messages))

    llm_context = Context(
        system_prompt=context.system_prompt or None,
        messages=llm_messages,
        tools=list(context.tools) if context.tools else None,
    )

    fn = stream_fn or stream_simple

    resolved_key: str | None = None
    if config.get_api_key is not None:
        resolved_key = await _maybe_await(config.get_api_key(config.model.provider))
    if resolved_key is None:
        resolved_key = config.api_key

    options = config.to_simple_stream_options(api_key=resolved_key)
    response = await fn(config.model, llm_context, options)

    partial_message: AssistantMessage | None = None
    added_partial = False

    async for event in response:
        if signal is not None and signal.aborted:
            break
        etype = event.type

        if etype == "start":
            partial_message = event.partial  # type: ignore[attr-defined]
            context.messages.append(partial_message)
            added_partial = True
            stream.push(_mk("message_start", message=partial_message.model_copy()))
            continue

        if etype in (
            "text_start",
            "text_delta",
            "text_end",
            "thinking_start",
            "thinking_delta",
            "thinking_end",
            "toolcall_start",
            "toolcall_delta",
            "toolcall_end",
        ):
            if partial_message is not None:
                partial_message = event.partial  # type: ignore[attr-defined]
                context.messages[-1] = partial_message
                stream.push(
                    _mk(
                        "message_update",
                        message=partial_message.model_copy(),
                        assistantMessageEvent=event,
                    )
                )
            continue

        if etype in ("done", "error"):
            final_message = await response.result()
            if added_partial:
                context.messages[-1] = final_message
            else:
                context.messages.append(final_message)
                stream.push(_mk("message_start", message=final_message.model_copy()))
            stream.push(_mk("message_end", message=final_message))
            return final_message

    return await response.result()


async def _execute_tool_calls(
    tools: list[AgentTool] | None,
    assistant_message: AssistantMessage,
    signal: AbortSignal | None,
    stream: AgentEventStream,
    get_steering_messages: Any,
) -> tuple[list[ToolResultMessage], list[AgentMessage] | None]:
    """Execute each tool call in order; preempt on steering messages.

    Returns `(tool_results, steering_messages_or_None)`.
    """

    tool_calls: list[ToolCall] = [
        c for c in assistant_message.content if c.type == "toolCall"
    ]
    results: list[ToolResultMessage] = []
    steering_messages: list[AgentMessage] | None = None

    for index, tool_call in enumerate(tool_calls):
        tool = next((t for t in (tools or []) if t.name == tool_call.name), None)

        stream.push(
            _mk(
                "tool_execution_start",
                toolCallId=tool_call.id,
                toolName=tool_call.name,
                args=tool_call.arguments,
            )
        )

        is_error = False
        try:
            if tool is None:
                raise RuntimeError(f"Tool {tool_call.name} not found")

            validated = validate_tool_arguments(tool, tool_call)

            def _on_update(partial: AgentToolResult, _tc: ToolCall = tool_call) -> None:
                stream.push(
                    _mk(
                        "tool_execution_update",
                        toolCallId=_tc.id,
                        toolName=_tc.name,
                        args=_tc.arguments,
                        partialResult=partial,
                    )
                )

            result = await tool.execute(tool_call.id, validated, signal, _on_update)
        except Exception as exc:  # noqa: BLE001 — mirror TS catch-all
            result = AgentToolResult(
                content=[TextContent(type="text", text=str(exc))],
                details={},
            )
            is_error = True

        stream.push(
            _mk(
                "tool_execution_end",
                toolCallId=tool_call.id,
                toolName=tool_call.name,
                result=result,
                isError=is_error,
            )
        )

        tool_result_message = ToolResultMessage(
            role="toolResult",
            tool_call_id=tool_call.id,
            tool_name=tool_call.name,
            content=result.content,
            is_error=is_error,
            timestamp=now_ms(),
        )
        results.append(tool_result_message)
        stream.push(_mk("message_start", message=tool_result_message))
        stream.push(_mk("message_end", message=tool_result_message))

        # Steering preemption: if the user injected messages mid-tool-execution,
        # skip remaining tools and return the steering up to the outer loop.
        if get_steering_messages is not None:
            steering = list(await get_steering_messages())
            if steering:
                steering_messages = steering
                for skipped in tool_calls[index + 1 :]:
                    results.append(_skip_tool_call(skipped, stream))
                break

    return results, steering_messages


def _skip_tool_call(tool_call: ToolCall, stream: AgentEventStream) -> ToolResultMessage:
    """Synthesize a skipped-result for a preempted tool call."""

    result = AgentToolResult(
        content=[TextContent(type="text", text=STEERING_SKIP_TEXT)],
        details={},
    )
    stream.push(
        _mk(
            "tool_execution_start",
            toolCallId=tool_call.id,
            toolName=tool_call.name,
            args=tool_call.arguments,
        )
    )
    stream.push(
        _mk(
            "tool_execution_end",
            toolCallId=tool_call.id,
            toolName=tool_call.name,
            result=result,
            isError=True,
        )
    )
    tool_result_message = ToolResultMessage(
        role="toolResult",
        tool_call_id=tool_call.id,
        tool_name=tool_call.name,
        content=result.content,
        is_error=True,
        timestamp=now_ms(),
    )
    stream.push(_mk("message_start", message=tool_result_message))
    stream.push(_mk("message_end", message=tool_result_message))
    return tool_result_message


__all__ = [
    "AgentEventStream",
    "STEERING_SKIP_TEXT",
    "agent_loop",
    "agent_loop_continue",
]
