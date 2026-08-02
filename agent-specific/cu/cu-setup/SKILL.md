---
name: cu-setup
description: Verify and repair claude-unleashed installation on macOS
---

# CU Setup Diagnostic

Validates claude-unleashed installation and guides user through repairs.

## Usage

Invoke: `/cu-setup` in Claude/Cursor

## Process

I'll run diagnostics and guide you through fixes for any issues.

### 1. Check Daemon

**Command:** `claude-unleashed daemon status --json`

**Expected:** `"running": true`

**If fails:** Try restarting:
```bash
claude-unleashed daemon restart
```

Still failing? See `skills/shared/wiki_cu/01-setup.md` Section 9.2 (Daemon won't start) for troubleshooting.

### 2. Check Authentication

**Command:** `claude-unleashed models --json`

**Expected:** `"source"` is `"probed"` or `"cache"` (NOT `"fallback"`)

**If fails:** Authentication not configured. See `skills/shared/wiki_cu/01-setup.md` Section 3 (Authentication) for setup instructions.

### 3. Check Git Configuration

**Command:** `claude-unleashed config get git.name git.email git.sshKeyPath`

**Expected:** All three values are non-empty

**If fails:** I'll prompt you for these values:
- Git name (for commits)
- Git email
- SSH key path (e.g., `~/.ssh/id_ed25519`)

Then run:
```bash
claude-unleashed config set git.name "Your Name"
claude-unleashed config set git.email "you@example.com"  
claude-unleashed config set git.sshKeyPath "/path/to/key"
```

### 4. Check Git SSH Connectivity

**Command:** `ssh -T git@<your-git-host>`

**Expected:** Connection succeeds (exit 1 with "successfully authenticated" is success)

**If fails:** 
- Check SSH key exists at configured path
- Check SSH config has your configured git host entry
- See `skills/shared/wiki_cu/01-setup.md` Section 7 (SSH Setup) for SSH configuration

### 5. Check Repos Discovered

**Command:** `claude-unleashed repos ls --json`

**Expected:** At least one repo returned

**If fails:** Run repo discovery:
```bash
claude-unleashed repos rescan
```

### 6. Check Overseer Enabled

**Command:** `claude-unleashed overseer status --json`

**Expected:** `"enabled": true`

**If fails:** Enable overseer:
```bash
claude-unleashed overseer mode on
```

### 7. Check Plugin Installed

**Command:** `claude-unleashed actions --json | grep cu_`

**Expected:** At least one `cu_*` tool found

**If fails:** Plugin not installed. See `skills/shared/wiki_cu/01-setup.md` Section 4 (Plugin Installation) for installation steps.

### 8. Check Slack Integration (Optional)

**Command:** `claude-unleashed config get slack.botToken slack.defaultChannel`

**Expected:** Either both configured or both empty

**If both empty:** ⚠️ Optional: Slack not configured (not a failure)

**If one configured:** Incomplete Slack setup. Need both botToken and defaultChannel.

## Output Summary

After all checks, I'll summarize:

```
✅ CU setup verified. All systems ready.
```

Or if issues found:

```
❌ Setup incomplete. Fix the following:
  - Daemon not running → See wiki_cu/01-setup.md Section 9.2
  - Auth not configured → See wiki_cu/01-setup.md Section 3
  - Git not configured → Provide git.name, git.email, git.sshKeyPath
```

Or with warnings:

```
✅ Core setup complete.
⚠️ Optional: Slack not configured
```

## References

- `skills/shared/wiki_cu/01-setup.md` — Installation and configuration guide
- `skills/shared/wiki_cu/02-daily-commands.md` — CLI reference
