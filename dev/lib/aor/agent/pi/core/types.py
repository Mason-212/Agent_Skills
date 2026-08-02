"""Core types for `agent.pi.core`.

Python port of `vendor/pi-mono-upstream/packages/agent/src/types.ts`.

Design notes
------------
- **AgentMessage** is a direct alias for the `agent.pi.ai` `Message`
  discriminated union (user / assistant / toolResult). Upstream's TS declares
  an extension seam (`CustomAgentMessages[keyof CustomAgentMessages]`) via
  declaration merging; in Python we pick the simplest faithful port — reusing
  `Message` — and document the extension seam here. Downstream code that needs
  custom agent-only message shapes can widen this alias in its own module, or
  in the future this can be widened to `Message | CustomMessageBase` without
  breaking existing callers.

- **AbortSignal / AbortController** are thin wrappers over `asyncio.Event`.
  The upstream loop checks `signal.aborted` at choke points and forwards the
  signal into tools. A wrapper keeps the TS call-sites translatable 1:1
  (`signal.aborted`, `controller.abort()`) while still playing well with
  `asyncio.Task.cancel()` — `Agent.abort()` will both set the signal and rely
  on task cancellation for the in-flight `streamFn` call.

- **Callables** on `AgentLoopConfig` and `AgentTool` are typed via `Callable`
  annotations and Pydantic's `arbitrary_types_allowed=True`; Pydantic will not
  attempt to validate them.

- `ThinkingLevel` adds `"off"` relative to `agent.pi.ai.types` because
  agent-core exposes "off" as a first-class user-visible state; the loop maps
  "off" to `reasoning=None` before calling `stream_simple`.
"""

from __future__ import annotations

import asyncio
from typing import Annotated, Any, Awaitable, Callable, Literal, Protocol, Union

from pydantic import BaseModel, ConfigDict, Field

from agent.pi.ai.event_stream import AssistantMessageEventStream
from agent.pi.ai.types import (
    AssistantMessage,
    AssistantMessageEvent,
    Context,
    Message,
    Model,
    SimpleStreamOptions,
    TextContent,
    Tool,
    ToolCall,
    ToolResultMessage,
    Transport,
    UserMessage,
)

# ---------------------------------------------------------------------------
# AgentMessage
# ---------------------------------------------------------------------------

AgentMessage = Message
"""Alias for the LLM message union. See module docstring for the extension seam."""


# ---------------------------------------------------------------------------
# ThinkingLevel
# ---------------------------------------------------------------------------

ThinkingLevel = Literal["off", "minimal", "low", "medium", "high", "xhigh"]
"""Thinking/reasoning level. Agent-core adds "off"; the loop maps it to no reasoning."""


# ---------------------------------------------------------------------------
# Abort plumbing
# ---------------------------------------------------------------------------


class AbortSignal:
    """Read-only view on an abort event.

    Mirrors `AbortSignal.aborted`. Tools can also `await signal.wait()` to
    cooperatively wake up as soon as the user requests abort.
    """

    def __init__(self, event: asyncio.Event) -> None:
        self._event = event

    @property
    def aborted(self) -> bool:
        return self._event.is_set()

    async def wait(self) -> None:
        """Block until aborted. Useful for `asyncio.wait(..., FIRST_COMPLETED)`."""
        await self._event.wait()


class AbortController:
    """Paired writer for `AbortSignal`.

    ``controller.abort()`` is idempotent; subsequent calls are no-ops.
    """

    def __init__(self) -> None:
        self._event = asyncio.Event()
        self.signal = AbortSignal(self._event)

    def abort(self) -> None:
        self._event.set()


# ---------------------------------------------------------------------------
# Tool types
# ---------------------------------------------------------------------------


class AgentToolResult(BaseModel):
    """Result returned by `AgentTool.execute`.

    `content` is restricted to text blocks in this port (image content is
    deferred with the rest of the pi-ai image scope). `details` is an opaque
    payload surfaced to UIs / logs.
    """

    content: list[TextContent] = Field(default_factory=list)
    details: Any = None

    model_config = ConfigDict(arbitrary_types_allowed=True)


AgentToolUpdateCallback = Callable[[AgentToolResult], None]
"""Callback invoked by a tool to stream partial progress."""


ToolExecuteFn = Callable[
    [str, dict[str, Any], "AbortSignal | None", "AgentToolUpdateCallback | None"],
    Awaitable[AgentToolResult],
]
"""Async tool implementation.

Signature: `(tool_call_id, validated_args, signal, on_update) -> AgentToolResult`.
"""


class AgentTool(Tool):
    """Tool definition augmented with a human label and an execute function.

    Subclasses `agent.pi.ai.types.Tool` so registries/transport code can
    treat an `AgentTool` as a plain `Tool` for the LLM hand-off, while the loop
    uses the added `label` / `execute` fields at execution time.
    """

    label: str
    execute: ToolExecuteFn

    model_config = ConfigDict(arbitrary_types_allowed=True)


# ---------------------------------------------------------------------------
# AgentContext, AgentState
# ---------------------------------------------------------------------------


class AgentContext(BaseModel):
    """Context passed to `agent_loop` / `agent_loop_continue`.

    Parallels `Context` but carries `AgentTool`s rather than plain `Tool`s.
    Construction uses snake_case Python field names; ``model_dump(by_alias=True)``
    emits the upstream camelCase wire format.
    """

    system_prompt: str = Field(default="", serialization_alias="systemPrompt")
    messages: list[AgentMessage] = Field(default_factory=list)
    tools: list[AgentTool] | None = None

    model_config = ConfigDict(arbitrary_types_allowed=True)


class AgentState(BaseModel):
    """Durable agent state owned by `Agent`.

    Mutable by design — `Agent._run_loop` updates this in place as events
    arrive from the loop. Construction uses snake_case; serialization with
    ``by_alias=True`` emits camelCase to match upstream.
    """

    system_prompt: str = Field(default="", serialization_alias="systemPrompt")
    model: Model | None = None
    thinking_level: ThinkingLevel = Field(default="off", serialization_alias="thinkingLevel")
    tools: list[AgentTool] = Field(default_factory=list)
    messages: list[AgentMessage] = Field(default_factory=list)
    is_streaming: bool = Field(default=False, serialization_alias="isStreaming")
    stream_message: AgentMessage | None = Field(default=None, serialization_alias="streamMessage")
    pending_tool_calls: set[str] = Field(
        default_factory=set, serialization_alias="pendingToolCalls"
    )
    error: str | None = None

    model_config = ConfigDict(arbitrary_types_allowed=True)


# ---------------------------------------------------------------------------
# AgentEvent discriminated union
# ---------------------------------------------------------------------------


class AgentStart(BaseModel):
    type: Literal["agent_start"] = "agent_start"


class AgentEnd(BaseModel):
    type: Literal["agent_end"] = "agent_end"
    messages: list[AgentMessage] = Field(default_factory=list)

    model_config = ConfigDict(arbitrary_types_allowed=True)


class TurnStart(BaseModel):
    type: Literal["turn_start"] = "turn_start"


class TurnEnd(BaseModel):
    type: Literal["turn_end"] = "turn_end"
    message: AgentMessage
    tool_results: list[ToolResultMessage] = Field(default_factory=list, alias="toolResults")

    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)


class MessageStart(BaseModel):
    type: Literal["message_start"] = "message_start"
    message: AgentMessage

    model_config = ConfigDict(arbitrary_types_allowed=True)


class MessageUpdate(BaseModel):
    """Emitted while an assistant message is being streamed.

    Carries both the latest assistant-message snapshot and the raw pi-ai
    `AssistantMessageEvent` that produced the update (for consumers that need
    deltas rather than the current snapshot).
    """

    type: Literal["message_update"] = "message_update"
    message: AgentMessage
    assistant_message_event: AssistantMessageEvent = Field(alias="assistantMessageEvent")

    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)


class MessageEnd(BaseModel):
    type: Literal["message_end"] = "message_end"
    message: AgentMessage

    model_config = ConfigDict(arbitrary_types_allowed=True)


class ToolExecutionStart(BaseModel):
    type: Literal["tool_execution_start"] = "tool_execution_start"
    tool_call_id: str = Field(alias="toolCallId")
    tool_name: str = Field(alias="toolName")
    args: dict[str, Any] = Field(default_factory=dict)

    model_config = ConfigDict(populate_by_name=True)


class ToolExecutionUpdate(BaseModel):
    type: Literal["tool_execution_update"] = "tool_execution_update"
    tool_call_id: str = Field(alias="toolCallId")
    tool_name: str = Field(alias="toolName")
    args: dict[str, Any] = Field(default_factory=dict)
    partial_result: Any = Field(default=None, alias="partialResult")

    model_config = ConfigDict(populate_by_name=True)


class ToolExecutionEnd(BaseModel):
    type: Literal["tool_execution_end"] = "tool_execution_end"
    tool_call_id: str = Field(alias="toolCallId")
    tool_name: str = Field(alias="toolName")
    result: Any = None
    is_error: bool = Field(default=False, alias="isError")

    model_config = ConfigDict(populate_by_name=True)


AgentEvent = Annotated[
    Union[
        AgentStart,
        AgentEnd,
        TurnStart,
        TurnEnd,
        MessageStart,
        MessageUpdate,
        MessageEnd,
        ToolExecutionStart,
        ToolExecutionUpdate,
        ToolExecutionEnd,
    ],
    Field(discriminator="type"),
]
"""Discriminated union emitted by the agent loop. Mirrors upstream `AgentEvent`."""


# ---------------------------------------------------------------------------
# StreamFn protocol
# ---------------------------------------------------------------------------


class StreamFn(Protocol):
    """Callable that produces an assistant-message event stream.

    Mirrors the signature of `agent.pi.ai.stream.stream_simple` so
    `stream_simple` itself satisfies the protocol as the default.
    """

    async def __call__(
        self,
        model: Model,
        context: Context,
        options: SimpleStreamOptions | None = None,
    ) -> AssistantMessageEventStream: ...


# ---------------------------------------------------------------------------
# AgentLoopConfig
# ---------------------------------------------------------------------------


ConvertToLlmFn = Callable[[list[AgentMessage]], Union[list[Message], Awaitable[list[Message]]]]
TransformContextFn = Callable[
    [list[AgentMessage], "AbortSignal | None"],
    Awaitable[list[AgentMessage]],
]
GetApiKeyFn = Callable[[str], Union[str, None, Awaitable[Union[str, None]]]]
GetMessagesFn = Callable[[], Awaitable[list[AgentMessage]]]
OnPayloadFn = Callable[[str, Any], None]


class AgentLoopConfig(BaseModel):
    """Loop configuration.

    Mirrors the fields of upstream `AgentLoopConfig extends SimpleStreamOptions`.
    Callables are stored as-is; Pydantic will not validate them.
    """

    model: Model

    # SimpleStreamOptions-equivalent knobs (subset that the loop actually forwards)
    reasoning: ThinkingLevel | None = None
    api_key: str | None = Field(default=None, serialization_alias="apiKey")
    temperature: float | None = None
    max_tokens: int | None = Field(default=None, serialization_alias="maxTokens")
    session_id: str | None = Field(default=None, serialization_alias="sessionId")
    transport: Transport | None = None
    thinking_budgets: dict[str, int] | None = Field(
        default=None, serialization_alias="thinkingBudgets"
    )
    max_retry_delay_ms: int | None = Field(default=None, serialization_alias="maxRetryDelayMs")
    on_payload: OnPayloadFn | None = Field(default=None, serialization_alias="onPayload")

    # Agent-level hooks
    convert_to_llm: ConvertToLlmFn = Field(serialization_alias="convertToLlm")
    transform_context: TransformContextFn | None = Field(
        default=None, serialization_alias="transformContext"
    )
    get_api_key: GetApiKeyFn | None = Field(default=None, serialization_alias="getApiKey")
    get_steering_messages: GetMessagesFn | None = Field(
        default=None, serialization_alias="getSteeringMessages"
    )
    get_follow_up_messages: GetMessagesFn | None = Field(
        default=None, serialization_alias="getFollowUpMessages"
    )

    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        extra="allow",
    )

    def to_simple_stream_options(
        self,
        *,
        api_key: str | None,
    ) -> SimpleStreamOptions:
        """Build a `SimpleStreamOptions` snapshot for a single streamFn call."""
        return SimpleStreamOptions(
            reasoning=self.reasoning if self.reasoning and self.reasoning != "off" else None,
            api_key=api_key,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
            session_id=self.session_id,
            transport=self.transport,
            thinking_budgets=self.thinking_budgets,
            max_retry_delay_ms=self.max_retry_delay_ms,
        )


__all__ = [
    "AbortController",
    "AbortSignal",
    "AgentContext",
    "AgentEnd",
    "AgentEvent",
    "AgentLoopConfig",
    "AgentMessage",
    "AgentStart",
    "AgentState",
    "AgentTool",
    "AgentToolResult",
    "AgentToolUpdateCallback",
    "AssistantMessage",
    "AssistantMessageEvent",
    "ConvertToLlmFn",
    "GetApiKeyFn",
    "GetMessagesFn",
    "MessageEnd",
    "MessageStart",
    "MessageUpdate",
    "Message",
    "StreamFn",
    "ThinkingLevel",
    "ToolCall",
    "ToolExecuteFn",
    "ToolExecutionEnd",
    "ToolExecutionStart",
    "ToolExecutionUpdate",
    "ToolResultMessage",
    "Transport",
    "TransformContextFn",
    "TurnEnd",
    "TurnStart",
    "UserMessage",
]
