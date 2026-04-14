---
name: git-commit
description: Create a git commit with a well-formatted message describing the changes
---

# Git Commit

## When to Use

- The user asks you to commit, create a commit, or save their work to git
- The user has finished a task and wants to commit the result
- The user invokes a commit command or workflow

## Operating Procedure

1. **Gather context.** Run the following commands to understand the current state of the repository:
   - `git status` — see staged, unstaged, and untracked files
   - `git diff HEAD` — review the full diff of all changes against HEAD
   - `git branch --show-current` — get the current branch name
   - `git log --oneline -10` — see recent commits for style and context

2. **Stage files.** Based on the status and diff:
   - If there are unstaged or untracked files that are part of the user's work, stage them with `git add`.
   - Do not stage files that are clearly unrelated to the task (e.g., editor swap files, OS metadata).
   - If the user has already staged specific files, respect their staging and do not add additional files without confirming.

3. **Determine the commit message.**
   - If the user provided a message, use it as the basis for the commit message.
   - If the user did not provide a message, generate a concise, descriptive commit message based on the diff.
   - Write the subject line in imperative mood (e.g., "Add retry logic to API client", not "Added retry logic").
   - Keep the subject line under 72 characters.
   - For complex changes, add a blank line after the subject followed by a body that explains **what** changed and **why**.

4. **Apply the GUS work-item prefix.** Check the current branch name:
   - If the branch matches the pattern `thomaschang/w-NNNNNNNNN-*` (where `NNNNNNNNN` is a numeric GUS work-item ID), prefix the commit subject with `@W-NNNNNNNNN: `.
   - Example: branch `thomschang/w-123456789-fix-login` produces a prefix of `@W-123456789: `.
   - If the branch does not match this pattern, do not add a prefix.

5. **Commit.** Run `git commit` with the final message.

6. **Report.** Show the user the resulting commit (subject line and short SHA) so they can confirm it looks correct.

## Commit Message Examples

Single-line (simple change):
```
Add input validation for email field
```

With GUS prefix:
```
@W-123456789: Add input validation for email field
```

Multi-line (complex change):
```
Refactor authentication middleware to support OAuth2

Extract token validation into a dedicated module so it can be reused
by both the REST and GraphQL endpoints. Update tests to cover the new
token refresh flow.
```

## Important Constraints

- **Do not** include "co-authored by" trailers or any AI attribution in the commit message.
- **Do not** push to a remote — only commit locally.
- **Do not** run destructive git commands (e.g., `reset`, `rebase`, `force-push`).
- Only use these git commands: `git add`, `git status`, `git diff`, `git log`, `git branch`, `git commit`.
