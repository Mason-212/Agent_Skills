"""Message and tool-call transforms shared across providers.

Partial port of vendor/pi-mono-upstream/packages/ai/src/providers/transform-messages.ts
and the tool-name normalization logic referenced by
anthropic-tool-name-normalization.test.ts / tool-call-id-normalization.test.ts.

Only the rules exercised by the four providers we support are ported; the
rest (Copilot, Mistral, Azure specifics) are out of scope.
"""

from __future__ import annotations

import re

from ..types import Tool

# Anthropic and some OpenAI-compat servers require tool names to match a narrow
# regex (letters, digits, underscore, dash). Anything outside is replaced with
# underscores; collisions are resolved with a short deterministic suffix.
_VALID_TOOL_NAME = re.compile(r"^[A-Za-z0-9_-]{1,64}$")
_INVALID_TOOL_NAME_CHARS = re.compile(r"[^A-Za-z0-9_-]")


def normalize_tool_name(name: str) -> str:
    """Return a name that satisfies _VALID_TOOL_NAME.

    Matches pi-ai's normalization for Anthropic. Preserves the input if already
    valid. Empty/whitespace-only names become 'tool'.
    """
    cleaned = _INVALID_TOOL_NAME_CHARS.sub("_", (name or "").strip())
    cleaned = cleaned[:64] or "tool"
    if not _VALID_TOOL_NAME.fullmatch(cleaned):
        cleaned = "tool"
    return cleaned


def build_tool_name_map(tools: list[Tool]) -> dict[str, str]:
    """Build a normalized->original tool name map.

    If two tools normalize to the same wire name, subsequent collisions get a
    numeric suffix (_2, _3, ...). The inverse map is what providers send to
    the LLM; `resolve_original_tool_name` walks it back.
    """
    wire_to_original: dict[str, str] = {}
    used: set[str] = set()
    for tool in tools:
        base = normalize_tool_name(tool.name)
        wire = base
        counter = 2
        while wire in used:
            wire = f"{base}_{counter}"[:64]
            counter += 1
        used.add(wire)
        wire_to_original[wire] = tool.name
    return wire_to_original


def resolve_original_tool_name(
    wire_name: str, wire_to_original: dict[str, str]
) -> str:
    """Return the original tool name for a normalized wire name, or the input."""
    return wire_to_original.get(wire_name, wire_name)


def normalize_tool_call_id(call_id: str | None, *, fallback_index: int = 0) -> str:
    """Coerce a tool-call id into a non-empty, stable string.

    Providers occasionally emit null / empty ids (seen in Gemini and some
    OpenAI Completions shims). Downstream code assumes ids are unique within a
    turn, so we fall back to a positional sentinel.
    """
    if call_id and call_id.strip():
        return call_id.strip()
    return f"call_{fallback_index}"


__all__ = [
    "build_tool_name_map",
    "normalize_tool_call_id",
    "normalize_tool_name",
    "resolve_original_tool_name",
]
