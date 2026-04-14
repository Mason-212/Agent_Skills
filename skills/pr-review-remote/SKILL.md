---
name: pr-review-remote
description: Review remote GitHub PRs for bugs, regressions, security risks, and missing tests.
---

# PR Review Remote

## When to Use

Use this skill when:
- The user asks you to review a pull request
- The user provides a PR URL or PR number
- The user wants review feedback before posting comments to GitHub

## Operating Procedure

1. **Identify the PR, repo, and host** -- The user may provide a URL, a PR number, or ask you to find the PR. If the PR is on `git.soma.salesforce.com`, keep that host for all `gh` and `gh api` calls. Prefer explicit repo targeting such as `--repo <host>/<owner>/<repo>` when the repo is not the current checkout.

2. **Gather structured metadata first** -- Prefer structured output before reading raw diffs:
   - `gh pr view <PR> --repo <host>/<owner>/<repo> --json title,body,author,files,reviews,latestReviews,comments,reviewDecision,statusCheckRollup,url`
   - `gh pr diff <PR> --repo <host>/<owner>/<repo> --name-only`

3. **Check prior discussion before drafting findings** -- Use the PR metadata, comments, reviews, and checks to avoid repeating feedback that has already been raised. If you need existing inline review comments, use `gh api repos/<owner>/<repo>/pulls/<PR>/comments` and pass `--hostname <host>` for GitHub Enterprise.

4. **Review the changes incrementally** -- Do not read the entire patch in one pass. Start with the highest-risk files first: core logic, auth/security, data writes, migrations, concurrency, error handling, public interfaces, and tests. Read surrounding code for context. Record any suspicious items as **candidate findings** -- these are unverified and must survive the verification step before appearing in your review.

5. **Verify each candidate finding** -- Each candidate must survive active scrutiny before it appears in your review. For every candidate, run through this checklist:
   - **Try to disprove it.** Read the surrounding code in the diff and the existing codebase. Look for guards, fallbacks, defaults, or upstream validation that would prevent the issue. Check whether tests in the diff already cover the scenario.
   - **Check for handling elsewhere.** Search the codebase and the rest of the diff for related error handling, type checks, configuration, or documentation that addresses the concern.
   - **State concrete evidence.** Write one sentence explaining *why this is a real problem*, citing specific code (file, line, function). If you cannot point to concrete evidence, the finding is not real.
   - **Classify or drop.** If the evidence holds, keep it as a finding. If you found handling that fully addresses it, drop it silently. If you lack the context to confirm or deny it, move it to **Open Questions** -- do not keep it as a finding.

   Do not downgrade weak findings to "Suggestion" severity as a hedge. Either the evidence supports the finding or it does not. For large PRs, note areas you could not inspect deeply under Open Questions.

6. **Present feedback** -- Format your review using the findings-first format below.

## Review Priorities

Review for these concerns in priority order:

1. **Bugs** -- Logic errors, off-by-one mistakes, null/undefined access, race conditions
2. **Regressions** -- Changes that break existing behavior or violate existing contracts
3. **Security** -- Injection, auth bypass, secrets exposure, unsafe deserialization
4. **Missing tests** -- Untested new behavior, edge cases without coverage
5. **Error handling** -- Unhandled exceptions, swallowed errors, misleading error messages
6. **Missing documentation** -- Changed behavior or interfaces without updated docs
7. **Design** -- Unnecessary complexity, poor separation of concerns, naming issues
8. **Performance** -- Inefficient algorithms, N+1 queries, unnecessary allocations

Focus on what matters most. A review that catches one real bug is more valuable than ten stylistic nitpicks.

## Feedback Format

Structure your review as follows:

### Findings
List issues in severity order:

- **Critical** -- Bugs, security issues, or regressions that must be fixed before merge
- **Warning** -- Problems that should likely be fixed but are not blocking
- **Suggestion** -- Improvements the author could consider

For each finding, include the file and line, what the problem is, why it matters, and the specific evidence that survived verification (e.g., "no null check exists in the call chain from X to Y" or "the test on line N only covers the happy path").

If there are no findings, say so explicitly and mention any residual risks or testing gaps.

### Open Questions or Assumptions
Use this section when missing context prevents a fully confident conclusion.

### Summary
A brief description of what the PR does and your overall assessment.

### What Looks Good
Optional positive feedback such as strong tests, clean abstractions, or thoughtful error handling.

## If Asked to Submit Review Comments

Only do this if the user explicitly asks and has seen the findings first.

- Present the review in chat before posting it to GitHub
- Ask for confirmation before submitting comments
- For a summary-only review, use `gh pr review <PR> --comment --body-file -`
- For inline comments or multi-comment reviews, prefer `gh api ... --input` with a real JSON body
- Do not pass `comments='[...]'` via `-f` or `-F`; that sends a string and can cause HTTP 422 errors such as `"comments" is not an array`
- For GitHub Enterprise, pass `--hostname <host>` when using `gh api`

Example:

```bash
gh api "repos/$OWNER/$REPO/pulls/$PR/reviews" \
  --hostname "$HOST" \
  --method POST \
  --input - <<'EOF'
{
  "body": "Please address the findings below.",
  "event": "COMMENT",
  "comments": [
    {
      "path": "src/file.py",
      "line": 42,
      "side": "RIGHT",
      "body": "This can fail when ..."
    }
  ]
}
EOF
```

## Important Constraints

- **Do not modify any files.** This is a read-only review.
- **Do not post comments to the PR** unless the user explicitly asks you to.
- **Use `gh` to fetch review context.** Do not invent repo or PR details.
- Be direct. If the code is fine, say so. Do not invent issues to fill space.
