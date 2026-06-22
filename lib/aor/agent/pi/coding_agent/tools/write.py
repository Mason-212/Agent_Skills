"""`write` tool — create or overwrite a file (auto-mkdir parents).

Python port of `coding-agent/src/core/tools/write.ts`.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any, Awaitable, Callable

from ...ai.types import TextContent
from ...core.types import AgentTool, AgentToolResult
from .path_utils import resolve_to_cwd

WriteToolInput = dict[str, Any]


@dataclass
class WriteOperations:
    write_file: Callable[[str, str], Awaitable[None]]
    mkdir: Callable[[str], Awaitable[None]]


async def _default_write_file(path: str, content: str) -> None:
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)


async def _default_mkdir(d: str) -> None:
    os.makedirs(d, exist_ok=True)


default_write_operations = WriteOperations(write_file=_default_write_file, mkdir=_default_mkdir)


_WRITE_PARAMS_SCHEMA = {
    "type": "object",
    "properties": {
        "path": {"type": "string", "description": "Path to the file to write (relative or absolute)"},
        "content": {"type": "string", "description": "Content to write to the file"},
    },
    "required": ["path", "content"],
}


def create_write_tool(
    cwd: str, *, operations: WriteOperations | None = None
) -> AgentTool:
    ops = operations or default_write_operations

    async def execute(
        _tool_call_id: str,
        args: dict[str, Any],
        signal=None,
        on_update=None,
    ) -> AgentToolResult:
        if signal and signal.aborted:
            raise RuntimeError("Operation aborted")
        path = args["path"]
        content = args["content"]
        absolute = resolve_to_cwd(path, cwd)
        await ops.mkdir(os.path.dirname(absolute) or ".")
        if signal and signal.aborted:
            raise RuntimeError("Operation aborted")
        await ops.write_file(absolute, content)
        return AgentToolResult(
            content=[
                TextContent(
                    type="text",
                    text=f"Successfully wrote {len(content)} bytes to {path}",
                )
            ],
            details=None,
        )

    return AgentTool(
        name="write",
        label="write",
        description=(
            "Write content to a file. Creates the file if missing, overwrites if "
            "present. Automatically creates parent directories."
        ),
        parameters=_WRITE_PARAMS_SCHEMA,
        execute=execute,
    )


__all__ = ["WriteOperations", "WriteToolInput", "create_write_tool", "default_write_operations"]
