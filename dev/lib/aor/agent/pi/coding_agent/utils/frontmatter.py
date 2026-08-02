"""YAML-ish frontmatter parser (minimal).

Python port of `vendor/pi-mono-upstream/packages/coding-agent/src/utils/frontmatter.ts`.
Supports only flat `key: value` pairs plus booleans — enough for Agent
Skills spec. No nested structures, no lists.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

_FRONTMATTER = re.compile(r"^---\r?\n(.*?)\r?\n---\r?\n?", re.DOTALL)


@dataclass
class ParsedFrontmatter:
    frontmatter: dict[str, Any]
    content: str


def parse_frontmatter(text: str) -> ParsedFrontmatter:
    """Return frontmatter dict + remaining body content."""
    m = _FRONTMATTER.match(text)
    if not m:
        return ParsedFrontmatter({}, text)
    body = text[m.end():]
    fm: dict[str, Any] = {}
    for raw_line in m.group(1).splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if ":" not in line:
            continue
        key, _, value = line.partition(":")
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if value.lower() in ("true", "false"):
            fm[key] = value.lower() == "true"
        elif value == "":
            fm[key] = ""
        else:
            fm[key] = value
    return ParsedFrontmatter(fm, body)


__all__ = ["ParsedFrontmatter", "parse_frontmatter"]
