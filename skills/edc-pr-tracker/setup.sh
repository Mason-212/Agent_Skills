#!/usr/bin/env bash
# setup.sh — onboard pr-tracker on a new Mac.
#
# Usage:
#   bash setup.sh [--repo-root PATH] [--vault-dir PATH] [--gh-login YOUR_LOGIN]
#
# Defaults:
#   --repo-root  ~/Documents/dev/git/a360/edc-python
#   --vault-dir  ~/Documents/dev/sfVault/1_orgs/0_edc/PRs
#   --gh-login   (prompts if not provided)
#
# Prerequisites:
#   - gh CLI installed and authenticated to git.soma.salesforce.com
#   - uv installed (https://github.com/astral-sh/uv)
#   - The edc-python repo cloned to --repo-root

set -euo pipefail

# ── Defaults ────────────────────────────────────────────────────────────────
REPO_ROOT="$HOME/Documents/dev/git/a360/edc-python"
VAULT_DIR="$HOME/Documents/dev/sfVault/1_orgs/0_edc/PRs"
GH_LOGIN=""

# ── Arg parsing ─────────────────────────────────────────────────────────────
while [[ $# -gt 0 ]]; do
    case "$1" in
        --repo-root) REPO_ROOT="$2"; shift 2 ;;
        --vault-dir) VAULT_DIR="$2"; shift 2 ;;
        --gh-login)  GH_LOGIN="$2";  shift 2 ;;
        *) echo "Unknown arg: $1"; exit 1 ;;
    esac
done

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PR_TRACKER_DIR="$REPO_ROOT/agents/apps/data/pr_tracker"
PLIST_DEST="$HOME/Library/LaunchAgents/com.edc.pr-tracker.plist"
LOG_PATH="$HOME/Library/Logs/pr-tracker.log"

# ── Preflight checks ────────────────────────────────────────────────────────
echo "=== pr-tracker setup ==="
echo "  repo root : $REPO_ROOT"
echo "  vault dir : $VAULT_DIR"
echo ""

if [[ ! -d "$PR_TRACKER_DIR" ]]; then
    echo "ERROR: pr_tracker directory not found at $PR_TRACKER_DIR"
    echo "       Clone the edc-python repo first, or pass --repo-root PATH"
    exit 1
fi

if ! command -v gh &>/dev/null; then
    echo "ERROR: gh CLI not found. Install from https://cli.github.com/"
    exit 1
fi

if ! command -v uv &>/dev/null; then
    echo "ERROR: uv not found. Install from https://github.com/astral-sh/uv"
    exit 1
fi

# ── Resolve GitHub login ─────────────────────────────────────────────────────
if [[ -z "$GH_LOGIN" ]]; then
    GH_LOGIN="$(GH_HOST=git.soma.salesforce.com gh api /user --jq '.login' 2>/dev/null || true)"
fi
if [[ -z "$GH_LOGIN" ]]; then
    read -rp "Enter your git.soma.salesforce.com GitHub login: " GH_LOGIN
fi
echo "  gh login  : $GH_LOGIN"
echo ""

# ── Update config.yaml ───────────────────────────────────────────────────────
CONFIG="$PR_TRACKER_DIR/config.yaml"
echo "Updating vault_dir in $CONFIG ..."

# Replace vault_dir line with the local path
sed -i.bak "s|^vault_dir:.*|vault_dir: $VAULT_DIR|" "$CONFIG"
rm -f "${CONFIG}.bak"

# Add gh login to people list if not already present
if ! grep -q "^  - $GH_LOGIN$" "$CONFIG"; then
    echo "Adding $GH_LOGIN to people list in config.yaml ..."
    # Insert after the last '  - ' line in the people block
    sed -i.bak "/^people:/,/^[^[:space:]]/{/^  - /{h;d};/^[^[:space:]]/{x;/^  - /{G;s/\n//;p};x}}" "$CONFIG" || true
    # Simpler fallback: append before the blank line after people block
    python3 - "$CONFIG" "$GH_LOGIN" <<'EOF'
import sys, re
path, login = sys.argv[1], sys.argv[2]
text = open(path).read()
# Find the people list and append the login if absent
def add_person(m):
    block = m.group(0)
    if f'  - {login}' in block:
        return block
    return block.rstrip('\n') + f'\n  - {login}\n'
new = re.sub(r'(?ms)^people:\n((?:  - .*\n)+)', add_person, text)
open(path, 'w').write(new)
print(f"  people list updated.")
EOF
    rm -f "${CONFIG}.bak"
fi

echo "config.yaml updated."
echo ""

# ── Create vault directory ───────────────────────────────────────────────────
mkdir -p "$VAULT_DIR"
echo "Vault directory ready: $VAULT_DIR"
echo ""

# ── Generate plist from template ─────────────────────────────────────────────
TEMPLATE="$SCRIPT_DIR/com.edc.pr-tracker.plist.template"
if [[ ! -f "$TEMPLATE" ]]; then
    echo "ERROR: plist template not found at $TEMPLATE"
    exit 1
fi

echo "Generating plist at $PLIST_DEST ..."
mkdir -p "$HOME/Library/LaunchAgents"
sed \
    -e "s|__SCRIPT_PATH__|$PR_TRACKER_DIR/run_pr_tracker.sh|g" \
    -e "s|__LOG_PATH__|$LOG_PATH|g" \
    "$TEMPLATE" > "$PLIST_DEST"

echo "Plist written."
echo ""

# ── Load launchd agent ───────────────────────────────────────────────────────
echo "Loading launchd agent ..."
launchctl unload "$PLIST_DEST" 2>/dev/null || true
launchctl load "$PLIST_DEST"

STATUS=$(launchctl list | grep pr-tracker || true)
echo "launchd status: $STATUS"
echo ""

# ── Done ─────────────────────────────────────────────────────────────────────
echo "=== Setup complete ==="
echo ""
echo "The tracker will run every 30 minutes. It skips silently if off VPN and"
echo "runs exactly once per day once the SF network is reachable."
echo ""
echo "To trigger a manual run:"
echo "  bash $PR_TRACKER_DIR/run_pr_tracker.sh"
echo ""
echo "To force a re-run after today's run already succeeded:"
echo "  PR_TRACKER_FORCE=1 bash $PR_TRACKER_DIR/run_pr_tracker.sh"
echo ""
echo "Logs: $LOG_PATH"
echo "Vault: $VAULT_DIR"
