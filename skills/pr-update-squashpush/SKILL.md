---
name: pr-update-squashpush
description: Squash all local commits on a PR branch into one (using the oldest commit's message) and force-push
---

# PR Update — Squash & Push

## When to Use

- A PR reviewer asked the user to **squash their commits** before merging.
- The user has multiple local commits on a feature branch and wants the remote PR branch to reflect a single, clean commit.
- The user invokes a "squash and push" workflow (e.g. `/pr-update-squashpush`, `git squash-push`).
- The user wants to collapse review-feedback fix-up commits into the original feature commit before re-requesting review.

Do **not** use this skill if:

- The user is on `master` / `main` or any branch others share — squashing rewrites history and a force-push would clobber other people's work.
- The branch is already a single commit ahead of the base branch — there is nothing to squash.
- The user wants to preserve individual commit boundaries (e.g. for `git bisect`) — recommend `git rebase -i --autosquash` with `--fixup=` commits instead.

## Operating Procedure

1. **Gather context.** Run these commands and report the findings to the user before mutating anything:
   - `git status` — confirm a clean working tree (no unstaged or untracked work that should be committed first).
   - `git branch --show-current` — get the current branch name.
   - `git rev-parse --abbrev-ref HEAD@{upstream} 2>/dev/null` — confirm the branch tracks a remote.
   - `git log --oneline ${BASE}..HEAD` — list the commits that will be squashed (where `${BASE}` is the resolved base ref from step 2).

2. **Resolve the base branch.** Determine the base in this order:
   - If the user specified one (e.g. "squash against develop"), use it.
   - If the env var `GIT_BASE_BRANCH` is set, use `origin/$GIT_BASE_BRANCH`.
   - Otherwise prefer `origin/master`. If `git rev-parse origin/master` fails, fall back to `origin/main`.
   - Cache the resolved value as `${BASE}` for the rest of the procedure.

3. **Pre-flight safety checks.** Abort and tell the user if any of these are true:
   - Working tree is dirty (uncommitted changes). The user should commit or stash first.
   - Current branch equals the base branch (squashing master into itself makes no sense).
   - Only one commit is ahead of the base (`git rev-list --count ${BASE}..HEAD` returns `1`). Nothing to squash; just `git push --force-with-lease` if needed.
   - The branch has **no** upstream and the user has not asked for a first push. Confirm intent before pushing a brand-new branch with `--set-upstream`.

4. **Capture the oldest commit's message.** This becomes the squashed commit's message:
   ```bash
   FIRST_SHA=$(git rev-list --reverse ${BASE}..HEAD | head -1)
   git show -s --format=%B "${FIRST_SHA}" > /tmp/squash-msg
   ```
   Show the user the captured message and ask whether they want to keep it as-is, edit it interactively, or supply a new one. If the user provides a different message, write that to `/tmp/squash-msg` instead.

5. **Refresh remote refs.** Run `git fetch origin` (no path filter) so `--force-with-lease` has up-to-date knowledge of every remote branch — including the user's own. Fetching only the base branch is the most common cause of `! [rejected] (stale info)` errors when pushing.

6. **Soft-reset to the base.** This collapses all commits without touching the working tree:
   ```bash
   git reset --soft ${BASE}
   ```
   After this, `git status` should show every change from the squashed commits as **staged**.

7. **Create the squashed commit.** Use the message captured in step 4:
   ```bash
   git commit -F /tmp/squash-msg
   ```
   - Use `-e` (edit) instead of plain `-F` if the user wanted to tweak the message interactively.
   - Preserve the `@W-NNNNNNNNN:` prefix if the original commit had one.

8. **Force-push safely.** Always use `--force-with-lease`, never plain `--force`:
   ```bash
   git push --force-with-lease
   ```
   If the push is rejected with `stale info`, the remote branch advanced after the fetch in step 5 — re-fetch (`git fetch origin`) and inspect new commits with `git log @{u}..HEAD` and `git log HEAD..@{u}` before deciding whether to integrate them or override.

9. **Report.** Show the user:
   - The new single-commit SHA and subject line (`git log -1 --oneline`).
   - The PR branch's remote URL if available (`gh pr view --json url -q .url 2>/dev/null` if `gh` is configured).
   - A reminder to refresh the PR page so the reviewer sees the squashed history.

## Example Session

Branch state before:

```
* a3f2b1c  Address PR feedback #2
* 9d8e7f1  Address PR feedback #1
* 0c9689a  @W-22052702: Port pi-coding-agent to edc_agent.pi.coding_agent
```

After running this skill (assuming the user keeps the original message):

```
* 5b1c4e8  @W-22052702: Port pi-coding-agent to edc_agent.pi.coding_agent
```

The remote branch is force-pushed; the GitHub PR diff is unchanged but the commit history is now a single commit.

## Optional: Install the `git squash-push` alias

If the user wants a one-command shortcut (no agent involvement), offer to install this alias once:

```bash
git config --global alias.squash-push '!f() { git fetch origin && git show -s --format="%B" $(git rev-list --reverse origin/master..HEAD | head -1) > /tmp/squash-msg && git reset --soft origin/master && git commit -e -F /tmp/squash-msg && git push --force-with-lease; }; f'
```

Then they can run `git squash-push` directly. Adjust `origin/master` to `origin/main` if the repo's default is `main`.

## Important Constraints

- **Do not** force-push to `master`, `main`, or any shared branch. Only operate on personal feature branches.
- **Always** use `--force-with-lease`, never plain `--force`. The `lease` form refuses to clobber if someone else pushed to the branch in the meantime.
- **Always** `git fetch origin` (all refs) before pushing so the lease is current. Fetching only the base branch leaves your branch's remote-tracking ref stale and triggers `! [rejected] (stale info)`.
- **Do not** run this skill if the working tree is dirty — commit or stash first to avoid mixing unrelated changes into the squashed commit.
- **Preserve** the `@W-NNNNNNNNN:` GUS prefix from the original commit subject when constructing the squashed commit message.
- **Do not** include "co-authored by" trailers or any AI attribution in the commit message.
- Only use these commands: `git status`, `git branch`, `git log`, `git diff`, `git rev-parse`, `git rev-list`, `git show`, `git fetch`, `git reset --soft`, `git commit`, `git push --force-with-lease`, optionally `gh pr view`.
