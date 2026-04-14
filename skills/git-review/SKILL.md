---
name: git-review
description: Review local branch and working tree vs master using the same bar as pr-review-remote (read-only).
---

# Git Review

## When to Use

- The user wants a **code review before a PR exists**, or without using GitHub PR APIs.
- The user asks to review **current branch work**, **local changes**, or **what differs from master**.

Prefer **`pr-review-remote`** once a PR exists and you need thread metadata, prior reviews, or CI rollup.

## Same standard as `pr-review-remote`

**`git-review` and `pr-review-remote` use one standard:** identical **review priorities**, **incremental + candidate + verification** discipline, **severity definitions** (Critical / Warning / Suggestion), **feedback section layout**, and **read-only / no-invented-issues** rules. The **only** deliberate difference is **how context is loaded** — here, **`git fetch`** + **`git diff origin/master`** (and file reads) instead of **`gh pr view` / `gh pr diff`**. Do not apply a looser or stricter bar for design vs correctness than you would on a remote PR review.

## Comparison baseline and scope

1. **Base branch — `master` (tracked on `origin`)**  
   - Default base: **`origin/master`**.  
   - Before reviewing, run **`git fetch origin master`** so **`origin/master`** matches the remote and comparisons are accurate.  
   - If the user names another integration branch (e.g. **`main`**), use **`origin/<branch>`** after **`git fetch origin <branch>`** and substitute it everywhere below instead of **`origin/master`**. You may also honor **`GIT_BASE_BRANCH`** from the environment. If the remote ref is still missing after fetch, say so and stop rather than guessing.

2. **Single diff for “everything vs master”**  
   Run:
   ```bash
   git fetch origin master
   git diff origin/master
   ```
   This compares the **tree at `origin/master`** to the **current working tree** (tracked paths). It **includes**:
   - All **committed** changes on the current branch that are not in `origin/master`
   - **Staged** changes (they are part of what differs from `origin/master` through the working tree / index as git presents it)
   - **Unstaged** changes in tracked files  

   Do **not** ignore dirty state; **include** staged and unstaged in the review. If **untracked** files matter to the task, mention them separately (they do not appear in `git diff origin/master` unless you also inspect `git status`).

3. **Line numbers and citations**  
   Use the **unified diff hunk headers** (`@@ -old_start,old_count +new_start,new_count @@`). For the **modified / resulting file**, cite **paths and line numbers from the `+` side** of the hunk — those correspond to the **current working tree** (including staged + unstaged) as compared to `origin/master`, which is what you want for an accurate review against master.  
   For removals-only hunks, cite the **`+` side context** or the **`old_start`** line on the pre-change side and state clearly that the line refers to **`origin/master`**, not the current file.  
   When verifying a finding, **open the file at the cited path** in the workspace and reconcile with the hunk; do not invent line numbers.

4. **Lightweight prelude (optional, before deep reading)**  
   You may use **`git diff --stat origin/master`**, **`git log --oneline origin/master..HEAD`** (commit-only story), and **`git status`** to frame scope — the authoritative review input for code content remains **`git diff origin/master`** plus file reads for context.

## Review priorities (same as `pr-review-remote`)

Review for these concerns in **priority order**:

1. **Bugs** — Logic errors, off-by-one mistakes, null/undefined access, race conditions  
2. **Regressions** — Changes that break existing behavior or violate existing contracts  
3. **Security** — Injection, auth bypass, secrets exposure, unsafe deserialization  
4. **Missing tests** — Untested new behavior, edge cases without coverage  
5. **Error handling** — Unhandled exceptions, swallowed errors, misleading error messages  
6. **Missing documentation** — Changed behavior or interfaces without updated docs  
7. **Design** — Unnecessary complexity, poor separation of concerns, naming issues  
8. **Performance** — Inefficient algorithms, N+1 queries, unnecessary allocations  

Focus on what matters most. A review that catches one real bug is more valuable than ten stylistic nitpicks.

## Incremental review and verification (same as `pr-review-remote`)

1. **Review incrementally** — Do not read the entire patch in one pass. Start with the highest-risk files first: core logic, auth/security, data writes, migrations, concurrency, error handling, public interfaces, and tests. Read surrounding code for context. Record any suspicious items as **candidate findings** — these are unverified and must survive the verification step before appearing in your review.

2. **Verify each candidate finding** — For every candidate, run through this checklist:
   - **Try to disprove it.** Read the surrounding code in the diff and the existing codebase. Look for guards, fallbacks, defaults, or upstream validation that would prevent the issue. Check whether tests in the diff already cover the scenario.
   - **Check for handling elsewhere.** Search the codebase and the rest of the diff for related error handling, type checks, configuration, or documentation that addresses the concern.
   - **State concrete evidence.** Write one sentence explaining *why this is a real problem*, citing specific code (file, line, function). If you cannot point to concrete evidence, the finding is not real.
   - **Classify or drop.** If the evidence holds, keep it as a finding. If you found handling that fully addresses it, drop it silently. If you lack the context to confirm or deny it, move it to **Open Questions** — do not keep it as a finding.

   Do not downgrade weak findings to "Suggestion" severity as a hedge. Either the evidence supports the finding or it does not. For large change sets, note areas you could not inspect deeply under Open Questions.

## Feedback format (same as `pr-review-remote`)

Structure your review as follows:

### Findings

List issues in severity order:

- **Critical** — Bugs, security issues, or regressions that must be fixed before merge  
- **Warning** — Problems that should likely be fixed but are not blocking  
- **Suggestion** — Improvements the author could consider  

For each finding, include the file and line, what the problem is, why it matters, and the specific evidence that survived verification (e.g., "no null check exists in the call chain from X to Y" or "the test on line N only covers the happy path").

If there are no findings, say so explicitly and mention any residual risks or testing gaps.

### Open Questions or Assumptions

Use this section when missing context prevents a fully confident conclusion.

### Summary

A brief description of what the change set does (vs `origin/master`) and your overall assessment.

### What Looks Good

Optional positive feedback such as strong tests, clean abstractions, or thoughtful error handling.

## Optional: posting to GitHub later

If the user explicitly asks to turn the review into PR comments **after** a PR exists, follow the **`pr-review-remote`** guidance for `gh pr review` / `gh api` (confirmation first, correct JSON for inline comments). This skill does not require `gh` for the default review.

## Operating procedure

1. **Fetch and confirm base** — `git fetch origin master` (or the user’s base). Confirm **`origin/master`** exists.
2. **Summarize scope** — optional: `git status`, `git diff --stat origin/master`, `git log --oneline origin/master..HEAD`.
3. **Ordered file list** — from `git diff --name-only origin/master` (or from the stat diff), order by risk (security, auth, data writes, migrations, concurrency, public API, tests, then the rest).
4. **Review incrementally** — for each file, use **`git diff origin/master -- <path>`** when helpful, read surrounding code in the repo, record **candidates**, then **verify** each using the checklist above.
5. **Present** the review using the **Feedback format** section.

## Important constraints

- **Read-only** — no edits, commits, or staging.
- **Git only** for scope against master — **`git diff origin/master`** (after fetch) as the canonical comparison; do not fabricate diffs.
- **Accurate vs `origin/master`** — always fetch before reviewing so line context matches the remote tip of **master**.
- **Staged and unstaged** — both are in scope via the working tree comparison above.
- **Do not invent issues** — be direct; if the change set looks fine, say so.
