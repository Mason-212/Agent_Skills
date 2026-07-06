---
name: pr-review-remote
description: Trigger a CodeNod PR review that shows in the Mac app, then display results in chat.
---

# PR Review Remote

## When to Use

- The user provides a `git.soma.salesforce.com` PR URL and wants a **quick AI review visible in the CodeNod Mac app**
- No local clone is needed
- For deep review with local files, `pr-understand`, and fan-out agents — use `pr-review-local` instead

## Operating Procedure

### Step 1: Parse the PR URL

Extract from `https://git.soma.salesforce.com/<owner>/<repo>/pull/<N>`:
- `owner` — org (e.g. `a360`)
- `repo` — repository name (e.g. `edc-python`)
- `pr_number` — PR number (e.g. `952`)
- `pr_ref` — `<owner>/<repo>#<pr_number>`

Print: `[pr-review-remote] PR: <pr_ref>`

### Step 2: Pull the PR into CodeNod (makes it appear in Mac app)

Print: `[pr-review-remote] Pulling PR into CodeNod...`

```bash
codenod sync pr <owner>/<repo>#<pr_number>
```

### Step 3: Trigger the PR review

Print: `[pr-review-remote] Triggering review for <pr_ref>...`

```bash
codenod pr review <owner>/<repo>#<pr_number>
```

Print: `[pr-review-remote] Review triggered — visible in CodeNod Mac app`

### Step 4: Poll until complete

Print: `[pr-review-remote] Waiting for review to complete...`

```bash
until [ "$(codenod review show <owner>/<repo>#<pr_number> --json | jq -r '.status')" != "pending" ]; do
  sleep 2
done
```

Print: `[pr-review-remote] Review complete`

### Step 5: Show results

```bash
codenod pr show <owner>/<repo>#<pr_number>
```

Read the output and present findings in chat using this format:

### Findings
List issues in severity order (map CodeNod severity to these labels):
- **Critical** — must fix before merge
- **Warning** — should fix but not blocking
- **Suggestion** — optional improvement

For each finding include: file, line, problem, why it matters.

### Summary
Brief description of the PR and overall assessment.

### What Looks Good
Strong tests, clean logic, good error handling, etc.

## Important Constraints

- **Do not modify any files.**
- **Do not post comments to the PR** unless the user explicitly asks.
- Results are visible in the CodeNod Mac app — remind the user to check there for the full interactive view.
