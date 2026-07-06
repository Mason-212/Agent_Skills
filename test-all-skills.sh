#!/usr/bin/env bash
set -euo pipefail

SKILLS_DIR="/Users/thomaschang/Documents/dev/git/thomaschangsf/skills"

echo "Testing all CU skills..."

# Test cu-setup
echo "→ Testing cu-setup..."
bash "$SKILLS_DIR/cu-setup/test-skill.sh"

# Test cu-wf-create guides
echo "→ Testing cu-wf-create guides..."
bash "$SKILLS_DIR/cu-wf-create/test-guides.sh"

# Test cu-wf-create skill
echo "→ Testing cu-wf-create skill..."
bash "$SKILLS_DIR/cu-wf-create/test-skill.sh"

# Test cu-wf-run
echo "→ Testing cu-wf-run..."
bash "$SKILLS_DIR/cu-wf-run/test-skill.sh"

# Check wiki_cu exists (can be directory or symlink)
if [[ ! -e "$SKILLS_DIR/shared/wiki_cu" ]]; then
  echo "FAIL: wiki_cu not found"
  exit 1
fi

echo ""
echo "✅ All skills tests PASSED"
