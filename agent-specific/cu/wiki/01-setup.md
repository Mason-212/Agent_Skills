# Setup Claude Unleashed on macOS

Get from zero to your first session in ~10 minutes.

## 1. Prerequisites

- macOS (Intel or Apple Silicon)
- Git installed
- GitHub Enterprise access (for installation script)

## 2. Install the Mac App

**Option A: One-liner install (recommended)**

```bash
gh api -H "Accept: application/vnd.github.v3.raw" \
  --hostname git.soma.salesforce.com \
  repos/cc-oms/claude-unleashed/contents/scripts/install-mac.sh | bash
```

This downloads and installs the DMG, then launches the app.

**Option B: Manual install**

1. Download the latest DMG from the releases page
2. Drag `ClaudeUnleashed.app` to `/Applications/`
3. Launch the app

**First launch:** macOS may prompt you to allow the app. Go to System Settings → Privacy & Security and click "Open Anyway" if needed.

## 3. Sign In (Authentication)

Claude Unleashed has **no in-app login**. It reads gateway credentials from `~/.claude/settings.json` — the same file Claude Code uses.

**If you already use Claude Code:** You're done. Skip to Step 3.

**If you don't have Claude Code:**

1. Install Claude Code: `brew install claude` **(run in your regular terminal)**
2. Run `claude` once to trigger the auth flow **(also in regular terminal)**
3. Follow the prompts to sign in
4. Restart the CU daemon:
   ```bash
   # Run in your regular terminal
   claude-unleashed daemon restart
   ```

**Verify authentication (in your regular terminal):**

```bash
claude-unleashed models
```

Expected output: `source: probed` or `source: cache`. If you see `source: fallback`, auth failed — see troubleshooting below.

## 4. Install the Claude Code Plugin

The `cu-cli` plugin gives sessions access to CU-specific tools (session management, approvals, workflows).

**Install from marketplace:**

**⚠️ Run these commands in a Claude Code conversation (NOT your regular terminal):**

```
/plugin marketplace add https://git.soma.salesforce.com/cc-oms/claude-unleashed.git
/plugin install cu-cli
```

**Reload the plugin:**

Restart Claude Code or run `/plugin reload cu-cli` (also in Claude Code, not terminal) so the MCP server registers.

**Verify (back in your regular terminal):**

```bash
# This command IS in your regular terminal
claude-unleashed actions --json | grep cu_
```

You should see tools like `cu_session_list`, `cu_approval_approve`, etc.

## 5. Configure Git

Sessions commit on your behalf. Set the name/email they should use:

**Option A: Via Mac app (easier)**
1. Open Mac app → Settings → Git
2. Fill in:
   - Name: `Your Name`
   - Email: `you@salesforce.com`
   - SSH Key: Path to your private key (e.g., `~/.ssh/id_ed25519`)

**Option B: Via terminal commands**

```bash
# Run these in your regular terminal
claude-unleashed config set git.name "Your Name"
claude-unleashed config set git.email "you@salesforce.com"
claude-unleashed config set git.sshKeyPath "$HOME/.ssh/id_ed25519"
```

## 6. Discover Repos

CU scans common directories (`~/dev`, `~/src`, `~/code`) for git repos.

**Option A: Via Mac app (easier):** Click "Discover repos" button

**Option B: Via terminal commands:**

```bash
# Run in your regular terminal
claude-unleashed repos rescan --json
claude-unleashed repos ls
```

You should see your repos listed.

## 7. Enable the Overseer (Optional but Recommended)

The Overseer is the fleet-level supervisor that watches for stalls, auto-approves safe tool calls, and extends turns when needed.

**Option A: Via Mac app (easier):** Settings → Overseer → Toggle ON

**Option B: Via terminal command:**

```bash
# Run in your regular terminal
claude-unleashed overseer mode on
```

## 8. Verify Everything Works

Run the full diagnostic in your **regular terminal**:

```bash
claude-unleashed doctor
```

Expected output: All green checks for:
- ✅ Daemon running
- ✅ Auth configured
- ✅ Git configured
- ✅ Repos discovered
- ✅ Plugins healthy

**Check daemon status:**

```bash
# Run in your regular terminal
claude-unleashed daemon status --json
```

Expected: `"running": true`

**Check models:**

```bash
# Run in your regular terminal
claude-unleashed models
```

Expected: `source: probed` (means gateway probe succeeded)

## 9. Troubleshooting

### 9.1. Auth fails (`source: fallback`)

The daemon couldn't reach the gateway. Check:

```bash
echo $ANTHROPIC_AUTH_TOKEN
cat ~/.claude/settings.json | grep ANTHROPIC_AUTH_TOKEN
```

If both are empty, run `claude` (Claude Code CLI) to bootstrap auth, then restart the daemon.

### 9.2. Daemon won't start

```bash
claude-unleashed daemon stop
pkill -9 -f daemon-main
rm -f ~/.claude-unleashed/daemon.sock
claude-unleashed daemon start
```

Check logs:

```bash
tail -f ~/.claude-unleashed/daemon.log
```

### 9.3. Plugin tools not showing

```bash
claude-unleashed plugins doctor --json
```

Look for connection errors. If `cu-cli` is disconnected, reinstall:

```bash
/plugin uninstall cu-cli
/plugin install cu-cli
```

## 10. Next Steps

- [02-daily-commands.md](02-daily-commands.md) — Learn the essential CLI commands
- [03-feature-workflow.md](03-feature-workflow.md) — Try your first feature development workflow
