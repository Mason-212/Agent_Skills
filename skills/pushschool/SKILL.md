---
name: pushschool
description: Commit and push local school notes to GitHub Mason-212/school
---

# Push School

## When to Use

- The user invokes `/pushschool`
- The user asks to push, upload, or sync local school notes to GitHub
- The user wants anything under the local school tree sent to `Mason-212/school`

Always operate on the **school** repository, even if the current workspace is a different project or a nested subject vault.

## Constants

| Item | Value |
|---|---|
| Local repo | `${SCHOOL_DIR:-$HOME/school}` |
| GitHub repo | `Mason-212/school` |
| Remote URL | `git@github.com:Mason-212/school.git` |
| Default branch | `main` |

## Operating Procedure

1. **Resolve the local repo.**
   - Use `$SCHOOL_DIR` if set; otherwise `$HOME/school`.
   - If that directory does not exist or is not a git repo, **stop**. Tell the user to run `/pullschool` first (or clone `Mason-212/school`).

2. **Verify the remote.** From the school directory:
   - `git remote -v` — confirm `origin` points at `Mason-212/school`.
   - If `origin` is missing or wrong, set it to `git@github.com:Mason-212/school.git`.

3. **Gather context.**
   - `git status`
   - `git diff HEAD`
   - `git branch --show-current`
   - `git log --oneline -5`

4. **If there is nothing to commit and nothing to push**, report that school is already up to date and stop.

5. **Stage everything under school.**
   - `git add -A`
   - Respect `.gitignore` (do not force-add ignored files).
   - Do not stage editor swap files or OS metadata if they somehow appear (e.g. `*.swp`).
   - Include notes, OCR inbox files, and vault files that are part of the school tree.

6. **Commit if there are staged changes.**
   - If the user provided a commit message, use it.
   - Otherwise write a short imperative subject from the diff (under 72 characters), for example:
     - `Add Living Earth unit notes`
     - `Update English grammar notes and OCR inbox`
   - Do **not** include "co-authored by" trailers or any AI attribution.
   - If there is nothing staged after `git add`, skip the commit.

7. **Refresh remote refs, then push.**
   ```
   git fetch origin
   git pull --ff-only origin main
   git push -u origin HEAD
   ```
   - If fast-forward is not possible because local and remote diverged, run `git pull --rebase origin main`, then push.
   - If rebase or push conflicts, **stop** and tell the user which files conflict. Do not force-push.

8. **Report.** Show:
   - Commit subject and short SHA (if a commit was created)
   - Files included
   - Push result and the GitHub URL: `https://github.com/Mason-212/school`

## Important Constraints

- **Do not** force-push (`--force`, `--force-with-lease`).
- **Do not** run destructive git commands (`reset --hard`, `clean -fd`, `rebase -i`).
- **Do not** push a different repository. Only `Mason-212/school`.
- Run every git command with the school directory as the working tree (`git -C "$SCHOOL_DIR" ...` or `cd` there first).
- Only use these commands: `git remote`, `git status`, `git diff`, `git log`, `git branch`, `git add`, `git commit`, `git fetch`, `git pull`, `git push`.
