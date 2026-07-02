#!/usr/bin/env bash
set -euo pipefail

SKILL_FILE="$(dirname "$0")/SKILL.md"

if [[ ! -f "$SKILL_FILE" ]]; then
  echo "FAIL: SKILL.md not found"
  exit 1
fi

# Check frontmatter
if ! grep -q "^name: cu-wf-create$" "$SKILL_FILE"; then
  echo "FAIL: name not set to cu-wf-create"
  exit 1
fi

# Check references guides
if ! grep -q "guides/node-boundary-criteria.md" "$SKILL_FILE"; then
  echo "FAIL: doesn't reference node-boundary-criteria.md"
  exit 1
fi

echo "PASS: cu-wf-create skill structure valid"
