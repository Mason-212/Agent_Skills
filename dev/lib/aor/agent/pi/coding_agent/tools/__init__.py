"""Built-in tools for the coding agent.

Mirrors `vendor/pi-mono-upstream/packages/coding-agent/src/core/tools/index.ts`.
Each tool exposes:

- A `create_*_tool(cwd, ...)` factory producing an `AgentTool`.
- A pre-built `*_tool` that uses `os.getcwd()` (lazy via factory).
- A `*Operations` callable bundle for swap-out (e.g., remote/SSH execution).

The `AgentTool` returned conforms to the contract expected by
`agent.pi.core.agent_loop`: `parameters` is a JSON Schema dict,
`execute(tool_call_id, args, signal, on_update)` returns an
`AgentToolResult`.
"""

from __future__ import annotations

import os
from collections.abc import Callable
from typing import Iterable

from ...core.types import AgentTool
from .bash import (
    BashOperations,
    BashToolDetails,
    BashToolInput,
    create_bash_tool,
    default_bash_operations,
)
from .edit import (
    EditOperations,
    EditToolDetails,
    EditToolInput,
    create_edit_tool,
    default_edit_operations,
)
from .find import (
    FindToolDetails,
    FindToolInput,
    create_find_tool,
)
from .grep import (
    GrepToolDetails,
    GrepToolInput,
    create_grep_tool,
)
from .ls import LsToolDetails, LsToolInput, create_ls_tool
from .read import (
    ReadOperations,
    ReadToolDetails,
    ReadToolInput,
    create_read_tool,
    default_read_operations,
)
from .truncate import (
    DEFAULT_MAX_BYTES,
    DEFAULT_MAX_LINES,
    GREP_MAX_LINE_LENGTH,
    TruncationResult,
    format_size,
    truncate_head,
    truncate_line,
    truncate_tail,
)
from .write import (
    WriteOperations,
    WriteToolInput,
    create_write_tool,
    default_write_operations,
)

# ---------------------------------------------------------------------------
# Pre-built bundles (lazy, use os.getcwd at call-time)
# ---------------------------------------------------------------------------


def create_coding_tools(cwd: str | None = None) -> list[AgentTool]:
    """Default 4-tool bundle: read, bash, edit, write."""
    base = cwd or os.getcwd()
    return [
        create_read_tool(base),
        create_bash_tool(base),
        create_edit_tool(base),
        create_write_tool(base),
    ]


def create_read_only_tools(cwd: str | None = None) -> list[AgentTool]:
    """Read-only 4-tool bundle: read, grep, find, ls."""
    base = cwd or os.getcwd()
    return [
        create_read_tool(base),
        create_grep_tool(base),
        create_find_tool(base),
        create_ls_tool(base),
    ]


def create_all_tools(cwd: str | None = None) -> list[AgentTool]:
    """All 7 built-in tools."""
    base = cwd or os.getcwd()
    return [
        create_read_tool(base),
        create_bash_tool(base),
        create_edit_tool(base),
        create_write_tool(base),
        create_grep_tool(base),
        create_find_tool(base),
        create_ls_tool(base),
    ]


_TOOL_FACTORIES: dict[str, Callable[[str], AgentTool]] = {
    "read": create_read_tool,
    "bash": create_bash_tool,
    "edit": create_edit_tool,
    "write": create_write_tool,
    "grep": create_grep_tool,
    "find": create_find_tool,
    "ls": create_ls_tool,
}


def select_tools(names: Iterable[str], cwd: str | None = None) -> list[AgentTool]:
    """Build the named subset of built-in tools.

    Unknown names raise `KeyError` so typos surface immediately rather than
    silently dropping a tool.
    """
    base = cwd or os.getcwd()
    return [_TOOL_FACTORIES[n](base) for n in names]


__all__ = [
    "DEFAULT_MAX_BYTES",
    "DEFAULT_MAX_LINES",
    "GREP_MAX_LINE_LENGTH",
    "BashOperations",
    "BashToolDetails",
    "BashToolInput",
    "EditOperations",
    "EditToolDetails",
    "EditToolInput",
    "FindToolDetails",
    "FindToolInput",
    "GrepToolDetails",
    "GrepToolInput",
    "LsToolDetails",
    "LsToolInput",
    "ReadOperations",
    "ReadToolDetails",
    "ReadToolInput",
    "TruncationResult",
    "WriteOperations",
    "WriteToolInput",
    "create_all_tools",
    "create_bash_tool",
    "create_coding_tools",
    "create_edit_tool",
    "create_find_tool",
    "create_grep_tool",
    "create_ls_tool",
    "create_read_only_tools",
    "create_read_tool",
    "create_write_tool",
    "default_bash_operations",
    "default_edit_operations",
    "default_read_operations",
    "default_write_operations",
    "format_size",
    "select_tools",
    "truncate_head",
    "truncate_line",
    "truncate_tail",
]
