"""Tool wrappers that bridge `AgentTool.execute` into extension events.

Python port of
``vendor/pi-mono-upstream/packages/coding-agent/src/core/extensions/wrapper.ts``.

Why this lives in the edc_harness, not in `pi.core`
-----------------------------------------------
Two of the four reducer events (`tool_call`, `tool_result`) need to run
*around* a tool's `execute` call: `tool_call` may **block** the
invocation, and `tool_result` may **rewrite** the returned content.
Doing that without leaking extension types into ``pi.core`` is achieved
by wrapping each tool here — the loop sees a normal ``AgentTool``, the
wrapper internally awaits the runner.

The third reducer (`context`) is wired separately in
``AgentSession`` via the existing ``transform_context`` seam in
``Agent``. The fourth (`before_agent_start`) is already dispatched from
``AgentSession.run``.
"""

from __future__ import annotations

from typing import Any

from ...ai.types import TextContent
from ...core.types import (
    AbortSignal,
    AgentTool,
    AgentToolResult,
    AgentToolUpdateCallback,
)
from .runner import ExtensionRunner
from .types import ToolCallEvent, ToolResultEvent


class _ExtensionBlockedError(RuntimeError):
    """Raised when a `tool_call` handler returns ``block=True``.

    A dedicated subclass lets `_execute_tool_calls` (or any caller that
    catches it) distinguish a deliberate extension veto from an
    unrelated tool exception. The loop catches all ``Exception``s and
    folds them into a tool-result message regardless, so the only
    behavioral consequence today is the marker text on the resulting
    error.
    """


def wrap_tool_with_extensions(tool: AgentTool, runner: ExtensionRunner) -> AgentTool:
    """Return a new ``AgentTool`` that emits `tool_call` / `tool_result`.

    Behavior, mirroring upstream ``wrapToolWithExtensions``:

    1. Before invoking the underlying tool, fire ``tool_call``. If any
       handler returns ``ToolCallEventResult(block=True, ...)``, raise
       with ``reason`` (or a default message) and skip execution.
    2. On success, fire ``tool_result`` with the returned content. If a
       handler returns ``ToolResultEventResult`` overrides, apply them
       per-field (last non-``None`` wins).
    3. On failure, still fire ``tool_result`` with ``is_error=True`` and
       the exception message as content, then re-raise. This gives
       observers a chance to log/transform error results, matching
       upstream symmetry.

    The wrapper short-circuits when the runner has no handlers for the
    relevant event, so a runner with zero extensions adds no overhead
    beyond the ``has_handlers`` checks.
    """

    underlying = tool.execute

    async def _execute(
        tool_call_id: str,
        params: dict[str, Any],
        signal: AbortSignal | None,
        on_update: AgentToolUpdateCallback | None,
    ) -> AgentToolResult:
        if runner.has_handlers("tool_call"):
            call_result = await runner.dispatch_tool_call(
                ToolCallEvent(
                    tool_call_id=tool_call_id,
                    tool_name=tool.name,
                    input=dict(params),
                )
            )
            if call_result.block:
                reason = call_result.reason or "Tool execution was blocked by an extension"
                raise _ExtensionBlockedError(reason)

        try:
            result = await underlying(tool_call_id, params, signal, on_update)
        except Exception as exc:
            if runner.has_handlers("tool_result"):
                await runner.dispatch_tool_result(
                    ToolResultEvent(
                        tool_call_id=tool_call_id,
                        tool_name=tool.name,
                        input=dict(params),
                        content=[TextContent(type="text", text=str(exc))],
                        details=None,
                        is_error=True,
                    )
                )
            raise

        if runner.has_handlers("tool_result"):
            override = await runner.dispatch_tool_result(
                ToolResultEvent(
                    tool_call_id=tool_call_id,
                    tool_name=tool.name,
                    input=dict(params),
                    content=list(result.content),
                    details=result.details,
                    is_error=False,
                )
            )
            new_content = override.content if override.content is not None else result.content
            new_details = override.details if override.details is not None else result.details
            return AgentToolResult(content=list(new_content), details=new_details)

        return result

    return tool.model_copy(update={"execute": _execute})


def wrap_tools_with_extensions(
    tools: list[AgentTool], runner: ExtensionRunner
) -> list[AgentTool]:
    """Return ``[wrap_tool_with_extensions(t, runner) for t in tools]``."""
    return [wrap_tool_with_extensions(t, runner) for t in tools]


__all__ = [
    "wrap_tool_with_extensions",
    "wrap_tools_with_extensions",
]
