---
name: pr-understand
description: Explain what a code change does — architecture, touched areas, intent, and how to navigate the codebase after it lands. Use when the user asks to walk through a diff, understand what a branch does, or wants a pre-read before reviewing.
---

# PR Understand

## When to Use

- "Walk me through this PR"
- "What does this branch / diff actually do?"
- "Explain this change before I review it"
- "What parts of the codebase does this touch?"
- "Help me write the PR description"

Do **not** use this skill to judge whether a change is safe to merge — use `pr-review-remote` (remote PR) or `git-review` (local branch) for that.

## Input Sources

Accept whatever the user provides and load context accordingly:

| Input | How to load |
|---|---|
| PR URL or PR number | `gh pr view <PR> --repo <host>/<owner>/<repo> --json title,body,author,files,comments,url` then `gh pr diff <PR> --repo <host>/<owner>/<repo>` |
| Local branch / working tree | `git fetch origin master && git diff origin/master` |
| SHA range | `git diff <BASE_SHA>..<HEAD_SHA>` |
| Pasted diff | Use as-is |

For GitHub Enterprise (`git.soma.salesforce.com`), pass `--hostname <host>` to all `gh api` calls.

## Walkthrough Workflow

1. **Load the change.** Use the appropriate input source above.
2. **State the apparent problem being solved.** One sentence, before any code details.
3. **Map touched areas.** List files/packages and their roles — entrypoints, models, helpers, tests, consumers.
4. **Separate signal from noise.** Distinguish behavioral changes from refactors, test-only edits, and mechanical churn. Compress boilerplate into a brief mention.
5. **Explain high-cognitive-overhead paths first.** Functions with branching, invariants, cross-layer transitions, or non-obvious data flow. Use tests as concrete examples when they clarify intent.
6. **Produce a navigation map.** Name the entrypoints, helpers, test files, and adjacent systems a future reader should check.
7. **Close with the restatement gate.** Ask the user to state the change's load-bearing invariant in one sentence in their own words. Confirm or correct it. A walkthrough that ends without the user reconstructing the *why* has produced familiarity, not understanding.

## Depth Rules

Go deep on:
- functions with branching or subtle invariants
- classes that coordinate multiple helpers
- transformations between representations
- code that crosses package or layer boundaries
- tests that are the clearest executable example of intent

Compress to one line:
- registration boilerplate
- repetitive wrappers
- obvious data shuffling with no tricky behavior

## Concrete Example Rule

When a concept is abstract, include an example. Prefer examples from:
1. Tests in the change
2. Nearby fixtures
3. A small synthetic scenario describable in one or two sentences

## Output Format

### Big Picture

- What problem the change is solving
- What behavior or architecture changed (not just what code changed)

### Touched Areas

- File or package — its role in the system

### Important Implementation Details

High-cognitive-overhead parts first. Glue code compressed to one line each.

### Tests as Examples

Which tests best demonstrate the behavior and what each one proves.

### How to Navigate This After Landing

- Entrypoints
- Helper modules
- Test files
- Adjacent systems worth checking

### What Still Feels Unclear

Assumptions, unclear intent, or places where naming or comments do not fully explain behavior.

## Style Notes

- Start broad, then zoom in
- Explain before evaluating — this is not a review
- Plain language for complex ideas
- If a function is simple, state its purpose and move on
- Do not produce a line-by-line changelog; produce understanding

## Anti-Rationalization Table

| Rationalization | Pre-committed rebuttal |
|---|---|
| "I followed along, so I get it." | "Following an explanation is not the same as being able to reconstruct it. State the invariant." |
| "Just summarize, I'll read details later." | "Later usually arrives during an incident. Hold the invariant now." |
| "The walkthrough was clear, no need to restate." | "Clarity is the easiest borrowed-confidence signal. Restate the load-bearing claim in one sentence." |
| "I am only skimming this PR." | "Then say *skim* explicitly. A walkthrough framed as understanding when it was skimming becomes silent comprehension debt." |

## Additional Resources

- See [examples.md](examples.md) for example output patterns covering Big Picture, Implementation Details, Tests as Examples, Navigation Map, and the restatement gate.

## Constraints

- **Read-only.** No edits, commits, or staging.
- **Do not judge.** Do not produce a findings list or severity ratings — that is `pr-review-remote`'s job.
- **Do not invent.** If intent is unclear, say so in "What Still Feels Unclear."
