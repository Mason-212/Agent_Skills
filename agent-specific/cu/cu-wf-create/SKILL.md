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
