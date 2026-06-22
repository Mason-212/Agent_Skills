"""`find` tool — locate files by glob pattern (respects .gitignore).

Python port of `coding-agent/src/core/tools/find.ts`.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any

from ...ai.types import TextContent
from ...core.types import AgentTool, AgentToolResult
from .grep import _build_spec, _ignored
from .path_utils import resolve_to_cwd
from .truncate import DEFAULT_MAX_LINES

try:
    import wcmatch.glob as wglob  # type: ignore
except Exception:  # noqa: BLE001
    wglob = None  # type: ignore[assignment]

import fnmatch

FindToolInput = dict[str, Any]


@dataclass
class FindToolDetails:
    files_listed: int = 0
    truncated: bool = False


_FIND_PARAMS_SCHEMA = {
    "type": "object",
    "properties": {
        "pattern": {"type": "string", "description": "Glob pattern, e.g., **/*.py"},
        "path": {"type": "string", "description": "Search root (default: cwd)"},
        "max_results": {"type": "integer"},
    },
    "required": ["pattern"],
}


def create_find_tool(cwd: str) -> AgentTool:
    async def execute(
        _tool_call_id: str,
        args: dict[str, Any],
        signal=None,
        on_update=None,
    ) -> AgentToolResult:
        if signal and signal.aborted:
            raise RuntimeError("Operation aborted")
        pattern = args["pattern"]
        search_root = resolve_to_cwd(args.get("path") or ".", cwd)
        max_results = args.get("max_results") or DEFAULT_MAX_LINES

        spec = _build_spec(search_root)
        results: list[str] = []
        truncated = False

        for dirpath, dirnames, filenames in os.walk(search_root):
            dirnames[:] = [
                d for d in dirnames
                if d not in {".git", "node_modules", "__pycache__"}
                and not _ignored(spec, search_root, os.path.join(dirpath, d))
            ]
            for fname in filenames:
                fpath = os.path.join(dirpath, fname)
                if _ignored(spec, search_root, fpath):
                    continue
                rel = os.path.relpath(fpath, search_root)
                if fnmatch.fnmatch(rel, pattern) or fnmatch.fnmatch(fname, pattern):
                    results.append(os.path.relpath(fpath, cwd))
                    if len(results) >= max_results:
                        truncated = True
                        break
            if truncated:
                break

        if not results:
            text = f"No files match {pattern} under {args.get('path') or '.'}"
        else:
            text = "\n".join(sorted(results))
            if truncated:
                text += f"\n\n[Truncated at {max_results} matches.]"
        return AgentToolResult(
            content=[TextContent(type="text", text=text)],
            details=FindToolDetails(files_listed=len(results), truncated=truncated),
        )

    return AgentTool(
        name="find",
        label="find",
        description="Find files by glob pattern. Respects .gitignore.",
        parameters=_FIND_PARAMS_SCHEMA,
        execute=execute,
    )


__all__ = ["FindToolDetails", "FindToolInput", "create_find_tool"]
