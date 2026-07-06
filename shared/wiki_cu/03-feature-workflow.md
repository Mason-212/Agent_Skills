# Use Case: Developing a New Feature

End-to-end workflow for using Claude Unleashed to develop a new feature, from planning to PR.

**Two ways to do this:**
- **Via terminal** (`cu` commands) - Good for scripting and automation
- **Via Claude Code conversation** - More natural, just talk to Claude (requires `cu-cli` plugin installed)

## 1. Scenario

You need to add a new feature to `edc-python`: **Add health check endpoint to the Flask API**.

**Requirements:**
- New `/health` endpoint that returns JSON status
- Check database connectivity
- Return 200 if healthy, 503 if unhealthy
- Unit tests and integration tests

## 2. Repo Setup

We'll use: `/Users/thomaschang/Documents/dev/git/a360/edc-python`

## 3. Prerequisites

- CU installed and configured ([01-setup.md](01-setup.md))
- Repo discovered: `/Users/thomaschang/Documents/dev/git/a360/edc-python`

## 4. Create Three Profiles

Profiles are saved launch configs. Instead of repeating flags, we'll create three profiles for our three-stage workflow.

**What's a profile?** A simple YAML file with:
- `name` - Profile identifier
- `model` - Which Claude model (opus/sonnet/haiku)
- `permissionMode` - Approval behavior (default/auto/bypassPermissions)
- `maxTurns` - Safety cap on turns
- `maxBudgetUsd` - Cost cap

**Wait, where's the agent field?**

Profiles **don't include the agent** - they're just settings (model, permissions, limits). You specify **both** the profile AND the agent when launching:

```bash
cu run --profile my-planner --agent planner --repo ~/my-app --prompt "..."
```

**Think of it like this:**
- **Agent** = The worker's job description and skills (163-line systemPrompt in `planner.yaml`)
- **Profile** = The worker's contract terms (model, budget, permissions)

So you mix and match: "Use the planner agent with the my-planner profile's settings."

**Why separate them?**

You might want to run the same agent with different settings:
- `--profile quick` (Haiku, 20 turns, $1 budget)
- `--profile thorough` (Opus, 100 turns, $20 budget)

Both use the same `--agent planner`, just different resource limits.

### 4.1. Check available agents first

Before creating profiles, see what agents are available:

```bash
cu agents ls
```

Output shows built-in agents:
```
planner
executor
reviewer
il-coordinator
il-implementer
...
```

Each of these has a full definition at `.claude-unleashed/agents/<name>.yaml`.

### 4.2. Create planner profile

Create file: `~/.claude-unleashed/profiles/my-planner.yaml`

```yaml
name: my-planner
description: Plans features and writes design docs
model: sonnet
permissionMode: default
maxTurns: 50
maxBudgetUsd: 5.0
```

**Save it (run in regular terminal):**

```bash
# Create the directory if it doesn't exist
mkdir -p ~/.claude-unleashed/profiles

# Create the file
cat > ~/.claude-unleashed/profiles/my-planner.yaml <<'EOF'
name: my-planner
description: Plans features and writes design docs
model: sonnet
permissionMode: default
maxTurns: 50
maxBudgetUsd: 5.0
EOF

# Verify it's recognized
cu profiles ls
```

You should see `my-planner` in the output. No separate `save` command needed - just creating the file is enough!

### 4.3. Create executor profile

Create file: `~/.claude-unleashed/profiles/my-executor.yaml`

```yaml
name: my-executor
description: Implements features using TDD
model: sonnet
permissionMode: auto
maxTurns: 100
maxBudgetUsd: 10.0
```

**Save it:**

```bash
cat > ~/.claude-unleashed/profiles/my-executor.yaml <<'EOF'
name: my-executor
description: Implements features using TDD
model: sonnet
permissionMode: auto
maxTurns: 100
maxBudgetUsd: 10.0
EOF
```

### 4.4. Create reviewer profile

Create file: `~/.claude-unleashed/profiles/my-reviewer.yaml`

```yaml
name: my-reviewer
description: Reviews code for quality and security
model: sonnet
permissionMode: default
maxTurns: 50
maxBudgetUsd: 5.0
```

**Save it:**

```bash
cat > ~/.claude-unleashed/profiles/my-reviewer.yaml <<'EOF'
name: my-reviewer
description: Reviews code for quality and security
model: sonnet
permissionMode: default
maxTurns: 50
maxBudgetUsd: 5.0
EOF
```

### 4.5. Verify profiles are saved

```bash
cu profiles ls
```

You should see:
```
my-planner
my-executor
my-reviewer
```

### 4.6. Where are the detailed agent instructions?

The profiles reference built-in agents that ship with CU. Their full definitions are at:

- **Planner**: `.claude-unleashed/agents/planner.yaml` (~163 lines of systemPrompt)
- **Executor**: `.claude-unleashed/agents/executor.yaml` (~140 lines)
- **Reviewer**: `.claude-unleashed/agents/reviewer.yaml` (~180 lines)

**To see what an agent does:**

```bash
cu agents show planner
cu agents show executor
cu agents show reviewer
```

**To create your own custom agent**, see [appendix-concepts.md#agents](appendix-concepts.md#agents) or the full wiki at [13-authoring-profiles-and-agents.md](../wiki/13-authoring-profiles-and-agents.md).

## 5. Plan the Feature

Use the `my-planner` profile to design the implementation.

### 5.1. Approach A: Via Claude Code Conversation (Recommended)

**Open Claude Code and say:**

> Start a planning session for edc-python to design a health check endpoint for the Flask API. Include database connectivity check, proper HTTP status codes (200/503), and unit + integration tests. Use the my-planner profile.

Claude will:
1. Call the `cu_run` tool with your prompt
2. Launch the session
3. Monitor it and tell you when it completes
4. Show you where the plan file is

You can also say:
> What sessions are running?

> Show me the plan that was created

> Get the branch name from the planner session

### 5.2. Approach B: Via Terminal Commands

**Run in your regular terminal:**

```bash
cu run --repo /Users/thomaschang/Documents/dev/git/a360/edc-python \
  --profile my-planner \
  --agent planner \
  --prompt "Design a health check endpoint for the Flask API. Include database connectivity check, proper HTTP status codes (200/503), and unit + integration tests."
```

### 5.3. What happens (both approaches)

- Session starts in a new worktree at `~/.claude-unleashed/worktrees/<session-id>/`
- Planner creates a design doc at `docs/plans/2026-06-23-health-check-design.md`
- Session completes when plan is written

### 5.4. Monitor progress

**Via Claude Code:**
> What's the status of the planner session?

> Show me live output from the plucky-lynx session

**Via Terminal:**
```bash
cu sessions ls --status running
cu tail plucky-lynx
```

### 5.5. Check the output

**Via Claude Code:**
> Show me the plan file that was created

> What's the working directory for the planner session?

**Via Terminal:**
```bash
# List completed sessions
cu sessions ls --status completed

# Get the session details
cu sessions get plucky-lynx --json

# View the plan file
cu sessions get plucky-lynx --json | jq -r '.workingDirectory'
cd /Users/thomaschang/.claude-unleashed/worktrees/abc123/
cat docs/plans/2026-06-23-health-check-design.md
```

### 5.6. Review and iterate

**Review the plan.** If it looks good, continue to section 6. If not, start a new session with refinements:

**Via Claude Code:**
> Start another planning session for edc-python to refine the health check plan: add Redis connectivity check in addition to database.

**Via Terminal:**
```bash
cu run --repo /Users/thomaschang/Documents/dev/git/a360/edc-python \
  --profile my-planner \
  --prompt "Refine the health check plan: add Redis connectivity check in addition to database."
```

## 6. Implement the Feature

Use the `my-executor` profile to write the code.

### 6.1. Approach A: Via Claude Code Conversation (Recommended)

**Say to Claude:**

> Get the branch name from the planner session, then start an executor session for edc-python continuing from that branch. Use the my-executor profile. The prompt is: "Implement the health check feature according to the plan in docs/plans/2026-06-23-health-check-design.md. Use TDD: write tests first, then implementation."

Claude will:
1. Look up the planner's branch name
2. Launch the executor session with `--from-branch`
3. Monitor progress
4. Tell you when it completes

**Or step by step:**

> What's the branch name for the plucky-lynx session?

(Claude responds: `claude-unleashed/abc123`)

> Start an executor session for edc-python continuing from claude-unleashed/abc123. Use my-executor profile and implement the health check according to the plan.

### 6.2. Approach B: Via Terminal Commands

**First, get the planner's branch name:**

```bash
cu sessions get plucky-lynx --json | jq -r '.branch'
# Example output: claude-unleashed/abc123
```

**Run the executor:**

```bash
cu run --repo /Users/thomaschang/Documents/dev/git/a360/edc-python \
  --profile my-executor \
  --agent executor \
  --from-branch claude-unleashed/abc123 \
  --prompt "Implement the health check feature according to the plan in docs/plans/2026-06-23-health-check-design.md. Use TDD: write tests first, then implementation."
```

### 6.3. What happens (both approaches)

- Executor starts a new worktree from the planner's branch
- Reads the plan
- Writes failing tests
- Implements the feature to make tests pass
- Commits incrementally (red → green → refactor cycle)

### 6.4. Monitor progress

**Via Claude Code:**
> Show me the recent commits from the executor session

> What's the status of the executor?

**Via Terminal:**
```bash
cu tail brave-fox
cu sessions get brave-fox --json | jq -r '.workingDirectory'
cd <working-directory>
git log --oneline -10
```

### 6.5. Handle approvals (if needed)

Our `my-executor` profile uses `permissionMode: auto` so it skips most prompts. But if you used `permissionMode: default`:

**Via Claude Code:**
> Are there any pending approvals?

> Approve the pending approval

**Via Terminal:**
```bash
cu approvals ls
cu approvals approve <approval-id>
```

## 7. Review the Implementation

Use the `my-reviewer` profile to audit the code.

### 7.1. Approach A: Via Claude Code Conversation (Recommended)

**Say to Claude:**

> Get the branch from the executor session, then start a reviewer session for edc-python continuing from that branch. Use my-reviewer profile. Review the health check implementation for correctness, error handling, and test coverage. Open a PR if everything passes.

Claude handles the branch lookup and session launch automatically.

**Or if you want to iterate on review issues:**

> Continue the reviewer session and fix the missing error handling in the database connectivity check.

### 7.2. Approach B: Via Terminal Commands

**First, get the executor's branch name:**

```bash
cu sessions get brave-fox --json | jq -r '.branch'
# Example output: claude-unleashed/def456
```

**Run the reviewer:**

```bash
cu run --repo /Users/thomaschang/Documents/dev/git/a360/edc-python \
  --profile my-reviewer \
  --agent reviewer \
  --from-branch claude-unleashed/def456 \
  --prompt "Review the health check implementation for correctness, error handling, and test coverage. Open a PR if everything passes."
```

### 7.3. What happens (both approaches)

- Reviewer starts from the executor's branch
- Runs the test suite
- Checks for issues (error handling, edge cases, security)
- Verifies test coverage
- Opens a PR if everything passes

### 7.4. Check the review

**Via Claude Code:**
> What did the reviewer find?

> Show me the PR URL

**Via Terminal:**
```bash
cu tail clever-owl
cu sessions get clever-owl --json | jq -r '.output'
```

### 7.5. Iterate if needed

**Via Claude Code:**
> Continue the reviewer session and fix the missing error handling in the database connectivity check.

**Via Terminal:**
```bash
cu continue clever-owl --prompt "Fix the missing error handling in the database connectivity check."
```

## 8. Merge the Branch

Once the reviewer approves and opens a PR:

### 8.1. Via Claude Code

**Say to Claude:**

> What's the PR URL from the reviewer session?

Claude shows you the URL. Open it in your browser and merge through GitHub's UI.

### 8.2. Via Terminal

**Option A: Merge via GitHub (recommended)**

```bash
# Find the PR URL
cu sessions get clever-owl --json | jq -r '.output' | grep "github.com"
```

Open that URL and merge.

**Option B: Merge manually**

```bash
# Get the final branch name
cu sessions get clever-owl --json | jq -r '.branch'

# Go to your repo
cd /Users/thomaschang/Documents/dev/git/a360/edc-python

# Merge it
git fetch origin
git checkout main
git pull origin main
git merge --no-ff claude-unleashed/def456
git push origin main
```

## 9. Clean Up

Delete the completed sessions and prune worktrees:

### 9.1. Via Claude Code

**Say to Claude:**

> Delete the planner, executor, and reviewer sessions

> Clean up old worktrees

### 9.2. Via Terminal

```bash
# Remove session rows
cu sessions rm plucky-lynx
cu sessions rm brave-fox
cu sessions rm clever-owl

# Clean up worktrees
cu diagnostics worktree-prune --confirm
```

## 10. Complete Examples

### 10.1. Example A: Full Claude Code Conversation

Here's what the entire workflow looks like as a natural conversation with Claude (requires `cu-cli` plugin installed):

```
You: Start a planning session for edc-python to design a health check 
     endpoint for the Flask API. Include database connectivity check 
     and tests. Use my-planner profile.

Claude: I'll launch a planning session for you.
        [calls cu_run tool]
        Session started: plucky-lynx (planner)
        Status: running
        
You: What's the status?

Claude: The planner session is still running. It's writing the design doc.
        [shows progress]
        
(Wait a few minutes...)

Claude: The planner session completed! 
        Plan file created at: docs/plans/2026-06-23-health-check-design.md
        Branch: claude-unleashed/abc123

You: Show me the plan

Claude: [reads and displays the plan file]

You: Looks good. Start an executor session continuing from that branch. 
     Use my-executor profile and implement according to the plan.

Claude: I'll start the executor session from branch claude-unleashed/abc123.
        [calls cu_run with --from-branch]
        Session started: brave-fox (executor)
        
(Wait for implementation...)

Claude: Executor completed! 
        - Wrote tests for /health endpoint
        - Implemented the endpoint with DB connectivity check
        - All tests passing
        - 6 commits made
        Branch: claude-unleashed/def456

You: Great! Start a reviewer session from that branch to audit it 
     and open a PR.

Claude: Starting reviewer session from claude-unleashed/def456.
        [launches reviewer]
        Session started: clever-owl (reviewer)
        
(Wait for review...)

Claude: Review complete!
        - All tests pass
        - Code quality good
        - PR opened: https://github.com/a360/edc-python/pull/123

You: Perfect! Clean up the sessions.

Claude: [removes the three sessions]
        Done. Sessions removed and worktrees will be pruned.
```

**Key benefits of this approach:**
- No need to memorize `cu` commands
- No need to manually track branch names
- Natural language ("looks good", "start the next step")
- Claude handles the tool calls and session coordination

### 10.2. Example B: Full Terminal Flow

Here's the complete copy-paste flow with actual session IDs:

```bash
# Step 0: Create profiles (one-time setup)
mkdir -p ~/.claude-unleashed/profiles

cat > ~/.claude-unleashed/profiles/my-planner.yaml <<'EOF'
name: my-planner
agent: planner
model: sonnet
permissionMode: default
maxTurns: 50
maxBudgetUsd: 5.0
EOF
cu profiles save my-planner ~/.claude-unleashed/profiles/my-planner.yaml

cat > ~/.claude-unleashed/profiles/my-executor.yaml <<'EOF'
name: my-executor
agent: executor
model: sonnet
permissionMode: auto
maxTurns: 100
maxBudgetUsd: 10.0
EOF
cu profiles save my-executor ~/.claude-unleashed/profiles/my-executor.yaml

cat > ~/.claude-unleashed/profiles/my-reviewer.yaml <<'EOF'
name: my-reviewer
agent: reviewer
model: sonnet
permissionMode: default
maxTurns: 50
maxBudgetUsd: 5.0
EOF
cu profiles save my-reviewer ~/.claude-unleashed/profiles/my-reviewer.yaml

# Verify
cu profiles ls

# Step 1: Plan
cu run --repo /Users/thomaschang/Documents/dev/git/a360/edc-python \
  --profile my-planner \
  --prompt "Design a health check endpoint for the Flask API with database connectivity check and tests."

# Wait for it to complete, then get the branch
cu sessions ls
PLANNER_BRANCH=$(cu sessions get plucky-lynx --json | jq -r '.branch')
echo "Planner branch: $PLANNER_BRANCH"

# Step 2: Execute
cu run --repo /Users/thomaschang/Documents/dev/git/a360/edc-python \
  --profile my-executor \
  --from-branch $PLANNER_BRANCH \
  --prompt "Implement the health check according to the plan. Use TDD."

# Wait for it to complete, then get the branch
cu sessions ls
EXECUTOR_BRANCH=$(cu sessions get brave-fox --json | jq -r '.branch')
echo "Executor branch: $EXECUTOR_BRANCH"

# Step 3: Review
cu run --repo /Users/thomaschang/Documents/dev/git/a360/edc-python \
  --profile my-reviewer \
  --from-branch $EXECUTOR_BRANCH \
  --prompt "Review the implementation and open a PR if it passes."

# Get the PR URL
cu sessions ls
cu sessions get clever-owl --json | jq -r '.output' | grep "github.com"

# Step 4: Merge via GitHub (open the URL from above)

# Step 5: Clean up
cu sessions rm plucky-lynx
cu sessions rm brave-fox
cu sessions rm clever-owl
cu diagnostics worktree-prune --confirm
```

## 11. Alternative: Use the Full-Process Workflow

Instead of manually chaining planner → executor → reviewer, use the built-in `full-process` workflow (it does all three steps automatically):

```bash
cu workflow run full-process \
  --repo /Users/thomaschang/Documents/dev/git/a360/edc-python \
  --input '{
    "prompt": "Add a health check endpoint to the Flask API with database connectivity check and tests."
  }'
```

**What happens:**
- Workflow spawns three sessions sequentially:
  1. **Plan** — Creates design doc
  2. **Execute** — Implements according to plan
  3. **Review** — Audits code, runs tests, opens PR

**Monitor the workflow:**

```bash
cu workflow runs
cu workflow runs --json | jq -r '.[0].status'
```

**If a step fails:**

```bash
cu workflow resume <runId>
```

## 12. Tips

### 12.1. Iterate mid-implementation

If you realize the plan needs adjustment:

```bash
cu continue <executor-session-id> --prompt "Actually, also check Redis connectivity in the health check."
```

### 12.2. Use branch mode for live work

If you're actively developing on a feature branch and want CU to help without creating worktrees:

```bash
cd /Users/thomaschang/Documents/dev/git/a360/edc-python
git checkout feature/health-check

cu run --repo . \
  --run-mode in-place \
  --profile my-executor \
  --prompt "Add caching to the health check endpoint"
```

See [appendix-concepts.md#branch-mode](appendix-concepts.md#branch-mode) for details.

### 12.3. Customize profiles per repo

You can create repo-specific profiles at `/Users/thomaschang/Documents/dev/git/a360/edc-python/.claude-unleashed/profiles/` that override your user-level ones.

## 13. Next Steps

- [04-cicd-automation.md](04-cicd-automation.md) — Automate CI monitoring and PR handling
- [appendix-concepts.md](appendix-concepts.md) — Understand workflows, agents, and orchestration
