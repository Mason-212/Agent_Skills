"""Event dispatcher for loaded extensions.

Python port of a scoped subset of
`vendor/pi-mono-upstream/packages/coding-agent/src/core/extensions/runner.ts`.

Responsibilities:

1. Bind `ExtensionAPI` actions (e.g., `send_message`) to agent hooks.
2. Dispatch events to every extension's registered handlers.
3. Collect returned results and reduce them (`context_event`, `tool_call`,
   `tool_result`, `before_agent_start`).
4. Provide a merged tool list + merged system prompt section.
"""

from __future__ import annotations

import asyncio
import inspect
import logging
from dataclasses import asdict, is_dataclass
from typing import Any, Iterable

from ...core.types import AgentTool
from .types import (
    EVENT_NAMES,
    BeforeAgentStartEventResult,
    ContextEventResult,
    Extension,
    ExtensionContext,
    ExtensionEvent,
    ToolCallEventResult,
    ToolResultEventResult,
)

_log = logging.getLogger(__name__)


class ExtensionRunner:
    def __init__(self, extensions: Iterable[Extension]) -> None:
        self._extensions: list[Extension] = list(extensions)
        self._context: ExtensionContext | None = None

    # ---- Lifecycle -----------------------------------------------------

    def bind_context(self, ctx: ExtensionContext) -> None:
        """Bind the runtime context + extension actions.

        Must be called before the first `dispatch`.
        """
        self._context = ctx
        actions = {
            "send_message": (ctx.send_message or (lambda *_a, **_kw: None)),
            "send_user_message": (ctx.send_user_message or (lambda *_a, **_kw: None)),
        }
        for ext in self._extensions:
            ext.api._bind_actions(actions)

    # ---- Aggregated views ----------------------------------------------

    @property
    def extensions(self) -> list[Extension]:
        return list(self._extensions)

    def collect_tools(self) -> list[AgentTool]:
        out: list[AgentTool] = []
        seen: set[str] = set()
        for ext in self._extensions:
            for name, reg in ext.api.tools.items():
                if name in seen:
                    continue
                seen.add(name)
                out.append(reg.tool)
        return out

    def collect_prompt_sections(self) -> list[str]:
        out: list[str] = []
        for ext in self._extensions:
            out.extend(ext.api.prompt_sections)
        return out

    def has_handlers(self, event_type: str) -> bool:
        """Return True if any loaded extension has registered for ``event_type``.

        Used by the tool wrapper and the agent-stream bridge to skip the
        async dispatch path entirely when no extension cares — keeps the
        zero-extension hot path free of needless event construction.
        """
        for ext in self._extensions:
            if ext.api.handlers.get(event_type):
                return True
        return False

    # ---- Dispatch ------------------------------------------------------

    async def dispatch(self, event: ExtensionEvent) -> list[Any]:
        """Dispatch `event` to every handler. Returns each handler's
        non-None return value in call order.
        """
        if self._context is None:
            raise RuntimeError("ExtensionRunner.bind_context() must be called first")
        if event.type not in EVENT_NAMES:
            raise ValueError(f"Unknown event: {event.type}")
        results: list[Any] = []
        for ext in self._extensions:
            for handler in ext.api.handlers.get(event.type, []):
                try:
                    out = handler(event, self._context)
                    if inspect.isawaitable(out):
                        out = await out
                    if out is not None:
                        results.append(out)
                except Exception as exc:  # noqa: BLE001
                    # Log eagerly — none of the typed reducers below act on
                    # ``_HandlerError`` sentinels, so without this an
                    # extension can crash silently and the user/agent will
                    # never see the failure.
                    _log.warning(
                        "Extension %s handler for event %r raised: %r",
                        ext.path,
                        event.type,
                        exc,
                        exc_info=exc,
                    )
                    results.append(_HandlerError(ext.path, event.type, exc))
        return results

    def dispatch_sync(self, event: ExtensionEvent) -> list[Any]:
        """Blocking variant for sync-only call sites."""
        return asyncio.get_event_loop().run_until_complete(self.dispatch(event))

    # ---- Typed reducers ------------------------------------------------

    async def dispatch_context(self, event: ExtensionEvent) -> list[Any]:
        """Dispatch a `context` event and apply message overrides in order."""
        raw = await self.dispatch(event)
        messages = list(getattr(event, "messages", []) or [])
        for r in raw:
            if isinstance(r, ContextEventResult) and r.messages is not None:
                messages = list(r.messages)
            elif is_dataclass(r) and not isinstance(r, _HandlerError):
                data = asdict(r)  # type: ignore[arg-type]
                if "messages" in data and data["messages"] is not None:
                    messages = list(data["messages"])
        return messages

    async def dispatch_tool_call(self, event: ExtensionEvent) -> ToolCallEventResult:
        raw = await self.dispatch(event)
        merged = ToolCallEventResult()
        for r in raw:
            if isinstance(r, ToolCallEventResult):
                if r.block:
                    merged.block = True
                if r.reason:
                    merged.reason = r.reason
        return merged

    async def dispatch_tool_result(self, event: ExtensionEvent) -> ToolResultEventResult:
        raw = await self.dispatch(event)
        merged = ToolResultEventResult()
        for r in raw:
            if isinstance(r, ToolResultEventResult):
                if r.content is not None:
                    merged.content = list(r.content)
                if r.details is not None:
                    merged.details = r.details
                if r.is_error is not None:
                    merged.is_error = r.is_error
        return merged

    async def dispatch_before_agent_start(self, event: ExtensionEvent) -> BeforeAgentStartEventResult:
        raw = await self.dispatch(event)
        chained_prompt: str | None = None
        for r in raw:
            if isinstance(r, BeforeAgentStartEventResult) and r.system_prompt is not None:
                chained_prompt = (
                    r.system_prompt if chained_prompt is None else chained_prompt + "\n\n" + r.system_prompt
                )
        return BeforeAgentStartEventResult(system_prompt=chained_prompt)


class _HandlerError:
    """Sentinel recording a handler exception. Kept in `dispatch` results
    so callers can log without losing the rest of the reduction."""

    def __init__(self, ext_path: str, event_name: str, exc: BaseException) -> None:
        self.extension_path = ext_path
        self.event_name = event_name
        self.exception = exc

    def __repr__(self) -> str:  # pragma: no cover
        return f"<HandlerError ext={self.extension_path} event={self.event_name} exc={self.exception!r}>"


__all__ = ["ExtensionRunner"]
