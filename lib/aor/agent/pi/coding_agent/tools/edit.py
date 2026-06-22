"""`edit` tool — surgical find/replace.

Python port of `coding-agent/src/core/tools/edit.ts`. Implements:

- BOM strip on input.
- Line-ending detection + restoration (CRLF/LF preservation).
- Exact match first, then a fuzzy normalization (collapses runs of
  whitespace and Unicode-space variants); rejects ambiguous replacements
  with >1 occurrence.
- Returns a unified diff in `details.diff`.
"""

from __future__ import annotations

import difflib
import os
import re
from dataclasses import dataclass
from typing import Any, Awaitable, Callable

from ...ai.types import TextContent
from ...core.types import AgentTool, AgentToolResult
from .path_utils import resolve_to_cwd

EditToolInput = dict[str, Any]


@dataclass
class EditToolDetails:
    diff: str
    first_changed_line: int | None = None


@dataclass
class EditOperations:
    read_file: Callable[[str], Awaitable[bytes]]
    write_file: Callable[[str, str], Awaitable[None]]
    access: Callable[[str], Awaitable[None]]


async def _default_read_file(path: str) -> bytes:
    with open(path, "rb") as f:
        return f.read()


async def _default_write_file(path: str, content: str) -> None:
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)


async def _default_access(path: str) -> None:
    if not os.access(path, os.R_OK | os.W_OK):
        raise PermissionError(f"Cannot read+write {path}")


default_edit_operations = EditOperations(
    read_file=_default_read_file, write_file=_default_write_file, access=_default_access
)


# ---------------------------------------------------------------------------
# Normalization helpers
# ---------------------------------------------------------------------------

_BOM = "\ufeff"
_UNICODE_SPACES_RE = re.compile("[\u00a0\u2000-\u200a\u202f\u205f\u3000]")


def _strip_bom(s: str) -> tuple[str, str]:
    if s.startswith(_BOM):
        return _BOM, s[len(_BOM):]
    return "", s


def _detect_line_ending(s: str) -> str:
    if "\r\n" in s:
        return "\r\n"
    return "\n"


def _normalize_to_lf(s: str) -> str:
    return s.replace("\r\n", "\n")


def _restore_line_endings(s: str, ending: str) -> str:
    if ending == "\n":
        return s
    return s.replace("\n", ending)


def _normalize_for_fuzzy(s: str) -> str:
    s = _UNICODE_SPACES_RE.sub(" ", s)
    return re.sub(r"[ \t]+", " ", s)


def _normalize_with_offsets(s: str) -> tuple[str, list[int]]:
    """Same normalization as `_normalize_for_fuzzy`, but also return an
    offset map so a match in the normalized string can be projected back
    onto the source.

    Returns ``(normalized, offsets)`` where ``offsets[i]`` is the start
    index in ``s`` of the character that produced ``normalized[i]`` and
    ``offsets[len(normalized)] == len(s)``. This sentinel makes it safe
    to compute the source end of a match as ``offsets[match_end]``.
    """
    out_chars: list[str] = []
    offsets: list[int] = []
    i = 0
    n = len(s)
    while i < n:
        ch = s[i]
        if _UNICODE_SPACES_RE.match(ch):
            ch = " "
        if ch == " " or ch == "\t":
            out_chars.append(" ")
            offsets.append(i)
            j = i + 1
            while j < n and (s[j] == " " or s[j] == "\t" or _UNICODE_SPACES_RE.match(s[j])):
                j += 1
            i = j
        else:
            out_chars.append(ch)
            offsets.append(i)
            i += 1
    offsets.append(n)
    return "".join(out_chars), offsets


@dataclass
class _MatchResult:
    found: bool
    # Source offsets into the *original* (post-LF, pre-fuzzy) content. The
    # span ``content[index:end]`` is what should be replaced, preserving
    # all surrounding whitespace verbatim.
    index: int = -1
    end: int = -1


def _fuzzy_find(content: str, old: str) -> _MatchResult:
    idx = content.find(old)
    if idx >= 0:
        return _MatchResult(found=True, index=idx, end=idx + len(old))

    fuzzy_content, offsets = _normalize_with_offsets(content)
    fuzzy_old = _normalize_for_fuzzy(old)
    fidx = fuzzy_content.find(fuzzy_old)
    if fidx >= 0:
        return _MatchResult(
            found=True,
            index=offsets[fidx],
            end=offsets[fidx + len(fuzzy_old)],
        )
    return _MatchResult(found=False)


def _generate_diff(old: str, new: str) -> tuple[str, int | None]:
    diff_lines = list(
        difflib.unified_diff(old.splitlines(keepends=True), new.splitlines(keepends=True), lineterm="")
    )
    diff = "\n".join(diff_lines)
    first_changed: int | None = None
    new_idx = 0
    for line in diff_lines:
        if line.startswith("@@"):
            m = re.match(r"@@ -\d+(?:,\d+)? \+(\d+)", line)
            if m:
                new_idx = int(m.group(1))
            continue
        if line.startswith("+") and not line.startswith("+++"):
            first_changed = new_idx
            break
        if not line.startswith("-"):
            new_idx += 1
    return diff, first_changed


_EDIT_PARAMS_SCHEMA = {
    "type": "object",
    "properties": {
        "path": {"type": "string", "description": "Path to the file to edit (relative or absolute)"},
        "oldText": {"type": "string", "description": "Exact text to find and replace (must match exactly)"},
        "newText": {"type": "string", "description": "New text to replace the old text with"},
    },
    "required": ["path", "oldText", "newText"],
}


def create_edit_tool(cwd: str, *, operations: EditOperations | None = None) -> AgentTool:
    ops = operations or default_edit_operations

    async def execute(
        _tool_call_id: str,
        args: dict[str, Any],
        signal=None,
        on_update=None,
    ) -> AgentToolResult:
        if signal and signal.aborted:
            raise RuntimeError("Operation aborted")
        path = args["path"]
        old_text = args["oldText"]
        new_text = args["newText"]
        absolute = resolve_to_cwd(path, cwd)

        try:
            await ops.access(absolute)
        except Exception:
            raise FileNotFoundError(f"File not found: {path}") from None

        buf = await ops.read_file(absolute)
        raw = buf.decode("utf-8", errors="replace")

        bom, content = _strip_bom(raw)
        original_ending = _detect_line_ending(content)
        normalized = _normalize_to_lf(content)
        normalized_old = _normalize_to_lf(old_text)
        normalized_new = _normalize_to_lf(new_text)

        match = _fuzzy_find(normalized, normalized_old)
        if not match.found:
            raise ValueError(
                f"Could not find the exact text in {path}. The old text must match exactly "
                "including all whitespace and newlines."
            )

        fuzzy_content = _normalize_for_fuzzy(normalized)
        fuzzy_old = _normalize_for_fuzzy(normalized_old)
        occurrences = fuzzy_content.count(fuzzy_old)
        if occurrences > 1:
            raise ValueError(
                f"Found {occurrences} occurrences of the text in {path}. The text must be unique. "
                "Please provide more context to make it unique."
            )

        new_content = (
            normalized[: match.index] + normalized_new + normalized[match.end :]
        )
        if normalized == new_content:
            raise ValueError(
                f"No changes made to {path}. The replacement produced identical content."
            )

        final = bom + _restore_line_endings(new_content, original_ending)
        await ops.write_file(absolute, final)

        diff, first_changed = _generate_diff(normalized, new_content)
        return AgentToolResult(
            content=[TextContent(type="text", text=f"Successfully replaced text in {path}.")],
            details=EditToolDetails(diff=diff, first_changed_line=first_changed),
        )

    return AgentTool(
        name="edit",
        label="edit",
        description=(
            "Edit a file by replacing exact text. The oldText must match exactly "
            "(including whitespace). Use this for precise, surgical edits."
        ),
        parameters=_EDIT_PARAMS_SCHEMA,
        execute=execute,
    )


__all__ = ["EditOperations", "EditToolDetails", "EditToolInput", "create_edit_tool", "default_edit_operations"]
