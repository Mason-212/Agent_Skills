# CU Workflow Skills Design

**Date:** 2026-07-02  
**Status:** Design phase  
**Skills:** cu-setup, cu-wf-create, cu-wf-run

---

## Overview

Three Claude Code skills that help users manage claude-unleashed workflows:

1. **cu-setup** — Verify and repair CU installation (diagnostic + interactive fixes)
2. **cu-wf-create** — Generate workflows through collaborative design (prompt or plan → spec → plan → workflow YAML + agents)
3. **cu-wf-run** — List and launch workflows with progress monitoring

---

## Goals

- **Lower barrier to CU adoption** — Interactive setup validation guides new users
- **Workflow creation without deep CU knowledge** — Collaborative design extracts intent, proposes structures
- **Reusable workflows across repos** — Skills generate self-contained workflow artifacts
- **Integrated into Claude/Cursor** — Skills invoked naturally in conversation

---

## Architecture

### Shared Knowledge Base

All three skills reference a single source of truth:

```
skills/shared/wiki_cu/  ← Source of truth
├── README.md
├── 01-setup.md
├── 02-daily-commands.md
├── 03-feature-workflow.md
├── 04-cicd-automation.md
└── appendix-concepts.md  ← Updated with agents vs profiles clarification
```

**Symlinks:**
- `compendium/.../wiki_tom` → `skills/shared/wiki_cu`
- `claude-unleashed/docs/wiki_cu` → `skills/shared/wiki_cu`

### Skill Directory Structure

```
skills/
├── cu-setup/
│   └── SKILL.md
│
├── cu-wf-create/
│   ├── SKILL.md
│   ├── guides/
│   │   ├── node-boundary-criteria.md
│   │   ├── domain-detection.md
│   │   └── agent-strategy.md
│   └── examples/
│       ├── coding-workflow-example.md
│       └── data-workflow-example.md
│
├── cu-wf-run/
│   └── SKILL.md
│
└── shared/
    └── wiki_cu/  ← All skills reference this
```

---

## Skill 1: cu-setup

**Purpose:** Validate CU installation and guide user through repairs.

**Invocation modes:**
1. Standalone: `/cu-setup` in Claude/Cursor
2. Pre-flight gate: Called by cu-wf-create and cu-wf-run

### Diagnostic Checks (in order)

1. **Daemon running**
   - Check: `claude-unleashed daemon status --json` → `"running": true`
   - Fix: `claude-unleashed daemon restart`
   - Guide: `wiki_cu/01-setup.md` § 9.2

2. **Authentication configured**
   - Check: `claude-unleashed models --json` → `"source"` is `"probed"` or `"cache"` (NOT `"fallback"`)
   - Fix: Guide user through auth setup from `wiki_cu/01-setup.md` § 3

3. **Git configured**
   - Check: `claude-unleashed config get git.name git.email git.sshKeyPath` all non-empty
   - Fix: Prompt user for values, run `claude-unleashed config set git.{name,email,sshKeyPath}`

4. **Git SSH connectivity**
   - Check: `ssh -T git@git.soma.salesforce.com` succeeds
   - Fix: Check SSH key exists, check SSH config, guide from `wiki_cu/01-setup.md`

5. **Repos discovered**
   - Check: `claude-unleashed repos ls --json` returns at least one repo
   - Fix: Run `claude-unleashed repos rescan`

6. **Overseer enabled**
   - Check: `claude-unleashed overseer status --json` → `"enabled": true`
   - Fix: Run `claude-unleashed overseer mode on`

7. **Plugin installed**
   - Check: `claude-unleashed actions --json | grep cu_` finds at least one `cu_*` tool
   - Fix: Direct user to install plugin from `wiki_cu/01-setup.md` § 4

8. **Slack integration (optional)**
   - Check: `claude-unleashed config get slack.botToken slack.defaultChannel`
   - If configured but broken: Guide user to fix token/channel
   - If empty: Mark as "⚠️ Optional: Slack not configured" (not a failure)

### Output

```
✅ CU setup verified. All systems ready.

Or:

❌ Setup incomplete. Fix the following:
  - Daemon not running → See wiki_cu/01-setup.md § 9.2
  - Auth not configured → See wiki_cu/01-setup.md § 3

Or:

✅ Core setup complete.
⚠️ Optional: Slack not configured
```

**Return status:** `{success: boolean, issues: string[], warnings: string[]}`

---

## Skill 2: cu-wf-create

**Purpose:** Generate complete CU workflows through collaborative design.

**Pre-flight:** Invoke cu-setup (stop if fails)

### Core Design Heuristic

**Domain → Roles → Nodes → Agents**

1. **Detect domain** — What kind of work? (coding, data aggregation, monitoring, research)
2. **Extract roles** — Natural responsibilities/phases in this domain
3. **Map roles to nodes** — Each role becomes a workflow node (using boundary criteria)
4. **Determine agents** — Reuse generic or create custom agents per node

### Node Boundary Criteria

Create separate nodes when:

1. **Distinct responsibility** — Different job (fetch vs transform vs notify)
2. **Data handoff** — Node A outputs artifact, Node B consumes it
3. **Different tools** — Read-only vs writes vs APIs vs MCP servers
4. **Independent failure** — Node A can fail without invalidating Node B
5. **Reusability** — Node could be extracted for other workflows
6. **⭐ Verification gate** — Node B independently verifies Node A achieved its goal

**Key principle:** Each node transition is a quality gate where a different agent validates prior work.

### Process Flow

**Step 1: Explain heuristic to user**

```
I'll help you design a workflow using:
1. Domain Detection
2. Role Extraction
3. Node Mapping (using 6 boundary criteria)
4. Agent Strategy

Let's start!
```

**Step 2: Analyze input**

**Prompt mode:** User provides freeform text
```
Analyzing: "Create a workflow to verify quality of my local branch"

Domain: Code quality verification (read-only analysis + reporting)
Key actions: test, lint, coverage, report
Data flow: Current branch → quality metrics → written report
```

**Plan file mode:** User provides path to plan document
```
Reading plan: docs/plans/2026-07-02-branch-quality-check.md

Classifying plan type:
- Has "Phase N:" headers → Multi-phase workflow plan
- Has "Task N: Write failing test" → Executor plan (single agent)
- Mixed → Top-level phases with TDD sub-tasks

[Apply heuristics to determine if workflow or single-agent session]
```

**Step 3: Propose 2-3 options WITH boundary rationale**

```
Here are 3 possible workflow structures:

Option A: Simple (2 nodes)
  1. analyzer — Run all checks (tests, lint, coverage)
  2. reporter — Write quality report

  Why this boundary?
  ✓ Distinct concerns: analysis (read) vs reporting (write)
  ✓ Data handoff: findings.json
  ✓ Different tools: test/lint tools vs Write
  ⭐ Verification: Reporter validates findings.json schema
     (catches if analyzer crashed or output malformed data)

Option B: Check + Fix + Verify (3 nodes)
  1. analyzer — Run checks, identify issues
  2. fixer — Auto-fix what can be fixed
  3. verifier — Re-run checks, confirm fixes worked

  Why these boundaries?
  ✓ Distinct concerns: detect vs repair vs validate
  ✓ Data handoff: issues.json → fixed.json → results.json
  ⭐ Verification gates:
     - Fixer validates issues.json before attempting fixes
     - Verifier independently confirms fixer succeeded
  
  Robustness: If fixer claims "fixed 10 issues" but verifier 
  sees 8 failures, we catch the mistake.

Which structure fits your needs?
- Type 'A', 'B' to choose
- Type 'none' to see more options
- Describe modifications: "Like A but add security scan"
```

**Step 4: User feedback loop**

If user picks option → Ask about agent strategy
If user says "none" → Refine based on feedback
If user modifies → Apply node boundary criteria to modification

**Step 5: Generate artifacts**

For each node, create:
- Custom agent YAML (`<slug>_<role>.yaml`)
- Workflow YAML referencing agents
- Spec document (if from prompt mode)
- Plan document (if from prompt mode)

**Workflow YAML structure:**

```yaml
name: branch-quality-check
description: Verify quality of local branch changes

nodes:
  - id: analyze
    agent: branch-quality-check_analyzer
    maxTurns: 100
    maxBudgetUsd: 5.0
    inputs:
      prompt: |
        Analyze the current branch. Run tests, check coverage,
        run linter. Output findings.json.

  - id: report
    agent: branch-quality-check_reporter
    needs: [analyze]
    maxTurns: 50
    maxBudgetUsd: 2.0
    inputs:
      prompt: |
        Read findings.json, validate schema, write report to
        docs/quality-report.md.
      findings: $nodes.analyze.findings
```

**Agent YAML structure:**

```yaml
name: branch-quality-check_analyzer
description: Analyzes branch quality
archetype: developer
model: sonnet
systemPrompt: |
  You analyze code quality.
  1. Run test suite
  2. Check coverage
  3. Run linter
  4. Output findings.json

allowedTools:
  - Bash
  - Read
  - Write
  - Grep

outputs:
  findings:
    description: Quality analysis results
    required: true
    kind: json
```

**Artifacts saved to:**
- Spec: `<repo>/docs/specs/YYYY-MM-DD-<slug>.md`
- Plan: `<repo>/docs/plans/YYYY-MM-DD-<slug>.md`
- Workflow: `<repo>/.claude-unleashed/workflows/<slug>.yaml`
- Agents: `<repo>/.claude-unleashed/agents/<slug>_*.yaml`

**Output:**

```
✅ Workflow created: branch-quality-check

Artifacts:
  📄 Spec:     docs/specs/2026-07-02-branch-quality-check.md
  📋 Plan:     docs/plans/2026-07-02-branch-quality-check.md
  🔧 Workflow: .claude-unleashed/workflows/branch-quality-check.yaml
  🤖 Agents:   .claude-unleashed/agents/branch-quality-check_{analyzer,reporter}.yaml

All artifacts committed to repo.

To run:
  cu workflow run branch-quality-check --repo . --input '{}'
```

---

## Skill 3: cu-wf-run

**Purpose:** List and launch workflows with progress monitoring.

**Pre-flight:** Invoke cu-setup (stop if fails)

### Flow

**1. Discover workflows**

```bash
# List workflows in target repo
ls <repo>/.claude-unleashed/workflows/*.yaml
```

**2. Present to user**

```
Available workflows in edc-python:

1. branch-quality-check
   Description: Verify quality of local branch
   Nodes: analyzer → reporter
   
2. test-fixer
   Description: Find and fix failing tests
   Nodes: detector → fixer → verifier

Which workflow would you like to run?
```

**3. Get workflow input** (if needed)

Some workflows require inputs. Parse workflow YAML to determine.

**4. Launch**

```bash
cu workflow run <workflow-name> --repo <path> --input '{...}'
```

**5. Show initial status + monitoring commands**

```
✅ Workflow launched!

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

Live events:
  cu workflow tail wf_abc123

Want me to monitor for you? (yes/no)
```

**6. Optional periodic checks** (if user said yes)

Poll every 2 minutes, show progress updates.

**7. Final status**

```
✅ Workflow completed!

Duration: 5m 32s
Nodes: 2/2 completed
Cost: $0.45

Outputs:
- Quality report: docs/quality-report.md
```

---

## Key Design Decisions

### 1. Agents vs Profiles

**Clarified in wiki_cu/appendix-concepts.md:**

- **Agents** define behavior (systemPrompt, tools, archetype)
- **Profiles** override settings (model, permissions, limits)
- Workflows reference agents directly, NOT profiles
- Profiles are for standalone `cu run` sessions

### 2. Node Boundaries

Six criteria applied to every proposed boundary. Emphasis on **verification gates** — each node independently validates prior node's output.

### 3. Custom Agents Per Workflow

cu-wf-create generates custom agents for each workflow node by default. This keeps workflows self-contained and repo-specific.

**Alternative:** Reuse generic agents (executor, reviewer) was considered but rejected because:
- Workflows need domain-specific systemPrompts
- Tool requirements vary per workflow
- Custom agents make workflows portable and self-documenting

### 4. Interactive Design vs Template-Based

Chose **interactive collaborative design** over template-based generation because:
- No two workflows are identical
- Domain detection requires understanding user intent
- Node boundaries aren't mechanical — require judgment
- User feedback improves output quality

---

## Non-Goals

- **Remote workflow execution** — Skills only work with local CU installation
- **Workflow editing** — Skills generate workflows; editing is manual (future enhancement)
- **Generic workflow library** — Each workflow is repo-specific (future: shareable templates)

---

## Success Criteria

- User can go from "I want to verify my branch" to running workflow in < 5 minutes
- cu-setup catches all common setup issues with actionable fixes
- cu-wf-create proposes node structures that make sense to users (< 2 iterations to approval)
- Generated workflows execute successfully without manual YAML editing

---

## Future Enhancements

1. **Workflow templates** — Shareable generic workflows users can install
2. **Workflow editing** — Update existing workflows via skill
3. **Multi-repo workflows** — Workflows that coordinate across repos
4. **Workflow visualization** — Generate diagrams from workflow YAML
5. **Agent library** — Reusable agent patterns beyond the built-in set

---

## References

- **wiki_cu/appendix-concepts.md** — Agents vs profiles, workflow patterns
- **wiki_cu/03-feature-workflow.md** — CU workflow examples
- **CLAUDE.md** — CU development conventions
