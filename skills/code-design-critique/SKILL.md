---
name: code-design-critique
description: Design critique scoped to local branch vs origin/master (commits + staged/unstaged); AI slop (read-only).
---

# Code Design Critique

## When to Use

- The user wants feedback on **approach, architecture, or tradeoffs** for work **on the current branch** — not a full merge-blocking code review (use **`git-review`** or **`pr-review-remote`** for the same **review standard** as a PR).
- The user asks for **blind spots**, **scalability**, **simplicity**, or help **avoiding generic “AI slop”** (vague names, over-abstraction, redundant layers, cookie-cutter structure) **limited to their local branch delta vs `master`**.

Do **not** use this skill as a substitute for **`git-review`** / **`pr-review-remote`** when the user needs bug/security/regression coverage against a concrete diff.

**Out-of-scope by default:** files outside the git-defined set below (e.g. a Google Doc or RFC). If the user explicitly points at an external artifact, they may widen scope in the prompt; otherwise stay inside the branch diff.

## Scope: which files and commits

This skill critiques **only** what differs from **`origin/master`** on the **current branch**, including **all local commits** on that branch since it diverged from `master`, **and** any **staged or unstaged** edits to **tracked** files — same comparison story as **`git-review`**.

1. **Fetch and pick the base** — Run **`git fetch origin master`**. Default base: **`origin/master`**. If the user or **`GIT_BASE_BRANCH`** indicates another branch (e.g. **`main`**), use **`git fetch origin <branch>`** and **`origin/<branch>`** everywhere below instead of **`origin/master`**. If the remote ref is missing after fetch, stop and say so.

2. **Build the path list (authoritative)** — After fetch, compute the set of paths to consider:
   ```bash
   git diff --name-only origin/master
   ```
   That list includes **every tracked path** that differs between **`origin/master`** and the **current working tree** — i.e. **all commits already on your branch** that are not in `origin/master`, **plus** staged and unstaged changes. **Only critique content under these paths** (and their in-repo dependencies you must open to judge boundaries — see below).

3. **Optional context outside the list** — You may open **adjacent** or **imported** files **only** when needed to understand an interface used by a changed file. Keep that minimal; name any such file in the critique so the user knows scope expanded briefly.

4. **Untracked files** — They do **not** appear in **`git diff --name-only origin/master`**. If **`git status`** shows important untracked files the user cares about, mention them in **Framing** as “not in diff scope unless added to git” — do not invent a deep critique of files you were not shown.

5. **Commit narrative (optional prelude)** — You may run **`git log --oneline origin/master..HEAD`** to summarize **previous local commits** on the branch; design critique should still **tie claims to the diff paths** above.

## Operating Procedure

1. **Establish scope from git** — Run the **Scope** steps above. State the base ref, number of changed paths, and (if useful) one-line **`git log --oneline origin/master..HEAD`** summary. If the diff set is empty, say there is nothing to critique and stop.

2. **Approach** — From **only** the scoped paths (and minimal adjacent reads), summarize the chosen approach. Evaluate: Does it match the problem size? Is there a simpler shape (fewer moving parts, clearer boundaries)? What alternatives were implicitly rejected — and is one of them clearly better for this context?

3. **Blind spots** — List plausible **failure modes** the design understates **within the scoped changes**: edge cases, operational burden (deploy, rollback, observability), team velocity, coupling to vendors or internal systems, security or privacy assumptions, migration path. Prefer “what could go wrong that we are not discussing?” over generic worry.

4. **Scale and simplicity** — Ask how **this branch’s changes** behave at **10× data, traffic, or team size**. Call out **accidental complexity** introduced here (extra layers, indirection, configuration surface) that does not buy clear capability. Prefer concrete simplifications (“merge X and Y”, “delete Z unless …”) over vague “simplify”.

5. **Mitigate AI slop** — Flag patterns in **scoped files** that often indicate **low-effort or template-driven** output: meaningless names (`data`, `handler`, `utils` blobs), shallow error handling, “enterprise” scaffolding without need, duplicated boilerplate, comments that restate code, inconsistent style vs the rest of the repo. Tie each flag to **why it hurts** maintainability or trust.

6. **Deliver the critique** — Use the sections below. Be **direct**; do not pad with filler. If the design is sound, say so and list only the highest-value risks or open questions.

## Output Format

### Framing
One short paragraph: what is being critiqued and the stated goal.

### Strengths
What is already clear, appropriate, or well-scoped (optional but keep brief).

### Risks and blind spots
Ordered by severity: what could fail, surprise operators or users, or block evolution. Each item: **claim → why it matters → what evidence or assumption it rests on**.

### Simplicity and scale
Tradeoffs and concrete options to reduce complexity or improve scaling story.

### AI slop check
Bullet list of **specific** patterns spotted (with file or section pointers if code exists) and how to fix or avoid them.

### Recommendations
Numbered, **actionable** next steps (smallest valuable change first). Distinguish “must fix before committing” from “consider later”.

## Important Constraints

- **Read-only** unless the user explicitly asks you to edit files — default is critique only.
- **Stay in scope** — critique **only** paths from **`git diff --name-only origin/master`** (after fetch, with the same base substitution as **`git-review`**), plus the small adjacent reads rule above. Do not roam the rest of the repo for generic opinions.
- **Do not invent problems** — every point should tie to observable structure in the scoped diff or a clearly stated assumption.
- **Do not duplicate a full PR-style review** — defer merge-bar correctness work to **`git-review`** / **`pr-review-remote`** so this skill stays focused on **design quality**.
