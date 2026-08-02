# Use Case: CI/CD Monitoring and PR Auto-Addressing

Orchestration workflow that monitors CI/CD, sends Slack alerts, and automatically addresses PR comments.

## 1. Scenario

You want CU to:
1. Watch for CI failures on open PRs
2. Send you a Slack message when CI breaks
3. Automatically address PR review comments
4. Retry CI after fixes

## 2. Architecture

This workflow combines:
- **Schedules** — Cron-driven polling of CI status
- **Agents** — Custom agents for CI checking, Slack posting, and PR fixing
- **Workflows** — Multi-step orchestration (check → notify → fix → verify)
- **Slack integration** — For real-time notifications

## Prerequisites

- CU installed and Slack connected ([01-setup.md](01-setup.md))
- GitHub CLI (`gh`) authenticated
- Repo with CI/CD (e.g., GitHub Actions)

## Step 1: Set Up Slack Integration

Connect CU to your Slack workspace:

```bash
# Check status
cu slack status

# If not connected, log in
cu slack login
```

Follow the OAuth flow. Once authenticated:

```bash
# Pin a channel for notifications
cu slack list-channels cicd
cu slack channel <channel-id>
```

Now CU can post to that channel.

## Step 2: Create the CI Monitor Agent

Create a custom agent that checks CI status via `gh` CLI.

**File: `~/.claude-unleashed/agents/ci-monitor.yaml`**

```yaml
name: ci-monitor
description: Monitors CI status for open PRs and reports failures
model: sonnet
systemPrompt: |
  You are a CI monitoring agent. Your job:
  1. List all open PRs in the repo
  2. Check CI status for each PR
  3. Return a structured list of failing PRs with error details
  
  Use the GitHub CLI (`gh`) to query PR status.
  
  Output format (JSON):
  {
    "failing": [
      {"pr": 123, "title": "Add auth", "errors": ["test failure in auth.test.js"]}
    ]
  }

allowedTools:
  - Bash
  - Read

limits:
  maxTurns: 10
  maxBudgetUsd: 0.50

recommendedSkills:
  - systematic-debugging
```

Save it:

```bash
cu agents save ci-monitor ~/.claude-unleashed/agents/ci-monitor.yaml
```

## Step 3: Create the PR Fixer Agent

This agent addresses PR comments and fixes CI failures.

**File: `~/.claude-unleashed/agents/pr-fixer.yaml`**

```yaml
name: pr-fixer
description: Addresses PR review comments and fixes CI failures
model: sonnet
systemPrompt: |
  You are a PR fixer agent. Your job:
  1. Read PR review comments
  2. Checkout the PR branch
  3. Make the requested changes
  4. Commit and push
  5. Re-trigger CI if needed
  
  Use TDD: write failing tests, then fix the code.

allowedTools:
  - Bash
  - Read
  - Edit
  - Write

limits:
  maxTurns: 50
  maxBudgetUsd: 5

recommendedSkills:
  - test-driven-development
  - systematic-debugging
```

Save it:

```bash
cu agents save pr-fixer ~/.claude-unleashed/agents/pr-fixer.yaml
```

## Step 4: Create the Orchestration Workflow

Tie it all together in a workflow.

**File: `~/.claude-unleashed/workflows/cicd-monitor.yaml`**

```yaml
name: cicd-monitor
description: Monitor CI, send Slack alerts, and auto-fix PR issues

nodes:
  - id: check-ci
    agent: ci-monitor
    prompt: |
      Check CI status for all open PRs in {{repo}}.
      Return JSON with failing PRs and error details.

  - id: notify
    agent: slack-notifier
    prompt: |
      Send a Slack message to #cicd channel:
      "CI failures detected: {{check-ci.output.failing | map(.pr) | join(', ')}}"
      
      Include a link to each failing PR.
    runIf: "check-ci.output.failing.length > 0"

  - id: fix-prs
    agent: pr-fixer
    prompt: |
      For each failing PR in {{check-ci.output.failing}}:
      1. Fetch PR comments
      2. Address the comments
      3. Fix CI failures
      4. Push changes
      5. Comment on the PR: "Automated fixes applied by CU"
    runIf: "check-ci.output.failing.length > 0"
    foreach: "check-ci.output.failing"

  - id: verify
    agent: ci-monitor
    prompt: |
      Re-check CI status for PRs that were fixed.
      Report which ones now pass.
    dependsOn:
      - fix-prs
```

Save it:

```bash
cu workflow save cicd-monitor ~/.claude-unleashed/workflows/cicd-monitor.yaml
```

## Step 5: Create the Slack Notifier Agent

Quick agent for posting to Slack.

**File: `~/.claude-unleashed/agents/slack-notifier.yaml`**

```yaml
name: slack-notifier
description: Posts messages to Slack
model: haiku  # Cheap model for simple tasks
systemPrompt: |
  You post messages to Slack. Use the Slack MCP tools to send messages.
  Keep messages concise and actionable.

allowedTools:
  - mcp__slack__*

limits:
  maxTurns: 5
  maxBudgetUsd: 0.10
```

Save it:

```bash
cu agents save slack-notifier ~/.claude-unleashed/agents/slack-notifier.yaml
```

## Step 6: Schedule the Workflow

Run the workflow every 30 minutes:

```bash
cu schedules add cicd-monitor \
  --kind workflow \
  --target cicd-monitor \
  --repo ~/my-app \
  --cron "*/30 * * * *" \
  --permission-mode auto
```

**Flags:**
- `--kind workflow` — Run a workflow (not a single session)
- `--target cicd-monitor` — Name of the workflow
- `--repo ~/my-app` — Where to run it
- `--cron "*/30 * * * *"` — Every 30 minutes
- `--permission-mode auto` — Skip approval prompts

**Verify:**

```bash
cu schedules ls
cu schedules next --hours 24
```

## Step 7: Test It Manually

Before trusting the schedule, run it once:

```bash
cu schedules run-now cicd-monitor --json
```

Watch the output:

```bash
cu workflow runs
cu tail <workflow-run-id>
```

**Expected flow:**
1. `check-ci` node lists PRs and checks CI
2. If failures exist, `notify` posts to Slack
3. `fix-prs` spawns one session per failing PR
4. `verify` re-checks CI status

## 11. Monitor and Iterate

**Check schedule history:**

```bash
cu schedules history cicd-monitor --json
```

**Check Slack:**

You should see messages like:

> CI failures detected: #123, #456
> 
> - PR #123: Test failure in auth.test.js
> - PR #456: Lint error in api.ts
> 
> Automated fixes in progress...

**Check PR comments:**

Each fixed PR should have a comment:

> Automated fixes applied by CU. Re-running CI now.

## 12. Advanced: Add PR Comment Auto-Response

Extend the workflow to respond to PR comments in real-time (not just scheduled checks).

### 12.1. Use GUS CDC (Change Data Capture)

GUS CDC can trigger CU sessions on GitHub webhook events. See [appendix-concepts.md#gus-cdc](appendix-concepts.md#gus-cdc) for setup.

**Add a CDC subscription:**

```bash
cu cdc add pr-comment-responder \
  --event pull_request_review_comment \
  --filter "repository.name == 'my-app'" \
  --template "Address this PR comment: {{comment.body}}" \
  --agent pr-fixer \
  --repo ~/my-app
```

Now whenever someone comments on a PR, CU spawns a `pr-fixer` session to address it.

## 13. Optimization: Use Agent Groups

Instead of chaining workflows manually, define an agent group that coordinates the sub-agents.

**File: `~/.claude-unleashed/agent-groups/cicd-team.yaml`**

```yaml
name: cicd-team
description: Team that monitors CI and fixes issues
coordinator: cicd-coordinator

members:
  - name: ci-monitor
    role: Check CI status
  - name: slack-notifier
    role: Send alerts
  - name: pr-fixer
    role: Fix issues

coordinatorPrompt: |
  You coordinate the CI monitoring team.
  
  Process:
  1. Ask ci-monitor to check CI status
  2. If failures exist, ask slack-notifier to send an alert
  3. For each failure, ask pr-fixer to fix it
  4. After fixes, ask ci-monitor to verify
```

Save it:

```bash
cu agent-groups save cicd-team ~/.claude-unleashed/agent-groups/cicd-team.yaml
```

**Launch with the group:**

```bash
cu run --repo ~/my-app \
  --agent-group cicd-team \
  --prompt "Monitor CI and fix any failures"
```

The coordinator handles orchestration — you don't need a workflow YAML.

## 14. Tips

### 14.1. Avoid over-polling

Polling every 30 minutes can be expensive if you have many repos. Use webhooks (GUS CDC) instead for real-time response.

### 14.2. Rate-limit Slack messages

Add logic to the `notify` agent to only post if there's a new failure (not re-posting the same issue):

```yaml
systemPrompt: |
  Before posting to Slack, check if this failure was already reported in the last hour.
  Use the Slack search API to avoid duplicate alerts.
```

### 14.3. Circuit breaker

If a schedule keeps failing, CU auto-disables it after 5 consecutive failures. Re-enable with:

```bash
cu schedules enable cicd-monitor
```

### 14.4. Test in dry-run mode

Before committing to auto-fixing PRs, run the workflow with `--dry-run` to preview actions:

```bash
cu workflow run cicd-monitor --repo ~/my-app --input '{"dryRun": true}'
```

## 15. Next Steps

- [appendix-concepts.md](appendix-concepts.md) — Deep dive into workflows, schedules, and CDC
- [02-daily-commands.md](02-daily-commands.md) — CLI reference for managing schedules and workflows
