#!/usr/bin/env bash
# Test cu-setup skill by simulating invocation

set -euo pipefail

SKILL_FILE="/Users/thomaschang/Documents/dev/git/thomaschangsf/skills/cu-setup/SKILL.md"

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
if ! grep -q "^name: cu-setup$" "$SKILL_FILE"; then
  echo "FAIL: name not set to cu-setup"
  exit 1
fi

echo "PASS: cu-setup skill structure valid"
