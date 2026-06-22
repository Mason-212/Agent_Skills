"""Path helpers shared by the file-touching tools.

Python port of `vendor/pi-mono-upstream/packages/coding-agent/src/core/tools/path-utils.ts`.

We preserve the macOS screenshot-name fallbacks (NFD form, narrow no-break
space before AM/PM, U+2019 curly apostrophe). These exist because the LLM
typically receives paths as the user typed them but the filesystem encodes
them differently.
"""

from __future__ import annotations

import os
import re
import unicodedata
from pathlib import Path

UNICODE_SPACES = re.compile("[\u00a0\u2000-\u200a\u202f\u205f\u3000]")
NARROW_NO_BREAK_SPACE = "\u202f"


def _normalize_unicode_spaces(s: str) -> str:
    return UNICODE_SPACES.sub(" ", s)


def _normalize_at_prefix(s: str) -> str:
    return s[1:] if s.startswith("@") else s


def expand_path(file_path: str) -> str:
    """Expand ~ and normalize unicode spaces (mirror of upstream)."""
    normalized = _normalize_unicode_spaces(_normalize_at_prefix(file_path))
    if normalized == "~":
        return str(Path.home())
    if normalized.startswith("~/"):
        return str(Path.home()) + normalized[1:]
    return normalized


def resolve_to_cwd(file_path: str, cwd: str) -> str:
    """Resolve a path against `cwd`, honoring absolute paths and ~."""
    expanded = expand_path(file_path)
    p = Path(expanded)
    if p.is_absolute():
        return str(p)
    return str((Path(cwd) / p).resolve(strict=False))


def _try_macos_am_pm(path: str) -> str:
    return re.sub(r" (AM|PM)\.", f"{NARROW_NO_BREAK_SPACE}\\1.", path)


def _try_nfd(path: str) -> str:
    return unicodedata.normalize("NFD", path)


def _try_curly_quote(path: str) -> str:
    return path.replace("'", "\u2019")


def resolve_read_path(file_path: str, cwd: str) -> str:
    """Resolve a path with macOS-friendly fallbacks for read operations."""
    resolved = resolve_to_cwd(file_path, cwd)
    if os.path.exists(resolved):
        return resolved

    am_pm = _try_macos_am_pm(resolved)
    if am_pm != resolved and os.path.exists(am_pm):
        return am_pm

    nfd = _try_nfd(resolved)
    if nfd != resolved and os.path.exists(nfd):
        return nfd

    curly = _try_curly_quote(resolved)
    if curly != resolved and os.path.exists(curly):
        return curly

    nfd_curly = _try_curly_quote(nfd)
    if nfd_curly != resolved and os.path.exists(nfd_curly):
        return nfd_curly

    return resolved


__all__ = ["expand_path", "resolve_read_path", "resolve_to_cwd"]
