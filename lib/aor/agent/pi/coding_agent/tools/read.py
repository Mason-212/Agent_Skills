"""`read` tool — read a text file with offset/limit + truncation.

Python port of `coding-agent/src/core/tools/read.ts`. Image handling is
intentionally omitted; `agent.pi.ai` does not yet expose
`ImageContent`. The tool surfaces text-only results today; the image path
is documented in the ADR for follow-up.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any, Awaitable, Callable

from ...ai.types import TextContent
from ...core.types import AgentTool, AgentToolResult
from .path_utils import resolve_read_path
from .truncate import (
    DEFAULT_MAX_BYTES,
    DEFAULT_MAX_LINES,
    TruncationResult,
    format_size,
    truncate_head,
)

ReadToolInput = dict[str, Any]


@dataclass
class ReadToolDetails:
    truncation: TruncationResult | None = None


@dataclass
class ReadOperations:
    """Pluggable I/O ops so the tool can be redirected (e.g., over SSH)."""

    read_file: Callable[[str], Awaitable[bytes]]
    access: Callable[[str], Awaitable[None]]


async def _default_read_file(path: str) -> bytes:
    with open(path, "rb") as f:
        return f.read()


async def _default_access(path: str) -> None:
    if not os.access(path, os.R_OK):
        raise PermissionError(f"Cannot read {path}")


default_read_operations = ReadOperations(read_file=_default_read_file, access=_default_access)


_READ_PARAMS_SCHEMA = {
    "type": "object",
    "properties": {
        "path": {"type": "string", "description": "Path to the file to read (relative or absolute)"},
        "offset": {"type": "integer", "description": "Line number to start reading from (1-indexed)"},
        "limit": {"type": "integer", "description": "Maximum number of lines to read"},
    },
    "required": ["path"],
}


def create_read_tool(
    cwd: str, *, operations: ReadOperations | None = None
) -> AgentTool:
    ops = operations or default_read_operations

    async def execute(
        _tool_call_id: str,
        args: dict[str, Any],
        signal=None,
        on_update=None,
    ) -> AgentToolResult:
        if signal and signal.aborted:
            raise RuntimeError("Operation aborted")

        path = args["path"]
        offset = args.get("offset")
        limit = args.get("limit")
        absolute = resolve_read_path(path, cwd)

        await ops.access(absolute)
        if signal and signal.aborted:
            raise RuntimeError("Operation aborted")

        buf = await ops.read_file(absolute)
        text = buf.decode("utf-8", errors="replace")
        all_lines = text.split("\n")
        total_lines = len(all_lines)

        start_line = max(0, (offset or 1) - 1) if offset else 0
        start_display = start_line + 1

        if start_line >= total_lines:
            raise ValueError(
                f"Offset {offset} is beyond end of file ({total_lines} lines total)"
            )

        user_limited_lines: int | None = None
        if limit is not None:
            end_line = min(start_line + limit, total_lines)
            selected = "\n".join(all_lines[start_line:end_line])
            user_limited_lines = end_line - start_line
        else:
            selected = "\n".join(all_lines[start_line:])

        truncation = truncate_head(selected)

        details: ReadToolDetails | None = None
        if truncation.first_line_exceeds_limit:
            first_size = format_size(len(all_lines[start_line].encode("utf-8")))
            output = (
                f"[Line {start_display} is {first_size}, exceeds "
                f"{format_size(DEFAULT_MAX_BYTES)} limit. Use bash: "
                f"sed -n '{start_display}p' {path} | head -c {DEFAULT_MAX_BYTES}]"
            )
            details = ReadToolDetails(truncation=truncation)
        elif truncation.truncated:
            end_display = start_display + truncation.output_lines - 1
            next_offset = end_display + 1
            output = truncation.content
            if truncation.truncated_by == "lines":
                output += (
                    f"\n\n[Showing lines {start_display}-{end_display} of "
                    f"{total_lines}. Use offset={next_offset} to continue.]"
                )
            else:
                output += (
                    f"\n\n[Showing lines {start_display}-{end_display} of "
                    f"{total_lines} ({format_size(DEFAULT_MAX_BYTES)} limit). "
                    f"Use offset={next_offset} to continue.]"
                )
            details = ReadToolDetails(truncation=truncation)
        elif user_limited_lines is not None and start_line + user_limited_lines < total_lines:
            remaining = total_lines - (start_line + user_limited_lines)
            next_offset = start_line + user_limited_lines + 1
            output = truncation.content + (
                f"\n\n[{remaining} more lines in file. Use offset={next_offset} to continue.]"
            )
        else:
            output = truncation.content

        return AgentToolResult(
            content=[TextContent(type="text", text=output)], details=details
        )

    return AgentTool(
        name="read",
        label="read",
        description=(
            "Read the contents of a file. Output is truncated to "
            f"{DEFAULT_MAX_LINES} lines or {DEFAULT_MAX_BYTES // 1024}KB "
            "(whichever is hit first). Use offset/limit for large files."
        ),
        parameters=_READ_PARAMS_SCHEMA,
        execute=execute,
    )


__all__ = [
    "ReadOperations",
    "ReadToolDetails",
    "ReadToolInput",
    "create_read_tool",
    "default_read_operations",
]
