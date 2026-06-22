"""`ls` tool — list directory contents with file metadata.

Python port of `coding-agent/src/core/tools/ls.ts`.
"""

from __future__ import annotations

import os
import stat
from dataclasses import dataclass
from typing import Any

from ...ai.types import TextContent
from ...core.types import AgentTool, AgentToolResult
from .grep import _build_spec, _ignored
from .path_utils import resolve_to_cwd
from .truncate import format_size

LsToolInput = dict[str, Any]


@dataclass
class LsToolDetails:
    entries: int = 0


_LS_PARAMS_SCHEMA = {
    "type": "object",
    "properties": {
        "path": {"type": "string", "description": "Path to list (default: cwd)"},
        "show_hidden": {"type": "boolean"},
    },
}


def create_ls_tool(cwd: str) -> AgentTool:
    async def execute(
        _tool_call_id: str,
        args: dict[str, Any],
        signal=None,
        on_update=None,
    ) -> AgentToolResult:
        if signal and signal.aborted:
            raise RuntimeError("Operation aborted")
        target = resolve_to_cwd(args.get("path") or ".", cwd)
        show_hidden = bool(args.get("show_hidden"))
        if not os.path.isdir(target):
            raise NotADirectoryError(f"Not a directory: {target}")

        spec = _build_spec(target)
        rows: list[str] = []
        entries = sorted(os.listdir(target))
        for entry in entries:
            if not show_hidden and entry.startswith("."):
                continue
            full = os.path.join(target, entry)
            if _ignored(spec, target, full):
                continue
            try:
                st = os.stat(full)
            except OSError:
                continue
            kind = "d" if stat.S_ISDIR(st.st_mode) else "f"
            size = "-" if kind == "d" else format_size(st.st_size)
            rows.append(f"{kind} {size:>8} {entry}")

        text = "\n".join(rows) if rows else "(empty)"
        return AgentToolResult(
            content=[TextContent(type="text", text=text)],
            details=LsToolDetails(entries=len(rows)),
        )

    return AgentTool(
        name="ls",
        label="ls",
        description=(
            "List directory contents with kind (d/f) and size. Respects .gitignore."
        ),
        parameters=_LS_PARAMS_SCHEMA,
        execute=execute,
    )


__all__ = ["LsToolDetails", "LsToolInput", "create_ls_tool"]
