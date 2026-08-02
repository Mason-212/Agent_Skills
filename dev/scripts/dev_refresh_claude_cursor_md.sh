#!/usr/bin/env bash
# dev_refresh_claude_cursor_md.sh
#
# Refreshes AI behavioral guidelines across Claude and Cursor.
#
# HOW CURSOR READS GUIDELINES
# ────────────────────────────
# Cursor has two sources of guidelines:
#
#   1. ~/.cursorrules  (global)
#      A plain text file read by the Cursor IDE at startup. Applies to every
#      project you open. Best for universal coding style and behavior rules.
#
#   2. AGENTS.md  (per-project)
#      A markdown file at the root of a project repo. Cursor reads it when
#      you open that project, giving project-specific context and conventions.
#      This is the right place for repo-specific rules (tech stack, patterns).
#
# This script manages both: it updates ~/.cursorrules globally, and optionally
# writes/updates AGENTS.md in one or more local project directories.
#
# WHAT THIS SCRIPT DOES
# ──────────────────────
# Part 1: Copy CLAUDE_USER.md -> ~/.claude/CLAUDE.md  (Claude global config)
# Part 2: Merge guidelines into ~/.cursorrules         (Cursor global config)
# Part 3: Optionally update AGENTS.md in local projects (Cursor project config)
# Part 4: Optionally verify Claude and Cursor see the updated guidelines
#
# Usage:
#   ./scripts/dev_refresh_claude_cursor_md.sh

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

CLAUDE_USER_MD="${REPO_ROOT}/use_cases/claude/CLAUDE_USER.md"
CLAUDE_MD_DEST="${HOME}/.claude/CLAUDE.md"
CURSORRULES_FILE="${HOME}/.cursorrules"

# Sentinel used to delimit the auto-generated block inside .cursorrules
SENTINEL_BEGIN="# --- BEGIN: agent guidelines (auto-generated) ---"
SENTINEL_END="# --- END: agent guidelines (auto-generated) ---"

echo "═══════════════════════════════════════════════════════════════"
echo "  Refreshing Claude and Cursor configuration"
echo "═══════════════════════════════════════════════════════════════"
echo ""

# ---------------------------------------------------------------------------
# Validate source
# ---------------------------------------------------------------------------

if [[ ! -f "${CLAUDE_USER_MD}" ]]; then
  echo "❌ Error: ${CLAUDE_USER_MD} not found" >&2
  exit 1
fi

# ---------------------------------------------------------------------------
# Part 1: Copy CLAUDE_USER.md -> ~/.claude/CLAUDE.md
# ---------------------------------------------------------------------------

echo "📝 Part 1: Updating ~/.claude/CLAUDE.md"
echo "─────────────────────────────────────────────────────────────────"

if [[ -f "${CLAUDE_MD_DEST}" ]]; then
  echo "Existing file found: ${CLAUDE_MD_DEST}"
  read -r -p "Overwrite? [y/N] " confirm_claude
  if [[ ! "${confirm_claude}" =~ ^[Yy]$ ]]; then
    echo "⏭  Skipped ~/.claude/CLAUDE.md"
  else
    BACKUP_FILE="${CLAUDE_MD_DEST}.backup.$(date +%Y%m%d_%H%M%S)"
    cp "${CLAUDE_MD_DEST}" "${BACKUP_FILE}"
    echo "Backed up existing CLAUDE.md → ${BACKUP_FILE}"
    mkdir -p "$(dirname "${CLAUDE_MD_DEST}")"
    cp "${CLAUDE_USER_MD}" "${CLAUDE_MD_DEST}"
    echo "✅ Copied → ${CLAUDE_MD_DEST}"
  fi
else
  mkdir -p "$(dirname "${CLAUDE_MD_DEST}")"
  cp "${CLAUDE_USER_MD}" "${CLAUDE_MD_DEST}"
  echo "✅ Copied → ${CLAUDE_MD_DEST}"
fi

echo ""

# ---------------------------------------------------------------------------
# Part 2: Merge guidelines into ~/.cursorrules
#
# ~/.cursorrules is a plain text file Cursor reads globally. We preserve all
# existing content and replace/append a clearly delimited block containing
# the full CLAUDE_USER.md guidelines. Re-running is idempotent.
# ---------------------------------------------------------------------------

echo "🖱️  Part 2: Merging guidelines into ~/.cursorrules"
echo "─────────────────────────────────────────────────────────────────"

if [[ -f "${CURSORRULES_FILE}" ]]; then
  echo "Existing file found: ${CURSORRULES_FILE}"
  read -r -p "Merge guidelines into existing .cursorrules? [y/N] " confirm_cursor
  if [[ ! "${confirm_cursor}" =~ ^[Yy]$ ]]; then
    echo "⏭  Skipped ~/.cursorrules"
  else
    BACKUP_FILE="${CURSORRULES_FILE}.backup.$(date +%Y%m%d_%H%M%S)"
    cp "${CURSORRULES_FILE}" "${BACKUP_FILE}"
    echo "Backed up existing .cursorrules → ${BACKUP_FILE}"

    # Strip any previous auto-generated block (idempotent re-runs)
    EXISTING_CONTENT="$(awk -v begin="${SENTINEL_BEGIN}" -v end="${SENTINEL_END}" '
      $0 == begin {skip=1; next}
      $0 == end   {skip=0; next}
      !skip       {print}
    ' "${CURSORRULES_FILE}" | sed '/^[[:space:]]*$/d')"

    # Write: preserved content + new guidelines block
    {
      printf '%s\n\n' "${EXISTING_CONTENT}"
      echo "${SENTINEL_BEGIN}"
      cat "${CLAUDE_USER_MD}"
      echo "${SENTINEL_END}"
    } > "${CURSORRULES_FILE}"

    echo "✅ Updated → ${CURSORRULES_FILE}"
  fi
else
  # No existing file — create from scratch
  {
    echo "${SENTINEL_BEGIN}"
    cat "${CLAUDE_USER_MD}"
    echo "${SENTINEL_END}"
  } > "${CURSORRULES_FILE}"
  echo "✅ Created → ${CURSORRULES_FILE}"
fi

echo ""

# ---------------------------------------------------------------------------
# Part 3: Optionally update local project directories
#
# HOW THIS WORKS
# ──────────────
# Cursor has two per-project guideline sources:
#
#   1. AGENTS.md (project root)
#      Simple markdown, read by Cursor and the headless cursor-agent CLI.
#      Often shared and git-tracked — modifying it would pollute the repo.
#
#   2. .cursor/rules/*.mdc (project root, version-controlled by default)
#      Modern format: markdown with YAML frontmatter controlling when the
#      rule applies. Also typically git-tracked.
#
# STRATEGY (Option D — detect and adapt)
# ───────────────────────────────────────
# For each project directory you provide, this script:
#
#   a) Checks whether AGENTS.md is tracked by git.
#
#   b) If AGENTS.md is NOT git-tracked (personal/untracked):
#      → Appends your guidelines to AGENTS.md using the sentinel block.
#        Safe to modify since it won't affect teammates.
#
#   c) If AGENTS.md IS git-tracked (shared repo):
#      → Writes your guidelines to .cursor/rules/personal-guidelines.mdc
#        with alwaysApply: true frontmatter (plain markdown body, not YAML).
#      → Adds .cursor/rules/personal-guidelines.mdc to .git/info/exclude
#        (the per-repo local gitignore) so it is NEVER committed or visible
#        to git, keeping the shared repo completely clean.
#
# This way your principles are always present in Cursor's context without
# surprising teammates or dirtying any shared file.
# ---------------------------------------------------------------------------

echo "📁 Part 3: Update local project directories (optional)"
echo "─────────────────────────────────────────────────────────────────"
echo ""
echo "  Cursor per-project guideline sources:"
echo "    • AGENTS.md                          — simple markdown, often git-tracked"
echo "    • .cursor/rules/personal-guidelines.mdc — modern .mdc, also git-tracked by default"
echo ""
echo "  This script detects whether AGENTS.md is git-tracked in each project:"
echo "    • Not git-tracked → appends to AGENTS.md (safe, personal file)"
echo "    • Git-tracked     → writes to .cursor/rules/personal-guidelines.mdc"
echo "                        and adds it to .git/info/exclude (local gitignore)"
echo "                        so it never appears in git status or gets committed"
echo ""
read -r -p "Update project directories? [y/N] " confirm_projects

PROJECT_DIRS=()

if [[ "${confirm_projects}" =~ ^[Yy]$ ]]; then
  echo ""
  echo "  Enter project directory paths one per line."
  echo "  Press Enter on a blank line when done."
  echo ""
  while true; do
    read -r -p "  Project path (blank to finish): " proj_path
    [[ -z "${proj_path}" ]] && break
    proj_path="${proj_path/#\~/$HOME}"
    if [[ ! -d "${proj_path}" ]]; then
      echo "  ⚠️  Directory not found, skipping: ${proj_path}"
      continue
    fi
    PROJECT_DIRS+=("${proj_path}")
  done

  if (( ${#PROJECT_DIRS[@]} == 0 )); then
    echo "  ⏭  No valid directories entered. Skipping."
  else
    echo ""
    for proj_dir in "${PROJECT_DIRS[@]}"; do
      AGENTS_MD="${proj_dir}/AGENTS.md"
      CURSOR_RULES_DIR="${proj_dir}/.cursor/rules"
      PERSONAL_RULE="${CURSOR_RULES_DIR}/personal-guidelines.mdc"
      GIT_EXCLUDE="${proj_dir}/.git/info/exclude"

      echo "  Processing: ${proj_dir}"

      # Detect if AGENTS.md is git-tracked
      AGENTS_TRACKED=false
      if git -C "${proj_dir}" ls-files --error-unmatch AGENTS.md &>/dev/null 2>&1; then
        AGENTS_TRACKED=true
      fi

      if [[ "${AGENTS_TRACKED}" == "false" ]]; then
        # --- Path A: AGENTS.md is not git-tracked — safe to modify ---
        echo "    Strategy: AGENTS.md is not git-tracked → appending to AGENTS.md"

        if [[ -f "${AGENTS_MD}" ]]; then
          EXISTING_AGENTS="$(awk -v begin="${SENTINEL_BEGIN}" -v end="${SENTINEL_END}" '
            $0 == begin {skip=1; next}
            $0 == end   {skip=0; next}
            !skip       {print}
          ' "${AGENTS_MD}" | sed '/^[[:space:]]*$/d')"
          BACKUP_FILE="${AGENTS_MD}.backup.$(date +%Y%m%d_%H%M%S)"
          cp "${AGENTS_MD}" "${BACKUP_FILE}"
          echo "    Backed up existing AGENTS.md → ${BACKUP_FILE}"
          {
            printf '%s\n\n' "${EXISTING_AGENTS}"
            echo "${SENTINEL_BEGIN}"
            cat "${CLAUDE_USER_MD}"
            echo "${SENTINEL_END}"
          } > "${AGENTS_MD}"
        else
          {
            echo "${SENTINEL_BEGIN}"
            cat "${CLAUDE_USER_MD}"
            echo "${SENTINEL_END}"
          } > "${AGENTS_MD}"
        fi
        echo "    ✅ Updated → ${AGENTS_MD}"

      else
        # --- Path B: AGENTS.md is git-tracked — write to .mdc, exclude from git ---
        echo "    Strategy: AGENTS.md is git-tracked → writing to .cursor/rules/personal-guidelines.mdc"
        echo "              + adding to .git/info/exclude (local gitignore, never committed)"

        mkdir -p "${CURSOR_RULES_DIR}"

        # Write .mdc file: YAML frontmatter + plain markdown body (not YAML)
        {
          echo "---"
          echo "description: Personal behavioral guidelines (local only, not committed)"
          echo "alwaysApply: true"
          echo "---"
          echo ""
          cat "${CLAUDE_USER_MD}"
        } > "${PERSONAL_RULE}"
        echo "    ✅ Written → ${PERSONAL_RULE}"

        # Add to .git/info/exclude so git never sees it
        if [[ -f "${GIT_EXCLUDE}" ]]; then
          if ! grep -qF ".cursor/rules/personal-guidelines.mdc" "${GIT_EXCLUDE}"; then
            echo ".cursor/rules/personal-guidelines.mdc" >> "${GIT_EXCLUDE}"
            echo "    ✅ Added to .git/info/exclude"
          else
            echo "    ℹ️  Already in .git/info/exclude"
          fi
        else
          echo "    ⚠️  No .git/info/exclude found — is this a git repo? Skipping gitignore step."
        fi
      fi

      echo ""
    done
  fi
else
  echo "  ⏭  Skipped project directory updates."
fi

echo ""
echo "═══════════════════════════════════════════════════════════════"
echo "✅ All Done!"
echo "═══════════════════════════════════════════════════════════════"
echo ""
echo "Summary:"
echo "  • Claude config:     ${CLAUDE_MD_DEST}"
echo "  • Cursor global:     ${CURSORRULES_FILE}"
if (( ${#PROJECT_DIRS[@]} > 0 )); then
  echo "  • Project AGENTS.md: ${#PROJECT_DIRS[@]} director(ies) updated"
fi
echo ""

# ---------------------------------------------------------------------------
# Part 4: Optional verification
# ---------------------------------------------------------------------------

echo "─────────────────────────────────────────────────────────────────"
read -r -p "Run verification checks? [y/N] " confirm_verify
if [[ ! "${confirm_verify}" =~ ^[Yy]$ ]]; then
  echo "⏭  Skipped verification."
  echo ""
  echo "Next steps:"
  echo "  • Restart Claude Code to load updated CLAUDE.md"
  echo "  • Restart Cursor IDE to load updated .cursorrules"
  exit 0
fi

echo ""
echo "🔍 Part 4: Verifying configuration"
echo "─────────────────────────────────────────────────────────────────"
echo ""

CHECKS_PASSED=0
CHECKS_FAILED=0

# --- Check 1: ~/.claude/CLAUDE.md file content ---
echo "Check 1: ~/.claude/CLAUDE.md (file content)"
echo "  Verifies the file exists and contains all 4 guideline sections."

if [[ ! -f "${CLAUDE_MD_DEST}" ]]; then
  echo "  ❌ File not found: ${CLAUDE_MD_DEST}"
  (( CHECKS_FAILED++ )) || true
else
  MISSING_SECTIONS=()
  for section in "Think Before Coding" "Simplicity First" "Surgical Changes" "Goal-Driven Execution"; do
    grep -q "${section}" "${CLAUDE_MD_DEST}" || MISSING_SECTIONS+=("${section}")
  done
  if (( ${#MISSING_SECTIONS[@]} == 0 )); then
    echo "  ✅ All 4 guideline sections present."
    (( CHECKS_PASSED++ )) || true
  else
    echo "  ❌ Missing sections: ${MISSING_SECTIONS[*]}"
    (( CHECKS_FAILED++ )) || true
  fi
fi

echo ""

# --- Check 2: ~/.cursorrules file content ---
echo "Check 2: ~/.cursorrules (file content)"
echo "  Verifies the sentinel block and guidelines content are present."

if [[ ! -f "${CURSORRULES_FILE}" ]]; then
  echo "  ❌ File not found: ${CURSORRULES_FILE}"
  (( CHECKS_FAILED++ )) || true
else
  if ! grep -q "${SENTINEL_BEGIN}" "${CURSORRULES_FILE}"; then
    echo "  ❌ Sentinel block not found."
    (( CHECKS_FAILED++ )) || true
  elif ! grep -q "Think Before Coding" "${CURSORRULES_FILE}"; then
    echo "  ❌ Guidelines content missing inside sentinel block."
    (( CHECKS_FAILED++ )) || true
  else
    GUIDELINE_LINES="$(awk "/^${SENTINEL_BEGIN}/{f=1} /^${SENTINEL_END}/{f=0} f" "${CURSORRULES_FILE}" | wc -l | tr -d ' ')"
    echo "  ✅ Sentinel block present (~${GUIDELINE_LINES} lines of guidelines)."
    (( CHECKS_PASSED++ )) || true
  fi
fi

echo ""

# --- Check 3: Headless Claude behavioral verification ---
echo "Check 3: Headless Claude — reads CLAUDE.md guidelines"
echo "  Spins up a headless Claude session and asks it to list its behavioral"
echo "  guidelines. Parses the response for all 4 expected sections."
echo ""

CLAUDE_RESPONSE="$(claude -p "What behavioral guidelines are you following in this session? List any sections or rules from your CLAUDE.md." 2>/dev/null < /dev/null || true)"

if [[ -z "${CLAUDE_RESPONSE}" ]]; then
  echo "  ❌ No response from claude CLI. Is Claude Code installed and authenticated?"
  (( CHECKS_FAILED++ )) || true
else
  MISSING_SECTIONS=()
  for section in "Think Before Coding" "Simplicity First" "Surgical Changes" "Goal-Driven Execution"; do
    echo "${CLAUDE_RESPONSE}" | grep -q "${section}" || MISSING_SECTIONS+=("${section}")
  done
  if (( ${#MISSING_SECTIONS[@]} == 0 )); then
    echo "  ✅ Claude sees all 4 guideline sections."
    (( CHECKS_PASSED++ )) || true
  else
    echo "  ❌ Missing sections: ${MISSING_SECTIONS[*]}"
    echo "  Response:"
    echo "${CLAUDE_RESPONSE}" | sed 's/^/    /'
    (( CHECKS_FAILED++ )) || true
  fi
fi

echo ""

# --- Check 4: Headless cursor-agent per-project verification ---
echo "Check 4: Headless cursor-agent — reads project guidelines"
echo "  cursor-agent reads AGENTS.md and .cursor/rules/*.mdc from the project"
echo "  directory. ~/.cursorrules is IDE-only and cannot be verified headlessly."

if (( ${#PROJECT_DIRS[@]} == 0 )); then
  echo "  ⏭  No project directories were updated in Part 3. Skipping."
  echo "  To enable this check: re-run and provide project paths in Part 3."
else
  echo ""
  for proj_dir in "${PROJECT_DIRS[@]}"; do
    echo "  Project: ${proj_dir}"

    # Determine which file was written (Path A or Path B)
    AGENTS_TRACKED=false
    if git -C "${proj_dir}" ls-files --error-unmatch AGENTS.md &>/dev/null 2>&1; then
      AGENTS_TRACKED=true
    fi

    if [[ "${AGENTS_TRACKED}" == "false" ]]; then
      echo "  Source verified: AGENTS.md (not git-tracked, appended)"
    else
      echo "  Source verified: .cursor/rules/personal-guidelines.mdc (git-excluded)"
    fi

    echo "  Asking cursor-agent: 'What behavioral guidelines are you following?'"

    CURSOR_RESPONSE="$(cd "${proj_dir}" && cursor-agent -p --force --trust \
      "What behavioral guidelines are you following? List any rules from AGENTS.md or .cursor/rules/." \
      2>/dev/null || true)"

    if [[ -z "${CURSOR_RESPONSE}" ]]; then
      echo "    ❌ No response from cursor-agent."
      (( CHECKS_FAILED++ )) || true
    else
      MISSING_SECTIONS=()
      for section in "Think Before Coding" "Simplicity First" "Surgical Changes" "Goal-Driven Execution"; do
        echo "${CURSOR_RESPONSE}" | grep -q "${section}" || MISSING_SECTIONS+=("${section}")
      done
      if (( ${#MISSING_SECTIONS[@]} == 0 )); then
        echo "    ✅ cursor-agent sees all 4 guideline sections."
        (( CHECKS_PASSED++ )) || true
      else
        echo "    ❌ Missing sections: ${MISSING_SECTIONS[*]}"
        echo "    Response:"
        echo "${CURSOR_RESPONSE}" | head -20 | sed 's/^/      /'
        (( CHECKS_FAILED++ )) || true
      fi
    fi
    echo ""
  done
fi

echo "  IDE verification (manual): Restart Cursor, open a chat, and ask:"
echo "    \"What rules or guidelines are you following?\""
echo "  Expected: Cursor lists the Karpathy guidelines from ~/.cursorrules"
echo "  and/or from .cursor/rules/personal-guidelines.mdc in each project."

echo ""

# --- Summary ---
echo "─────────────────────────────────────────────────────────────────"
echo "Verification summary: ${CHECKS_PASSED} passed, ${CHECKS_FAILED} failed"
echo ""
echo "Next steps:"
echo "  • Restart Claude Code to load updated CLAUDE.md"
echo "  • Restart Cursor IDE to load updated .cursorrules"
echo ""
