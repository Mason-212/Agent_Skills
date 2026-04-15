# Study document generation (authoritative prompt)

The agent must follow this specification when building the Markdown study document from the link collection file.

---

You are helping me build a structured study document (Markdown) from a curated list of links (e.g. a "Design Primitives" section in a README).

For each link, do the following:

1. Read the linked source critically  
   Skim for claims, constraints, and failure modes—not a generic summary. If you cannot fetch the page, say so briefly and lean on the list’s editorial note only where needed.

2. One second-level Markdown section per article  
   Use a single `##` heading for each resource, with:
   - Incremental hierarchical numbering in the title, e.g. `## 3.0` for a primitive overview (optional) and `## 3.1`, `## 3.2`, … for articles in that group (same major digit as the primitive, minor increments per article).
   - A succinct human-readable title after the number.
   - The article URL in the heading as a Markdown link, e.g.  
     `## 3.2 [Short title](https://example.com/article)`.

   Outline convention (pick one and stick to it):
   - Option A (flat under doc): `## 1.0 Agent Loop` (one short intro for the primitive), then `## 1.1 …`, `## 1.2 …` for each link in that primitive.
   - Option B (no primitive intro): Start articles at `## 2.1`, `## 2.2`, … after a single doc-level `#` title.

3. Under that `##`, add two short blocks
   - What it is: 2–4 sentences on what the piece actually covers.
   - Why it matters: 1–3 sentences on why it matters for harness engineering (reliability, safety, cost, velocity, debuggability)—not "why AI is important."

4. Five actionable takeaways  
   Number them `1.`–`5.`. For each takeaway:
   - State what to do or what to decide in your harness.
   - Tie it to a concrete artifact (schema, hook, eval, metric, ADR, CI check).
   - Where it helps, add a small text diagram (ASCII or box drawing) or a tight pseudo-flow so the idea is memorable without re-reading the source.

5. Output discipline
   - One `##` block per link (no duplicate headings).
   - Keep numbering stable and iterable (same scheme end-to-end).
   - Append or write to the file I name (e.g. `learning-designprimitives.md`); do not scatter content across unrelated files.
