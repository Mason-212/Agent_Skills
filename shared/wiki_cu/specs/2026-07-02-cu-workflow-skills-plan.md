# CU Workflow Skills Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Create three Claude Code skills (cu-setup, cu-wf-create, cu-wf-run) that help users validate CU installation, generate workflows, and launch them.

**Architecture:** Three independent skills sharing a common knowledge base (wiki_cu). Each skill is a markdown file with frontmatter defining invocation and behavior. cu-setup runs diagnostics interactively. cu-wf-create uses collaborative design to generate workflow YAMLs + agents. cu-wf-run lists and launches workflows with progress monitoring.

**Tech Stack:** Claude Code skills (markdown + frontmatter), bash commands (cu CLI), YAML generation

## Global Constraints

- Skills must be invocable via `/skill-name` in Claude/Cursor conversations
- All skills reference `skills/shared/wiki_cu/` for documentation
- Skills directory: `/Users/thomaschang/Documents/dev/git/thomaschangsf/skills/`
- YAML generation must match CU schema (see `.claude-unleashed/agents/*.yaml` and `.claude-unleashed/workflows/*.yaml` examples)
- No external dependencies beyond bash, cu CLI, and standard file operations

---

### Task 1: Create cu-setup Skill

**Files:**
- Create: `/Users/thomaschang/Documents/dev/git/thomaschangsf/skills/cu-setup/SKILL.md`

**Interfaces:**
- Consumes: None (first skill)
- Produces: Diagnostic output format that cu-wf-create and cu-wf-run can check

- [ ] **Step 1: Write test verification script**

Create `/Users/thomaschang/Documents/dev/git/thomaschangsf/skills/cu-setup/test-skill.sh`:

```bash
#!/usr/bin/env bash
# Test cu-setup skill by simulating invocation

set -euo pipefail

SKILL_FILE="/Users/thomaschang/Documents/dev/git/thomaschangsf/skills/cu-setup/SKILL.md"

if [[ ! -f "$SKILL_FILE" ]]; then
  echo "FAIL: SKILL.md not found"
  exit 1
fi

# Check frontmatter exists
if ! grep -q "^---$" "$SKILL_FILE"; then
  echo "FAIL: No frontmatter found"
  exit 1
fi

# Check skill name
if ! grep -q "^name: cu-setup$" "$SKILL_FILE"; then
  echo "FAIL: name not set to cu-setup"
  exit 1
fi

echo "PASS: cu-setup skill structure valid"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `bash /Users/thomaschang/Documents/dev/git/thomaschangsf/skills/cu-setup/test-skill.sh`

Expected: FAIL with "SKILL.md not found"

- [ ] **Step 3: Create cu-setup skill file**

Create `/Users/thomaschang/Documents/dev/git/thomaschangsf/skills/cu-setup/SKILL.md`:

```markdown
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

Still failing? See `skills/shared/wiki_cu/01-setup.md` § 9.2 for troubleshooting.

### 2. Check Authentication

**Command:** `claude-unleashed models --json`

**Expected:** `"source"` is `"probed"` or `"cache"` (NOT `"fallback"`)

**If fails:** Authentication not configured. See `skills/shared/wiki_cu/01-setup.md` § 3 for setup instructions.

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

**Command:** `ssh -T git@git.soma.salesforce.com`

**Expected:** Connection succeeds (exit 1 with "successfully authenticated" is success)

**If fails:** 
- Check SSH key exists at configured path
- Check SSH config has git.soma.salesforce.com entry
- See `skills/shared/wiki_cu/01-setup.md` for SSH setup

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

**If fails:** Plugin not installed. See `skills/shared/wiki_cu/01-setup.md` § 4 for installation steps.

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
  - Daemon not running → See wiki_cu/01-setup.md § 9.2
  - Auth not configured → See wiki_cu/01-setup.md § 3
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
```

- [ ] **Step 4: Run test to verify it passes**

Run: `bash /Users/thomaschang/Documents/dev/git/thomaschangsf/skills/cu-setup/test-skill.sh`

Expected: PASS with "cu-setup skill structure valid"

- [ ] **Step 5: Commit**

```bash
cd /Users/thomaschang/Documents/dev/git/thomaschangsf/skills
git add cu-setup/SKILL.md cu-setup/test-skill.sh
git commit -m "feat: add cu-setup skill for CU installation validation"
```

---

### Task 2: Create cu-wf-create Guides

**Files:**
- Create: `/Users/thomaschang/Documents/dev/git/thomaschangsf/skills/cu-wf-create/guides/node-boundary-criteria.md`
- Create: `/Users/thomaschang/Documents/dev/git/thomaschangsf/skills/cu-wf-create/guides/domain-detection.md`
- Create: `/Users/thomaschang/Documents/dev/git/thomaschangsf/skills/cu-wf-create/guides/agent-strategy.md`

**Interfaces:**
- Consumes: None (reference files for cu-wf-create skill)
- Produces: Documentation that cu-wf-create SKILL.md references

- [ ] **Step 1: Write test for guides directory**

Create `/Users/thomaschang/Documents/dev/git/thomaschangsf/skills/cu-wf-create/test-guides.sh`:

```bash
#!/usr/bin/env bash
set -euo pipefail

GUIDES_DIR="/Users/thomaschang/Documents/dev/git/thomaschangsf/skills/cu-wf-create/guides"

if [[ ! -d "$GUIDES_DIR" ]]; then
  echo "FAIL: guides directory not found"
  exit 1
fi

FILES=("node-boundary-criteria.md" "domain-detection.md" "agent-strategy.md")
for file in "${FILES[@]}"; do
  if [[ ! -f "$GUIDES_DIR/$file" ]]; then
    echo "FAIL: $file not found"
    exit 1
  fi
done

echo "PASS: All guide files exist"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `bash /Users/thomaschang/Documents/dev/git/thomaschangsf/skills/cu-wf-create/test-guides.sh`

Expected: FAIL with "guides directory not found"

- [ ] **Step 3: Create guides directory and files**

```bash
mkdir -p /Users/thomaschang/Documents/dev/git/thomaschangsf/skills/cu-wf-create/guides
```

Create `/Users/thomaschang/Documents/dev/git/thomaschangsf/skills/cu-wf-create/guides/node-boundary-criteria.md`:

```markdown
# Node Boundary Criteria

When designing workflows, use these 6 criteria to determine node boundaries:

## 1. Distinct Responsibility

**Rule:** Different "job" (fetch vs transform vs notify)

**Example:**
- Fetcher node: Calls GitHub API for PRs
- Processor node: Aggregates PR data
- Different jobs → separate nodes

## 2. Data Handoff

**Rule:** Node A outputs artifact, Node B consumes it

**Example:**
- Analyzer outputs findings.json
- Reporter reads findings.json
- Clear handoff → separate nodes

## 3. Different Tools

**Rule:** Read-only vs writes vs APIs vs MCP servers

**Example:**
- Analyzer needs: Bash, Read, Grep (read-only)
- Reporter needs: Write (writes files)
- Different tool sets → separate nodes

## 4. Independent Failure

**Rule:** Node A can fail without invalidating Node B

**Example:**
- Fetcher can fail (network error)
- Processor still valid (can retry fetch)
- Independent failure modes → separate nodes

## 5. Reusability

**Rule:** Node could be extracted for other workflows

**Example:**
- Security scanner node could be reused across workflows
- Reusable component → separate node

## 6. ⭐ Verification Gate

**Rule:** Node B independently verifies Node A achieved its goal

**Example:**
- Analyzer produces findings.json
- Reporter validates findings.json schema before writing report
- Different agent = independent verification
- Catches if analyzer crashed or output malformed

**Key insight:** Each node transition is a quality gate.

## Decision Framework

Create separate nodes when **≥ 3 criteria apply**.

Keep nodes together when:
- Tightly coupled (can't do B without A)
- No useful intermediate output
- Same failure domain

## Examples

**Good: 2-node structure**
```
analyzer → reporter

Criteria:
✓ 1. Distinct: analysis vs reporting
✓ 2. Handoff: findings.json
✓ 3. Tools: test/lint vs Write
✓ 6. Verification: reporter validates schema

Result: 4/6 criteria → separate nodes justified
```

**Bad: Single node**
```
all-in-one (analyze + report)

Criteria:
✗ No verification gate
✗ No handoff checkpoint
✗ Same agent validates its own work

Result: 0/6 criteria → should split
```
```

Create `/Users/thomaschang/Documents/dev/git/thomaschangsf/skills/cu-wf-create/guides/domain-detection.md`:

```markdown
# Domain Detection

Classify the user's workflow request into a domain, then extract domain-specific roles.

## Common Domains

### 1. Coding Workflows

**Indicators:** plan, implement, test, review, refactor, fix, debug

**Natural roles:** planner → executor → reviewer

**Example:** "Build feature X" → plan → implement → review

### 2. Data Aggregation

**Indicators:** fetch, aggregate, transform, summarize, report

**Natural roles:** fetcher → processor → reporter

**Example:** "Aggregate PRs and post to Slack" → fetch → aggregate → notify

### 3. Monitoring & Response

**Indicators:** detect, monitor, alert, respond, fix, notify

**Natural roles:** detector → responder → notifier

**Example:** "Monitor CI and fix failures" → detect → diagnose → fix → notify

### 4. Research & Documentation

**Indicators:** search, analyze, synthesize, document, write

**Natural roles:** searcher → analyzer → synthesizer → documenter

**Example:** "Research topic X" → search → analyze → synthesize → document

### 5. Quality Verification

**Indicators:** check, verify, test, lint, audit, scan

**Natural roles:** checker → reporter (or checker → fixer → verifier)

**Example:** "Verify branch quality" → analyze → report

## Detection Process

1. **Extract verbs** from prompt: "fetch", "aggregate", "post"
2. **Extract nouns** from prompt: "PRs", "summary", "Slack"
3. **Match to domain** based on verb patterns
4. **Determine natural roles** for that domain

## Examples

**Prompt:** "Create a workflow to verify quality of my local branch"

- Verbs: verify, check
- Nouns: branch, quality
- Domain: Quality Verification
- Roles: analyzer (run checks) → reporter (write report)

**Prompt:** "Find and fix all failing tests"

- Verbs: find, fix
- Nouns: tests, failures
- Domain: Monitoring & Response
- Roles: detector (find failures) → fixer (repair) → verifier (confirm)

**Prompt:** "Aggregate PRs merged this week and post to Slack"

- Verbs: aggregate, post
- Nouns: PRs, Slack
- Domain: Data Aggregation
- Roles: fetcher (get PRs) → processor (aggregate) → notifier (post)
```

Create `/Users/thomaschang/Documents/dev/git/thomaschangsf/skills/cu-wf-create/guides/agent-strategy.md`:

```markdown
# Agent Strategy

When to create custom agents vs reuse generic agents.

## Default: Custom Agents Per Workflow

cu-wf-create generates custom agents by default because:

1. **Domain-specific systemPrompts** — Each workflow needs tailored instructions
2. **Tool requirements vary** — Different workflows need different tool sets
3. **Self-contained workflows** — Portable, self-documenting

## Agent Naming Convention

**Pattern:** `<workflow-slug>_<role>`

**Examples:**
- `branch-quality-check_analyzer`
- `branch-quality-check_reporter`
- `test-fixer_detector`
- `test-fixer_fixer`
- `test-fixer_verifier`

## Common Roles

- `_analyzer` — Analyzes/checks (read-only)
- `_fixer` — Repairs issues (writes code)
- `_reporter` — Writes reports/documentation
- `_verifier` — Validates prior work
- `_coordinator` — Orchestrates sub-tasks
- `_fetcher` — Retrieves data (API calls)
- `_processor` — Transforms data
- `_notifier` — Sends notifications

## Agent YAML Template

```yaml
name: <workflow-slug>_<role>
description: <What this agent does>
archetype: <developer|reviewer|writer|other>
model: <sonnet|opus|haiku>

systemPrompt: |
  <Detailed instructions for this agent>
  
  <What to do>
  <What to output>
  <How to handle errors>

allowedTools:
  - Bash
  - Read
  - Write
  - <other tools>

outputs:
  <output-name>:
    description: <What this output contains>
    required: true
    kind: <json|string|file>
```

## Tool Selection by Role

**Analyzer (read-only):**
- Bash (run tests/lint)
- Read
- Grep

**Fixer (writes code):**
- Bash
- Read
- Edit
- Write

**Reporter (writes docs):**
- Read
- Write

**Fetcher (API calls):**
- Bash (curl, gh CLI)
- Write (save data)

**Notifier (external systems):**
- Bash (slack CLI, email)
- Read (get content to send)

## Model Selection

**Analyzer/Fixer (complex logic):**
- `model: sonnet` (balance of speed and capability)
- `model: opus` (for very complex analysis)

**Reporter/Notifier (simple formatting):**
- `model: haiku` (fast, cheap)
- `model: sonnet` (if needs judgment)

## When to Ask User

If workflow seems generic (could apply to many repos), ask:

> "Should I create custom agents or reuse generic agents (executor/reviewer) with workflow-specific prompts?"

Most workflows: custom agents (recommended)
Rare cases: generic agents with inline prompts
```

- [ ] **Step 4: Run test to verify it passes**

Run: `bash /Users/thomaschang/Documents/dev/git/thomaschangsf/skills/cu-wf-create/test-guides.sh`

Expected: PASS with "All guide files exist"

- [ ] **Step 5: Commit**

```bash
cd /Users/thomaschang/Documents/dev/git/thomaschangsf/skills
git add cu-wf-create/guides/ cu-wf-create/test-guides.sh
git commit -m "feat: add cu-wf-create guides for workflow design"
```

---

### Task 3: Create cu-wf-create Skill

**Files:**
- Create: `/Users/thomaschang/Documents/dev/git/thomaschangsf/skills/cu-wf-create/SKILL.md`

**Interfaces:**
- Consumes: cu-setup status (can invoke cu-setup as pre-flight), guides from Task 2
- Produces: Workflow YAML files + agent YAML files in target repo

- [ ] **Step 1: Write test for cu-wf-create skill**

Create `/Users/thomaschang/Documents/dev/git/thomaschangsf/skills/cu-wf-create/test-skill.sh`:

```bash
#!/usr/bin/env bash
set -euo pipefail

SKILL_FILE="/Users/thomaschang/Documents/dev/git/thomaschangsf/skills/cu-wf-create/SKILL.md"

if [[ ! -f "$SKILL_FILE" ]]; then
  echo "FAIL: SKILL.md not found"
  exit 1
fi

# Check frontmatter
if ! grep -q "^name: cu-wf-create$" "$SKILL_FILE"; then
  echo "FAIL: name not set to cu-wf-create"
  exit 1
fi

# Check references guides
if ! grep -q "guides/node-boundary-criteria.md" "$SKILL_FILE"; then
  echo "FAIL: doesn't reference node-boundary-criteria.md"
  exit 1
fi

echo "PASS: cu-wf-create skill structure valid"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `bash /Users/thomaschang/Documents/dev/git/thomaschangsf/skills/cu-wf-create/test-skill.sh`

Expected: FAIL with "SKILL.md not found"

- [ ] **Step 3: Create cu-wf-create skill file**

Create `/Users/thomaschang/Documents/dev/git/thomaschangsf/skills/cu-wf-create/SKILL.md`:

```markdown
---
name: cu-wf-create
description: Generate claude-unleashed workflows through collaborative design
---

# CU Workflow Creator

Generate workflows from prompts or plan files through interactive design.

## Usage

Invoke: `/cu-wf-create` in Claude/Cursor

**Inputs:**
- Freeform prompt: "Create a workflow to verify quality of my local branch"
- OR plan file path: `docs/plans/2026-07-02-branch-check.md`
- Target repo path: `/Users/thomaschang/Documents/dev/git/a360/edc-python`

## Process

### Pre-flight: Setup Check

First, I'll verify CU is set up by invoking `/cu-setup`.

If setup fails, I'll stop and show you how to fix issues.

### Design Heuristic

I use: **Domain → Roles → Nodes → Agents**

Before proposing structures, I'll read:
- `guides/node-boundary-criteria.md` (6 criteria for node boundaries)
- `guides/domain-detection.md` (how to classify workflows)
- `guides/agent-strategy.md` (when to create custom agents)
- `skills/shared/wiki_cu/appendix-concepts.md` (CU patterns)

### Step 1: Explain Approach

I'll tell you:

```
I'll help you design a workflow using:
1. Domain Detection — What kind of work is this?
2. Role Extraction — What are the natural responsibilities?
3. Node Mapping — Apply 6 boundary criteria
4. Agent Strategy — Custom agents per workflow

Let's start!
```

### Step 2: Analyze Your Input

**If prompt:**
```
Analyzing: "Create a workflow to verify quality of my local branch"

Domain: Code quality verification (read-only analysis + reporting)
Key actions: test, lint, coverage, report
Data flow: Current branch → metrics → report
```

**If plan file:**
```
Reading plan: docs/plans/2026-07-02-branch-check.md

Plan type:
- Multi-phase workflow (has "Phase N:" headers)
- OR executor plan (has "Task N: Write failing test")
- OR mixed (phases with TDD sub-tasks)

[I'll classify and tell you what I found]
```

### Step 3: Propose 2-3 Options

I'll apply the 6 node boundary criteria to each option:

```
Here are 3 possible workflow structures:

Option A: Simple (2 nodes)
  1. analyzer — Run all checks
  2. reporter — Write quality report

  Why this boundary?
  ✓ Criterion 1 (Distinct responsibility): analysis vs reporting
  ✓ Criterion 2 (Data handoff): findings.json
  ✓ Criterion 3 (Different tools): test/lint vs Write
  ✓ Criterion 6 (Verification): reporter validates findings.json
  
  Rationale: 4/6 criteria apply → boundary justified

Option B: Check + Fix (3 nodes)
  1. analyzer — Find issues
  2. fixer — Auto-fix
  3. verifier — Confirm fixes

  Why these boundaries?
  ✓ All 6 criteria apply
  ⭐ Verification gates at each transition
  
  Robustness: Fixer validates analyzer output, verifier validates fixer

Option C: Single node
  1. all-in-one — Analyze + report

  Why avoid this?
  ✗ No verification gates (0/6 criteria)
  
Which structure fits? Type 'A', 'B', 'C', or 'none' for more options
```

### Step 4: Iterate on Feedback

**If you pick an option:** I'll ask about agent strategy

**If you say "none":** I'll refine based on what doesn't fit

**If you modify:** "Like A but add security scan" → I'll apply criteria to the modification

### Step 5: Generate Artifacts

For approved structure, I'll create:

**1. Workflow YAML** (`<repo>/.claude-unleashed/workflows/<slug>.yaml`)

```yaml
name: branch-quality-check
description: Verify quality of local branch

nodes:
  - id: analyze
    agent: branch-quality-check_analyzer
    maxTurns: 100
    maxBudgetUsd: 5.0
    inputs:
      prompt: |
        Run tests, lint, coverage. Output findings.json.

  - id: report
    agent: branch-quality-check_reporter
    needs: [analyze]
    maxTurns: 50
    maxBudgetUsd: 2.0
    inputs:
      prompt: |
        Read findings.json, validate, write report.
```

**2. Custom Agents** (`<repo>/.claude-unleashed/agents/<slug>_<role>.yaml`)

For each node, I'll create an agent following `guides/agent-strategy.md`.

**3. Spec + Plan** (if from prompt mode)

- Spec: `<repo>/docs/specs/YYYY-MM-DD-<slug>.md`
- Plan: `<repo>/docs/plans/YYYY-MM-DD-<slug>.md`

**4. Commit Everything**

All artifacts committed to the target repo.

### Output

```
✅ Workflow created: branch-quality-check

Artifacts:
  📄 Spec:     docs/specs/2026-07-02-branch-quality-check.md
  📋 Plan:     docs/plans/2026-07-02-branch-quality-check.md
  🔧 Workflow: .claude-unleashed/workflows/branch-quality-check.yaml
  🤖 Agents:   .claude-unleashed/agents/branch-quality-check_{analyzer,reporter}.yaml

All artifacts committed.

To run:
  cu workflow run branch-quality-check --repo . --input '{}'
```

## References

- `guides/node-boundary-criteria.md` — 6 criteria for node boundaries
- `guides/domain-detection.md` — Domain classification patterns
- `guides/agent-strategy.md` — Agent creation guidelines
- `skills/shared/wiki_cu/appendix-concepts.md` — CU concepts (agents vs profiles)
- `skills/shared/wiki_cu/03-feature-workflow.md` — Workflow examples
```

- [ ] **Step 4: Run test to verify it passes**

Run: `bash /Users/thomaschang/Documents/dev/git/thomaschangsf/skills/cu-wf-create/test-skill.sh`

Expected: PASS with "cu-wf-create skill structure valid"

- [ ] **Step 5: Commit**

```bash
cd /Users/thomaschang/Documents/dev/git/thomaschangsf/skills
git add cu-wf-create/SKILL.md cu-wf-create/test-skill.sh
git commit -m "feat: add cu-wf-create skill for workflow generation"
```

---

### Task 4: Create cu-wf-run Skill

**Files:**
- Create: `/Users/thomaschang/Documents/dev/git/thomaschangsf/skills/cu-wf-run/SKILL.md`

**Interfaces:**
- Consumes: cu-setup status (pre-flight), workflow YAML files from cu-wf-create
- Produces: Launched workflow run ID, monitoring commands

- [ ] **Step 1: Write test for cu-wf-run skill**

Create `/Users/thomaschang/Documents/dev/git/thomaschangsf/skills/cu-wf-run/test-skill.sh`:

```bash
#!/usr/bin/env bash
set -euo pipefail

SKILL_FILE="/Users/thomaschang/Documents/dev/git/thomaschangsf/skills/cu-wf-run/SKILL.md"

if [[ ! -f "$SKILL_FILE" ]]; then
  echo "FAIL: SKILL.md not found"
  exit 1
fi

# Check frontmatter
if ! grep -q "^name: cu-wf-run$" "$SKILL_FILE"; then
  echo "FAIL: name not set to cu-wf-run"
  exit 1
fi

# Check mentions cu CLI commands
if ! grep -q "cu workflow run" "$SKILL_FILE"; then
  echo "FAIL: doesn't reference cu workflow run command"
  exit 1
fi

echo "PASS: cu-wf-run skill structure valid"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `bash /Users/thomaschang/Documents/dev/git/thomaschangsf/skills/cu-wf-run/test-skill.sh`

Expected: FAIL with "SKILL.md not found"

- [ ] **Step 3: Create cu-wf-run skill file**

Create `/Users/thomaschang/Documents/dev/git/thomaschangsf/skills/cu-wf-run/SKILL.md`:

```markdown
---
name: cu-wf-run
description: List and launch claude-unleashed workflows with progress monitoring
---

# CU Workflow Runner

List available workflows and launch them with progress monitoring.

## Usage

Invoke: `/cu-wf-run` in Claude/Cursor

**Inputs:**
- Target repo path: `/Users/thomaschang/Documents/dev/git/a360/edc-python`
- Optional: workflow name (if omitted, I'll show list)

## Process

### Pre-flight: Setup Check

First, I'll verify CU is set up by invoking `/cu-setup`.

If setup fails, I'll stop and show you how to fix issues.

### Step 1: Discover Workflows

I'll list workflows in the target repo:

```bash
ls <repo>/.claude-unleashed/workflows/*.yaml
```

If none found:

```
Error: No workflows found in .claude-unleashed/workflows/

Would you like to create one? (yes/no)
[If yes, invoke /cu-wf-create]
```

### Step 2: Present Workflows

```
Available workflows in edc-python:

1. branch-quality-check
   Description: Verify quality of local branch
   Nodes: analyzer → reporter
   
2. test-fixer
   Description: Find and fix failing tests
   Nodes: detector → fixer → verifier

Which workflow would you like to run? (type number or name)
```

### Step 3: Check Workflow Input Requirements

I'll parse the workflow YAML to see if it needs inputs.

**If inputs required:**

```
This workflow requires:
- prompt: What to do

Please provide:
  Prompt: [wait for your input]

Ready to launch? (yes/no)
```

**If no inputs:**

```
Ready to launch? (yes/no)
```

### Step 4: Launch Workflow

```bash
cu workflow run <workflow-name> --repo <path> --input '{...}'
```

### Step 5: Show Initial Status

```
✅ Workflow launched!

Workflow: branch-quality-check
Run ID: wf_abc123
Status: running
Current node: analyzer

📊 Monitor progress:

Via CLI:
  cu sessions ls --status running
  cu workflow runs --json | jq '.[] | select(.runId=="wf_abc123")'
  cu tail <session-id>

Via Mac app:
  Open ClaudeUnleashed → Sessions tab
  Or: Dashboard → Workflows section

Live events:
  cu workflow tail wf_abc123

Want me to monitor for you? (yes/no)
```

### Step 6: Optional Monitoring

**If you say "yes":**

I'll poll every 2 minutes and show updates:

```
[2 minutes later]

Checking workflow status...

✓ Node 'analyzer' completed
  Output: findings.json created
  
→ Node 'reporter' running
  Reading findings.json...

I'll check again in 2 minutes.
```

**If you say "no":**

I'll give you the commands and stop.

### Step 7: Final Status (if monitoring)

```
✅ Workflow completed!

Duration: 5m 32s
Nodes: 2/2 completed
Cost: $0.45

Outputs:
- Quality report: docs/quality-report.md

Next steps:
- Review report: cat docs/quality-report.md
- Continue to PR: cu run --agent reviewer --repo . --prompt "Open PR"
```

## Error Handling

**Node failure:**

```
⚠️ Node 'analyzer' failed

Error: Test suite returned non-zero exit code

Options:
1. Check logs: cu tail <session-id>
2. Resume workflow: cu workflow resume wf_abc123
3. Cancel workflow: cu workflow cancel wf_abc123

What would you like to do?
```

## References

- `skills/shared/wiki_cu/02-daily-commands.md` — CLI reference
- `skills/shared/wiki_cu/03-feature-workflow.md` — Workflow patterns
```

- [ ] **Step 4: Run test to verify it passes**

Run: `bash /Users/thomaschang/Documents/dev/git/thomaschangsf/skills/cu-wf-run/test-skill.sh`

Expected: PASS with "cu-wf-run skill structure valid"

- [ ] **Step 5: Commit**

```bash
cd /Users/thomaschang/Documents/dev/git/thomaschangsf/skills
git add cu-wf-run/SKILL.md cu-wf-run/test-skill.sh
git commit -m "feat: add cu-wf-run skill for workflow launching"
```

---

### Task 5: Integration Test

**Files:**
- Create: `/Users/thomaschang/Documents/dev/git/thomaschangsf/skills/test-all-skills.sh`

**Interfaces:**
- Consumes: All three skills from Tasks 1, 3, 4
- Produces: Integration test results

- [ ] **Step 1: Write integration test**

Create `/Users/thomaschang/Documents/dev/git/thomaschangsf/skills/test-all-skills.sh`:

```bash
#!/usr/bin/env bash
set -euo pipefail

SKILLS_DIR="/Users/thomaschang/Documents/dev/git/thomaschangsf/skills"

echo "Testing all CU skills..."

# Test cu-setup
echo "→ Testing cu-setup..."
bash "$SKILLS_DIR/cu-setup/test-skill.sh"

# Test cu-wf-create guides
echo "→ Testing cu-wf-create guides..."
bash "$SKILLS_DIR/cu-wf-create/test-guides.sh"

# Test cu-wf-create skill
echo "→ Testing cu-wf-create skill..."
bash "$SKILLS_DIR/cu-wf-create/test-skill.sh"

# Test cu-wf-run
echo "→ Testing cu-wf-run..."
bash "$SKILLS_DIR/cu-wf-run/test-skill.sh"

# Check wiki_cu symlink exists
if [[ ! -L "$SKILLS_DIR/shared/wiki_cu" ]]; then
  echo "FAIL: wiki_cu symlink not found"
  exit 1
fi

echo ""
echo "✅ All skills tests PASSED"
```

- [ ] **Step 2: Run integration test**

Run: `bash /Users/thomaschang/Documents/dev/git/thomaschangsf/skills/test-all-skills.sh`

Expected: All tests pass with "✅ All skills tests PASSED"

- [ ] **Step 3: Commit integration test**

```bash
cd /Users/thomaschang/Documents/dev/git/thomaschangsf/skills
git add test-all-skills.sh
git commit -m "test: add integration test for all CU skills"
```

---

## Self-Review

**1. Spec coverage:**
- ✅ Task 1: cu-setup skill (Skill 1 in spec)
- ✅ Task 2: cu-wf-create guides (Support files for Skill 2)
- ✅ Task 3: cu-wf-create skill (Skill 2 in spec)
- ✅ Task 4: cu-wf-run skill (Skill 3 in spec)
- ✅ Task 5: Integration test (Quality gate)
- ✅ All diagnostic checks from spec § "Skill 1: cu-setup" included
- ✅ All design heuristics from spec § "Skill 2: cu-wf-create" included
- ✅ All workflow launching steps from spec § "Skill 3: cu-wf-run" included

**2. Placeholder scan:**
- ✅ No TBD/TODO
- ✅ All code blocks complete
- ✅ All commands with exact syntax
- ✅ All file paths absolute

**3. Type consistency:**
- ✅ Skill frontmatter format consistent across all three skills
- ✅ Test script patterns consistent
- ✅ Commit message format consistent

**4. Issues found:** None

---

Plan complete and saved to `skills/shared/wiki_cu/specs/2026-07-02-cu-workflow-skills-plan.md`.

**Two execution options:**

**1. Subagent-Driven (recommended)** - I dispatch a fresh subagent per task, review between tasks, fast iteration

**2. Inline Execution** - Execute tasks in this session using executing-plans, batch execution with checkpoints

**Which approach?**
