---
name: summarize-chat
description: Summarize a long chat into a clean handoff for a fresh thread.
---

# Summarize Chat

## When to use

- The user asks for a summary they can paste into a new chat or fresh thread.
- The conversation is long and the user wants to keep only the durable source of truth.
- The user says `summarize_chat`, "summarize chat", "handoff summary", "fresh thread", or similar.

## Goal

Produce a concise, paste-ready handoff that preserves progress, key decisions, and exact next steps without carrying over the full troubleshooting history.

## Instructions

1. Read the relevant conversation and infer the current state of the work.
2. Keep only durable information:
   - completed work and verified outcomes
   - key code, concepts, decisions, and constraints established
   - important files, symbols, commands, APIs, or errors that still matter
   - the exact next steps needed to continue
3. Exclude noise:
   - redundant back-and-forth
   - dead ends unless they explain a current constraint
   - apologies, filler, and other meta commentary
4. If something is uncertain, label it clearly as an open question instead of presenting it as settled.
5. Prefer concrete references over vague summaries. Name files, branches, commands, env vars, or TODOs when they are important for continuation.
6. Do not invent progress. If little was completed, say so and summarize the blocker or remaining task directly.
7. If the user provides exact wording they want preserved, keep it verbatim.
8. End with a compact block the user can paste into a new thread immediately.

## Output format

Use this structure and omit empty sections:

```markdown
## Progress
- ...

## Source of truth
- ...

## Important context
- ...

## Open questions
- ...

## Next steps
1. ...
2. ...

## Paste into a new thread
Here is the context of what I've built/learned so far:
[Paste a compact version of the summary above.]

Let's pick up on step [N].
```

## Style rules

- Keep the summary compact and scannable.
- Optimize for continuity, not completeness.
- Preserve the user's terminology for project-specific concepts.
- Include only details that help the next thread start productively.
