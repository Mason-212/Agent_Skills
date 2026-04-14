#!/usr/bin/env bash
# dev_refresh_skill_from_repo.sh
#
# Install or refresh the global skills package for multiple agent targets using
# the official skills CLI (https://github.com/vercel-labs/skills). Each target
# has its own on-disk location; there is no single directory every product reads.
#
# ---------------------------------------------------------------------------
# Where skill folders end up (global install, per skills CLI matrix)
# ---------------------------------------------------------------------------
#
# ~/.cursor/skills/<skill-name>/
#   Agent id: cursor
#   Consumer: Cursor IDE. Cursor loads each skill as a directory containing
#   SKILL.md under this path.
#
# ~/.claude/skills/<skill-name>/
#   Agent id: claude-code
#   Consumer: Claude Code (Anthropic). Same SKILL.md layout.
#
# ~/.agents/skills/<skill-name>/
#   Agent id: cline (we pass --agent cline here on purpose)
#   The skills CLI maps the Cline/Warp global target to this directory. Several
#   tools and docs in the “open agent skills” ecosystem treat ~/.agents/skills
#   as a shared personal skills tree; you do not need the Cline extension installed
#   for files to be written here—this is just the CLI’s stable path for that
#   agent id.
#
# We use --copy so each location gets real directories (not symlinks). Cursor in
# particular often does not follow symlinks into another tree, so copies avoid
# stale or invisible skills.
#
# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
#
# SKILLS_GIT_REMOTE_PREFIX — SSH host and org (or user) before the repo name; no
#   trailing slash, no `.git`. Default: git@github.com:thomaschangsf
# SKILLS_SSH_URL   — Full Git SSH URL of this package. Default:
#   ${SKILLS_GIT_REMOTE_PREFIX}/skills.git (override if the repo is not named skills).
# SKILLS_PACKAGE_PATH — If set to the absolute path of *this* git repo (directory
#   containing skills/), `npx skills add` uses that tree instead of SKILLS_SSH_URL.
#   Use this when renames/new skills are not pushed to GitHub yet; otherwise the CLI
#   only sees what is on the remote.
# SKILLS_AGENTS    — Space-separated agent ids for npx skills add (default below).
#
# Usage:
#   ./scripts/dev_refresh_skill_from_repo.sh
#   bash scripts/dev_refresh_skill_from_repo.sh

set -euo pipefail

SKILLS_GIT_REMOTE_PREFIX="${SKILLS_GIT_REMOTE_PREFIX:-git@github.com:thomaschangsf}"
SKILLS_SSH_URL="${SKILLS_SSH_URL:-${SKILLS_GIT_REMOTE_PREFIX}/skills.git}"
SKILLS_AGENTS="${SKILLS_AGENTS:-cursor claude-code cline}"

CURSOR_SKILLS="${HOME}/.cursor/skills"
CLAUDE_SKILLS="${HOME}/.claude/skills"
AGENTS_SKILLS="${HOME}/.agents/skills"

agent_args=()
read -r -a _agents <<< "${SKILLS_AGENTS}"
for a in "${_agents[@]}"; do
  [[ -n "${a}" ]] || continue
  agent_args+=(-a "${a}")
done

if (( ${#agent_args[@]} == 0 )); then
  echo "SKILLS_AGENTS is empty; set it to a space-separated list (e.g. cursor claude-code cline)." >&2
  exit 1
fi

skills_package="${SKILLS_SSH_URL}"
if [[ -n "${SKILLS_PACKAGE_PATH:-}" ]]; then
  if [[ ! -d "${SKILLS_PACKAGE_PATH}/skills" ]]; then
    echo "SKILLS_PACKAGE_PATH must point at this repo root (a directory containing skills/). Got: ${SKILLS_PACKAGE_PATH}" >&2
    exit 1
  fi
  skills_package="$(cd "${SKILLS_PACKAGE_PATH}" && pwd)"
  echo "Using local package path: ${skills_package}"
else
  echo "Using remote package: ${skills_package}"
  echo "(Unpushed commits are not included. Set SKILLS_PACKAGE_PATH to this repo root to install from disk.)"
fi

echo "Registering / refreshing global package for agents: ${SKILLS_AGENTS}"
echo "  (see header comments for ~/.cursor/skills, ~/.claude/skills, ~/.agents/skills)"
npx skills add -g -y "${skills_package}" "${agent_args[@]}" --all --copy

echo "Updating global skills (npx skills update -g)..."
npx skills update -g

echo "Done."
echo "  Cursor:       ${CURSOR_SKILLS}"
echo "  Claude Code:  ${CLAUDE_SKILLS}"
echo "  Shared tree:  ${AGENTS_SKILLS}"
echo "Reload Cursor: Cmd+Shift+P → Developer: Reload Window"
echo "If Claude Code is open, restart it or reload so it picks up ~/.claude/skills changes."
