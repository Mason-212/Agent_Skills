# Appendix: Key Concepts and Capabilities

Deep reference for claude-unleashed concepts, architecture, and capabilities.

## Table of Contents

- [1. Core Concepts](#1-core-concepts)
  - [1.1. Sessions](#11-sessions)
  - [1.2. Profiles](#12-profiles)
  - [1.3. Agents](#13-agents)
  - [1.4. Worktrees](#14-worktrees)
  - [1.5. Branch Mode](#15-branch-mode)
- [2. Orchestration](#2-orchestration)
  - [2.1. Workflows](#21-workflows)
  - [2.2. Agent Groups](#22-agent-groups)
  - [2.3. Swarms](#23-swarms)
  - [2.4. Schedules](#24-schedules)
- [3. Automation](#3-automation)
  - [3.1. GUS CDC](#31-gus-cdc)
  - [3.2. Overseer](#32-overseer)
  - [3.3. Approvals](#33-approvals)
- [4. Architecture](#4-architecture)
  - [4.1. Daemon](#41-daemon)
  - [4.2. Mac App](#42-mac-app)
  - [4.3. CLI](#43-cli)
  - [4.4. Workers](#44-workers)

---

## 1. Core Concepts

### 1.1. Sessions

A **session** is a supervised Claude Code worker running in an isolated git worktree. Each session:

- Runs in its own worktree at `~/.claude-unleashed/worktrees/<session-id>/`
- Has its own branch: `claude-unleashed/<session-id>`
- Has a lifecycle: `pending` → `running` → `completed|failed|cancelled`
- Emits events (tool calls, commits, approvals) streamed via SSE

**Key properties:**
- `id` — UUID
- `shortName` — Human-readable (e.g., `plucky-lynx`)
- `status` — Current state
- `repoPath` — Absolute path to the source repo
- `branch` — Git branch (usually `claude-unleashed/<id>`)
- `workingDirectory` — Path to the worktree
- `agent` — Agent name (e.g., `executor`)
- `model` — Model ID (e.g., `claude-sonnet-4-6`)

**Session modes:**
- **Worktree mode (default):** Each session gets an isolated worktree
- **Branch mode:** Session runs in-place on your current branch (serialized per-repo)

### 1.2. Profiles

A **profile** is a saved launch configuration preset (settings overlay). Profiles do NOT define behavior — they only override resource limits and permissions.

**What profiles contain:**
- `model` — Which Claude model to use (optional override)
- `permissionMode` — Approval behavior (optional override)
- `maxTurns` / `maxBudgetUsd` — Resource limits (optional override)
- `systemPrompt` — ADDITIONAL prompt text (optional, appended to agent's prompt)
- `agentGroup` — Reference to an agent group (mutually exclusive with single agent)
- `swarm` — Reference to a swarm (mutually exclusive with agentGroup)
- `permissions` — Pre-approved tool allowlist
- `runMode` — Worktree vs branch mode

**What profiles do NOT contain:**
- NO `agent` field — you specify the agent separately at launch
- NO behavior definition — that's the agent's job

**Why use profiles?**

Instead of repeating flags every launch:

```bash
cu run --repo ~/my-app --agent executor --model sonnet --permission-mode auto --max-budget-usd 10
```

Save a profile and launch with BOTH profile AND agent:

```bash
cu run --repo ~/my-app --profile my-executor --agent executor --prompt "fix bug"
```

**Profile YAML structure:**

```yaml
name: my-executor
description: Resource limits for executor sessions
model: sonnet                # Override agent's default model
permissionMode: auto         # Override agent's permission mode
maxTurns: 100
maxBudgetUsd: 10.0
systemPrompt: |              # OPTIONAL: Additional instructions
  You are working on the edc-python codebase.
  Follow pytest-bdd patterns.
```

**Merge order:** Agent defaults → Profile overrides → CLI flag overrides

**Example:** If `executor` agent specifies `model: opus` and `my-executor` profile specifies `model: sonnet`, the session uses **sonnet** (profile wins).

**Scope:**
- **User-level:** `~/.claude-unleashed/profiles/`
- **Repo-level:** `<repo>/.claude-unleashed/profiles/`

Repo-level profiles override user-level ones with the same name.

**Think of it as:** A contract template — "the resource limits and permissions for this launch"

**Profiles vs Agents — The Key Distinction:**

| Aspect | Agent | Profile |
|--------|-------|---------|
| **Purpose** | Defines behavior | Overrides settings |
| **Contains** | systemPrompt (100+ lines), tools, skills | model, permissions, limits |
| **Think of it as** | Job description | Contract terms |
| **Required?** | YES (every session needs an agent) | NO (optional overrides) |
| **Usage** | `--agent executor` | `--profile my-executor` |
| **Launch** | `cu run --agent executor --repo ~/app --prompt "fix bug"` | `cu run --profile my-executor --agent executor --repo ~/app --prompt "fix bug"` |

**Merge order when launching:**
1. Agent provides base: systemPrompt, tools, default model, default limits
2. Profile overrides: model, permissionMode, maxTurns, maxBudgetUsd
3. CLI flags override: `--model opus` beats profile's model

**Example:**
- `executor` agent says: `model: opus`, `maxTurns: 400`
- `my-executor` profile says: `model: sonnet`, `maxBudgetUsd: 10.0`
- Result: Uses executor's systemPrompt + sonnet model + 400 turns + $10 budget

### 1.3. Agents

An **agent** defines the worker's complete behavior — what it knows how to do and how it should act. Agents are the job description; profiles are the contract terms.

**What agents contain:**
- `name` — Identifier
- `systemPrompt` — Full instruction set (can be 100+ lines)
- `allowedTools` / `disallowedTools` — Tool permissions
- `allowedSkills` / `recommendedSkills` — Skill catalog
- `model` — Which Claude model (optional default)
- `permissionMode` — Approval behavior (optional default)
- `maxTurns` / `maxUsdCost` — Resource limits (optional defaults)
- `archetype` — UI display category (developer/reviewer/etc.)
- `outputs` — Expected result structure for workflows

**Built-in agents:**
- `planner` — Designs features, writes specs (163-line systemPrompt)
- `executor` — Implements code via TDD (173-line systemPrompt)
- `reviewer` — Audits code, runs tests, opens PRs (180-line systemPrompt)

**Agent YAML structure:**

```yaml
name: executor
description: Implements features using test-driven development
archetype: developer
model: opus                # Default model (can be overridden by profile/CLI)
permissionMode: acceptEdits # Default permission mode
maxTurns: 400
maxUsdCost: 40.0

systemPrompt: |
  You execute the plan. One task at a time, in order, with
  red-green-refactor discipline.
  
  For each task:
  1. Red: write the failing test
  2. Green: write minimal implementation
  3. Commit
  
  [... 150 more lines of detailed instructions ...]

allowedTools:
  - Bash
  - Read
  - Edit
  - Write
  - Grep
  - TodoWrite

recommendedSkills:
  - test-driven-development
  - systematic-debugging

outputs:
  commits_range:
    description: Git commit range produced (e.g. HEAD~3..HEAD)
    required: true
    kind: string
  pr_url:
    description: URL of the PR opened against main
    required: true
    kind: string
```

**Scope:**
- **Built-in:** Shipped with CU at `.claude-unleashed/agents/`
- **User-level:** `~/.claude-unleashed/agents/`
- **Repo-level:** `<repo>/.claude-unleashed/agents/`

**Think of it as:** A job description — "what this worker knows how to do and how it should behave"

**Key difference from profiles:** Agents define behavior (systemPrompt, tools). Profiles override settings (model, limits, permissions).

### 1.4. Worktrees

A **worktree** is an isolated git workspace. CU creates one per session so they don't conflict.

**Why worktrees?**

Without worktrees, two sessions editing the same repo would:
- Overwrite each other's uncommitted changes
- Conflict on branch checkouts
- Race on git operations

With worktrees:
- Each session gets its own directory
- Each has its own branch checked out
- Git operations are isolated

**Worktree lifecycle:**

1. **Created** when session starts: `~/.claude-unleashed/worktrees/<session-id>/`
2. **Used** by the worker for all file operations
3. **Auto-pruned** when session completes (configurable grace period)

**Manual cleanup:**

```bash
cu diagnostics worktree-prune --confirm
```

### 1.5. Branch Mode

**Branch mode** (`runMode: in-place`) lets sessions run directly on your current branch without creating worktrees.

**When to use:**
- You're actively working on a feature branch
- You want CU to help without creating throwaway worktrees
- You trust the agent (no conflicts expected)

**How it works:**
- Sessions serialize per-repo via an `InPlaceQueue`
- Only one session per repo runs at a time
- Next session waits until the first completes
- Clean working tree required (no uncommitted changes)

**Launch in branch mode:**

```bash
cd ~/my-app
git checkout feature/2fa

cu run --repo . \
  --run-mode in-place \
  --agent executor \
  --prompt "Add rate limiting"
```

**Trade-offs:**
- **Pro:** No worktree overhead, changes land directly on your branch
- **Con:** Sessions block each other, can't run in parallel

See [15-branch-mode.md](../wiki/15-branch-mode.md) for details.

---

## 2. Orchestration

### 2.1. Workflows

A **workflow** is a multi-step orchestrated run. Each step (node) spawns a session with its own agent.

**Workflows reference agents directly — NOT profiles.** All configuration is inline in the workflow YAML.

**Built-in workflows:**
- `full-process` — plan → execute → review
- `innerloop` — execute → review (skip planning)
- `investigation` — Multi-agent debugging team

**Workflow YAML structure:**

```yaml
name: full-process
description: Plan, implement, and review a feature

nodes:
  - id: plan
    agent: planner          # Direct agent reference
    maxTurns: 50            # Inline configuration
    maxBudgetUsd: 5.0       # (no profile used)
    inputs:
      prompt: "Design {{input.prompt}}"

  - id: execute
    agent: executor
    needs: [plan]           # Dependency declaration
    maxTurns: 750
    maxBudgetUsd: 75.0
    inputs:
      prompt: "Implement the plan at {{nodes.plan.plan_path}}"

  - id: review
    agent: reviewer
    needs: [execute]
    maxTurns: 300
    maxBudgetUsd: 30.0
    inputs:
      prompt: "Review and open PR"
```

**Run a workflow:**

```bash
cu workflow run full-process \
  --repo ~/my-app \
  --input '{"prompt":"Add 2FA"}'
```

**Why workflows don't use profiles:**
- Workflow YAML already contains all settings (maxTurns, model, etc.)
- Each node can have different limits
- Profiles are for **standalone** `cu run` sessions, not orchestrated workflows

### 2.2. Agent Groups

An **agent group** is a named bundle of agents with a coordinator.

**Why use groups?**

Instead of manually orchestrating sub-agents, the coordinator handles it:

```yaml
name: cicd-team
coordinator: team-lead
members:
  - name: ci-checker
  - name: pr-fixer
  - name: slack-notifier

coordinatorPrompt: |
  You lead the CI team.
  1. Ask ci-checker to find failures
  2. Ask pr-fixer to fix them
  3. Ask slack-notifier to report results
```

**Launch with a group:**

```bash
cu run --repo ~/my-app \
  --agent-group cicd-team \
  --prompt "Monitor and fix CI"
```

### 2.3. Swarms

A **swarm** is a reusable parameterized agent fan-out. Unlike agent groups, swarms are **never run standalone** — they're referenced from a profile or workflow node.

**Swarm YAML structure:**

```yaml
name: audit-swarm
description: Fan-out auditor for multiple files
lead: audit-coordinator

members:
  - name: security-auditor
  - name: performance-auditor
  - name: correctness-auditor

leadPrompt: |
  You coordinate the audit.
  Fan out to each auditor for their domain.
  Synthesize findings.
```

**Reference from a workflow:**

```yaml
nodes:
  - id: audit
    swarm: audit-swarm
    prompt: "Audit {{input.files}}"
```

### 2.4. Schedules

A **schedule** is a cron-driven deferred launch. It fires `cu run` or `cu workflow run` on a cadence.

**Create a schedule:**

```bash
cu schedules add daily-audit \
  --kind workflow \
  --target full-process \
  --repo ~/my-app \
  --cron "0 9 * * *" \
  --prompt "Audit yesterday's commits" \
  --agent reviewer
```

**Schedule lifecycle:**
- **Enabled** — Fires on schedule
- **Disabled** — Paused (manual toggle)
- **Auto-disabled** — Circuit breaker after 5 consecutive failures

**Re-enable:**

```bash
cu schedules enable daily-audit
```

---

## 3. Automation

### 3.1. GUS CDC

**GUS CDC (Change Data Capture)** binds Salesforce events to CU launches. When a GUS work item or GitHub webhook fires, CU spawns a session.

**Example: Auto-triage bugs**

```bash
cu cdc add bug-triager \
  --event work.created \
  --filter "work.type == 'Bug'" \
  --template "Triage bug: {{work.subject}}" \
  --agent triager \
  --repo ~/my-app
```

Now whenever a bug is filed in GUS, CU launches a triager session.

**CDC scopes:**
- GUS work item events
- GitHub webhook events (PR, issue, push)
- Custom Salesforce CDC

See [19-gus-cdc.md](../wiki/19-gus-cdc.md) for setup.

### 3.2. Overseer

The **Overseer** is the always-on fleet supervisor. It:
- Watches for stalled sessions and nudges them
- Auto-extends turns when a session hits the cap but is making progress
- Auto-approves safe tool calls (via policy cascade)
- Routes alerts to Slack

**Enable the Overseer:**

```bash
cu overseer mode on
```

**Auto-approval cascade:**

When a session requests approval, the Overseer runs three tiers:
1. **Deny policies** — Reject if matches (e.g., `rm -rf /`)
2. **Allow policies** — Approve if matches (e.g., `npm install`)
3. **LLM tier** — Ask Claude to judge (within budget)

**Configure policies:**

Edit via Mac app (Setup → Approvals) or CLI:

```bash
cu overseer policies show
```

See [21-overseer.md](../wiki/21-overseer.md) for details.

### 3.3. Approvals

When a session calls a risky tool (e.g., `git push`, `npm install`), it pauses and requests approval.

**Approval lifecycle:**
1. Session emits `approval-requested` event
2. Overseer checks policies (if enabled)
3. If no policy matches, approval waits for operator
4. Operator approves/denies/replies
5. Session resumes

**Approval types:**
- **Tool call** — Permission for a specific tool invocation
- **AskUserQuestion** — Multiple-choice prompt for the session

**Auto-approval cache:**

Once you approve a tool call, similar calls auto-approve for 24 hours (configurable).

---

## 4. Architecture

### 4.1. Daemon

The **daemon** is the core Node.js process that:
- Manages session lifecycle
- Stores state in SQLite (`~/.claude-unleashed/state.db`)
- Serves HTTP + SSE over Unix domain socket (`~/.claude-unleashed/daemon.sock`)
- Loads agent catalog, model registry, and config

**Start/stop:**

```bash
cu daemon start
cu daemon stop
cu daemon restart
```

**Logs:**

```bash
tail -f ~/.claude-unleashed/daemon.log
```

### 4.2. Mac App

The **Mac app** (SwiftUI) is a thin client over the daemon. It:
- Displays sessions, approvals, and events
- Provides UI for launching sessions
- Manages settings (git, Slack, Overseer)

**No business logic lives in the app** — it's all in the daemon. The app just renders state and sends commands.

### 4.3. CLI

The **CLI** (`cu` / `claude-unleashed`) is a thin HTTP client over the daemon socket. Every command hits an endpoint:

| Command | Endpoint |
|---------|----------|
| `cu sessions ls` | `GET /sessions` |
| `cu run ...` | `POST /sessions` |
| `cu approvals approve <id>` | `POST /approvals/:id/approve` |

**No business logic in the CLI** — it's all in the daemon.

### 4.4. Workers

A **worker** is a Claude Code CLI process spawned by the daemon. Each session gets one worker.

**Worker lifecycle:**
1. Daemon spawns `claude` via `child_process.spawn`
2. Worker connects to gateway, starts conversation loop
3. Worker emits events to daemon via JSONL on stdout
4. Worker terminates when session completes

**Worker isolation:**
- Each runs in its own worktree (or in-place for branch mode)
- Each has its own branch
- Workers can't see each other's state

---

## 5. Capabilities Summary

### 5.1. What CU Can Do

- **Run Claude Code as a background job** with supervision
- **Isolate sessions** in git worktrees or run in-place on your branch
- **Orchestrate multi-agent workflows** (plan → execute → review)
- **Schedule recurring tasks** (cron-driven launches)
- **Monitor and auto-approve** tool calls via the Overseer
- **Integrate with Slack** for alerts and interactive control
- **Bind to external events** (GUS CDC, GitHub webhooks)
- **Manage fleets** (pause/resume/kill all sessions)

### 5.2. What CU Cannot Do

- **Remote daemon** — CU only runs locally (no TCP/auth for remote access)
- **Cross-repo coordination** — Sessions are scoped to one repo
- **Real-time collaboration** — Sessions run async, not interactive
- **Windows/Linux** — Mac-only for now (CLI works on Linux, but Mac app is required for full experience)

---

## 6. Next Steps

- [02-daily-commands.md](02-daily-commands.md) — CLI reference
- [03-feature-workflow.md](03-feature-workflow.md) — Feature development use case
- [04-cicd-automation.md](04-cicd-automation.md) — CI/CD automation use case
- [Full wiki](../wiki/README.md) — Comprehensive reference
