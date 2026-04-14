---
name: pr-create
description: Create a pull request using the GitHub CLI
---

# PR Create

## When to Use

- The user asks you to create a PR, open a pull request, or submit their work for review
- The user has finished a task and wants to push and open a PR
- The user invokes a pull request command or workflow

## Operating Procedure

1. **Gather context.** Run the following commands to understand the current state:
   - `git status` — check for uncommitted changes
   - `git branch --show-current` — get the current branch name
   - `git log --oneline -5` — see recent commits on the branch
   - `git remote -v` — confirm the remote target

2. **Check for uncommitted changes.** If there are staged or unstaged changes that have not been committed, warn the user before proceeding. Do not create a PR with uncommitted work unless the user explicitly says to ignore it.

3. **Determine the base branch.** Use `master` as the default base branch. If the user specifies a different base branch (e.g., "create a PR against develop"), use that instead.

4. **Push the branch.** If the current branch has not been pushed to the remote, or has unpushed commits, run `git push` (with `--set-upstream` if needed) to ensure the remote is up to date.

5. **Generate the PR title.**
   - Derive a concise title from the commits and changes on the branch.
   - If the user provided a title, use it.
   - If the current branch matches the pattern `thomaschang/w-NNNNNNNNN-*` (where `NNNNNNNNN` is a numeric GUS work-item ID), prefix the title with `@W-NNNNNNNNN: `.
   - Example: branch `thomaschang/w-123456789-fix-login` produces a prefix of `@W-123456789: `.

6. **Generate the PR description.**
   - Summarize what changed and why, based on the commit log and diffs.
   - If the user provided a description, use it.
   - If changes affect behavior, workflows, or interfaces, note whether documentation has been updated. If it has not, remind the user to include documentation updates in the PR.

7. **Create the PR.** Run `gh pr create` with the title, body, and base branch. For example:
   ```
   gh pr create --base master --title "PR title" --body "PR description"
   ```

8. **Report.** Show the user the PR URL and title so they can verify it looks correct. If the user requests follow-up changes (e.g., adding reviewers, updating the description), use `gh pr edit`.

## Important Constraints

- **Do not** include "created with Claude" or any AI attribution in the PR title or description.
- **Do not** run destructive git commands (e.g., `reset`, `rebase`, `force-push`).
- Use `gh` for all GitHub interactions. `gh` works with both `github.com` and `git.soma.salesforce.com`.
- Prefer `gh pr create` for creation and `gh pr edit` for follow-up updates.
- Only use these commands: `git status`, `git branch`, `git log`, `git push`, `git remote`, `gh pr`, `gh repo`, `gh auth`, `gh api`.
