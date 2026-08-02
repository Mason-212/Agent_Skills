"""Entry point for `uv run check` — runs ruff + pyright over the aor source tree."""

import subprocess
import sys
from pathlib import Path

TARGETS = ["agent", "orchestrator", "packs"]


def main() -> None:
    root = Path(__file__).parent.parent
    failed = False

    for tool, cmd in [
        ("ruff", ["ruff", "check"] + TARGETS),
        ("pyright", ["pyright"] + TARGETS),
        ("pytest", ["pytest", "tests/"]),
    ]:
        print(f"==> {tool}", flush=True)
        result = subprocess.run(cmd, cwd=root)
        if result.returncode != 0:
            failed = True

    if failed:
        sys.exit(1)
    print("\nCHECK PASSED")
