---
name: edc-cicd-babysit
description: Babysit a CI/CD pipeline for an edc-python (or similar) pull request — polls for failures every 30 seconds, diagnoses and fixes issues, runs repo checks, stages and commits fixes, then squash-pushes via pr-update-squashpush. Use when the user gives a PR URL and wants the agent to watch CI/CD and automatically address any failures.
disable-model-invocation: true
---

# EDC CI/CD Babysit

## When to Use

User provides a PR URL (e.g. `https://git.soma.salesforce.com/a360/edc-python/pull/957`) and wants the agent to watch CI/CD, fix failures, and push fixes automatically.

## Phase 1 — Setup

### 1.1 Get the PR URL

If not already provided, ask:

> "Please paste the CI/CD PR URL (e.g. `https://git.soma.salesforce.com/a360/edc-python/pull/957`)."

### 1.2 Determine repo checks

Run `ls` in the repo root and look for common check scripts:

- `Makefile` → `make lint`, `make test`
- `tox.ini` → `tox`
- `pyproject.toml` / `setup.cfg` → `pytest`, `ruff check .`, `mypy .`
- `.pre-commit-config.yaml` → `pre-commit run --all-files`

If nothing is found, ask the user:

> "What commands should I run to validate changes locally? (e.g. `make lint && pytest`)"

Store the commands as `REPO_CHECKS`.

### 1.3 Initialize the log

Create a local log file at `/tmp/edc-cicd-babysit.log` with a header:

```
=== edc-cicd-babysit started ===
PR: <url>
Started: <timestamp>
Repo checks: <REPO_CHECKS>
```

Append all subsequent activity to this file. Tell the user: "I'll write a running log to `/tmp/edc-cicd-babysit.log`."

---

## Phase 2 — Poll Loop (every 30 seconds)

Repeat the following until CI/CD passes or the user cancels.

### 2.1 Fetch CI/CD status

Use `gh pr checks <PR_URL>` (or equivalent) to get the current check status. If `gh` is not configured for the remote host, use `curl` with the host's REST API.

Parse the output and classify each check as: `passing`, `failing`, `pending`, or `skipped`.

Append a timestamped status summary to the log:

```
[HH:MM:SS] --- Poll ---
  passing: <n>  failing: <n>  pending: <n>
  <failing check names>
```

### 2.2 If all checks pass

Log:
```
[HH:MM:SS] All checks PASSED. Done.
```
Report success to the user and stop.

### 2.3 If only pending (no failures)

Wait 30 seconds and repeat from 2.1.

### 2.4 If there are failures

For each failing check, in order of priority:

1. Fetch the check's log URL or inline output.
2. Identify the root cause (error message, failed assertion, lint violation, import error, etc.).
3. Log the diagnosis:
   ```
   [HH:MM:SS] FAIL: <check name>
     Cause: <one-line summary>
     Plan:  <what will be changed>
   ```
4. Apply the fix to the codebase.
5. After all fixes are applied, continue to Phase 3.

---

## Phase 3 — Validate Locally

Run `REPO_CHECKS` from Phase 1. For each command:

- If it passes, log `[HH:MM:SS] LOCAL CHECK PASS: <command>`.
- If it fails, diagnose and fix, then re-run. Repeat up to 3 times before surfacing the error to the user.

Do **not** proceed to Phase 4 if any local check is still failing.

---

## Phase 4 — Stage and Commit

```bash
git add -A
git status
```

Log all staged files.

Compose a short commit message summarizing the fixes (e.g. `fix: address CI lint failures — ruff E501, F401`). Confirm with the user or auto-commit if they asked for fully autonomous mode.

```bash
git commit -m "<message>"
```

---

## Phase 5 — Squash and Push

Follow the `pr-update-squashpush` skill. Read and execute all steps from:
`skills/pr-update-squashpush/SKILL.md`

After the push, log:
```
[HH:MM:SS] Force-pushed. Returning to poll loop.
```

Then return to Phase 2 and wait 30 seconds before the next poll.

---

## Stopping Conditions

Stop the loop when any of the following is true:

- All CI/CD checks pass (success).
- A failure cannot be diagnosed or fixed after 2 attempts (surface to user and stop).
- The user explicitly cancels.
- Phase 4 local checks still fail after 3 retries (surface to user and stop).

On stop, print the log path and a final status:

```
=== edc-cicd-babysit finished ===
Status: <PASSED | BLOCKED>
Log: /tmp/edc-cicd-babysit.log
```

---

## Notes

- Always append to the log; never truncate it during a session.
- Use `--force-with-lease` (never `--force`) for all pushes — delegated to `pr-update-squashpush`.
- Do not squash if there is only one commit ahead of the base (the squash skill handles this automatically).
- Do not push to `main` or `master`.
