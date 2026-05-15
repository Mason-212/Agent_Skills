#!/usr/bin/env bash
# dev_refresh_skills_and_tools_and_claudemd.sh
#
# Enhanced version of dev_refresh_skills_and_tools.sh that also:
# 1. Runs all functionality from dev_refresh_skills_and_tools.sh
# 2. Copies CLAUDE_USER.md to ~/.claude/CLAUDE.md
#
# Usage:
#   ./scripts/dev_refresh_skills_and_tools_and_claudemd.sh
#   TOOLS_MODE=github bash scripts/dev_refresh_skills_and_tools_and_claudemd.sh

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

echo "═══════════════════════════════════════════════════════════════"
echo "  Refreshing Skills, Tools, and CLAUDE.md"
echo "═══════════════════════════════════════════════════════════════"
echo ""

# ---------------------------------------------------------------------------
# Part 1: Run dev_refresh_skills_and_tools.sh
# ---------------------------------------------------------------------------

echo "🔄 Part 1: Running dev_refresh_skills_and_tools.sh"
echo "─────────────────────────────────────────────────────────────────"
echo ""

DEV_REFRESH_SCRIPT="${SCRIPT_DIR}/dev_refresh_skills_and_tools.sh"

if [[ ! -f "${DEV_REFRESH_SCRIPT}" ]]; then
  echo "❌ Error: ${DEV_REFRESH_SCRIPT} not found" >&2
  exit 1
fi

if [[ ! -x "${DEV_REFRESH_SCRIPT}" ]]; then
  echo "Making ${DEV_REFRESH_SCRIPT} executable..."
  chmod +x "${DEV_REFRESH_SCRIPT}"
fi

# Run the original script with same environment variables
bash "${DEV_REFRESH_SCRIPT}"

echo ""
echo "✅ Skills and tools refresh complete"
echo ""

# ---------------------------------------------------------------------------
# Part 2: Copy CLAUDE_USER.md to ~/.claude/CLAUDE.md
# ---------------------------------------------------------------------------

echo "📝 Part 2: Updating CLAUDE.md"
echo "─────────────────────────────────────────────────────────────────"

CLAUDE_USER_MD="${REPO_ROOT}/use_cases/claude/CLAUDE_USER.md"
CLAUDE_MD_DEST="${HOME}/.claude/CLAUDE.md"

if [[ ! -f "${CLAUDE_USER_MD}" ]]; then
  echo "❌ Error: ${CLAUDE_USER_MD} not found" >&2
  echo "   Expected location: use_cases/claude/CLAUDE_USER.md" >&2
  exit 1
fi

# Backup existing CLAUDE.md if it exists
if [[ -f "${CLAUDE_MD_DEST}" ]]; then
  BACKUP_FILE="${CLAUDE_MD_DEST}.backup.$(date +%Y%m%d_%H%M%S)"
  cp "${CLAUDE_MD_DEST}" "${BACKUP_FILE}"
  echo "Backed up existing CLAUDE.md to: ${BACKUP_FILE}"
fi

# Create ~/.claude directory if it doesn't exist
mkdir -p "$(dirname "${CLAUDE_MD_DEST}")"

# Copy CLAUDE_USER.md to ~/.claude/CLAUDE.md
cp "${CLAUDE_USER_MD}" "${CLAUDE_MD_DEST}"
echo "✅ Copied ${CLAUDE_USER_MD}"
echo "   → ${CLAUDE_MD_DEST}"

echo ""
echo "═══════════════════════════════════════════════════════════════"
echo "✅ All Done!"
echo "═══════════════════════════════════════════════════════════════"
echo ""
echo "Summary:"
echo "  • Skills refreshed for: cursor, claude-code, cline"
echo "  • MCP plugins configured in Claude Code and Cursor"
echo "  • CLAUDE.md updated with user preferences"
echo ""
echo "Next steps:"
echo "  • Restart Claude Code to load updated configuration"
echo "  • Restart Cursor to load updated configuration"
echo "  • Run /reload-plugins in Claude Code to reload skills"
echo ""
