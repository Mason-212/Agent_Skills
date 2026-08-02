#!/usr/bin/env bash
# Start Arize Phoenix trace viewer for dev/lib/aor packs.
# Traces appear at http://localhost:6006 while this is running.
#
# Prerequisites:
#   1. dev/lib/aor/.env exists with PHOENIX_TRACING=true
#   2. uv is installed (https://docs.astral.sh/uv/)
#
# Usage: ./dev/scripts/start_aor_tracing.sh

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
LIB_AOR="$REPO_ROOT/dev/lib/aor"

if [[ ! -f "$LIB_AOR/.env" ]]; then
  echo "ERROR: $LIB_AOR/.env not found."
  echo "       Run: cp $LIB_AOR/.env.example $LIB_AOR/.env"
  echo "       Then set PHOENIX_TRACING=true in that file."
  exit 1
fi

if ! grep -q "PHOENIX_TRACING=true" "$LIB_AOR/.env"; then
  echo "WARNING: PHOENIX_TRACING is not set to true in $LIB_AOR/.env"
  echo "         Packs will run without sending traces to Phoenix."
  echo ""
fi

echo ""
echo "Starting Arize Phoenix trace viewer..."
echo ""
echo "  View traces : http://localhost:6006"
echo "  Stop server : Ctrl+C"
echo ""
echo "While this is running, any pack invocation with PHOENIX_TRACING=true"
echo "will send traces here automatically. Look for:"
echo "  - aor.node.*   spans  — per DAG node (attempt, prompt/response length)"
echo "  - aor.llm_call spans  — per LLM call (provider, model)"
echo "  - aor.policy.* spans  — per policy decision (action, next node, reason)"
echo ""

cd "$LIB_AOR"
exec uv run python -m phoenix.server.main serve
