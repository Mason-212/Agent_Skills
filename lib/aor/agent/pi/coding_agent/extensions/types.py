"""Extension types and `ExtensionAPI` surface.

Python port of a focused subset of
`vendor/pi-mono-upstream/packages/coding-agent/src/core/extensions/types.ts`.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Awaitable, Callable, Literal, Protocol, Union

from ...ai.types import TextContent
from ...core.types import AgentMessage, AgentTool

# ---------------------------------------------------------------------------
# Events (discriminated by `type`)
# ---------------------------------------------------------------------------


@dataclass
class SessionStartEvent:
    type: Literal["session_start"] = "session_start"


@dataclass
class SessionCompactEvent:
    summary: str = ""
    type: Literal["session_compact"] = "session_compact"


@dataclass
class SessionShutdownEvent:
    type: Literal["session_shutdown"] = "session_shutdown"


@dataclass
class ContextEvent:
    messages: list[AgentMessage] = field(default_factory=list)
    type: Literal["context"] = "context"


@dataclass
class BeforeAgentStartEvent:
    prompt: str = ""
    system_prompt: str = ""
    type: Literal["before_agent_start"] = "before_agent_start"


@dataclass
class AgentStartEvent:
    type: Literal["agent_start"] = "agent_start"


@dataclass
class AgentEndEvent:
    messages: list[AgentMessage] = field(default_factory=list)
    type: Literal["agent_end"] = "agent_end"


@dataclass
class TurnStartEvent:
    turn_index: int = 0
    type: Literal["turn_start"] = "turn_start"


@dataclass
class TurnEndEvent:
    turn_index: int = 0
    message: AgentMessage | None = None
    type: Literal["turn_end"] = "turn_end"


@dataclass
class MessageStartEvent:
    message: AgentMessage | None = None
    type: Literal["message_start"] = "message_start"


@dataclass
class MessageUpdateEvent:
    message: AgentMessage | None = None
    type: Literal["message_update"] = "message_update"


@dataclass
class MessageEndEvent:
    message: AgentMessage | None = None
    type: Literal["message_end"] = "message_end"


@dataclass
class ToolExecutionStartEvent:
    tool_call_id: str = ""
    tool_name: str = ""
    args: dict[str, Any] = field(default_factory=dict)
    type: Literal["tool_execution_start"] = "tool_execution_start"


@dataclass
class ToolExecutionUpdateEvent:
    tool_call_id: str = ""
    tool_name: str = ""
    args: dict[str, Any] = field(default_factory=dict)
    partial_result: Any = None
    type: Literal["tool_execution_update"] = "tool_execution_update"


@dataclass
class ToolExecutionEndEvent:
    tool_call_id: str = ""
    tool_name: str = ""
    result: Any = None
    is_error: bool = False
    type: Literal["tool_execution_end"] = "tool_execution_end"


@dataclass
class ToolCallEvent:
    """Fired *before* a tool executes. Handlers may return a
    `ToolCallEventResult` to block execution with a reason."""

    tool_call_id: str = ""
    tool_name: str = ""
    input: dict[str, Any] = field(default_factory=dict)
    type: Literal["tool_call"] = "tool_call"


@dataclass
class ToolResultEvent:
    """Fired *after* a tool executes. Handlers may return a
    `ToolResultEventResult` to overwrite the content / details."""

    tool_call_id: str = ""
    tool_name: str = ""
    input: dict[str, Any] = field(default_factory=dict)
    content: list[TextContent] = field(default_factory=list)
    is_error: bool = False
    details: Any = None
    type: Literal["tool_result"] = "tool_result"


ExtensionEvent = Union[
    SessionStartEvent,
    SessionCompactEvent,
    SessionShutdownEvent,
    ContextEvent,
    BeforeAgentStartEvent,
    AgentStartEvent,
    AgentEndEvent,
    TurnStartEvent,
    TurnEndEvent,
    MessageStartEvent,
    MessageUpdateEvent,
    MessageEndEvent,
    ToolExecutionStartEvent,
    ToolExecutionUpdateEvent,
    ToolExecutionEndEvent,
    ToolCallEvent,
    ToolResultEvent,
]

EVENT_NAMES: tuple[str, ...] = (
    "session_start",
    "session_compact",
    "session_shutdown",
    "context",
    "before_agent_start",
    "agent_start",
    "agent_end",
    "turn_start",
    "turn_end",
    "message_start",
    "message_update",
    "message_end",
    "tool_execution_start",
    "tool_execution_update",
    "tool_execution_end",
    "tool_call",
    "tool_result",
)


# ---------------------------------------------------------------------------
# Event results
# ---------------------------------------------------------------------------


@dataclass
class ContextEventResult:
    messages: list[AgentMessage] | None = None


@dataclass
class ToolCallEventResult:
    block: bool = False
    reason: str | None = None


@dataclass
class ToolResultEventResult:
    content: list[TextContent] | None = None
    details: Any = None
    is_error: bool | None = None


@dataclass
class BeforeAgentStartEventResult:
    system_prompt: str | None = None


# ---------------------------------------------------------------------------
# Extension context
# ---------------------------------------------------------------------------


class SendMessageFn(Protocol):
    def __call__(self, text: str, *, display: bool = True) -> None: ...


class SendUserMessageFn(Protocol):
    def __call__(self, text: str) -> None: ...


@dataclass
class ExtensionContext:
    """Runtime context passed to every handler call.

    The fields are populated by the `ExtensionRunner` before it dispatches
    an event, and stay valid for the lifetime of the current agent session.
    """

    cwd: str
    is_idle: Callable[[], bool]
    abort: Callable[[], None]
    send_message: SendMessageFn | None = None
    send_user_message: SendUserMessageFn | None = None
    get_system_prompt: Callable[[], str] = lambda: ""


# ---------------------------------------------------------------------------
# Tool registration
# ---------------------------------------------------------------------------


@dataclass
class RegisteredTool:
    tool: AgentTool
    extension_path: str


# ---------------------------------------------------------------------------
# Extension API (exposed to `register(pi)`)
# ---------------------------------------------------------------------------


Handler = Callable[[ExtensionEvent, ExtensionContext], Union[Any, Awaitable[Any]]]


class ExtensionAPI:
    """API object passed to each extension's `register(pi)` function.

    The API is intentionally minimal and mirrors the shape of upstream
    `ExtensionAPI` for common operations only. Unused upstream methods
    are omitted so the surface is honest rather than stubby.
    """

    def __init__(self, *, extension_path: str) -> None:
        self._extension_path = extension_path
        self._handlers: dict[str, list[Handler]] = {}
        self._tools: dict[str, RegisteredTool] = {}
        self._prompt_sections: list[str] = []
        self._runtime_actions: dict[str, Callable[..., Any]] = {}

    # ---- Event subscription ----

    def on(self, event: str, handler: Handler) -> None:
        if event not in EVENT_NAMES:
            raise ValueError(
                f"Unknown event '{event}'. Known: {', '.join(EVENT_NAMES)}"
            )
        self._handlers.setdefault(event, []).append(handler)

    # ---- Tool registration ----

    def register_tool(self, tool: AgentTool) -> None:
        """Register an LLM-callable `AgentTool`.

        Duplicate names raise `ValueError` — extensions should namespace their
        tools (e.g., `myext_search`) rather than reusing built-in tool names.
        """
        if tool.name in self._tools:
            raise ValueError(f"tool '{tool.name}' already registered by this extension")
        self._tools[tool.name] = RegisteredTool(tool=tool, extension_path=self._extension_path)

    # ---- System prompt ----

    def add_system_prompt_section(self, text: str) -> None:
        """Append an extension-owned section to the default system prompt."""
        if text and text.strip():
            self._prompt_sections.append(text.strip())

    # ---- Actions (bound by runner) ----

    def send_message(self, text: str, *, display: bool = True) -> None:
        action = self._runtime_actions.get("send_message")
        if action is None:
            raise RuntimeError("send_message not available until the runner has bound")
        action(text, display=display)

    def send_user_message(self, text: str) -> None:
        action = self._runtime_actions.get("send_user_message")
        if action is None:
            raise RuntimeError("send_user_message not available until the runner has bound")
        action(text)

    # ---- Internal (read by runner) ----

    @property
    def handlers(self) -> dict[str, list[Handler]]:
        return self._handlers

    @property
    def tools(self) -> dict[str, RegisteredTool]:
        return self._tools

    @property
    def prompt_sections(self) -> list[str]:
        return list(self._prompt_sections)

    def _bind_actions(self, actions: dict[str, Callable[..., Any]]) -> None:
        self._runtime_actions.update(actions)


# ---------------------------------------------------------------------------
# Loaded extension
# ---------------------------------------------------------------------------


@dataclass
class Extension:
    path: str
    resolved_path: str
    api: ExtensionAPI


@dataclass
class ExtensionError:
    path: str
    error: str


__all__ = [
    "AgentEndEvent",
    "AgentStartEvent",
    "BeforeAgentStartEvent",
    "BeforeAgentStartEventResult",
    "ContextEvent",
    "ContextEventResult",
    "EVENT_NAMES",
    "Extension",
    "ExtensionAPI",
    "ExtensionContext",
    "ExtensionError",
    "ExtensionEvent",
    "Handler",
    "MessageEndEvent",
    "MessageStartEvent",
    "MessageUpdateEvent",
    "RegisteredTool",
    "SendMessageFn",
    "SendUserMessageFn",
    "SessionCompactEvent",
    "SessionShutdownEvent",
    "SessionStartEvent",
    "ToolCallEvent",
    "ToolCallEventResult",
    "ToolExecutionEndEvent",
    "ToolExecutionStartEvent",
    "ToolExecutionUpdateEvent",
    "ToolResultEvent",
    "ToolResultEventResult",
    "TurnEndEvent",
    "TurnStartEvent",
]
