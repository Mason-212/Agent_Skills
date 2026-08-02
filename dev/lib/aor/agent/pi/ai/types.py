"""Core types for agent.pi.ai.

Python port of vendor/pi-mono-upstream/packages/ai/src/types.ts.

Scope: Required types + in-scope Maybe types per specs/plan_rewrite_piai.md.
Deferred: ImageContent, full CacheRetention/Transport semantics, TypeBox-specific
tool schemas. Tool.parameters here holds a JSON Schema dict; use Tool.from_model()
to convert a Pydantic BaseModel into one.

Design notes
------------
- AssistantMessageEvent is a Pydantic discriminated union on `type`. The
  `partial` / `message` / `error` fields carry an AssistantMessage snapshot at
  the moment the event was emitted; pi-ai mutates a single shared reference
  across a stream, and we preserve that pattern (these models are intentionally
  mutable).
- StopReason mirrors pi-ai exactly so downstream agent-core-style ports can
  reuse the same vocabulary without translation.
- Model<TApi> becomes Model with an `api: str` field (Literal for known APIs,
  but open-ended for custom providers, matching `Api = KnownApi | (string & {})`).
"""

from __future__ import annotations

from typing import Annotated, Any, ClassVar, Literal, Union

from pydantic import BaseModel, ConfigDict, Field

# ---------------------------------------------------------------------------
# Enum-like literals (direct ports from types.ts)
# ---------------------------------------------------------------------------

KnownApi = Literal[
    "openai-completions",
    "openai-responses",
    "anthropic-messages",
    "google-generative-ai",
]
"""Subset of pi-ai KnownApi relevant to this port's four target providers."""

KnownProvider = Literal[
    "openai",
    "anthropic",
    "google",
    "salesforce-gateway",
]

ThinkingLevel = Literal["minimal", "low", "medium", "high", "xhigh"]

StopReason = Literal["stop", "length", "toolUse", "error", "aborted"]

CacheRetention = Literal["none", "short", "long"]

Transport = Literal["sse", "websocket", "auto"]


# ---------------------------------------------------------------------------
# Content blocks
# ---------------------------------------------------------------------------


class TextContent(BaseModel):
    """Plain text assistant/user content block (port of TextContent)."""

    type: Literal["text"] = "text"
    text: str
    text_signature: str | None = Field(default=None, validation_alias="textSignature")

    model_config = ConfigDict(populate_by_name=True)


class ThinkingContent(BaseModel):
    """Reasoning / thinking block (Anthropic thinking, OpenAI reasoning, Gemini thought).

    Unified representation across all three thinking-capable providers. See
    notebook section 7 for the side-by-side and the ADR for the rationale.
    """

    type: Literal["thinking"] = "thinking"
    thinking: str
    thinking_signature: str | None = Field(default=None, validation_alias="thinkingSignature")
    redacted: bool = False

    model_config = ConfigDict(populate_by_name=True)


class ToolCall(BaseModel):
    """Assistant request to invoke a tool (port of ToolCall)."""

    type: Literal["toolCall"] = "toolCall"
    id: str
    name: str
    arguments: dict[str, Any] = Field(default_factory=dict)
    thought_signature: str | None = Field(default=None, validation_alias="thoughtSignature")

    model_config = ConfigDict(populate_by_name=True)


AssistantContentBlock = Annotated[
    Union[TextContent, ThinkingContent, ToolCall],
    Field(discriminator="type"),
]
UserContentBlock = Annotated[TextContent, Field(discriminator="type")]
ToolResultContentBlock = Annotated[TextContent, Field(discriminator="type")]


# ---------------------------------------------------------------------------
# Usage + cost
# ---------------------------------------------------------------------------


class UsageCost(BaseModel):
    """Per-category cost in USD (port of Usage.cost)."""

    input: float = 0.0
    output: float = 0.0
    cache_read: float = Field(default=0.0, validation_alias="cacheRead")
    cache_write: float = Field(default=0.0, validation_alias="cacheWrite")
    total: float = 0.0

    model_config = ConfigDict(populate_by_name=True)


class Usage(BaseModel):
    """Token + cost accounting for a single assistant turn."""

    input: int = 0
    output: int = 0
    cache_read: int = Field(default=0, validation_alias="cacheRead")
    cache_write: int = Field(default=0, validation_alias="cacheWrite")
    total_tokens: int = Field(default=0, validation_alias="totalTokens")
    cost: UsageCost = Field(default_factory=UsageCost)

    model_config = ConfigDict(populate_by_name=True)


# ---------------------------------------------------------------------------
# Messages
# ---------------------------------------------------------------------------


class UserMessage(BaseModel):
    role: Literal["user"] = "user"
    content: str | list[UserContentBlock]
    timestamp: int

    model_config = ConfigDict(populate_by_name=True)


class AssistantMessage(BaseModel):
    """Mutable running state of the model's response.

    pi-ai streams events that mutate a single `partial: AssistantMessage`
    instance; we preserve that shared-reference pattern. Do not freeze.
    """

    role: Literal["assistant"] = "assistant"
    content: list[AssistantContentBlock] = Field(default_factory=list)
    api: str
    provider: str
    model: str
    usage: Usage = Field(default_factory=Usage)
    stop_reason: StopReason = Field(default="stop", validation_alias="stopReason")
    error_message: str | None = Field(default=None, validation_alias="errorMessage")
    timestamp: int

    model_config = ConfigDict(populate_by_name=True)


class ToolResultMessage(BaseModel):
    """Model-facing projection of a tool invocation's result.

    This is the compact transcript the LLM sees on its next turn. It is NOT
    the canonical record of what the tool actually did. Every pi.ai provider
    adapter flattens this message to its wire-format text equivalent; any
    structured data embedded here that is not ``TextContent`` will be
    silently lost across a provider round-trip.

    Structured execution metadata -- artifacts, manifests, metrics,
    diagnostics, session handles, exit status, latency -- lives on the
    edc_harness layer's :class:`agent.pi.edc_harness.ToolExecutionResult`, which
    produces this message via an explicit projection
    (``ToolExecutionResult.to_model_message``). Harness / runtime callers
    should construct ``ToolExecutionResult`` and project down to this type;
    they should not stuff structured state directly into ``content``.

    Note: this intentionally diverges from pi-ai upstream, which exposes a
    free-form ``details: any`` passthrough on the tool-result message. That
    field was carried over in an earlier port, never consulted by any
    adapter here, and therefore removed to avoid a silent-drop footgun. See
    ``specs/pi-edc_harness/tool-execution-result.spec.md`` (follow-up) for the
    canonical edc_harness-layer contract.
    """

    role: Literal["toolResult"] = "toolResult"
    tool_call_id: str = Field(validation_alias="toolCallId")
    tool_name: str = Field(validation_alias="toolName")
    content: list[ToolResultContentBlock]
    is_error: bool = Field(default=False, validation_alias="isError")
    timestamp: int

    model_config = ConfigDict(populate_by_name=True)


Message = Annotated[
    Union[UserMessage, AssistantMessage, ToolResultMessage],
    Field(discriminator="role"),
]


# ---------------------------------------------------------------------------
# Tool + Context
# ---------------------------------------------------------------------------


class Tool(BaseModel):
    """Tool definition.

    `parameters` is a JSON Schema dict. For Pydantic authors, use
    `Tool.from_model(name, description, MyModel)` to derive the schema.
    """

    name: str
    description: str
    parameters: dict[str, Any] = Field(default_factory=dict)

    @classmethod
    def from_model(
        cls,
        name: str,
        description: str,
        model: type[BaseModel],
    ) -> Tool:
        """Build a Tool whose parameters schema is derived from a Pydantic model."""
        return cls(
            name=name,
            description=description,
            parameters=model.model_json_schema(),
        )


class Context(BaseModel):
    """Input to a stream call (port of Context)."""

    system_prompt: str | None = Field(default=None, validation_alias="systemPrompt")
    messages: list[Message] = Field(default_factory=list)
    tools: list[Tool] | None = None

    model_config = ConfigDict(populate_by_name=True)


# ---------------------------------------------------------------------------
# Stream options
# ---------------------------------------------------------------------------


class StreamOptions(BaseModel):
    """Base options all providers share (port of StreamOptions).

    `signal` (TS AbortSignal) is not carried here. In Python we cancel via
    asyncio task cancellation; provider implementations must honor
    CancelledError. See notebook section 10.
    """

    temperature: float | None = None
    max_tokens: int | None = Field(default=None, validation_alias="maxTokens")
    api_key: str | None = Field(default=None, validation_alias="apiKey")
    transport: Transport | None = None
    cache_retention: CacheRetention | None = Field(default=None, validation_alias="cacheRetention")
    session_id: str | None = Field(default=None, validation_alias="sessionId")
    headers: dict[str, str] | None = None
    max_retry_delay_ms: int | None = Field(default=None, validation_alias="maxRetryDelayMs")
    metadata: dict[str, Any] | None = None

    model_config = ConfigDict(populate_by_name=True, extra="allow")


class SimpleStreamOptions(StreamOptions):
    """Unified-reasoning options passed to stream_simple / complete_simple."""

    reasoning: ThinkingLevel | None = None
    thinking_budgets: dict[str, int] | None = Field(default=None, validation_alias="thinkingBudgets")


# ---------------------------------------------------------------------------
# Model handle
# ---------------------------------------------------------------------------


class ModelCost(BaseModel):
    """Pricing in USD per million tokens."""

    input: float
    output: float
    cache_read: float = Field(validation_alias="cacheRead")
    cache_write: float = Field(validation_alias="cacheWrite")

    model_config = ConfigDict(populate_by_name=True)


class Model(BaseModel):
    """Model handle used to dispatch to a provider (port of Model<TApi>)."""

    id: str
    name: str
    api: str
    provider: str
    base_url: str = Field(validation_alias="baseUrl")
    reasoning: bool = False
    input: list[Literal["text", "image"]] = Field(default_factory=lambda: ["text"])
    cost: ModelCost
    context_window: int = Field(validation_alias="contextWindow")
    max_tokens: int = Field(validation_alias="maxTokens")
    headers: dict[str, str] | None = None
    compat: dict[str, Any] | None = None

    model_config = ConfigDict(populate_by_name=True)


# ---------------------------------------------------------------------------
# AssistantMessageEvent discriminated union
# ---------------------------------------------------------------------------


class _EventBase(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    # Sentinel so subclass references to `type` stay clear in docs/IDE.
    type: ClassVar[str]


class StartEvent(BaseModel):
    type: Literal["start"] = "start"
    partial: AssistantMessage


class TextStartEvent(BaseModel):
    type: Literal["text_start"] = "text_start"
    content_index: int = Field(validation_alias="contentIndex")
    partial: AssistantMessage
    model_config = ConfigDict(populate_by_name=True)


class TextDeltaEvent(BaseModel):
    type: Literal["text_delta"] = "text_delta"
    content_index: int = Field(validation_alias="contentIndex")
    delta: str
    partial: AssistantMessage
    model_config = ConfigDict(populate_by_name=True)


class TextEndEvent(BaseModel):
    type: Literal["text_end"] = "text_end"
    content_index: int = Field(validation_alias="contentIndex")
    content: str
    partial: AssistantMessage
    model_config = ConfigDict(populate_by_name=True)


class ThinkingStartEvent(BaseModel):
    type: Literal["thinking_start"] = "thinking_start"
    content_index: int = Field(validation_alias="contentIndex")
    partial: AssistantMessage
    model_config = ConfigDict(populate_by_name=True)


class ThinkingDeltaEvent(BaseModel):
    type: Literal["thinking_delta"] = "thinking_delta"
    content_index: int = Field(validation_alias="contentIndex")
    delta: str
    partial: AssistantMessage
    model_config = ConfigDict(populate_by_name=True)


class ThinkingEndEvent(BaseModel):
    type: Literal["thinking_end"] = "thinking_end"
    content_index: int = Field(validation_alias="contentIndex")
    content: str
    partial: AssistantMessage
    model_config = ConfigDict(populate_by_name=True)


class ToolCallStartEvent(BaseModel):
    type: Literal["toolcall_start"] = "toolcall_start"
    content_index: int = Field(validation_alias="contentIndex")
    partial: AssistantMessage
    model_config = ConfigDict(populate_by_name=True)


class ToolCallDeltaEvent(BaseModel):
    type: Literal["toolcall_delta"] = "toolcall_delta"
    content_index: int = Field(validation_alias="contentIndex")
    delta: str
    partial: AssistantMessage
    model_config = ConfigDict(populate_by_name=True)


class ToolCallEndEvent(BaseModel):
    type: Literal["toolcall_end"] = "toolcall_end"
    content_index: int = Field(validation_alias="contentIndex")
    tool_call: ToolCall = Field(validation_alias="toolCall")
    partial: AssistantMessage
    model_config = ConfigDict(populate_by_name=True)


DoneReason = Literal["stop", "length", "toolUse"]
ErrorReason = Literal["aborted", "error"]


class DoneEvent(BaseModel):
    type: Literal["done"] = "done"
    reason: DoneReason
    message: AssistantMessage


class ErrorEvent(BaseModel):
    type: Literal["error"] = "error"
    reason: ErrorReason
    error: AssistantMessage


AssistantMessageEvent = Annotated[
    Union[
        StartEvent,
        TextStartEvent,
        TextDeltaEvent,
        TextEndEvent,
        ThinkingStartEvent,
        ThinkingDeltaEvent,
        ThinkingEndEvent,
        ToolCallStartEvent,
        ToolCallDeltaEvent,
        ToolCallEndEvent,
        DoneEvent,
        ErrorEvent,
    ],
    Field(discriminator="type"),
]
"""Discriminated union matching pi-ai AssistantMessageEvent (types.ts line 221)."""


# ---------------------------------------------------------------------------
# Stream-function protocol
# ---------------------------------------------------------------------------

# The actual callable protocol lives in registry.py to avoid circular imports;
# see StreamFunction / SimpleStreamFunction there.


__all__ = [
    "AssistantContentBlock",
    "AssistantMessage",
    "AssistantMessageEvent",
    "CacheRetention",
    "Context",
    "DoneEvent",
    "DoneReason",
    "ErrorEvent",
    "ErrorReason",
    "KnownApi",
    "KnownProvider",
    "Message",
    "Model",
    "ModelCost",
    "SimpleStreamOptions",
    "StartEvent",
    "StopReason",
    "StreamOptions",
    "TextContent",
    "TextDeltaEvent",
    "TextEndEvent",
    "TextStartEvent",
    "ThinkingContent",
    "ThinkingDeltaEvent",
    "ThinkingEndEvent",
    "ThinkingLevel",
    "ThinkingStartEvent",
    "Tool",
    "ToolCall",
    "ToolCallDeltaEvent",
    "ToolCallEndEvent",
    "ToolCallStartEvent",
    "ToolResultMessage",
    "Transport",
    "Usage",
    "UsageCost",
    "UserContentBlock",
    "UserMessage",
]
