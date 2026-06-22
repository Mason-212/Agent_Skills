"""Convenience subclass for tools-only packs with minimal boilerplate.

A ``ToolPack`` exposes a collection of agent tools without requiring the
author to implement workflow plumbing. Subclasses set ``descriptor`` as a
class attribute and decorate tool methods with :func:`pack_tool`. Lifecycle,
result envelope, and tool registration are defaulted.

Example::

    class WeatherPack(ToolPack):
        descriptor = PackDescriptor(
            id="weather",
            name="Weather",
            version="0.1.0",
        )

        @pack_tool(parameters={
            "type": "object",
            "properties": {
                "city": {"type": "string", "description": "City name."},
            },
            "required": ["city"],
        })
        async def lookup(self, ctx, city: str) -> dict:
            \"\"\"Return current temperature for a city.\"\"\"
            return {"temp_c": 21.5}

A ``ToolPack`` does not expose a workflow. ``run_direct`` and
``resume_direct`` raise ``NotImplementedError`` — call ``get_tools(session_id)``
to obtain the agent-loop-compatible tool list instead.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Callable, ClassVar, cast

from agent.packs.adapter import PackToolFn, create_tool_adapter
from agent.packs.base import BoundDomainPack, ExecutionContext, PackDescriptor, PackResult

if TYPE_CHECKING:
    from agent.pi.core.types import AgentTool


_PACK_TOOL_PARAMETERS_ATTR = "_pack_tool_parameters"


def pack_tool(
    *, parameters: dict[str, Any]
) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """Mark a method as an agent tool exposed by ``ToolPack``.

    The ``parameters`` argument is the JSON-schema object the LLM sees when
    deciding how to call the tool. The decorator stores it on the function
    so :meth:`ToolPack.get_tools` can build the corresponding ``AgentTool``.

    Args:
        parameters: JSON Schema object describing the tool's arguments.
            Typically ``{"type": "object", "properties": {...}, "required": [...]}``.

    Example::

        @pack_tool(parameters={
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Filesystem path."},
            },
            "required": ["path"],
        })
        async def load(self, ctx, path: str) -> dict:
            ...
    """

    def decorator(fn: Callable[..., Any]) -> Callable[..., Any]:
        setattr(fn, _PACK_TOOL_PARAMETERS_ATTR, parameters)
        return fn

    return decorator


class ToolPack(BoundDomainPack):
    """Tools-only pack with minimal boilerplate.

    Subclasses must set the ``descriptor`` class attribute and decorate
    tool methods with :func:`pack_tool`. Lifecycle hooks (``_open_impl`` /
    ``_close_impl``) default to no-ops; ``build_result`` returns a standard
    envelope; ``get_workflow_wrapper`` returns ``None`` so the pack is
    tools-only by construction.

    Tool methods must follow the signature::

        async def my_tool(self, ctx: PackExecutionContext, **args) -> AgentToolResult

    The ``ctx.workspace_dir`` and ``ctx.session_id`` properties give the tool
    access to the per-session workspace.
    """

    descriptor: ClassVar[PackDescriptor]  # type: ignore[assignment]

    async def _open_impl(self) -> None:  # noqa: B027 - intentional default no-op
        """Default no-op. Override to allocate session-shared resources."""

    async def _close_impl(self) -> None:  # noqa: B027 - intentional default no-op
        """Default no-op. Override to release resources allocated in ``_open_impl``."""

    def build_result(
        self, orchestrator_output: Any, context: ExecutionContext
    ) -> PackResult:
        """Wrap raw output in the standard ``PackResult`` envelope."""
        return PackResult(
            pack_id=self.descriptor.id,
            request_id=context.request_id,
            output=orchestrator_output,
        )

    def get_tools(self, session_id: str | None = None) -> "list[AgentTool]":
        """Build adapted ``AgentTool``s from ``@pack_tool``-decorated methods.

        Returns an empty list when ``session_id`` is ``None`` (REST callers
        that have no conversational session).
        """
        if session_id is None:
            return []

        from agent.pi.core.types import AgentTool

        tools: list[AgentTool] = []
        for attr_name in dir(self):
            if attr_name.startswith("_"):
                continue
            attr = getattr(self, attr_name, None)
            if not callable(attr):
                continue
            parameters = getattr(attr, _PACK_TOOL_PARAMETERS_ATTR, None)
            if parameters is None:
                continue

            description = (attr.__doc__ or attr_name).strip()
            label = description.split("\n", 1)[0]

            # The decorated bound method matches PackToolFn structurally;
            # pyright loses the precise type through getattr+dir, so cast.
            tools.append(
                AgentTool(
                    name=attr_name,
                    label=label,
                    description=description,
                    parameters=parameters,
                    execute=create_tool_adapter(
                        cast(PackToolFn, attr), session_id
                    ),
                )
            )
        return tools
