# Daily Commands

Essential CLI commands for day-to-day claude-unleashed usage.

## 1. Three Ways to Control Claude Unleashed

You can interact with CU in three ways:

### 1.1. Mac App (GUI)
**When to use:** Quick visual overview, clicking through approvals, configuring settings

**Examples:**
- Launch sessions: Click "New Session" button
- View running sessions: Main window dashboard
- Approve tool calls: Click "Approve" in approvals list
- Configure git: Settings → Git pane

### 1.2. Terminal Commands (Scripting)
**When to use:** Automation, scripting, CI/CD integration, when you prefer CLI

**Commands:**
- `cu` (shorthand) or `claude-unleashed` (full name) - **they're the same command**
- Run in your **regular terminal** (bash/zsh), NOT in Claude Code

**Examples:**
```bash
# These are ALL regular terminal commands
cu daemon status
cu sessions ls
cu run --repo ~/my-project --prompt "Add tests"
claude-unleashed approvals approve <id>  # Same as "cu approvals approve <id>"
```

### 1.3. Claude Code Conversation (Natural Language)
**When to use:** When you want to just talk to Claude about CU sessions

**Setup:** Install the `cu-cli` plugin (see [01-setup.md](01-setup.md))

**Examples:**
```
You: "What sessions are running?"
Claude: [calls cu_session_list tool and shows results]

You: "Approve the pending approval"
Claude: [calls cu_approval_approve]

You: "Start a session in ~/my-app to add auth tests"
Claude: [calls cu_run to launch]
```

**Note:** The `/plugin` commands (like `/plugin install cu-cli`) ARE typed in Claude Code, not terminal.

---

## 2. All Commands Below Are Terminal Commands

Every command in the rest of this guide is run in your **regular terminal**, not Claude Code or the Mac app.

Format: `cu <subcommand>` (or `claude-unleashed <subcommand>` - they're identical)

## 3. Core Concepts (Quick Reference)

Before diving into commands, understand these four concepts:

- **Session:** A supervised Claude Code worker running in a git worktree. Each session has its own isolated branch.
- **Profile:** A saved launch template (repo + agent + model + permissions). Think of it as a preset.
- **Agent:** Defines the worker's behavior (planner vs executor vs reviewer). Lives in `.claude-unleashed/agents/*.yaml`.
- **Worktree:** Isolated git workspace. Sessions run in `~/.claude-unleashed/worktrees/<sessionId>/` so they don't conflict.

See [appendix-concepts.md](appendix-concepts.md) for deeper explanations.

## 4. Daemon Management

Always ensure the daemon is running first:

```bash
# Check status
cu daemon status

# Start (if not running)
cu daemon start

# Restart (preserves running sessions)
cu daemon restart

# Stop
cu daemon stop
```

**Alias tip:** `cu` is shorthand for `claude-unleashed` — use whichever you prefer.

## 5. Session Lifecycle

### 5.1. Start a new session

**Basic form:**

```bash
cu run --repo ~/my-project --prompt "Add unit tests for auth module"
```

**With a profile:**

```bash
cu run --repo ~/my-project --profile executor --prompt "Refactor database layer"
```

**With agent override:**

```bash
cu run --repo ~/my-project --agent planner --prompt "Design a new feature"
```

**Key flags:**
- `--repo <path>` — Absolute path to your git repo
- `--profile <name>` — Use a saved profile (lists with `cu profiles ls`)
- `--agent <name>` — Override the agent (lists with `cu agents ls`)
- `--prompt "<text>"` — What you want the session to do
- `--permission-mode auto` — Skip approval prompts (use with caution)
- `--model opus` — Override model (opus/sonnet/haiku)

### 5.2. List sessions

```bash
# All sessions
cu sessions ls

# JSON output (machine-readable)
cu sessions ls --json

# Filter by status
cu sessions ls --status running
cu sessions ls --status completed

# Filter by repo
cu sessions ls --repo ~/my-project

# Group by repo
cu sessions ls --group-by repo
```

### 5.3. Check a specific session

```bash
# Get details
cu sessions get <id-or-shortname>

# JSON output
cu sessions get plucky-lynx --json

# Watch live output
cu tail <id>

# Watch from the beginning
cu tail <id> --from-start
```

**Short names:** CU generates memorable names like `plucky-lynx` for each session. Use these instead of UUIDs.

### 5.4. Resume a session

Add another turn to a running session:

```bash
cu continue <id> --prompt "Now add integration tests"
```

### 5.5. Control sessions

```bash
# Pause (SIGSTOP)
cu sessions pause <id>

# Resume (SIGCONT)
cu sessions resume <id>

# Cancel (graceful)
cu sessions kill <id>

# Nudge a stalled session
cu sessions unstick <id>
```

### 5.6. Clean up completed sessions

```bash
# Preview what would be deleted
cu sessions prune --older-than 30 --dry-run

# Actually delete
cu sessions prune --older-than 30
```

## 6. Approvals

When a session requests permission for a tool call:

```bash
# List pending approvals
cu approvals ls

# Approve
cu approvals approve <id>

# Deny
cu approvals deny <id>

# Reply with custom message
cu approvals reply <id> "Use the staging database instead"
```

**Tip:** If there's only one pending approval, just say "approve it" to Claude (if you have the cu-cli plugin loaded). It'll resolve it for you.

## 7. Profiles & Agents

### 7.1. Profiles

Profiles save launch configurations so you don't repeat `--repo`, `--agent`, `--model` every time.

```bash
# List profiles
cu profiles ls

# Show a profile
cu profiles show executor

# Save a new profile
cu profiles save my-profile ~/path/to/profile.yaml

# Delete a profile
cu profiles rm my-profile
```

**Profile YAML structure:**

```yaml
name: executor
agent: executor
model: sonnet
permissionMode: default
limits:
  maxTurns: 50
  maxBudgetUsd: 5
```

### 7.2. Agents

Agents define worker behavior (skills, tools, system prompt).

```bash
# List agents
cu agents ls

# Show an agent
cu agents show executor

# Save a new agent
cu agents save my-agent ~/path/to/agent.yaml

# Delete an agent
cu agents rm my-agent
```

## 8. Repos

```bash
# List discovered repos
cu repos ls

# Rescan for new repos
cu repos rescan

# Bind a default profile to a repo
cu repos set-profile ~/my-project executor
```

## 9. Workflows

Multi-step orchestrated runs (plan → execute → review).

```bash
# List workflows
cu workflow ls

# Run a workflow
cu workflow run full-process --repo ~/my-project --input '{"prompt":"Add auth tests"}'

# List past runs
cu workflow runs

# Resume a failed run
cu workflow resume <runId>
```

## 10. Fleet Operations

### 10.1. Broadcast to all running sessions

```bash
# Ask all sessions a question
cu sessions ask-all "What file are you editing?" --json
```

### 10.2. Pause/resume/kill all

```bash
# Pause all running sessions
cu sessions pause-all

# Resume all paused sessions
cu sessions resume-all

# Kill all sessions (filtered)
cu sessions kill-all --status running --repo ~/my-project
```

## 11. Observability

### 11.1. Dashboard

```bash
# Rollup stats (sessions, cost, approvals)
cu dashboard --json
```

### 11.2. Reports

```bash
# Weekly cost/turns summary
cu report --json
```

### 11.3. Diagnostics

```bash
# Full health check
cu doctor

# Worktree cleanup (preview)
cu diagnostics worktree-prune --dry-run

# Worktree cleanup (execute)
cu diagnostics worktree-prune --confirm
```

## 12. Quick Workflows

### 12.1. "Start a session on this repo"

```bash
cd ~/my-project
cu run --repo . --profile executor --prompt "Fix the login bug"
```

### 12.2. "Check what's running"

```bash
cu sessions ls --status running
```

### 12.3. "Approve pending and continue"

```bash
cu approvals ls
cu approvals approve <id>
cu tail <session-id>
```

### 12.4. "Kill stuck sessions older than 2 hours"

```bash
cu sessions kill --status running --older-than 2h --dry-run
cu sessions kill --status running --older-than 2h
```

### 12.5. "Clean up completed sessions and worktrees"

```bash
cu sessions prune --older-than 7 --dry-run
cu sessions prune --older-than 7
cu diagnostics worktree-prune --confirm
```

## 13. Common Pitfalls

### 13.1. Session starts but makes no progress

Check if it's waiting for approval:

```bash
cu approvals ls
```

### 13.2. "Cannot find session X"

List all sessions and use the exact short name or ID:

```bash
cu sessions ls --json | grep -i lynx
```

### 13.3. Daemon won't respond

Restart it:

```bash
cu daemon restart
```

Check logs:

```bash
tail -f ~/.claude-unleashed/daemon.log
```

### 13.4. Git conflicts in worktree

Sessions run in isolated worktrees — conflicts shouldn't happen. If they do:

```bash
cu sessions get <id> --json | grep workingDirectory
cd <working-directory>
git status
```

Resolve manually, then resume with `cu continue <id>`.

## 14. Next Steps

- [03-feature-workflow.md](03-feature-workflow.md) — Walk through developing a feature with CU
- [04-cicd-automation.md](04-cicd-automation.md) — Automate CI monitoring and PR handling
- [appendix-concepts.md](appendix-concepts.md) — Deep dive into concepts
