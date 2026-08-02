"""`grep` tool — search file contents (respects .gitignore via pathspec).

Python port of `coding-agent/src/core/tools/grep.ts`. Uses the
`pathspec` library to honor `.gitignore`/`.ignore`/`.fdignore` files
(falls back to no filtering if the package is missing).
"""

from __future__ import annotations

import os
import re
from dataclasses import dataclass
from typing import Any

from ...ai.types import TextContent
from ...core.types import AgentTool, AgentToolResult
from .path_utils import resolve_to_cwd
from .truncate import (
    DEFAULT_MAX_LINES,
    GREP_MAX_LINE_LENGTH,
    truncate_line,
)

try:
    import pathspec  # type: ignore
except Exception:  # noqa: BLE001
    pathspec = None  # type: ignore[assignment]


GrepToolInput = dict[str, Any]


@dataclass
class GrepToolDetails:
    matches_truncated: bool = False
    files_searched: int = 0


_IGNORE_FILE_NAMES = (".gitignore", ".ignore", ".fdignore")


def _build_spec(root: str) -> Any:
    if pathspec is None:
        return None
    patterns: list[str] = []
    for filename in _IGNORE_FILE_NAMES:
        path = os.path.join(root, filename)
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    patterns += [ln.rstrip("\n") for ln in f if ln.strip() and not ln.lstrip().startswith("#")]
            except OSError:
                pass
    if not patterns:
        return None
    return pathspec.PathSpec.from_lines("gitwildmatch", patterns)


def _ignored(spec: Any, root: str, path: str) -> bool:
    if spec is None:
        return False
    try:
        rel = os.path.relpath(path, root)
    except ValueError:
        return False
    return spec.match_file(rel)


_GREP_PARAMS_SCHEMA = {
    "type": "object",
    "properties": {
        "pattern": {"type": "string", "description": "Regex pattern to search for"},
        "path": {"type": "string", "description": "Path or glob to search (default: cwd)"},
        "case_insensitive": {"type": "boolean"},
        "max_results": {"type": "integer"},
    },
    "required": ["pattern"],
}


def create_grep_tool(cwd: str) -> AgentTool:
    async def execute(
        _tool_call_id: str,
        args: dict[str, Any],
        signal=None,
        on_update=None,
    ) -> AgentToolResult:
        if signal and signal.aborted:
            raise RuntimeError("Operation aborted")

        pattern = args["pattern"]
        search_path = args.get("path") or "."
        flags = re.IGNORECASE if args.get("case_insensitive") else 0
        max_results = args.get("max_results") or DEFAULT_MAX_LINES
        regex = re.compile(pattern, flags)

        absolute = resolve_to_cwd(search_path, cwd)
        root = absolute if os.path.isdir(absolute) else os.path.dirname(absolute) or cwd
        spec = _build_spec(root)

        out_lines: list[str] = []
        files_searched = 0
        truncated = False

        if os.path.isfile(absolute):
            walker: list[tuple[str, list[str], list[str]]] = [(os.path.dirname(absolute), [], [os.path.basename(absolute)])]
        else:
            walker = list(os.walk(absolute))

        for dirpath, dirnames, filenames in walker:
            dirnames[:] = [
                d for d in dirnames
                if d not in {".git", "node_modules", "__pycache__"}
                and not _ignored(spec, root, os.path.join(dirpath, d))
            ]
            for fname in filenames:
                fpath = os.path.join(dirpath, fname)
                if _ignored(spec, root, fpath):
                    continue
                files_searched += 1
                try:
                    with open(fpath, "r", encoding="utf-8", errors="ignore") as f:
                        for lineno, line in enumerate(f, start=1):
                            if regex.search(line):
                                truncated_line, _ = truncate_line(line.rstrip("\n"), GREP_MAX_LINE_LENGTH)
                                rel = os.path.relpath(fpath, cwd)
                                out_lines.append(f"{rel}:{lineno}:{truncated_line}")
                                if len(out_lines) >= max_results:
                                    truncated = True
                                    break
                except (OSError, UnicodeDecodeError):
                    continue
                if truncated:
                    break
            if truncated:
                break

        if not out_lines:
            text = f"No matches for /{pattern}/ in {search_path}"
        else:
            text = "\n".join(out_lines)
            if truncated:
                text += f"\n\n[Truncated at {max_results} matches.]"

        return AgentToolResult(
            content=[TextContent(type="text", text=text)],
            details=GrepToolDetails(matches_truncated=truncated, files_searched=files_searched),
        )

    return AgentTool(
        name="grep",
        label="grep",
        description=(
            "Search file contents for a regex pattern. Respects .gitignore. "
            "Returns matches as `path:line:content`."
        ),
        parameters=_GREP_PARAMS_SCHEMA,
        execute=execute,
    )


__all__ = ["GrepToolDetails", "GrepToolInput", "create_grep_tool"]
