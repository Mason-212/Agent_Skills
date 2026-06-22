"""Output truncation utilities.

Python port of `vendor/pi-mono-upstream/packages/coding-agent/src/core/tools/truncate.ts`.

Two limits independently bound an output: lines and bytes. Whichever fires
first wins. `truncate_head` keeps the start (used by file reads),
`truncate_tail` keeps the end (used by bash output where the interesting
bits — errors, results — live near the end).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

DEFAULT_MAX_LINES = 2000
DEFAULT_MAX_BYTES = 50 * 1024
GREP_MAX_LINE_LENGTH = 500


@dataclass
class TruncationResult:
    content: str
    truncated: bool
    truncated_by: Literal["lines", "bytes", None]
    total_lines: int
    total_bytes: int
    output_lines: int
    output_bytes: int
    last_line_partial: bool
    first_line_exceeds_limit: bool
    max_lines: int
    max_bytes: int


def format_size(b: int) -> str:
    if b < 1024:
        return f"{b}B"
    if b < 1024 * 1024:
        return f"{b / 1024:.1f}KB"
    return f"{b / (1024 * 1024):.1f}MB"


def _utf8_len(s: str) -> int:
    return len(s.encode("utf-8"))


def truncate_head(
    content: str, *, max_lines: int = DEFAULT_MAX_LINES, max_bytes: int = DEFAULT_MAX_BYTES
) -> TruncationResult:
    total_bytes = _utf8_len(content)
    lines = content.split("\n")
    total_lines = len(lines)

    if total_lines <= max_lines and total_bytes <= max_bytes:
        return TruncationResult(
            content=content,
            truncated=False,
            truncated_by=None,
            total_lines=total_lines,
            total_bytes=total_bytes,
            output_lines=total_lines,
            output_bytes=total_bytes,
            last_line_partial=False,
            first_line_exceeds_limit=False,
            max_lines=max_lines,
            max_bytes=max_bytes,
        )

    first_line_bytes = _utf8_len(lines[0])
    if first_line_bytes > max_bytes:
        return TruncationResult(
            content="",
            truncated=True,
            truncated_by="bytes",
            total_lines=total_lines,
            total_bytes=total_bytes,
            output_lines=0,
            output_bytes=0,
            last_line_partial=False,
            first_line_exceeds_limit=True,
            max_lines=max_lines,
            max_bytes=max_bytes,
        )

    out: list[str] = []
    out_bytes = 0
    truncated_by: Literal["lines", "bytes"] = "lines"
    for i, line in enumerate(lines):
        if i >= max_lines:
            break
        line_bytes = _utf8_len(line) + (1 if i > 0 else 0)
        if out_bytes + line_bytes > max_bytes:
            truncated_by = "bytes"
            break
        out.append(line)
        out_bytes += line_bytes

    if len(out) >= max_lines and out_bytes <= max_bytes:
        truncated_by = "lines"

    out_str = "\n".join(out)
    return TruncationResult(
        content=out_str,
        truncated=True,
        truncated_by=truncated_by,
        total_lines=total_lines,
        total_bytes=total_bytes,
        output_lines=len(out),
        output_bytes=_utf8_len(out_str),
        last_line_partial=False,
        first_line_exceeds_limit=False,
        max_lines=max_lines,
        max_bytes=max_bytes,
    )


def _truncate_string_to_bytes_from_end(s: str, max_bytes: int) -> str:
    buf = s.encode("utf-8")
    if len(buf) <= max_bytes:
        return s
    start = len(buf) - max_bytes
    while start < len(buf) and (buf[start] & 0xC0) == 0x80:
        start += 1
    return buf[start:].decode("utf-8", errors="replace")


def truncate_tail(
    content: str, *, max_lines: int = DEFAULT_MAX_LINES, max_bytes: int = DEFAULT_MAX_BYTES
) -> TruncationResult:
    total_bytes = _utf8_len(content)
    lines = content.split("\n")
    total_lines = len(lines)

    if total_lines <= max_lines and total_bytes <= max_bytes:
        return TruncationResult(
            content=content,
            truncated=False,
            truncated_by=None,
            total_lines=total_lines,
            total_bytes=total_bytes,
            output_lines=total_lines,
            output_bytes=total_bytes,
            last_line_partial=False,
            first_line_exceeds_limit=False,
            max_lines=max_lines,
            max_bytes=max_bytes,
        )

    out: list[str] = []
    out_bytes = 0
    truncated_by: Literal["lines", "bytes"] = "lines"
    last_line_partial = False
    i = len(lines) - 1
    while i >= 0 and len(out) < max_lines:
        line = lines[i]
        line_bytes = _utf8_len(line) + (1 if len(out) > 0 else 0)
        if out_bytes + line_bytes > max_bytes:
            truncated_by = "bytes"
            if len(out) == 0:
                truncated_line = _truncate_string_to_bytes_from_end(line, max_bytes)
                out.insert(0, truncated_line)
                out_bytes = _utf8_len(truncated_line)
                last_line_partial = True
            break
        out.insert(0, line)
        out_bytes += line_bytes
        i -= 1

    if len(out) >= max_lines and out_bytes <= max_bytes:
        truncated_by = "lines"

    out_str = "\n".join(out)
    return TruncationResult(
        content=out_str,
        truncated=True,
        truncated_by=truncated_by,
        total_lines=total_lines,
        total_bytes=total_bytes,
        output_lines=len(out),
        output_bytes=_utf8_len(out_str),
        last_line_partial=last_line_partial,
        first_line_exceeds_limit=False,
        max_lines=max_lines,
        max_bytes=max_bytes,
    )


def truncate_line(line: str, max_chars: int = GREP_MAX_LINE_LENGTH) -> tuple[str, bool]:
    """Truncate a single line for grep output."""
    if len(line) <= max_chars:
        return line, False
    return f"{line[:max_chars]}... [truncated]", True


__all__ = [
    "DEFAULT_MAX_BYTES",
    "DEFAULT_MAX_LINES",
    "GREP_MAX_LINE_LENGTH",
    "TruncationResult",
    "format_size",
    "truncate_head",
    "truncate_line",
    "truncate_tail",
]
