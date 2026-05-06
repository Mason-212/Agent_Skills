#!/usr/bin/env bash
# dev_refresh_skills_and_tools.sh
#
# Unified script to:
# 1. Install/refresh global skills package for multiple agent targets
# 2. Install/refresh MCP tools to Claude Code settings
#
# ---------------------------------------------------------------------------
# Skills Installation (via npx skills CLI)
# ---------------------------------------------------------------------------
#
# Skills are installed to:
# - ~/.cursor/skills/<skill-name>/
# - ~/.claude/skills/<skill-name>/
# - ~/.agents/skills/<skill-name>/
#
# ---------------------------------------------------------------------------
# MCP Tools Installation
# ---------------------------------------------------------------------------
#
# MCP tools are configured in:
# - ~/.claude/settings.json (Claude Code)
# - ~/.cursor/mcp.json (Cursor)
#
# For local development, tools point to absolute paths.
# For sharing, tools use: github:thomaschangsf/skills#tools/<tool-name>
#
# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
#
# SKILLS_GIT_REMOTE_PREFIX — SSH host and org/user (default: git@github.com:thomaschangsf)
# SKILLS_SSH_URL   — Full Git SSH URL (default: ${SKILLS_GIT_REMOTE_PREFIX}/skills.git)
# SKILLS_PACKAGE_PATH — Absolute path to this repo for local development
# SKILLS_AGENTS    — Space-separated agent ids (default: cursor claude-code cline)
# TOOLS_MODE       — "local" for development, "github" for sharing (default: local)
#
# Usage:
#   ./scripts/dev_refresh_skills_and_tools.sh
#   TOOLS_MODE=github bash scripts/dev_refresh_skills_and_tools.sh

set -euo pipefail

SKILLS_GIT_REMOTE_PREFIX="${SKILLS_GIT_REMOTE_PREFIX:-git@github.com:thomaschangsf}"
SKILLS_SSH_URL="${SKILLS_SSH_URL:-${SKILLS_GIT_REMOTE_PREFIX}/skills.git}"
SKILLS_AGENTS="${SKILLS_AGENTS:-cursor claude-code cline}"
TOOLS_MODE="${TOOLS_MODE:-local}"

CURSOR_SKILLS="${HOME}/.cursor/skills"
CLAUDE_SKILLS="${HOME}/.claude/skills"
AGENTS_SKILLS="${HOME}/.agents/skills"
CLAUDE_SETTINGS="${HOME}/.claude/settings.json"
CURSOR_MCP="${HOME}/.cursor/mcp.json"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

echo "═══════════════════════════════════════════════════════════════"
echo "  Refreshing Skills and Tools"
echo "═══════════════════════════════════════════════════════════════"
echo ""

# ---------------------------------------------------------------------------
# Part 1: Refresh Skills
# ---------------------------------------------------------------------------

echo "📚 Part 1: Installing/Refreshing Skills"
echo "─────────────────────────────────────────────────────────────────"

agent_args=()
read -r -a _agents <<< "${SKILLS_AGENTS}"
for a in "${_agents[@]}"; do
  [[ -n "${a}" ]] || continue
  agent_args+=(-a "${a}")
done

if (( ${#agent_args[@]} == 0 )); then
  echo "❌ SKILLS_AGENTS is empty; set it to a space-separated list (e.g. cursor claude-code cline)." >&2
  exit 1
fi

skills_package="${SKILLS_SSH_URL}"
if [[ -n "${SKILLS_PACKAGE_PATH:-}" ]]; then
  if [[ ! -d "${SKILLS_PACKAGE_PATH}/skills" ]]; then
    echo "❌ SKILLS_PACKAGE_PATH must point at repo root (directory containing skills/). Got: ${SKILLS_PACKAGE_PATH}" >&2
    exit 1
  fi
  skills_package="$(cd "${SKILLS_PACKAGE_PATH}" && pwd)"
  echo "Using local package path: ${skills_package}"
else
  # Auto-detect if we're in the repo
  if [[ -d "${REPO_ROOT}/skills" ]]; then
    skills_package="${REPO_ROOT}"
    echo "Auto-detected local repo: ${skills_package}"
    echo "(Using local skills/ directory for unpushed changes)"
  else
    echo "Using remote package: ${skills_package}"
    echo "(Unpushed commits not included. Set SKILLS_PACKAGE_PATH=${REPO_ROOT} for local install)"
  fi
fi

echo "Registering/refreshing global package for agents: ${SKILLS_AGENTS}"
npx skills add -g -y "${skills_package}" "${agent_args[@]}" --all --copy

echo "Updating global skills..."
npx skills update -g

echo "✅ Skills refreshed:"
echo "   Cursor:       ${CURSOR_SKILLS}"
echo "   Claude Code:  ${CLAUDE_SKILLS}"
echo "   Shared tree:  ${AGENTS_SKILLS}"
echo ""

# ---------------------------------------------------------------------------
# Part 2: Configure MCP Tools
# ---------------------------------------------------------------------------

echo "🔧 Part 2: Configuring MCP Tools"
echo "─────────────────────────────────────────────────────────────────"

# Find all tools in tools/ directory
TOOLS_DIR="${REPO_ROOT}/tools"
if [[ ! -d "${TOOLS_DIR}" ]]; then
  echo "⚠️  No tools/ directory found. Skipping MCP tools configuration."
  exit 0
fi

tools_found=()
while IFS= read -r -d '' tool_dir; do
  tool_name="$(basename "${tool_dir}")"
  if [[ -f "${tool_dir}/index.js" && -f "${tool_dir}/package.json" ]]; then
    tools_found+=("${tool_name}")
  fi
done < <(find "${TOOLS_DIR}" -mindepth 1 -maxdepth 1 -type d -print0)

if (( ${#tools_found[@]} == 0 )); then
  echo "⚠️  No MCP tools found in ${TOOLS_DIR}"
  exit 0
fi

echo "Found ${#tools_found[@]} MCP tool(s): ${tools_found[*]}"
echo ""

# Create or update Claude Code settings
if [[ ! -f "${CLAUDE_SETTINGS}" ]]; then
  echo "Creating new Claude settings file: ${CLAUDE_SETTINGS}"
  mkdir -p "$(dirname "${CLAUDE_SETTINGS}")"
  echo '{"mcpServers":{}}' > "${CLAUDE_SETTINGS}"
fi

# Create or update Cursor MCP config
if [[ ! -f "${CURSOR_MCP}" ]]; then
  echo "Creating new Cursor MCP file: ${CURSOR_MCP}"
  mkdir -p "$(dirname "${CURSOR_MCP}")"
  echo '{"mcpServers":{}}' > "${CURSOR_MCP}"
fi

# Backup existing settings
cp "${CLAUDE_SETTINGS}" "${CLAUDE_SETTINGS}.backup"
cp "${CURSOR_MCP}" "${CURSOR_MCP}.backup"
echo "Backed up existing settings:"
echo "  Claude: ${CLAUDE_SETTINGS}.backup"
echo "  Cursor: ${CURSOR_MCP}.backup"

# Generate MCP configuration based on mode
mcp_config_claude=""
mcp_config_cursor=""

for tool_name in "${tools_found[@]}"; do
  tool_dir="${TOOLS_DIR}/${tool_name}"

  if [[ "${TOOLS_MODE}" == "github" ]]; then
    # GitHub mode: use npx with GitHub URL (same for both)
    mcp_entry=$(cat <<EOF
    "${tool_name}": {
      "command": "npx",
      "args": ["-y", "github:thomaschangsf/skills#tools/${tool_name}"],
      "env": {}
    }
EOF
)
    cursor_entry=$(cat <<EOF
    "${tool_name}": {
      "type": "stdio",
      "command": "npx",
      "args": ["-y", "github:thomaschangsf/skills#tools/${tool_name}"]
    }
EOF
)
  else
    # Local mode: use direct node path
    mcp_entry=$(cat <<EOF
    "${tool_name}": {
      "command": "node",
      "args": ["${tool_dir}/index.js"],
      "env": {}
    }
EOF
)
    cursor_entry=$(cat <<EOF
    "${tool_name}": {
      "type": "stdio",
      "command": "node",
      "args": ["${tool_dir}/index.js"]
    }
EOF
)
  fi

  if [[ -n "${mcp_config_claude}" ]]; then
    mcp_config_claude="${mcp_config_claude},
${mcp_entry}"
    mcp_config_cursor="${mcp_config_cursor},
${cursor_entry}"
  else
    mcp_config_claude="${mcp_entry}"
    mcp_config_cursor="${cursor_entry}"
  fi
done

# Update Claude Code settings.json
if command -v jq &> /dev/null; then
  echo "{\"mcpServers\":{${mcp_config_claude}}}" | jq -s '.[0] * .[1]' "${CLAUDE_SETTINGS}" - > "${CLAUDE_SETTINGS}.tmp"
  mv "${CLAUDE_SETTINGS}.tmp" "${CLAUDE_SETTINGS}"
  echo "✅ Updated ${CLAUDE_SETTINGS} using jq"
else
  echo "⚠️  jq not found. Manual merge required for Claude Code."
  echo ""
  echo "Add this to your ${CLAUDE_SETTINGS} under 'mcpServers':"
  echo ""
  echo "${mcp_config_claude}"
fi

echo ""

# Update Cursor mcp.json
if command -v jq &> /dev/null; then
  echo "{\"mcpServers\":{${mcp_config_cursor}}}" | jq -s '.[0] * .[1]' "${CURSOR_MCP}" - > "${CURSOR_MCP}.tmp"
  mv "${CURSOR_MCP}.tmp" "${CURSOR_MCP}"
  echo "✅ Updated ${CURSOR_MCP} using jq"
else
  echo "⚠️  jq not found. Manual merge required for Cursor."
  echo ""
  echo "Add this to your ${CURSOR_MCP} under 'mcpServers':"
  echo ""
  echo "${mcp_config_cursor}"
fi

echo ""
echo "🎯 MCP Tools configured (mode: ${TOOLS_MODE}):"
echo ""
echo "Claude Code (${CLAUDE_SETTINGS}):"
for tool_name in "${tools_found[@]}"; do
  if [[ "${TOOLS_MODE}" == "github" ]]; then
    echo "   ${tool_name}: github:thomaschangsf/skills#tools/${tool_name}"
  else
    echo "   ${tool_name}: ${TOOLS_DIR}/${tool_name}/index.js"
  fi
done

echo ""
echo "Cursor (${CURSOR_MCP}):"
for tool_name in "${tools_found[@]}"; do
  if [[ "${TOOLS_MODE}" == "github" ]]; then
    echo "   ${tool_name}: github:thomaschangsf/skills#tools/${tool_name}"
  else
    echo "   ${tool_name}: ${TOOLS_DIR}/${tool_name}/index.js"
  fi
done

echo ""
echo "═══════════════════════════════════════════════════════════════"
echo "✅ Done! Next steps:"
echo "═══════════════════════════════════════════════════════════════"
echo ""
echo "Skills:"
echo "  • Cursor: Cmd+Shift+P → Developer: Reload Window"
echo "  • Claude Code: Restart or reload to pick up ~/.claude/skills changes"
echo ""
echo "MCP Tools:"
echo "  • Claude Code: Restart to load MCP servers from settings.json"
echo "  • Cursor: Restart to load MCP servers from mcp.json"
echo "  • Verify Claude Code: Check startup logs for MCP initialization"
echo "  • Verify Cursor: Check Cursor Settings → Features → Beta"
echo ""
echo "To switch MCP tools mode:"
echo "  • Development: TOOLS_MODE=local bash $0"
echo "  • Sharing:     TOOLS_MODE=github bash $0"
echo ""
