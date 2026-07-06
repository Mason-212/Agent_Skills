---
name: pr-review-local
description: Review a GHE PR (by URL) or a local working branch — runs pr-understand walkthrough and prints ready-to-paste fan-out commands.
---

# PR Review Local

## When to Use

- The user provides a `git.soma.salesforce.com` PR URL — agent clones the PR locally and reviews it
- The user provides a local repo path and/or branch name — agent reviews the existing working branch directly
- Downstream skills like `pr-understand` or fan-out parallel subagent review are planned

For lightweight remote-only review that shows in the CodeNod Mac app, use `pr-review-remote`.

## Step 0: Detect input mode

Look at what the user provided:

- **URL mode** — input contains `https://git.soma.salesforce.com/.../pull/<N>` → follow Steps 1–4 (PR path)
- **Local mode** — input is a local directory path and/or branch name, or no input (use agent cwd) → skip to Step 4 (Local path)

Print to user:
```
[pr-review-local] Mode: PR URL    (cloning remote PR)
```
or
```
[pr-review-local] Mode: Local branch    (reviewing existing working branch)
```

---

## PR PATH (URL mode) — Steps 1–3

### Step 1: Parse the PR URL

Extract from `https://git.soma.salesforce.com/<owner>/<repo>/pull/<N>`:
- `owner` — org (e.g. `a360`)
- `repo` — repository name (e.g. `edc-python`)
- `pr_number` — PR number (e.g. `952`)
- `ssh_url` — `git@git.soma.salesforce.com:<owner>/<repo>.git`
- `repo_path` — `<cwd>/PR-<pr_number>` where `<cwd>` is agent's current working directory
- `pr_branch` — `pr-<pr_number>`
- `pr_ref` — `<owner>/<repo>#<pr_number>`

Print:
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

---

## LOCAL PATH — Step 4a (local mode only)

### Step 4a: Enter the repo and confirm branch

If the user provided a path, `cd` to it. Otherwise use the agent's current working directory.

```bash
cd <path>          # if provided; otherwise already in cwd
git fetch origin
```

Determine the current branch and `owner/repo` from the git remote URL:
```bash
git branch --show-current
git remote get-url origin
```

Set:
- `repo_path` — the directory used above
- `pr_branch` — current branch name (e.g. `W-Tool-Registry`)
- `owner/repo` — parsed from the remote URL
- `base` — `origin/master` (default; use `origin/main` if master doesn't exist)

Print:
```
[pr-review-local] Repo: <repo_path>
[pr-review-local] Branch: <pr_branch>
[pr-review-local] Base: origin/master
```

---

## SHARED STEPS — Steps 4–6 (both modes)

### Step 4: Verify the diff

Print: `[pr-review-local] Changed files vs origin/master:`

```bash
git diff --name-only origin/master...<pr_branch>
```

Print the file list. If it is empty or looks wrong, stop and report before proceeding.

### Step 5: Invoke pr-understand

Print: `[pr-review-local] Running pr-understand walkthrough...`

Read and follow the `pr-understand` skill at `/Users/thomaschang/.claude/skills/pr-understand/SKILL.md`.

Load context via:
```bash
git diff origin/master...<pr_branch>
```

Produce the full `pr-understand` output: Big Picture, Touched Areas, Implementation Details, Tests as Examples, Navigation Map, What Still Feels Unclear, and the restatement gate.

### Step 6: Print the copy-paste command block

Print (substituting real values):

```
==============================================================
NEXT STEPS — run these when ready
==============================================================

# 1. CodeNod local review (terminal only, NOT Mac app):
cd <repo_path>
codenod branch review --base origin/master --repo <owner>/<repo>

# 2. Deep parallel agent review (open a new chat from this directory):
cd <repo_path>
/pr-review-toolkit:review-pr all parallel

==============================================================
Tip for step 2: open the new chat with working directory set to <repo_path>
==============================================================
```

## Important Constraints

- **Run all git commands directly** — do not print them for the user to copy; execute them.
- The only output for user copy-paste is the block in Step 6.
- In URL mode, clone target is relative to the agent's cwd at invocation time — never hardcoded.
- **Read-only** — no edits to any files.
- If any git command fails, report the error and stop.
- Always use three-dot diff (`origin/master...<branch>`) to show only branch changes, not master changes merged in.
