---
name: learn-from-github-collection
description: >-
  Study doc from link file; harness takeaways. learn-from-github-collection
---

# Learn from GitHub collection

## When to Use

- The user invokes **learn-from-github-collection** or wants a **structured study Markdown** built from a **file of curated links** (README section, link list, etc.)
- The user points at a collection and wants **per-article `##` sections**, **what it is / why it matters**, and **five harness takeaways** per link

## Operating Procedure

1. **Require the collection file path.** Do not start until the user provides the **path to the file** that contains the collection links (and any section context or primitive grouping notes). If they omit it, ask once for the path. Read that file with the Read tool.

2. **Require the output file path.** Ask which **single Markdown file** to create or append to (e.g. `learning-designprimitives.md`). Do not write study content to any other path.

3. **Read the full specification.** Open and follow [resources/study-document-spec.md](resources/study-document-spec.md) exactly for structure, tone, numbering, and output discipline.

4. **Extract work items.** From the collection file, derive the list of URLs (and any per-link titles or editorial notes the file provides). Respect README hierarchy if it groups links under primitives—use that to choose **Option A vs Option B** numbering and to assign major/minor section numbers consistently.

5. **Process each link.** For each URL: fetch and read the source when possible (use web fetch or repo-local resolution if the link is relative to a GitHub repo the user has open). Apply the spec: critical read, one `##` per article, the two short blocks, five numbered takeaways with concrete artifacts and optional ASCII or pseudo-flow.

6. **Write output once.** Produce the complete document (or the new appended portion, if the user asked to append) in the **named output file only**. Use a single top-level `#` title if using Option B; follow Option A if using primitive intros. Keep numbering stable across the run.

7. **Failures.** If a link cannot be fetched, follow the spec: brief note, lean on editorial context from the collection file, still emit the `##` section so numbering stays iterable.

## Notes

- **Harness engineering** means agent/skill/prompt/tooling/eval/ops concerns—not generic AI hype.
- Prefer one pass per link so the output file stays coherent; if the document is very large, confirm with the user before splitting work across turns.
