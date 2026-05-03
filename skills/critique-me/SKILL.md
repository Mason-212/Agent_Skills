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

## Rubrics (multi-select — do not assume)

Read **only** the selected files under [resources/rubrics/](resources/rubrics/) for this run. **Do not** load or run a rubric until it is **explicitly selected** (user message or reply to the menu below).

### When to skip the menu

If the user **already** specifies rubrics in their message (ids, names, or numbers—e.g. `Rubrics: 1,3`, `stress-test and anti-ai-slop`, `all rubrics`, `1–5`, `6`), use that set and proceed.

### Multi-select menu (show when rubrics are not already specified)

Present **once** before reading rubric files:

| # | Id | Menu label |
|---|-----|------------|
| 1 | `stress-test-decisions` | Stress-test decisions |
| 2 | `blind-spots` | Blind spots and coverage |
| 3 | `anti-ai-slop` | Anti–AI slop (substance / value density) |
| 4 | `code-quality` | Code quality |
| 5 | `ml-design` | ML design |
| **6** | *(all)* | **All rubrics (1–5)** — same as selecting every row above |

**Shortcuts (equivalent to choosing 6):** `Rubrics: all`, `Rubrics: 1-5`, `Rubrics: 1–5` (en dash), or `Rubrics: 6`.

**Other shortcuts:** “**Truth and evidence**” = **1 + 2** only (not all rubrics).

**Reply format (plain chat):** `Rubrics: 1,2,3` or `Rubrics: 2,4` or `Rubrics: all`. User may pick **any non-empty subset** of **1–5**, or **6 / all** for the full set.

**AskQuestion:** When the tool is available, use **one** multi-select question listing options **1–6** with `allow_multiple: true`. Selecting **6** should mean “include all of 1–5” (if the UI cannot express that, treat a dedicated “All (1–5)” option as selecting 1–5).

**Suggested copy in the prompt (optional hint to the user):** “Typical first pass: `Rubrics: 1,2,3` or `Rubrics: all` for everything including code and ML lenses.”

**After selection:** If **4** is included but there is **no code** in the artifact set, **warn** and either drop **4** or ask for a code path/snippet before critiquing.

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
2. **Resolve rubrics:** if the user already listed them in the message → use that set. **Otherwise** show the **multi-select menu (§ Rubrics)** and **stop until they reply** with `Rubrics: …` (or AskQuestion answers mapped to numbers). **Do not** silently apply all rubrics or auto-add 4/5 without user selection—except the user chose **6** / **all** / **1–5**.
3. If **artifact** still ambiguous, one follow-up (see § Artifacts).
4. **Validate:** if **code-quality** (4) is in the set but there is no code in scope, warn—drop 4 or ask for a path/snippet.
5. **Read** each selected `resources/rubrics/<id>.md` (ids **1–5** only; **6** expands to all five files).
6. **Read** artifact corpus (files / dirs within caps; thread content as given).
7. **Deliver** the critique using the output format below. Be direct; no filler.

## Output format

Use these sections **in order**. Omit rubric sections that were not selected. **Section order matches rubric numbers 1–5.**

1. **Framing** — Goal, constraints, **rubrics used** (numbers or ids; note if **6 / all**), **artifacts** (conversation and/or paths read; note if caps applied).
2. **Stress-test decisions** — if **1** selected.
3. **Blind spots and coverage** — if **2** selected.
4. **Anti–AI slop** — if **3** selected.
5. **Code quality** — if **4** selected; else omit (or one line “N/A”).
6. **ML design** — if **5** selected.
7. **Recommendations** — numbered, smallest valuable change first; tag **must-fix** vs **later** when useful.

**Per finding:** **claim → why it matters → evidence** (quote or `path:line`). **Primary rubric** per finding: assertions under stress-test; silences under blind spots; hollow density under anti–AI slop; at most one “see also” to another rubric.

**Rules:** Do not invent problems. Tie every point to observable text or code. If the work is sound, say so briefly and list only high-value risks or open questions.

## Rubric file map

- [resources/rubrics/stress-test-decisions.md](resources/rubrics/stress-test-decisions.md)
- [resources/rubrics/blind-spots.md](resources/rubrics/blind-spots.md)
- [resources/rubrics/anti-ai-slop.md](resources/rubrics/anti-ai-slop.md)
- [resources/rubrics/code-quality.md](resources/rubrics/code-quality.md)
- [resources/rubrics/ml-design.md](resources/rubrics/ml-design.md)
