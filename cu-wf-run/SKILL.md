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
