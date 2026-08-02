#!/usr/bin/env bash
# Run all static checks for lib/aor.
# Usage: cd lib/aor && ./check.sh
set -euo pipefail

TARGETS="agent/ orchestrator/ packs/"

echo "==> ruff"
uv run ruff check $TARGETS

echo "==> pyright"
uv run pyright $TARGETS

echo ""
echo "CHECK PASSED"
