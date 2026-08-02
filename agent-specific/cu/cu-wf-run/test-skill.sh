#!/usr/bin/env bash
set -euo pipefail

SKILL_FILE="$(dirname "$0")/SKILL.md"

if [[ ! -f "$SKILL_FILE" ]]; then
  echo "FAIL: SKILL.md not found"
  exit 1
fi

# Check frontmatter exists
if ! grep -q "^---$" "$SKILL_FILE"; then
  echo "FAIL: No frontmatter found"
  exit 1
fi

# Check skill name
if ! grep -q "^name: cu-wf-run$" "$SKILL_FILE"; then
  echo "FAIL: name not set to cu-wf-run"
  exit 1
fi

# Check mentions cu workflow run command
if ! grep -q "cu workflow run" "$SKILL_FILE"; then
  echo "FAIL: doesn't reference cu workflow run command"
  exit 1
fi

echo "PASS: cu-wf-run skill structure valid"
