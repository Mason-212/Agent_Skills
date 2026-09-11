---
name: pullschool
description: Pull latest commits from GitHub Mason-212/school into the local school repo
---

# Pull School

## When to Use

- The user invokes `/pullschool`
- The user asks to pull, sync, or download updates from `Mason-212/school`
- The user wants the local school notes to match GitHub

Always operate on the **school** repository, even if the current workspace is a different project.

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
   - If that directory does not exist, clone it:
     ```
     git clone git@github.com:Mason-212/school.git "$SCHOOL_DIR"
     ```
     Then report the clone result and stop (the tree is already up to date).

2. **Verify the remote.** From the school directory:
   - `git remote -v` — confirm `origin` points at `Mason-212/school`.
   - If `origin` is missing or wrong, set it:
     ```
     git remote add origin git@github.com:Mason-212/school.git
     ```
     or `git remote set-url origin git@github.com:Mason-212/school.git`.

3. **Gather status** before mutating anything:
   - `git status -sb`
   - `git branch --show-current`
   - `git stash list`

4. **Fetch.**
   ```
   git fetch origin
   ```

5. **Update the working tree.**
   - If the working tree is **clean**:
     ```
     git pull --ff-only origin main
     ```
     If fast-forward is not possible (local commits diverged), run `git pull --rebase origin main` instead. If rebase conflicts, **stop** and tell the user which files conflict.
   - If the working tree is **dirty**:
     1. `git stash push -u -m "pullschool: auto-stash before pull"`
     2. `git pull --ff-only origin main` (or `--rebase` if not fast-forwardable)
     3. `git stash pop`
     4. If stash pop conflicts, **stop** and tell the user which files conflict. Do not drop the stash.

6. **Report.** Show:
   - Whether the clone/pull succeeded
   - Current branch and short SHA
   - How many commits were pulled (`git log --oneline OLD..HEAD` when possible)
   - Any leftover local changes or stash conflicts

## Important Constraints

- **Do not** run `reset --hard`, `clean -fd`, or any command that discards local school work.
- **Do not** force-push.
- **Do not** commit or push as part of this skill. Use `/pushschool` to send local updates up.
- Run every git command with the school directory as the working tree (`git -C "$SCHOOL_DIR" ...` or `cd` there first).
- Only use these commands: `git clone`, `git remote`, `git status`, `git branch`, `git stash`, `git fetch`, `git pull`, `git log`, `git rev-parse`.
