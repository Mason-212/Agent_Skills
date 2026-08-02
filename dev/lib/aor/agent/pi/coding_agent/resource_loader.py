"""Load project/global context files (AGENTS.md chain).

Python port of `vendor/pi-mono-upstream/packages/coding-agent/src/core/resource-loader.ts`.

Scope: we only load `AGENTS.md`-style context files. Skills/extensions have
their own loaders. `load_context_files` walks from `cwd` up to the
filesystem root collecting any `AGENTS.md`; then reads the agent-dir global
one (`{agent_dir}/AGENTS.md`).
"""

from __future__ import annotations

import os
from dataclasses import dataclass

from .config import get_agent_dir

_CONTEXT_FILENAMES = ("AGENTS.md",)


@dataclass
class ContextFile:
    path: str
    content: str


def _read_safe(path: str) -> str | None:
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except OSError:
        return None


def load_context_files(
    cwd: str | None = None,
    *,
    include_global: bool = True,
    extra_paths: list[str] | None = None,
) -> list[ContextFile]:
    """Walk `cwd → /` collecting AGENTS.md; add global agent-dir AGENTS.md."""
    out: list[ContextFile] = []
    seen: set[str] = set()

    def _add(path: str) -> None:
        abs_path = os.path.abspath(path)
        if abs_path in seen or not os.path.isfile(abs_path):
            return
        content = _read_safe(abs_path)
        if content is None:
            return
        seen.add(abs_path)
        out.append(ContextFile(path=abs_path, content=content))

    if include_global:
        global_file = os.path.join(str(get_agent_dir()), "AGENTS.md")
        _add(global_file)

    current = os.path.abspath(cwd or os.getcwd())
    while True:
        for name in _CONTEXT_FILENAMES:
            _add(os.path.join(current, name))
        parent = os.path.dirname(current)
        if parent == current:
            break
        current = parent

    for extra in extra_paths or []:
        _add(os.path.expanduser(extra))

    return out


__all__ = ["ContextFile", "load_context_files"]
