---
name: critique-me
description: Critique plans, specs, or pasted output using rubrics; infers paths. Not for PR merge-bar review.
---

# critique-me

## When to use

- The user invokes **critique-me**, **critique me**, or asks for a **structured critique** of design text, specs, plans, markdown, pasted AI output, or **explicit file/dir paths** in the message.
- They want **stress-testing**, **blind spots**, **substance / value density**, **code quality**, and/or **ML-specific** checks using **selectable rubrics**.

## When not to use (use other skills)

- **Merge-bar PR review** (bugs, security, regressions on a diff) → **`git-review`** or **`pr-review-remote`**.
- **Branch-scoped design** (approach, scale, simplicity vs base branch) → **`code-design-critique`**.

This skill is for **conversation scope**, **explicit paths**, or **mixed**—not a substitute for those workflows unless the user explicitly wants only a rubric-style pass.

## Rubrics (pick before or during the run)

Read **only** the selected files under [resources/rubrics/](resources/rubrics/) for this run.

| # | Id | Menu label |
|---|-----|------------|
| 1 | `stress-test-decisions` | Stress-test decisions |
| 2 | `blind-spots` | Blind spots and coverage |
| 3 | `anti-ai-slop` | Anti–AI slop (substance / value density) |
| 4 | `code-quality` | Code quality |
| 5 | `ml-design` | ML design |

**Shortcut:** “**Truth and evidence**” = rubrics **1 + 2** together.

**Default set** when the user does not choose: **1, 2, 3**. Add **4** when **code files or directories** are in the artifact set (or code is clearly the subject in-thread). Add **5** when the user asks or the content is clearly an ML / data / modeling design.

If rubrics are unclear, show the table and ask for a reply like `Rubrics: 1,2,3` or use **AskQuestion** with `allow_multiple` when available.

## Artifacts (infer from the message first)

1. **Parse paths** in the user message (repo-relative paths, `on path/to/file`, backtick-wrapped paths, multiple paths). **Read those files** (and dirs per caps below). Treat `.md` / `.mdx` as doc artifacts; code extensions and directories as **code paths**.
2. **No paths** and no explicit file/dir target → artifact is **conversation** (this thread / quoted blocks only).
3. If a path is **missing or unreadable**, say so and ask for a fix **before** a long rubric menu.
4. If intent is ambiguous (“critique my design” with no path) after rubrics are settled, ask **one** focused question: e.g. “Thread only, or paste a file path?”

**Do not** force a generic A/B/C artifact menu when paths are already supplied.

### Code path caps

When the user points at a **directory** or many files:

- Prefer **user-listed files** if they gave a list.
- Otherwise cap **20 files** total read for this critique and **depth 2** from each listed directory root unless the user raises the cap in the prompt.
- State in **Framing** which paths were read and if the cap truncated scope.

## Procedure

1. **Infer artifacts** from the user text (paths → read; else conversation).
2. **Resolve rubrics** from the user text, shortcut names, or defaults above; ask only if still unclear.
3. If **artifact** still ambiguous, one follow-up (see § Artifacts).
4. **Validate:** if **code-quality** (4) is selected but there is no code in scope, warn—drop 4 or ask for a path/snippet.
5. **Read** each selected `resources/rubrics/<id>.md` (ids from the table).
6. **Read** artifact corpus (files / dirs within caps; thread content as given).
7. **Deliver** the critique using the output format below. Be direct; no filler.

## Output format

Use these sections **in order**. Omit rubric sections that were not selected.

1. **Framing** — Goal, constraints, **rubrics used** (numbers or ids), **artifacts** (conversation and/or paths read; note if caps applied).
2. **Stress-test decisions** — if selected.
3. **Blind spots and coverage** — if selected.
4. **ML design** — if selected.
5. **Code quality** — if selected; else omit (or one line “N/A”).
6. **Anti–AI slop** — if selected.
7. **Recommendations** — numbered, smallest valuable change first; tag **must-fix** vs **later** when useful.

**Per finding:** **claim → why it matters → evidence** (quote or `path:line`). **Primary rubric** per finding: assertions under stress-test; silences under blind spots; hollow density under anti–AI slop; at most one “see also” to another rubric.

**Rules:** Do not invent problems. Tie every point to observable text or code. If the work is sound, say so briefly and list only high-value risks or open questions.

## Rubric file map

- [resources/rubrics/stress-test-decisions.md](resources/rubrics/stress-test-decisions.md)
- [resources/rubrics/blind-spots.md](resources/rubrics/blind-spots.md)
- [resources/rubrics/anti-ai-slop.md](resources/rubrics/anti-ai-slop.md)
- [resources/rubrics/code-quality.md](resources/rubrics/code-quality.md)
- [resources/rubrics/ml-design.md](resources/rubrics/ml-design.md)
