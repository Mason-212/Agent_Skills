# PR & Review Skill Comparison

> **Note:** `pr-review-toolkit:review-pr` is a Claude Code plugin command, not a portable skill. It only works in Claude Code environments.

## At a Glance

| | `git-review` | `pr-review-remote` | `pr-review-toolkit:review-pr` *(Claude only)* | `pr-understand` | `critique-me` |
|---|---|---|---|---|---|
| **Purpose** | Judge local changes for correctness | Judge a remote PR for correctness | Comprehensive multi-aspect review using specialized agents | Explain what a change does | Stress-test designs, specs, or output against rubrics |
| **Question answered** | "Is my local work safe to merge?" | "Is this remote PR safe to merge?" | "Is this PR ready across all quality dimensions?" | "What does this change do and why?" | "Is this plan / spec / output well-reasoned?" |
| **Output** | Defect list (Critical/Warning/Suggestion) | Defect list (Critical/Warning/Suggestion) | Aggregated defect list from multiple agents (Critical/Important/Suggestions) + Strengths + Action Plan | Narrative (Big Picture, Touched Areas, Navigation Map) | Rubric-scored critique (Stress-test, Blind spots, Anti-slop, Code quality, ML design, Boundary integrity) |
| **Read-only?** | Yes | Yes | No — spawns multiple agents that analyze and can simplify code | Yes | Yes |

---

## Input Source

| | `git-review` | `pr-review-remote` | `pr-review-toolkit:review-pr` | `pr-understand` | `critique-me` |
|---|---|---|---|---|---|
| **Primary source** | Local working tree | Remote PR (URL or number) | Local working tree (git diff) | Any (URL, local, SHA, pasted diff) | Conversation thread, pasted text, or file/dir paths |
| **How loaded** | `git fetch origin master` + `git diff origin/master` | `gh pr view` + `gh pr diff` | `git diff --name-only` to identify changes, agents analyze via git diff | `gh pr diff` or `git diff` depending on input | Reads files from paths in message, or uses thread content |
| **Staged + unstaged?** | Yes | N/A | Yes | Yes (when local) | N/A |
| **GHE support** | No | Yes (`--hostname`) | No | Yes (`--hostname`) | No |
| **Needs `gh` CLI?** | No | Yes | Optional (`gh pr view` to check if PR exists) | Only for remote URLs | No |

---

## Phase of the Coding Workflow

```
Write code → Local review → Push → PR created → PR reviewed → Merge
   ↑               ↑                                 ↑
critique-me    git-review                      pr-review-remote
(before code)  pr-review-toolkit:review-pr
               (comprehensive local review)

                    ↑ pr-understand can be used at any of these points
                      (it explains, not judges, regardless of phase)
```

| Skill | Phase | Who initiates |
|---|---|---|
| `critique-me` | Pre-code: validating a plan, spec, or design before writing | You reviewing your own thinking |
| `git-review` | Post-code, pre-push: single-agent sanity check before creating a PR | Author self-reviewing |
| `pr-review-toolkit:review-pr` | Post-code, pre-push: multi-agent comprehensive review across quality dimensions | Author requesting thorough pre-PR review |
| `pr-review-remote` | Post-PR: reviewing someone else's (or your own) remote PR | Reviewer |
| `pr-understand` | Any phase: pre-review pre-read, onboarding, PR description drafting | Anyone who needs comprehension before judgment |

---

## Who Acts

| | `git-review` | `pr-review-remote` | `pr-review-toolkit:review-pr` | `pr-understand` | `critique-me` |
|---|---|---|---|---|---|
| **Actor** | This agent | This agent | Orchestrates multiple specialized agents | This agent | This agent |
| **Caller intent** | "Review my work" | "Review this PR" | "Thoroughly vet this PR across all dimensions" | "Teach me this change" | "Stress-test my thinking" |
| **Part of larger workflow?** | Standalone | Standalone | Standalone (orchestration workflow) | Standalone or pre-review prep | Standalone |

---

## Review Depth Comparison

### Single-Agent Reviews: `git-review` and `pr-review-remote`

Both use a unified review approach:
- Single agent performs the review
- Fast turnaround (seconds to low minutes)
- Covers: correctness bugs, project guideline adherence, obvious issues
- Output: defect list with Critical/Warning/Suggestion severity levels
- Best for: quick sanity checks, catching obvious issues

**When to use:**
- `git-review`: Fast local check before pushing
- `pr-review-remote`: Reviewing remote PRs (yours or others')

### Multi-Agent Review: `pr-review-toolkit:review-pr` *(Claude Code only)*

Orchestrates multiple specialized agents:
- **comment-analyzer**: Comment accuracy, documentation completeness, comment rot
- **pr-test-analyzer**: Test coverage quality, behavioral coverage, test gaps
- **silent-failure-hunter**: Silent failures, error handling, logging adequacy
- **type-design-analyzer**: Type encapsulation, invariant expression, type design quality
- **code-reviewer**: CLAUDE.md compliance, bugs, general code quality
- **code-simplifier**: Code clarity, readability, project standards (polish phase)

**Characteristics:**
- Slower (multiple agent spawns, minutes)
- Deeper coverage across specific dimensions
- Can run agents sequentially (default) or in parallel (user request)
- Aggregates findings from all agents into unified report
- Best for: thorough pre-PR vetting, complex changes, high-stakes code

**When to use:**
- Before creating PR for significant changes
- When you want comprehensive quality assurance
- When specific dimensions matter (tests, error handling, types)
- Can target specific aspects: `/pr-review-toolkit:review-pr tests errors`

---

## Overlap and Boundaries

### What is genuinely shared
- `git-review` and `pr-review-remote` use identical review priorities, severity levels, candidate-verify discipline, and output format. They differ only in input source.
- `pr-review-toolkit:review-pr` orchestrates multiple specialized agents (comment-analyzer, pr-test-analyzer, silent-failure-hunter, type-design-analyzer, code-reviewer, code-simplifier) to provide comprehensive coverage.

### Where skills are complementary, not redundant
- `pr-understand` produces a narrative explanation. The "Summary" section in `pr-review-remote` is its only overlap; `pr-understand`'s output is far richer and serves a different job.
- `critique-me` operates on pre-code artifacts (plans, specs, markdown). It never reads a diff. It is the only skill here that works before any code exists.
- `git-review` is a fast single-pass review; `pr-review-toolkit:review-pr` is a thorough multi-agent review across specific dimensions (comments, tests, errors, types, code quality, simplification).

### Handoff pattern
A well-ordered workflow looks like:

**Fast iteration:**
1. **`critique-me`** — validate the design before coding
2. **`git-review`** — quick sanity check after implementation
3. **`pr-understand`** — build a mental model of the change before reviewing
4. **`pr-review-remote`** — produce the formal review on the open PR

**Thorough pre-PR review:**
1. **`critique-me`** — validate the design before coding
2. **`pr-review-toolkit:review-pr`** — comprehensive multi-dimensional review before pushing
3. **`pr-understand`** — build a mental model of the change before reviewing
4. **`pr-review-remote`** — produce the formal review on the open PR

---

## Quick Selection Guide

| User says... | Skill to use |
|---|---|
| "Is my plan solid?" / "Critique this spec" | `critique-me` |
| "Review my local branch before I push" | `git-review` |
| "Comprehensively review this PR" / "Check tests, errors, types, comments" | `pr-review-toolkit:review-pr` |
| "Walk me through this PR / diff / branch" | `pr-understand` |
| "Review this PR" + provides URL or PR number | `pr-review-remote` |
