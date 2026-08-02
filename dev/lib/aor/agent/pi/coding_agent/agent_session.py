"""`AgentSession` — the coding-agent-specific wrapper around `Agent`.

Python port of `vendor/pi-mono-upstream/packages/coding-agent/src/core/agent-session.ts`
(scoped: no TUI, no RPC, no model registry).

Responsibilities:

1. Own the underlying `agent.pi.core.Agent` and its lifecycle.
2. Build the system prompt (default or custom) from selected tools,
   loaded skills, context files, and extension prompt sections.
3. Maintain a `SessionManager` and persist every assistant / user /
   toolResult message as it arrives via `Agent.subscribe`.
4. Dispatch extension events around each turn — `before_agent_start`,
   `agent_start`, `turn_start`, `turn_end`, `agent_end`, plus wrapped
   tool-call / tool-result events.
5. Run compaction before each turn when the current compactor says so.
"""

from __future__ import annotations

import asyncio
import logging
import os
import time
from dataclasses import dataclass, field
from typing import Any, Callable

from ..ai.types import (
    AssistantMessage,
    Model,
    TextContent,
    ToolResultMessage,
    UserMessage,
)
from ..core.agent import Agent
from ..core.types import (
    AbortController,
    AbortSignal,
    AgentMessage,
    AgentTool,
)
from .compaction import Compactor, DefaultCompactor
from .defaults import DEFAULT_THINKING_LEVEL, DEFAULT_TOOL_NAMES, ThinkingLevel
from .extensions import (
    AgentEndEvent,
    AgentStartEvent,
    BeforeAgentStartEvent,
    ContextEvent,
    Extension,
    ExtensionContext,
    ExtensionRunner,
    SessionCompactEvent,
    SessionShutdownEvent,
    SessionStartEvent,
    ToolExecutionEndEvent,
    ToolExecutionStartEvent,
    ToolExecutionUpdateEvent,
    TurnEndEvent,
    TurnStartEvent,
    wrap_tools_with_extensions,
)
from .messages import (
    CodingAgentMessage,
    convert_to_llm,
    create_custom_message,
)
from .resource_loader import ContextFile, load_context_files
from .session_manager import SessionManager
from .skills import Skill, load_skills
from .system_prompt import BuildSystemPromptOptions, build_system_prompt
from .tools import select_tools

_log = logging.getLogger(__name__)


def _now_ms() -> int:
    return int(time.time() * 1000)


@dataclass
class AgentSessionOptions:
    """Knobs for `create_agent_session` / direct construction."""

    model: Model
    cwd: str | None = None
    include_pi_tools: bool = True
    # Pi's built-in filesystem/shell tools added when include_pi_tools=True:
    #   read  — read file contents
    #   bash  — execute shell commands
    #   edit  — make surgical text edits to files
    #   write — create or overwrite files
    # Set include_pi_tools=False for pack nodes that expose only their own
    # domain tools and must not give the model filesystem/shell access.
    tools: list[AgentTool] = field(default_factory=list)
    thinking_level: ThinkingLevel = DEFAULT_THINKING_LEVEL
    custom_system_prompt: str | None = None
    append_system_prompt: str | None = None
    prompt_guidelines: list[str] = field(default_factory=list)
    tool_snippets: dict[str, str] = field(default_factory=dict)
    extensions: list[Extension] = field(default_factory=list)
    skill_paths: list[str] = field(default_factory=list)
    include_default_skills: bool = True
    include_global_context: bool = True
    extra_context_paths: list[str] = field(default_factory=list)
    compactor: Compactor | None = None
    session_manager: SessionManager | None = None
    sessions_dir: str | None = None
    api_key: str | None = None


class AgentSession:
    """Owning wrapper around an `Agent` plus coding-agent infrastructure."""

    def __init__(self, options: AgentSessionOptions) -> None:
        self._options = options
        self._cwd = options.cwd or _default_cwd()

        self._skills: list[Skill] = []
        self._context_files: list[ContextFile] = []
        self._load_resources()

        self._runner = ExtensionRunner(options.extensions)
        self._system_prompt = self._build_system_prompt()

        self._compactor: Compactor = options.compactor or DefaultCompactor()
        self._session_manager = options.session_manager

        tools = list(select_tools(DEFAULT_TOOL_NAMES, self._cwd) if options.include_pi_tools else [])
        tools.extend(options.tools)
        tools.extend(self._runner.collect_tools())
        # Track unwrapped tools for `.tools` accessor; the wrapped copies
        # below are what the loop actually invokes. `tools` is the public
        # face (what an extension's `register_tool` produced); the
        # wrapped copies route each call through `tool_call` /
        # `tool_result` reducers when handlers exist.
        self._tools = tools
        wrapped_tools = wrap_tools_with_extensions(tools, self._runner)

        self._agent = Agent(
            initial_state={
                "systemPrompt": self._system_prompt,
                "model": options.model,
                "thinkingLevel": options.thinking_level,
                "tools": wrapped_tools,
                "messages": [],
            },
            convert_to_llm=convert_to_llm,  # type: ignore[arg-type]
            transform_context=self._dispatch_context_event,
            get_api_key=(lambda _name: options.api_key) if options.api_key else None,
        )

        self._abort_controller: AbortController | None = None
        self._persist_unsubscribe: Callable[[], None] | None = None
        self._bridge_unsubscribe: Callable[[], None] | None = None
        self._bridge_tasks: set[asyncio.Task[Any]] = set()
        self._runner.bind_context(self._make_extension_context())
        self._attach_persistence()
        self._attach_event_bridge()

    # ------------------------------------------------------------------
    # Resource loading
    # ------------------------------------------------------------------

    def _load_resources(self) -> None:
        res = load_skills(
            cwd=self._cwd,
            skill_paths=self._options.skill_paths,
            include_defaults=self._options.include_default_skills,
        )
        self._skills = res.skills
        _user_skill_roots = tuple(
            os.path.abspath(p) for p in (self._options.skill_paths or [])
        )
        for diag in res.diagnostics:
            if diag.type == "collision":
                # Warn only when both sides of the collision come from user-supplied
                # skill_paths (always a programming error). Pack-vs-default collisions
                # are expected and only logged at debug to avoid noise.
                loser_path = os.path.abspath(diag.path) if diag.path else ""
                is_user_vs_user = _user_skill_roots and loser_path.startswith(_user_skill_roots)
                if is_user_vs_user:
                    _log.warning("skill name collision: %s", diag.message)
                else:
                    _log.debug("skill name collision: %s", diag.message)
            elif diag.type == "warning":
                _log.warning("skill load warning: %s", diag.message)
        self._context_files = load_context_files(
            self._cwd,
            include_global=self._options.include_global_context,
            extra_paths=self._options.extra_context_paths,
        )

    # ------------------------------------------------------------------
    # System prompt
    # ------------------------------------------------------------------

    def _build_system_prompt(self) -> str:
        extension_append = "\n\n".join(self._runner.collect_prompt_sections())
        append = self._options.append_system_prompt or ""
        if extension_append:
            append = (append + "\n\n" + extension_append).strip()
        opts = BuildSystemPromptOptions(
            custom_prompt=self._options.custom_system_prompt,
            selected_tools=list(DEFAULT_TOOL_NAMES) if self._options.include_pi_tools else [],
            tool_snippets=self._options.tool_snippets,
            prompt_guidelines=self._options.prompt_guidelines,
            append_system_prompt=append or None,
            cwd=self._cwd,
            context_files=self._context_files,
            skills=self._skills,
        )
        return build_system_prompt(opts)

    # ------------------------------------------------------------------
    # Extension context + actions
    # ------------------------------------------------------------------

    def _make_extension_context(self) -> ExtensionContext:
        def _send_message(text: str, *, display: bool = True) -> None:
            msg = create_custom_message(
                custom_type="extension",
                content=text,
                display=display,
                details=None,
            )
            self._agent.append_message(msg)  # type: ignore[arg-type]
            self._persist_message_if_needed(msg)

        def _send_user_message(text: str) -> None:
            msg = UserMessage(
                role="user",
                content=[TextContent(type="text", text=text)],
                timestamp=_now_ms(),
            )
            self._agent.follow_up(msg)

        return ExtensionContext(
            cwd=self._cwd,
            is_idle=lambda: not self._agent.state.is_streaming,
            abort=self._agent.abort,
            send_message=_send_message,
            send_user_message=_send_user_message,
            get_system_prompt=lambda: self._system_prompt,
        )

    # ------------------------------------------------------------------
    # Persistence (Agent events → SessionManager)
    # ------------------------------------------------------------------

    def _attach_persistence(self) -> None:
        if self._session_manager is None:
            return

        def _on_event(event: Any) -> None:
            # `message_end` is the delivery channel for every persisted
            # message: assistant turns, tool results (one `message_end`
            # per result, emitted from `_execute_tool_calls` in
            # `agent_loop.py`), and steering / follow-up user messages.
            # `turn_end.tool_results` is an aggregate summary for
            # subscribers that want a turn-level view (renderers,
            # telemetry); it is NOT a re-delivery. `agent.py::_on_event`
            # follows the same contract — it appends to internal state
            # only on `message_end`. Reacting to both would double-write
            # every tool result to the JSONL.
            if event.type == "message_end":
                self._persist_message_if_needed(event.message)

        self._persist_unsubscribe = self._agent.subscribe(_on_event)

    # ------------------------------------------------------------------
    # Agent-stream → ExtensionRunner bridge (observability events)
    # ------------------------------------------------------------------

    def _attach_event_bridge(self) -> None:
        """Forward observability events from the core agent to extensions.

        `core/agent_loop.py` pushes ``tool_execution_start``,
        ``tool_execution_update`` and ``tool_execution_end`` onto the
        agent's internal event stream. Without this bridge an extension
        that does ``pi.on("tool_execution_start", h)`` registers a
        handler that silently never fires. We forward each event by
        scheduling an ``asyncio.create_task`` (`Agent.subscribe` is
        sync, but ``runner.dispatch`` is async); strong references to
        the tasks are kept on ``self._bridge_tasks`` to defeat
        ``asyncio``'s weak-reference GC of background tasks.

        Reducer events (`tool_call`, `tool_result`, `context`,
        `before_agent_start`) are *not* bridged here — they need to be
        ``await``ed inline at the decision site, which is what the tool
        wrapper, the ``transform_context`` adapter, and ``run`` already
        do.
        """

        runner = self._runner

        def _on_event(event: Any) -> None:
            ext_event = _translate_stream_event(event)
            if ext_event is None:
                return
            if not runner.has_handlers(ext_event.type):
                return
            try:
                loop = asyncio.get_running_loop()
            except RuntimeError:
                # No running loop (defensive — `Agent` events are emitted
                # from inside the agent loop's task, so a loop should
                # always be present). If we're somehow off-loop, log and
                # drop the event rather than corrupt state.
                _log.debug(
                    "No running event loop while bridging %s; dropping.",
                    ext_event.type,
                )
                return
            task = loop.create_task(runner.dispatch(ext_event))
            self._bridge_tasks.add(task)
            task.add_done_callback(self._bridge_tasks.discard)

        self._bridge_unsubscribe = self._agent.subscribe(_on_event)

    async def _drain_bridge_tasks(self) -> None:
        """Await any outstanding bridge dispatches.

        Called from ``shutdown`` so a caller that immediately tears down
        ``ExtensionContext``-bound resources (file handles, sockets) can
        rely on every fired observability event having reached its
        handler first. ``asyncio.gather`` with ``return_exceptions=True``
        prevents a single mis-behaving handler from masking shutdown.
        """
        if not self._bridge_tasks:
            return
        pending = list(self._bridge_tasks)
        await asyncio.gather(*pending, return_exceptions=True)

    async def _dispatch_context_event(
        self,
        messages: list[AgentMessage],
        _signal: AbortSignal | None,
    ) -> list[AgentMessage]:
        """Adapter wired into ``Agent``'s ``transform_context``.

        Called once per turn just before ``convert_to_llm``. Skips the
        runner round-trip entirely when no extension has subscribed,
        keeping the zero-extension hot path free of overhead.
        """
        if not self._runner.has_handlers("context"):
            return list(messages)
        return await self._runner.dispatch_context(
            ContextEvent(messages=list(messages))
        )

    def _persist_message_if_needed(self, message: Any) -> None:
        if self._session_manager is None:
            return
        if message is None:
            return
        if isinstance(message, (UserMessage, AssistantMessage, ToolResultMessage)):
            self._session_manager.append_message(message)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    @property
    def agent(self) -> Agent:
        return self._agent

    @property
    def session_manager(self) -> SessionManager | None:
        return self._session_manager

    @property
    def runner(self) -> ExtensionRunner:
        return self._runner

    @property
    def system_prompt(self) -> str:
        return self._system_prompt

    @property
    def skills(self) -> list[Skill]:
        return list(self._skills)

    @property
    def cwd(self) -> str:
        return self._cwd

    @property
    def tools(self) -> list[AgentTool]:
        return list(self._tools)

    def messages(self) -> list[CodingAgentMessage]:
        return list(self._agent.state.messages)

    def abort(self) -> None:
        self._agent.abort()

    async def shutdown(self) -> None:
        """Dispatch shutdown events and unsubscribe from agent updates."""
        if self._persist_unsubscribe is not None:
            self._persist_unsubscribe()
            self._persist_unsubscribe = None
        if self._bridge_unsubscribe is not None:
            self._bridge_unsubscribe()
            self._bridge_unsubscribe = None
        await self._drain_bridge_tasks()
        await self._runner.dispatch(SessionShutdownEvent())

    # ---- Turn loop ----

    async def run(self, prompt: str) -> AssistantMessage:
        """Send `prompt`, await completion, return the last assistant message."""
        await self._dispatch(SessionStartEvent())
        await self._maybe_compact()

        ba_result = await self._runner.dispatch_before_agent_start(
            BeforeAgentStartEvent(prompt=prompt, system_prompt=self._system_prompt)
        )
        if ba_result.system_prompt:
            self._system_prompt = ba_result.system_prompt
            self._agent.system_prompt = self._system_prompt

        await self._dispatch(AgentStartEvent())
        await self._dispatch(TurnStartEvent(turn_index=self._turn_index()))

        await self._agent.prompt(prompt)

        last = self._last_assistant()
        await self._dispatch(
            TurnEndEvent(turn_index=self._turn_index(), message=last)
        )
        await self._dispatch(AgentEndEvent(messages=list(self._agent.state.messages)))
        if last is None:
            raise RuntimeError("Agent produced no assistant message")
        return last

    async def _dispatch(self, event: Any) -> None:
        await self._runner.dispatch(event)

    async def _maybe_compact(self) -> None:
        messages = list(self._agent.state.messages)
        if not messages:
            return
        if not self._compactor.should_compact(messages):  # type: ignore[arg-type]
            return
        result = await self._compactor.compact(messages)  # type: ignore[arg-type]
        if not result.messages:
            return
        self._agent.replace_messages(result.messages)  # type: ignore[arg-type]
        await self._runner.dispatch(SessionCompactEvent(summary=result.summary))
        if self._session_manager is not None and result.summary:
            self._session_manager.append_compaction(
                summary=result.summary,
                first_kept_entry_id=self._session_manager.leaf_id or "",
                tokens_before=result.tokens_before,
            )

    def _turn_index(self) -> int:
        return sum(1 for m in self._agent.state.messages if m.role == "assistant")

    def _last_assistant(self) -> AssistantMessage | None:
        for m in reversed(self._agent.state.messages):
            if isinstance(m, AssistantMessage):
                return m
        return None


def _default_cwd() -> str:
    import os

    return os.getcwd()


def _translate_stream_event(event: Any) -> Any:
    """Translate a `core.AgentEvent` into the matching `ExtensionEvent`.

    Returns ``None`` for events that are not bridged (lifecycle and
    message events are dispatched directly from ``run``; reducer events
    aren't on the stream at all). Keeping the mapping in one place
    means future event additions only need a single edit.
    """
    etype = event.type
    if etype == "tool_execution_start":
        return ToolExecutionStartEvent(
            tool_call_id=event.tool_call_id,
            tool_name=event.tool_name,
            args=dict(event.args),
        )
    if etype == "tool_execution_update":
        return ToolExecutionUpdateEvent(
            tool_call_id=event.tool_call_id,
            tool_name=event.tool_name,
            args=dict(event.args),
            partial_result=event.partial_result,
        )
    if etype == "tool_execution_end":
        return ToolExecutionEndEvent(
            tool_call_id=event.tool_call_id,
            tool_name=event.tool_name,
            result=event.result,
            is_error=event.is_error,
        )
    return None


__all__ = ["AgentSession", "AgentSessionOptions"]
