#!/usr/bin/env bash
# Update local master from origin, then create a new branch (git-only, no sf CLI).
#
# Usage:
#   ./scripts/dev_start_branch_from_master.sh [branch-name]
#
# If branch-name is omitted or empty after trimming, the script prompts until you
# enter a non-empty name.
#
# Environment:
#   GIT_BASE_BRANCH — Branch to track (default: master). Must exist as origin/<name>.

set -euo pipefail

usage() {
  cat <<'EOF' >&2
Usage:
  dev_start_branch_from_master.sh [branch-name]

Creates branch <branch-name> from the latest origin/<base> (default base: master).
If [branch-name] is omitted, you are prompted interactively.

Environment:
  GIT_BASE_BRANCH   Base branch (default: master)

Requires no staged or unstaged changes to tracked files (untracked files are OK).
EOF
  exit 1
}

[[ "${1:-}" == "-h" || "${1:-}" == "--help" ]] && usage

command -v git >/dev/null || { echo "git not found" >&2; exit 1; }

trim() {
  local s="${1:-}"
  s="${s#"${s%%[![:space:]]*}"}"
  s="${s%"${s##*[![:space:]]}"}"
  printf '%s' "${s}"
}

new_branch=""
if [[ $# -ge 1 ]]; then
  new_branch="$(trim "$1")"
fi

while [[ -z "${new_branch}" ]]; do
  read -r -p "Branch name: " _line || exit 1
  new_branch="$(trim "${_line}")"
  if [[ -z "${new_branch}" ]]; then
    echo "Branch name cannot be empty." >&2
  fi
done

if ! git check-ref-format --branch "${new_branch}"; then
  echo "Invalid branch name for git: ${new_branch}" >&2
  exit 1
fi

# Ignore untracked files: porcelain without them matches "clean" for branch switches.
if [[ -n "$(git status --porcelain --untracked-files=no 2>/dev/null)" ]]; then
  echo "Working tree has staged or unstaged changes to tracked files. Commit or stash before switching branches." >&2
  exit 1
fi

BASE_BRANCH="${GIT_BASE_BRANCH:-master}"

if ! git rev-parse --git-dir >/dev/null 2>&1; then
  echo "Not a git repository." >&2
  exit 1
fi

git fetch origin "${BASE_BRANCH}"

remote_base="refs/remotes/origin/${BASE_BRANCH}"
if ! git show-ref --verify --quiet "${remote_base}"; then
  echo "Missing ${remote_base}. Push ${BASE_BRANCH} or set GIT_BASE_BRANCH to an existing remote branch." >&2
  exit 1
fi

if git show-ref --verify --quiet "refs/heads/${new_branch}"; then
  echo "Branch already exists locally: ${new_branch}" >&2
  exit 1
fi
if git show-ref --verify --quiet "refs/remotes/origin/${new_branch}"; then
  echo "Branch already exists on origin: ${new_branch}" >&2
  exit 1
fi

# Fast-forward local base to match remote (create local base if missing).
if git show-ref --verify --quiet "refs/heads/${BASE_BRANCH}"; then
  git checkout "${BASE_BRANCH}"
  git merge --ff-only "origin/${BASE_BRANCH}"
else
  git checkout -b "${BASE_BRANCH}" "origin/${BASE_BRANCH}"
fi

git checkout -b "${new_branch}"

echo "Created branch '${new_branch}' from up-to-date '${BASE_BRANCH}'."
