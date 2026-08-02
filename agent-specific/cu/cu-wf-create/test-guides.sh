#!/usr/bin/env bash
set -euo pipefail

GUIDES_DIR="/Users/thomaschang/Documents/dev/git/thomaschangsf/skills/cu-wf-create/guides"

if [[ ! -d "$GUIDES_DIR" ]]; then
  echo "FAIL: guides directory not found"
  exit 1
fi

FILES=("node-boundary-criteria.md" "domain-detection.md" "agent-strategy.md")
for file in "${FILES[@]}"; do
  if [[ ! -f "$GUIDES_DIR/$file" ]]; then
    echo "FAIL: $file not found"
    exit 1
  fi
done

echo "PASS: All guide files exist"
