---
name: pr-review-local
description: Clone a GHE PR locally to /reviews/, run pr-understand walkthrough, then print a ready-to-paste fan-out review block.
---

# PR Review Local

## When to Use

- The user provides a `git.soma.salesforce.com` PR URL and wants a **deep review** using local files
- Downstream skills like `pr-understand` or fan-out parallel subagent review are planned
- Replaces `gu pr_review_v2` — the agent runs all commands directly, no copy-paste required

Do **not** use this skill for lightweight remote-only review — use `pr-review-remote` for that.

## Operating Procedure

### Step 1: Parse the PR URL

Extract from `https://git.soma.salesforce.com/<owner>/<repo>/pull/<N>`:
- `owner` — org (e.g. `a360`)
- `repo` — repository name (e.g. `edc-python`)
- `pr_number` — PR number (e.g. `952`)
- `ssh_url` — `git@git.soma.salesforce.com:<owner>/<repo>.git`
- `clone_dir` — `PR-<pr_number>` (relative to agent's current working directory)
- `repo_path` — `<cwd>/PR-<pr_number>` where `<cwd>` is the agent's current working directory at invocation time
- `pr_branch` — `pr-<pr_number>`
- `pr_ref` — `<owner>/<repo>#<pr_number>`

Print to user:
```
[pr-review-local] Parsed: owner=<owner> repo=<repo> PR=<pr_number>
[pr-review-local] Clone target: <cwd>/PR-<pr_number>
```

### Step 2: Clone or update the repo

Print: `[pr-review-local] Cloning PR-<pr_number>...` (or `Updating...` if dir exists)

If `PR-<pr_number>` does **not** exist in cwd:
```bash
git clone git@git.soma.salesforce.com:<owner>/<repo>.git PR-<pr_number>
```

If it already exists:
```bash
cd PR-<pr_number> && git fetch origin && cd ..
```

Print: `[pr-review-local] Repo ready at: <repo_path>`

### Step 3: Fetch the PR head ref and switch to it

Print: `[pr-review-local] Fetching PR head ref → branch pr-<pr_number>...`

```bash
cd <repo_path>
git remote set-url origin git@git.soma.salesforce.com:<owner>/<repo>.git
git fetch origin refs/pull/<pr_number>/head:pr-<pr_number>
git switch pr-<pr_number>
```

Print: `[pr-review-local] Switched to branch: pr-<pr_number>`

### Step 4: Verify the diff

Print: `[pr-review-local] Changed files vs origin/master:`

```bash
git diff --name-only origin/master...pr-<pr_number>
```

Print the file list. If it is empty or looks wrong (e.g. contains unrelated files), stop and report the issue before proceeding.

### Step 5: Invoke pr-understand

Print: `[pr-review-local] Running pr-understand walkthrough...`

Read and follow the `pr-understand` skill at `/Users/thomaschang/.claude/skills/pr-understand/SKILL.md`.

Use the local repo as the source — load context via:
```bash
git diff origin/master...pr-<pr_number>
```

Produce the full `pr-understand` output: Big Picture, Touched Areas, Implementation Details, Tests as Examples, Navigation Map, What Still Feels Unclear, and the restatement gate.

### Step 6: Print the copy-paste command block

After the `pr-understand` walkthrough, print this block so the user can run these commands when ready.

Print exactly (substituting real values for `<cwd>`, `<pr_number>`, `<owner>`, `<repo>`):

```
==============================================================
NEXT STEPS — run these when ready
==============================================================

# 1. CodeNod local review (results visible in terminal only, NOT Mac app):
cd <cwd>/PR-<pr_number>
codenod branch review --base origin/master --repo <owner>/<repo>

# 2. Deep parallel agent review (open a new chat from inside the PR directory):
cd <cwd>/PR-<pr_number>
/pr-review-toolkit:review-pr all parallel

==============================================================
Tip for step 2: open the new chat with working directory set to <cwd>/PR-<pr_number>
==============================================================
```

## Important Constraints

- **Run all git commands directly** — do not print commands for the user to copy; execute them.
- The only output intended for user copy-paste is the fan-out block in Step 6.
- Clone target is always relative to the agent's current working directory at invocation time — never a hardcoded path.
- Do not fabricate file-level agent prompts in the fan-out block; the `pr-review-toolkit:review-pr all parallel` command handles that automatically.
- **Read-only after clone** — no edits to cloned files.
- If any git command fails, report the error and stop; do not proceed with a broken repo state.
- The three-dot diff (`origin/master...pr-<N>`) is mandatory — it shows only PR changes, not master changes merged in.
