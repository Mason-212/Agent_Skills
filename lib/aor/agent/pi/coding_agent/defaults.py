"""Default constants for `agent.pi.coding_agent`.

Mirrors `vendor/pi-mono-upstream/packages/coding-agent/src/core/defaults.ts`
plus the compaction default settings from `compaction/compaction.ts` and the
session schema version from `session-manager.ts`.
"""

from __future__ import annotations

from typing import Literal

ThinkingLevel = Literal["off", "minimal", "low", "medium", "high", "xhigh"]

DEFAULT_THINKING_LEVEL: ThinkingLevel = "medium"
"""Default reasoning effort. Matches upstream `defaults.ts`."""

CURRENT_SESSION_VERSION = 3
"""JSONL session-file schema version. Mirrors `session-manager.ts` line 27."""

DEFAULT_TOOL_NAMES: tuple[str, ...] = ("read", "bash", "edit", "write")
"""Tool names enabled by default for `create_agent_session`."""

READ_ONLY_TOOL_NAMES: tuple[str, ...] = ("read", "grep", "find", "ls")
"""Tool names enabled for the `--tools read,grep,find,ls` profile."""

ALL_TOOL_NAMES: tuple[str, ...] = ("read", "bash", "edit", "write", "grep", "find", "ls")

__all__ = [
    "ALL_TOOL_NAMES",
    "CURRENT_SESSION_VERSION",
    "DEFAULT_THINKING_LEVEL",
    "DEFAULT_TOOL_NAMES",
    "READ_ONLY_TOOL_NAMES",
    "ThinkingLevel",
]
