#!/usr/bin/env bash
# dev_refresh_skills_and_tools.sh
#
# Metadata-driven script to:
# 1. Auto-discover and install skills (via npx skills CLI)
# 2. Auto-discover and configure MCP servers (universal for all agents)
# 3. Auto-discover and install agent-specific plugins
#
# ---------------------------------------------------------------------------
# Discovery Logic (Metadata-Driven)
# ---------------------------------------------------------------------------
#
# Skills: Any directory in skills/ containing SKILL.md
#
# MCP Servers (universal - configured for all MCP-compatible agents):
#   mcps/nodejs/*  → Node.js MCPs (using @modelcontextprotocol/sdk)
#   mcps/python/*  → Python MCPs (stdin/stdout protocol)
#   Must have: index.js + package.json (Node) OR server.py + pyproject.toml (Python)
#
# Agent-Specific Plugins (by agent):
#   agent-specific/claude/*  → Claude Code plugins
#   agent-specific/cu/*      → Claude Unleashed plugins
#   Must have: .claude-plugin/plugin.json
#
# ---------------------------------------------------------------------------
# Installation Targets
# ---------------------------------------------------------------------------
#
# Skills installed to:
# - ~/.cursor/skills/<skill-name>/
# - ~/.claude/skills/<skill-name>/
# - ~/.agents/skills/<skill-name>/
#
# MCP servers configured in:
# - ~/.claude/settings.json (Claude Code)
# - ~/.cursor/mcp.json (Cursor)
#
# Agent-specific plugins copied to:
# - ~/.claude/plugins/<plugin-name>/
#
# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
#
# SKILLS_GIT_REMOTE_PREFIX — SSH host and org/user (default: git@github.com:thomaschangsf)
# SKILLS_SSH_URL   — Full Git SSH URL (default: ${SKILLS_GIT_REMOTE_PREFIX}/skills.git)
# SKILLS_PACKAGE_PATH — Absolute path to this repo for local development
# SKILLS_AGENTS    — Space-separated agent ids (default: cursor claude-code)
# TOOLS_MODE       — "local" for development, "github" for sharing (default: local)
#
# Usage:
#   ./dev/scripts/dev_refresh_skills_and_tools.sh
#   TOOLS_MODE=github bash dev/scripts/dev_refresh_skills_and_tools.sh

set -euo pipefail

SKILLS_GIT_REMOTE_PREFIX="${SKILLS_GIT_REMOTE_PREFIX:-git@github.com:thomaschangsf}"
SKILLS_SSH_URL="${SKILLS_SSH_URL:-${SKILLS_GIT_REMOTE_PREFIX}/skills.git}"
SKILLS_AGENTS="${SKILLS_AGENTS:-cursor claude-code}"
TOOLS_MODE="${TOOLS_MODE:-local}"

CURSOR_SKILLS="${HOME}/.cursor/skills"
CURSOR_PLUGINS="${HOME}/.cursor/plugins"
CURSOR_MCP="${HOME}/.cursor/mcp.json"

CLAUDE_SKILLS="${HOME}/.claude/skills"
CLAUDE_PLUGINS="${HOME}/.claude/plugins"
CLAUDE_SETTINGS="${HOME}/.claude/settings.json"

AGENTS_SKILLS="${HOME}/.agents/skills"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"

create_record_file() {
  mktemp "${TMPDIR:-/tmp}/dev_refresh_records.XXXXXX"
}

append_record() {
  local target_file="$1"
  local record_name="$2"
  local record_path="$3"

  printf '%s\t%s\n' "${record_name}" "${record_path}" >> "${target_file}"
}

dedupe_last_wins() {
  local target_file="$1"
  local tmp_file

  tmp_file="$(create_record_file)"

  awk -F '\t' '
    {
      order[++n] = $1
      record[$1] = $0
    }
    END {
      for (i = n; i >= 1; i--) {
        name = order[i]
        if (!(name in seen)) {
          seen[name] = 1
          keep[++k] = name
        }
      }
      for (i = k; i >= 1; i--) {
        print record[keep[i]]
      }
    }
  ' "${target_file}" > "${tmp_file}"

  mv "${tmp_file}" "${target_file}"
}

record_count() {
  local target_file="$1"

  if [[ -s "${target_file}" ]]; then
    awk 'END { print NR }' "${target_file}"
  else
    echo "0"
  fi
}

record_names() {
  local target_file="$1"

  awk -F '\t' '
    NF {
      names = names (names ? " " : "") $1
    }
    END {
      print names
    }
  ' "${target_file}"
}

mcp_plugins_claude_records="$(create_record_file)"
mcp_plugins_cursor_records="$(create_record_file)"
cc_plugins_claude_records="$(create_record_file)"
cc_plugins_cursor_records="$(create_record_file)"

cleanup_record_files() {
  rm -f \
    "${mcp_plugins_claude_records}" \
    "${mcp_plugins_cursor_records}" \
    "${cc_plugins_claude_records}" \
    "${cc_plugins_cursor_records}"
}

trap cleanup_record_files EXIT

echo "═══════════════════════════════════════════════════════════════"
echo "  Metadata-Driven Skills & Tools Refresh"
echo "═══════════════════════════════════════════════════════════════"
echo ""

# ---------------------------------------------------------------------------
# Part 1: Auto-Discover and Refresh Skills
# ---------------------------------------------------------------------------

echo "📚 Part 1: Auto-Discovering and Installing Skills"
echo "─────────────────────────────────────────────────────────────────"

# Validate agents
agent_args=()
agent_count=0
for a in ${SKILLS_AGENTS}; do
  [[ -n "${a}" ]] || continue
  agent_args+=(-a "${a}")
  agent_count=$((agent_count + 1))
done

if (( agent_count == 0 )); then
  echo "❌ SKILLS_AGENTS is empty; set it to space-separated list (e.g. cursor claude-code)." >&2
  exit 1
fi

# Determine package path
skills_package="${SKILLS_SSH_URL}"
if [[ -n "${SKILLS_PACKAGE_PATH:-}" ]]; then
  if [[ ! -d "${SKILLS_PACKAGE_PATH}/skills" ]]; then
    echo "❌ SKILLS_PACKAGE_PATH must point at repo root (containing skills/). Got: ${SKILLS_PACKAGE_PATH}" >&2
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

# Discover skills
SKILLS_DIR="${REPO_ROOT}/skills"
discovered_skills=()
if [[ -d "${SKILLS_DIR}" ]]; then
  while IFS= read -r -d '' skill_file; do
    skill_name="$(basename "$(dirname "${skill_file}")")"
    discovered_skills+=("${skill_name}")
  done < <(find "${SKILLS_DIR}" -mindepth 2 -maxdepth 2 -name "SKILL.md" -type f -print0)
fi

if (( ${#discovered_skills[@]} == 0 )); then
  echo "⚠️  No skills found in ${SKILLS_DIR}"
else
  echo "Discovered ${#discovered_skills[@]} skill(s): ${discovered_skills[*]}"
fi

echo ""
echo "Installing skills for agents: ${SKILLS_AGENTS}"
npx skills add -g -y "${skills_package}" "${agent_args[@]}" --all --copy

echo "Updating global skills..."
npx skills update -g

echo ""
echo "✅ Skills refreshed:"
echo "   Cursor:       ${CURSOR_SKILLS}"
echo "   Claude Code:  ${CLAUDE_SKILLS}"
echo "   Shared tree:  ${AGENTS_SKILLS}"
echo ""

# ---------------------------------------------------------------------------
# Part 2: Auto-Discover and Configure MCP Plugins (Agent-Scoped)
# ---------------------------------------------------------------------------

echo "🔧 Part 2: Auto-Discovering and Configuring MCP Plugins"
echo "─────────────────────────────────────────────────────────────────"

PLUGINS_DIR="${REPO_ROOT}/plugins"
MCPS_DIR="${REPO_ROOT}/mcps"

# Discover MCP plugins from mcps/ directory (universal - all MCPs for both agents)

# Scan plugins/ directory (legacy - remove after migration)
if [[ ! -d "${PLUGINS_DIR}" ]]; then
  echo "✅ Old plugins/ directory removed (migrated to mcps/)"
else
  echo "⚠️  Legacy plugins/ directory still exists. Consider removing after migration."
fi

# Scan mcps/ directory
if [[ ! -d "${MCPS_DIR}" ]]; then
  echo "⚠️  No mcps/ directory found."
else
  # Scan mcps/nodejs/ for Node.js MCPs
  if [[ -d "${MCPS_DIR}/nodejs" ]]; then
    while IFS= read -r -d '' mcp_dir; do
      mcp_name="$(basename "${mcp_dir}")"
      if [[ -f "${mcp_dir}/index.js" && -f "${mcp_dir}/package.json" ]]; then
        append_record "${mcp_plugins_claude_records}" "${mcp_name}" "${mcp_dir}"
        append_record "${mcp_plugins_cursor_records}" "${mcp_name}" "${mcp_dir}"
      fi
    done < <(find "${MCPS_DIR}/nodejs" -mindepth 1 -maxdepth 1 -type d -print0 2>/dev/null || true)
  fi

  # Scan mcps/python/ for Python MCPs
  if [[ -d "${MCPS_DIR}/python" ]]; then
    while IFS= read -r -d '' mcp_dir; do
      mcp_name="$(basename "${mcp_dir}")"
      if [[ -f "${mcp_dir}/server.py" && -f "${mcp_dir}/pyproject.toml" ]]; then
        append_record "${mcp_plugins_claude_records}" "${mcp_name}" "${mcp_dir}"
        append_record "${mcp_plugins_cursor_records}" "${mcp_name}" "${mcp_dir}"
      fi
    done < <(find "${MCPS_DIR}/python" -mindepth 1 -maxdepth 1 -type d -print0 2>/dev/null || true)
  fi
fi

if (( $(record_count "${mcp_plugins_claude_records}") == 0 && $(record_count "${mcp_plugins_cursor_records}") == 0 )); then
  echo "⚠️  No MCP plugins found. Skipping."
else

  dedupe_last_wins "${mcp_plugins_claude_records}"
  dedupe_last_wins "${mcp_plugins_cursor_records}"

  mcp_plugins_claude_count="$(record_count "${mcp_plugins_claude_records}")"
  mcp_plugins_cursor_count="$(record_count "${mcp_plugins_cursor_records}")"
  mcp_plugins_claude_names="$(record_names "${mcp_plugins_claude_records}")"
  mcp_plugins_cursor_names="$(record_names "${mcp_plugins_cursor_records}")"

  echo "Discovered MCP plugins:"
  echo "  Claude Code: ${mcp_plugins_claude_count} plugin(s) (${mcp_plugins_claude_names})"
  echo "  Cursor:      ${mcp_plugins_cursor_count} plugin(s) (${mcp_plugins_cursor_names})"
fi

# Configure Claude Code MCP plugins
if (( $(record_count "${mcp_plugins_claude_records}") > 0 )); then
  echo ""
  echo "Configuring Claude Code MCP plugins..."

  if [[ ! -f "${CLAUDE_SETTINGS}" ]]; then
    mkdir -p "$(dirname "${CLAUDE_SETTINGS}")"
    echo '{"mcpServers":{}}' > "${CLAUDE_SETTINGS}"
  fi

  cp "${CLAUDE_SETTINGS}" "${CLAUDE_SETTINGS}.backup.$(date +%Y%m%d_%H%M%S)"

  mcp_config_claude=""
  while IFS=$'\t' read -r plugin_name plugin_dir; do
    [[ -n "${plugin_name}" ]] || continue

    # Determine if this is Python or Node.js MCP
    if [[ -f "${plugin_dir}/server.py" ]]; then
      # Python MCP
      if [[ "${TOOLS_MODE}" == "github" ]]; then
        scope="all"
        if [[ "${plugin_dir}" == *"/mcps/claude/"* || "${plugin_dir}" == *"/plugins/claude/"* ]]; then
          scope="claude"
        fi

        mcp_entry=$(cat <<EOF
    "${plugin_name}": {
      "command": "bash",
      "args": ["-lc", "cd \"${plugin_dir}\" && uv run server.py"],
      "env": {}
    }
EOF
)
      else
        mcp_entry=$(cat <<EOF
    "${plugin_name}": {
      "command": "bash",
      "args": ["-lc", "cd \"${plugin_dir}\" && uv run server.py"],
      "env": {}
    }
EOF
)
      fi
    else
      # Node.js MCP
      if [[ "${TOOLS_MODE}" == "github" ]]; then
        scope="all"
        if [[ "${plugin_dir}" == *"/plugins/claude/"* ]]; then
          scope="claude"
        fi

        mcp_entry=$(cat <<EOF
    "${plugin_name}": {
      "command": "npx",
      "args": ["-y", "github:thomaschangsf/skills#plugins/${scope}/${plugin_name}"],
      "env": {}
    }
EOF
)
      else
        mcp_entry=$(cat <<EOF
    "${plugin_name}": {
      "command": "node",
      "args": ["${plugin_dir}/index.js"],
      "env": {}
    }
EOF
)
      fi
    fi

    if [[ -n "${mcp_config_claude}" ]]; then
      mcp_config_claude="${mcp_config_claude},
${mcp_entry}"
    else
      mcp_config_claude="${mcp_entry}"
    fi
  done < "${mcp_plugins_claude_records}"

  if command -v jq &> /dev/null; then
    echo "{\"mcpServers\":{${mcp_config_claude}}}" | jq -s '.[0] * .[1]' "${CLAUDE_SETTINGS}" - > "${CLAUDE_SETTINGS}.tmp"
    mv "${CLAUDE_SETTINGS}.tmp" "${CLAUDE_SETTINGS}"
    echo "✅ Updated ${CLAUDE_SETTINGS}"
  else
    echo "⚠️  jq not found. Manual merge required."
    echo "Add to ${CLAUDE_SETTINGS}:"
    echo "${mcp_config_claude}"
  fi
fi

# Configure Cursor MCP plugins
if (( $(record_count "${mcp_plugins_cursor_records}") > 0 )); then
  echo ""
  echo "Configuring Cursor MCP plugins..."

  if [[ ! -f "${CURSOR_MCP}" ]]; then
    mkdir -p "$(dirname "${CURSOR_MCP}")"
    echo '{"mcpServers":{}}' > "${CURSOR_MCP}"
  fi

  cp "${CURSOR_MCP}" "${CURSOR_MCP}.backup.$(date +%Y%m%d_%H%M%S)"

  mcp_config_cursor=""
  while IFS=$'\t' read -r plugin_name plugin_dir; do
    [[ -n "${plugin_name}" ]] || continue

    # Determine if this is Python or Node.js MCP
    if [[ -f "${plugin_dir}/server.py" ]]; then
      # Python MCP
      if [[ "${TOOLS_MODE}" == "github" ]]; then
        scope="all"
        if [[ "${plugin_dir}" == *"/mcps/cursor/"* || "${plugin_dir}" == *"/plugins/cursor/"* ]]; then
          scope="cursor"
        elif [[ "${plugin_dir}" == *"/mcps/claude/"* || "${plugin_dir}" == *"/plugins/claude/"* ]]; then
          scope="claude"
        fi

        cursor_entry=$(cat <<EOF
    "${plugin_name}": {
      "type": "stdio",
      "command": "bash",
      "args": ["-lc", "cd \"${plugin_dir}\" && uv run server.py"]
    }
EOF
)
      else
        cursor_entry=$(cat <<EOF
    "${plugin_name}": {
      "type": "stdio",
      "command": "bash",
      "args": ["-lc", "cd \"${plugin_dir}\" && uv run server.py"]
    }
EOF
)
      fi
    else
      # Node.js MCP
      if [[ "${TOOLS_MODE}" == "github" ]]; then
        scope="all"
        if [[ "${plugin_dir}" == *"/plugins/cursor/"* ]]; then
          scope="cursor"
        fi

        cursor_entry=$(cat <<EOF
    "${plugin_name}": {
      "type": "stdio",
      "command": "npx",
      "args": ["-y", "github:thomaschangsf/skills#plugins/${scope}/${plugin_name}"]
    }
EOF
)
      else
        cursor_entry=$(cat <<EOF
    "${plugin_name}": {
      "type": "stdio",
      "command": "node",
      "args": ["${plugin_dir}/index.js"]
    }
EOF
)
      fi
    fi

    if [[ -n "${mcp_config_cursor}" ]]; then
      mcp_config_cursor="${mcp_config_cursor},
${cursor_entry}"
    else
      mcp_config_cursor="${cursor_entry}"
    fi
  done < "${mcp_plugins_cursor_records}"

  if command -v jq &> /dev/null; then
    echo "{\"mcpServers\":{${mcp_config_cursor}}}" | jq -s '.[0] * .[1]' "${CURSOR_MCP}" - > "${CURSOR_MCP}.tmp"
    mv "${CURSOR_MCP}.tmp" "${CURSOR_MCP}"
    echo "✅ Updated ${CURSOR_MCP}"
  else
    echo "⚠️  jq not found. Manual merge required."
    echo "Add to ${CURSOR_MCP}:"
    echo "${mcp_config_cursor}"
  fi
fi

echo ""

# ---------------------------------------------------------------------------
# Part 3: Auto-Discover and Install Claude Code Plugins (Agent-Scoped)
# ---------------------------------------------------------------------------

echo "🔌 Part 3: Auto-Discovering and Installing Claude Code Plugins"
echo "─────────────────────────────────────────────────────────────────"

AGENT_SPECIFIC_DIR="${REPO_ROOT}/agent-specific"

# Discover Claude Code plugins (Claude-specific bundles only)

if [[ ! -d "${AGENT_SPECIFIC_DIR}/claude" ]]; then
  echo "⚠️  No agent-specific/claude/ directory found. Skipping Claude Code plugins."
else
  # Scan agent-specific/claude/ for .claude-plugin/plugin.json
  while IFS= read -r -d '' manifest; do
    plugin_dir="$(dirname "$(dirname "${manifest}")")"
    plugin_name="$(basename "${plugin_dir}")"
    append_record "${cc_plugins_claude_records}" "${plugin_name}" "${plugin_dir}"
  done < <(find "${AGENT_SPECIFIC_DIR}/claude" -mindepth 3 -maxdepth 3 -path "*/.claude-plugin/plugin.json" -type f -print0 2>/dev/null || true)

  dedupe_last_wins "${cc_plugins_claude_records}"

  echo "Discovered Claude Code plugins:"
  claude_count="$(record_count "${cc_plugins_claude_records}")"
  claude_names="$(record_names "${cc_plugins_claude_records}")"

  if (( claude_count > 0 )); then
    echo "  Claude Code: ${claude_count} plugin(s) (${claude_names})"
  else
    echo "  Claude Code: 0 plugin(s)"
  fi
fi

# Install Claude Code plugins
if (( $(record_count "${cc_plugins_claude_records}") > 0 )); then
  echo ""
  echo "Installing Claude Code plugins..."
  mkdir -p "${CLAUDE_PLUGINS}"

  while IFS=$'\t' read -r plugin_name src_dir; do
    [[ -n "${plugin_name}" ]] || continue
    dest="${CLAUDE_PLUGINS}/${plugin_name}"

    if [[ -d "${dest}" ]]; then
      rm -rf "${dest}"
    fi
    cp -r "${src_dir}" "${dest}"
    echo "✅ ${plugin_name} → ${dest}"
  done < "${cc_plugins_claude_records}"
fi

echo ""
echo "═══════════════════════════════════════════════════════════════"
echo "✅ Done! Summary:"
echo "═══════════════════════════════════════════════════════════════"
echo ""
echo "Skills: ${#discovered_skills[@]} discovered and installed"
echo "MCP Servers:"
echo "  Claude Code: $(record_count "${mcp_plugins_claude_records}") configured"
echo "  Cursor:      $(record_count "${mcp_plugins_cursor_records}") configured"
echo "Claude Code Plugins:"
echo "  Claude Code: $(record_count "${cc_plugins_claude_records}") installed"
echo ""
echo "Next steps:"
echo "  • Claude Code: Restart or /reload-plugins"
echo "  • Cursor: Restart Cursor CLI to activate MCPs"
echo ""
echo "To switch MCP servers mode:"
echo "  • Development: TOOLS_MODE=local bash $0"
echo "  • Sharing:     TOOLS_MODE=github bash $0"
echo ""
