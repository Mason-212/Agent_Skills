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
   - The branch has **no** upstream and the user has not asked for a first push. Confirm intent before pushing a brand-new branch with `--set-upstream`.

   **Single-commit fast-path:** If `git rev-list --count ${BASE}..HEAD` returns `1`, there is nothing to squash. Skip steps 6–8 (message capture, soft-reset, commit) and proceed directly to step 4 (fetch), step 5 (rebase onto latest base), and step 10 (push). This handles the common "PR is out of date with base" case where the branch has exactly one commit but master has advanced.

4. **Snapshot the pre-fetch base, then refresh remote refs.** Capture the current `${BASE}` SHA *before* fetching so you have a reference point for the post-squash verification in step 9:
   ```bash
   OLD_BASE=$(git rev-parse ${BASE})
   git fetch origin
   NEW_BASE=$(git rev-parse ${BASE})
   ```
   Fetching with no path filter (just `git fetch origin`) ensures `--force-with-lease` has up-to-date knowledge of every remote branch — including the user's own. Fetching only the base branch is the most common cause of `! [rejected] (stale info)` errors when pushing.

5. **Rebase onto the latest base.** This is **critical** — without it, a `reset --soft ${BASE}` after the base has moved will silently revert the new base commits in your squashed commit:
   ```bash
   git rebase ${BASE}
   ```
   - If the rebase reports conflicts, **stop**. Tell the user which files conflict and ask them to resolve, then run `git rebase --continue`. Do not proceed to the squash until the rebase is complete.
   - If the user prefers not to integrate the latest base changes (e.g. they want a pure history-rewrite), let them opt out — but warn that any commits the base picked up since the branch diverged will appear as **reverts** in the squashed diff.
   - After this step, `git log --oneline ${BASE}..HEAD` should show the same logical commits as in step 1, just possibly with new SHAs.

6. **Capture the oldest commit's message and strip AI-attribution trailers.** This becomes the squashed commit's message:
   ```bash
   FIRST_SHA=$(git rev-list --reverse ${BASE}..HEAD | head -1)
   git show -s --format=%B "${FIRST_SHA}" \
     | grep -v -iE '^(made[ -]with|created by cursor|generated [bw]ith|co-authored-by:|🤖)' \
     | awk 'BEGIN{p=0}
            { if (NF) p=1; if (p) lines[++n]=$0 }
            END { while (n>0 && lines[n] ~ /^[[:space:]]*$/) n--;
                  for (i=1;i<=n;i++) print lines[i] }' \
     > /tmp/squash-msg
   ```
   The `grep -v` removes lines like `Made-with: Cursor`, `Created by Cursor`, `Generated with ...`, `Co-Authored-By: ...`, and the 🤖 emoji prefix. The `awk` trims leading and trailing blank lines that may remain after stripping.

   Show the user the captured (and cleaned) message and ask whether they want to keep it as-is, edit it interactively, or supply a new one. If the user provides a different message, write that to `/tmp/squash-msg` instead — and re-run the same `grep` filter on it before saving.

7. **Soft-reset to the base.** This collapses all commits without touching the working tree:
   ```bash
   git reset --soft ${BASE}
   ```
   After this, `git status` should show every change from the squashed commits as **staged**. Because step 5 rebased onto the latest `${BASE}`, the staged diff represents only the user's work — not a reversal of base commits.

8. **Create the squashed commit.** Use the message captured in step 6:
   ```bash
   git commit -F /tmp/squash-msg
   ```
   - Use `-e` (edit) instead of plain `-F` if the user wanted to tweak the message interactively.
   - Preserve the `@W-NNNNNNNNN:` prefix if the original commit had one.

9. **Verify the squash didn't accidentally revert base commits.** This guards against subtle resolution mistakes during the step 5 rebase (e.g., taking `--ours` when `--theirs` was correct) that would produce a squashed diff which silently undoes commits the base picked up while the branch was alive. **Skip if `OLD_BASE == NEW_BASE`** (no new base commits to worry about).
   ```bash
   if [ "${OLD_BASE}" != "${NEW_BASE}" ]; then
     # Files touched by base commits added since the branch existed
     git log --name-only --pretty=format: "${OLD_BASE}..${NEW_BASE}" \
       | sort -u > /tmp/new-base-files.txt

     # Files in your squashed commit
     git diff "${NEW_BASE}" --name-only \
       | sort -u > /tmp/squash-files.txt

     # Overlap — files modified by both
     comm -12 /tmp/squash-files.txt /tmp/new-base-files.txt > /tmp/overlap.txt

     if [ -s /tmp/overlap.txt ]; then
       echo "WARNING: squashed commit modifies files also touched by recent ${BASE} commits:"
       cat /tmp/overlap.txt
       echo ""
       echo "This may be intentional (your work and a base PR both touch the same file)"
       echo "or accidental (the squash reverts a base commit). Inspect each file with:"
       echo "  git diff ${NEW_BASE} -- <file>"
       echo ""
       echo "ABORTING push. To recover or proceed:"
       echo "  - If unintentional: git reset --hard HEAD@{1}, fix the rebase, re-run skill."
       echo "  - If intentional:   git push --force-with-lease   (manual override)"
       exit 1
     fi
   fi
   ```
   - Stop and surface the overlap list to the user. **Do not push** without explicit user confirmation that each overlapping file is intentional.
   - This check has a small false-positive rate (legitimate overlap is possible) but reliably catches the silent-revert bug from a botched rebase.

10. **Force-push safely.** Always use `--force-with-lease`, never plain `--force`:
    ```bash
    git push --force-with-lease
    ```
    If the push is rejected with `stale info`, the remote branch advanced after the fetch in step 4 — re-fetch (`git fetch origin`) and inspect new commits with `git log @{u}..HEAD` and `git log HEAD..@{u}` before deciding whether to integrate them or override.

11. **Report.** Show the user:
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

The alias is now non-trivial (it includes the AI-trailer strip and the post-squash overlap verification), so we install it as a shell function in `~/.gitconfig` rather than a one-liner. Run this once:

```bash
git config --global alias.squash-push '!f() {
  set -e
  OLD_BASE=$(git rev-parse origin/master)
  git fetch origin
  NEW_BASE=$(git rev-parse origin/master)
  git rebase origin/master
  FIRST_SHA=$(git rev-list --reverse origin/master..HEAD | head -1)
  git show -s --format=%B "$FIRST_SHA" \
    | grep -v -iE "^(made[ -]with|created by cursor|generated [bw]ith|co-authored-by:|🤖)" \
    | awk "BEGIN{p=0} { if (NF) p=1; if (p) lines[++n]=\$0 } END { while (n>0 && lines[n] ~ /^[[:space:]]*\$/) n--; for (i=1;i<=n;i++) print lines[i] }" \
    > /tmp/squash-msg
  git reset --soft origin/master
  git commit -e -F /tmp/squash-msg
  if [ "$OLD_BASE" != "$NEW_BASE" ]; then
    git log --name-only --pretty=format: "$OLD_BASE..$NEW_BASE" | sort -u > /tmp/new-base-files.txt
    git diff "$NEW_BASE" --name-only | sort -u > /tmp/squash-files.txt
    comm -12 /tmp/squash-files.txt /tmp/new-base-files.txt > /tmp/overlap.txt
    if [ -s /tmp/overlap.txt ]; then
      echo "WARNING: squashed commit overlaps with recent origin/master commits:"
      cat /tmp/overlap.txt
      echo "Inspect: git diff origin/master -- <file>"
      echo "ABORT push. Run git push --force-with-lease manually if intentional."
      exit 1
    fi
  fi
  git push --force-with-lease
}; f'
```

Then they can run `git squash-push` directly. Adjust `origin/master` to `origin/main` if the repo's default is `main`.

Behavior:

- `set -e` halts on the first failure.
- If `git rebase origin/master` reports conflicts, the alias halts. Resolve conflicts, run `git rebase --continue`, then re-run `git squash-push`.
- If the post-squash overlap check fires, the alias aborts before pushing. Inspect the listed files; if intentional, push manually with `git push --force-with-lease`. If unintentional, recover via `git reset --hard HEAD@{1}` and re-attempt the rebase.

## Important Constraints

- **Do not** force-push to `master`, `main`, or any shared branch. Only operate on personal feature branches.
- **Always** use `--force-with-lease`, never plain `--force`. The `lease` form refuses to clobber if someone else pushed to the branch in the meantime.
- **Always** `git fetch origin` (all refs) before pushing so the lease is current. Fetching only the base branch leaves your branch's remote-tracking ref stale and triggers `! [rejected] (stale info)`.
- **Always** rebase onto the freshly-fetched base **before** the soft-reset. A `git reset --soft origin/master` on a stale branch will produce a squashed commit whose diff *reverts* any commits the base picked up since the branch diverged.
- **Always** run the post-squash overlap check (step 9) when the base advanced during this run (`OLD_BASE != NEW_BASE`). Abort the push if any files in the squashed commit overlap with files touched by the new base commits, until the user confirms each overlap is intentional.
- **Always** strip AI-attribution trailers from commit messages before committing. This includes (case-insensitive) lines starting with `Made-with:`, `Made With`, `Created by Cursor`, `Generated with`, `Generated by`, `Co-Authored-By:`, and the 🤖 emoji prefix. Step 6's `grep -v` pipeline does this automatically; do not bypass it.
- **Do not** run this skill if the working tree is dirty — commit or stash first to avoid mixing unrelated changes into the squashed commit.
- **Preserve** the `@W-NNNNNNNNN:` GUS prefix from the original commit subject when constructing the squashed commit message.
- Only use these commands: `git status`, `git branch`, `git log`, `git diff`, `git rev-parse`, `git rev-list`, `git show`, `git fetch`, `git rebase`, `git reset --soft`, `git commit`, `git push --force-with-lease`, plus `grep`, `awk`, `sort`, `comm` (for the message-strip and overlap-check pipelines), optionally `gh pr view`.
