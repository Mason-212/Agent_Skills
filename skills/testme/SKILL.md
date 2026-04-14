---
name: testme
description: >-
  Bloom drill on a file (testme): one question at a time, critique, missed summary.
---

# Testme (Bloom taxonomy drill)

## When to Use

- The user asks for **testme**, a **Bloom** quiz, **active recall**, or a **drill** on a file they will provide
- The user wants questions at specific cognitive levels on material in a path or pasted content

## Bloom’s Revised Taxonomy (2001) — lens for the source

Use these levels to **interpret** the file and to **design** questions. Match each question to **one** primary level.

| Level | Focus | Example prompts (patterns, not scripts) |
|-------|--------|-------------------------------------------|
| **Remember** | Recall facts, terms, lists, definitions | What is…? Who…? When…? List…? |
| **Understand** | Explain meaning in own words; summarize; compare | Explain why… in plain terms; what does X mean here? |
| **Apply** | Use ideas in a new concrete situation | Given scenario Y, how would you apply X? |
| **Analyze** | Break into parts; infer structure, assumptions, cause/effect | What are the main components or dependencies? What trade-off is implied? |
| **Evaluate** | Judge against criteria; critique; prioritize | What is the strongest weakness? What would you change first and why? |
| **Create** | Produce something new (outline, design, alternative) | Propose a different structure or API; draft a minimal counter-example |

If the file is thin at some levels (e.g., no room for **Create**), say so briefly and favor levels that fit the content.

## Operating Procedure

1. **Obtain the source.** Ask for a **file path** (preferred) or pasted text. Read the file with the Read tool (or accept paste in chat). If the file is huge, agree on a **section** or **line range** before drilling.

2. **Understand the file through Bloom.** Silently organize what a learner should be able to do at each level (facts, explanations, applications, analyses, judgments, novel outputs). Do not dump this map unless the user asks.

3. **Choose levels.** Ask which level(s) to include: **Remember**, **Understand**, **Apply**, **Analyze**, **Evaluate**, **Create** — one or more. Confirm any **difficulty** or **topic focus** only if needed.

4. **One question at a time.** Ask exactly **one** clear question, tagged with its Bloom level (e.g., `**Analyze:** …`). Wait for the user’s answer before continuing.

5. **Critique each answer.** After every response:
   - Say what was **correct** or partially correct
   - Give **corrections** and the **preferred** or **complete** answer grounded in the file
   - Keep feedback proportional to the mistake

6. **Track misses.** Maintain a private running list of items where the user was **materially wrong or clearly incomplete** after your critique:
   - Bloom level
   - Your question
   - User’s answer (short paraphrase if long)
   - Key correction (bullets)

7. **Continue until stop.** After each round, invite the next question. If the user says **stop**, **end**, **done**, or equivalent, **do not** ask another question.

8. **Closing summary.** When the session ends, output a **Missteps summary**: only the missed Q/A items from step 6. If there were none, say so briefly. Optionally add one line on **what to restudy** in the file (sections or concepts), without re-quizzing.

## Style

- Questions should be **answerable from the file** (or from reasonable inferences the file supports); if you need an assumption, state it.
- Do not reveal answers before the user attempts the question.
- Stay neutral and constructive in critique.
