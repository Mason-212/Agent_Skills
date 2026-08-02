"""Partial JSON parsing for streaming tool arguments.

Python port of vendor/pi-mono-upstream/packages/ai/src/utils/json-parse.ts.

pi-ai uses the `partial-json` npm package. Python lacks a drop-in equivalent
so we implement a pragmatic fallback: try strict json.loads first, then a
best-effort completion by closing unbalanced containers/strings. This handles
the common case of mid-stream JSON fragments emitted by OpenAI / Anthropic /
Gemini while tool arguments are still assembling.
"""

from __future__ import annotations

import json
from typing import Any


def parse_streaming_json(partial_json: str | None) -> Any:
    """Best-effort parse of a possibly-incomplete JSON string.

    Never raises. Returns {} on unparseable input, matching pi-ai's contract.
    """
    if not partial_json or not partial_json.strip():
        return {}
    try:
        return json.loads(partial_json)
    except json.JSONDecodeError:
        completed = _try_complete(partial_json)
        if completed is None:
            return {}
        try:
            return json.loads(completed)
        except json.JSONDecodeError:
            return {}


def _try_complete(text: str) -> str | None:
    """Close unbalanced strings/braces/brackets. Returns None if irrecoverable.

    Only double-quoted strings are recognized: JSON does not permit
    single-quoted strings, and treating `'` as a delimiter would incorrectly
    swallow apostrophes that appear inside valid JSON string content.
    """
    out = []
    stack: list[str] = []
    in_string = False
    escape = False

    for ch in text:
        if in_string:
            out.append(ch)
            if escape:
                escape = False
            elif ch == "\\":
                escape = True
            elif ch == '"':
                in_string = False
            continue

        if ch == '"':
            in_string = True
            out.append(ch)
            continue

        if ch in "{[":
            stack.append(ch)
        elif ch in "}]":
            if not stack:
                return None
            stack.pop()
        out.append(ch)

    if in_string:
        out.append('"')
    while stack:
        # Strip any trailing whitespace + comma before inserting the closer, so
        # `[1, 2,` -> `[1, 2]` and `{"a": 1,` -> `{"a": 1}`.
        while out and out[-1] in (" ", "\t", "\n", "\r"):
            out.pop()
        if out and out[-1] == ",":
            out.pop()
        opener = stack.pop()
        out.append("}" if opener == "{" else "]")
    return "".join(out)


__all__ = ["parse_streaming_json"]
