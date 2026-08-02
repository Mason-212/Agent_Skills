"""Pi Agent tool adapter for domain pack tools.

Pack tool functions have the signature:
    async def my_tool(ctx: PackExecutionContext, args: dict) -> AgentToolResult

Pi Agent's tool system calls:
    execute(tool_call_id, args, signal, on_update) -> AgentToolResult

This module bridges the two by:
1. Building a :class:`SessionContext` **once** at adapter-creation time
   (validation + mkdir run exactly once per session, not once per tool call).
2. Stamping per-turn fields (tool_call_id, signal, on_update) onto the shared
   SessionContext on each invocation to produce a fresh :class:`PackExecutionContext`.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import TYPE_CHECKING, Any, Awaitable, Callable

from agent.packs.context import DEFAULT_SESSION_WORKSPACE_ROOT, PackExecutionContext, SessionContext

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from agent.pi.core.types import AbortSignal, AgentToolResult, AgentToolUpdateCallback

PackToolFn = Callable[
    [PackExecutionContext, dict[str, Any]],
    Awaitable["AgentToolResult"],
]
"""Type alias for a pack tool function.

Signature: ``async (ctx: PackExecutionContext, args: dict) -> AgentToolResult``
"""


def create_tool_adapter(
    pack_tool_fn: PackToolFn,
    session_id: str,
    workspace_root: Path = DEFAULT_SESSION_WORKSPACE_ROOT,
) -> Callable[
    [str, dict[str, Any], "AbortSignal | None", "AgentToolUpdateCallback | None"],
    Awaitable["AgentToolResult"],
]:
    """Wrap a pack tool function to satisfy the Pi Agent ``ToolExecuteFn`` contract.

    Builds a :class:`SessionContext` **once** (validation + ``mkdir`` run at
    adapter-creation time, not on every tool call), then stamps per-turn fields
    on each invocation to produce a :class:`PackExecutionContext`.

    Args:
        pack_tool_fn: Async function with signature
                      ``(ctx: PackExecutionContext, args: dict) -> AgentToolResult``.
        session_id: Session identifier (from ``SessionManager.header.id``).
                   **Must be stable for the lifetime of the conversation.**
                   Determines the workspace directory for this session.
        workspace_root: Root directory for all session workspaces.
                       Default: ``/tmp/edc_sessions``.

    Returns:
        A ``ToolExecuteFn``-compatible coroutine function that injects
        a fresh ``PackExecutionContext`` (backed by the shared ``SessionContext``)
        before delegating to ``pack_tool_fn``.

    Example::

        class MyPack(BoundDomainPack):
            def get_tools(self, session_id: str | None = None) -> list[AgentTool]:
                if session_id is None:
                    return []
                return [
                    AgentTool(
                        name="my_tool",
                        label="My Tool",
                        description="Does something",
                        parameters={...},
                        execute=create_tool_adapter(self.my_tool, session_id),
                    )
                ]

            async def my_tool(self, ctx: PackExecutionContext, args: dict) -> AgentToolResult:
                result_file = ctx.workspace_dir / "result.json"
                ...
    """
    tool_name = getattr(pack_tool_fn, "__name__", "unknown")

    # Build SessionContext once — validation and mkdir run here, not per call.
    try:
        session_ctx = SessionContext(session_id=session_id, _workspace_root=workspace_root)
    except Exception:
        logger.exception(
            "pack tool adapter: session context creation failed "
            "[tool=%s session_id=%s]",
            tool_name,
            session_id,
        )
        raise

    async def adapted_execute(
        tool_call_id: str,
        args: dict[str, Any],
        signal: "AbortSignal | None",
        on_update: "AgentToolUpdateCallback | None",
    ) -> "AgentToolResult":
        # Stamp per-turn fields cheaply — no validation or I/O.
        ctx = session_ctx.for_call(tool_call_id=tool_call_id, signal=signal, on_update=on_update)

        try:
            return await pack_tool_fn(ctx, args)
        except (KeyboardInterrupt, SystemExit):
            # Never catch cancellation or shutdown signals
            raise
        except Exception:
            logger.exception(
                "pack tool adapter: tool execution failed "
                "[tool=%s session_id=%s tool_call_id=%s]",
                tool_name,
                session_id,
                tool_call_id,
            )
            raise

    adapted_execute.__name__ = f"adapted_{getattr(pack_tool_fn, '__name__', 'unknown')}"
    adapted_execute.__qualname__ = f"adapted_{getattr(pack_tool_fn, '__qualname__', 'unknown')}"
    return adapted_execute
