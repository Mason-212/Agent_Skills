"""User-config paths for `agent.pi.coding_agent`.

Mirrors `vendor/pi-mono-upstream/packages/coding-agent/src/config.ts` — the
"where do skills, extensions, prompts, sessions live" knobs.

Notable differences from upstream:

- We omit Bun/jiti binary detection. The Python loader uses `importlib`.
- `agent_dir` defaults to `~/.pi/agent-py` to avoid colliding with a
  TypeScript install on the same machine.
- Documentation paths are unused in the Python port (we don't ship a docs/
  tree); they are defined for parity with the TS system-prompt builder so
  callers can override.
"""

from __future__ import annotations

import os
from pathlib import Path

CONFIG_DIR_NAME = ".pi"
"""Project-local config directory (mirrors upstream)."""

DEFAULT_AGENT_DIRNAME = "agent-py"


def get_agent_dir() -> Path:
    """Resolve the global agent config directory.

    Honors the `PI_AGENT_DIR` environment variable as an explicit override.
    Default is `~/.pi/agent-py`.
    """
    override = os.environ.get("PI_AGENT_DIR")
    if override:
        return Path(override).expanduser()
    return Path.home() / CONFIG_DIR_NAME / DEFAULT_AGENT_DIRNAME


def get_project_config_dir(cwd: Path | str) -> Path:
    """Project-local `.pi/` directory."""
    return Path(cwd) / CONFIG_DIR_NAME


def get_readme_path() -> str:
    """Stub: documentation root path (Python port has no docs tree)."""
    return os.environ.get("PI_README_PATH", "")


def get_docs_path() -> str:
    return os.environ.get("PI_DOCS_PATH", "")


def get_examples_path() -> str:
    return os.environ.get("PI_EXAMPLES_PATH", "")


__all__ = [
    "CONFIG_DIR_NAME",
    "DEFAULT_AGENT_DIRNAME",
    "get_agent_dir",
    "get_docs_path",
    "get_examples_path",
    "get_project_config_dir",
    "get_readme_path",
]
