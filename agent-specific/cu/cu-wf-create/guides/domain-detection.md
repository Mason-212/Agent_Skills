# Domain Detection

Classify the user's workflow request into a domain, then extract domain-specific roles.

## Common Domains

### 1. Coding Workflows

**Indicators:** plan, implement, test, review, refactor, fix, debug

**Natural roles:** planner → executor → reviewer

**Example:** "Build feature X" → plan → implement → review

### 2. Data Aggregation

**Indicators:** fetch, aggregate, transform, summarize, report

**Natural roles:** fetcher → processor → reporter

**Example:** "Aggregate PRs and post to Slack" → fetch → aggregate → notify

### 3. Monitoring & Response

**Indicators:** detect, monitor, alert, respond, fix, notify

**Natural roles:** detector → responder → notifier

**Example:** "Monitor CI and fix failures" → detect → diagnose → fix → notify

### 4. Research & Documentation

**Indicators:** search, analyze, synthesize, document, write

**Natural roles:** searcher → analyzer → synthesizer → documenter

**Example:** "Research topic X" → search → analyze → synthesize → document

### 5. Quality Verification

**Indicators:** check, verify, test, lint, audit, scan

**Natural roles:** checker → reporter (or checker → fixer → verifier)

**Example:** "Verify branch quality" → analyze → report

## Detection Process

1. **Extract verbs** from prompt: "fetch", "aggregate", "post"
2. **Extract nouns** from prompt: "PRs", "summary", "Slack"
3. **Match to domain** based on verb patterns
4. **Determine natural roles** for that domain

## Examples

**Prompt:** "Create a workflow to verify quality of my local branch"

- Verbs: verify, check
- Nouns: branch, quality
- Domain: Quality Verification
- Roles: analyzer (run checks) → reporter (write report)

**Prompt:** "Find and fix all failing tests"

- Verbs: find, fix
- Nouns: tests, failures
- Domain: Monitoring & Response
- Roles: detector (find failures) → fixer (repair) → verifier (confirm)

**Prompt:** "Aggregate PRs merged this week and post to Slack"

- Verbs: aggregate, post
- Nouns: PRs, Slack
- Domain: Data Aggregation
- Roles: fetcher (get PRs) → processor (aggregate) → notifier (post)
