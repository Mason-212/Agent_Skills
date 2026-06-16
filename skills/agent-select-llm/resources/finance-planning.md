## Finance Planning

Use this overlay for retirement models, stock research workflows, portfolio planning, tax-aware scenarios, financial engines, and related analytical planning.

This overlay adapts the capability framing from the user's finance notes without turning those notes into a fixed global ranking.

## Domain Signals

- the task includes projections, scenarios, or compounding over time
- tax, regulatory, or compliance-like rules matter
- filings, transcripts, statements, or large evidence sets are in scope
- subtle errors could materially change conclusions

## Decision Lenses

| Finance lens | What to evaluate | Critical failure state | Model tendency |
|---|---|---|---|
| `temporal-math` | long-horizon state tracking and iterative finance logic | a small early error compounds into a major long-run mistake | high temporal load pushes toward stronger reasoning models |
| `evidence-retrieval` | ability to hold and search dense financial context | the model misses a buried footnote, caveat, or disclosure | large evidence sets push toward stronger long-context models |
| `rule-fidelity` | strictness around tax, legal, and policy constraints | the model invents an exemption or applies the wrong rule | rigid constraints favor less improvisational models |
| `structured-integrity` | accuracy of tables, JSON, formulas, and handoff formats | malformed output breaks downstream analysis or code | structured workflows favor dependable schema output |
| `decision-consequence` | how costly a subtle mistake would be | a plausible but wrong answer drives a major financial decision | higher consequence pushes toward stronger models and more caveats |

## Good Follow-up Questions

- "Does this involve multi-step projections, compounding, or tax logic over time?"
- "How much source material needs to be read at once: one document, several filings, or a larger corpus?"
- "Do you need strict structured output, or mainly a reasoning partner?"
- "Is this exploratory analysis, or a high-consequence task where subtle mistakes are expensive?"

## Recommendation Tendencies

- For high-consequence financial planning, bias toward maximum reasoning quality and rule fidelity.
- For dense filing review or large evidence ingestion, prioritize long-context reliability.
- For structured pipelines, prefer models that are dependable with tables, JSON, and typed outputs.
- For exploratory research and idea generation, balanced models are often enough unless the math or compliance burden is heavy.

## Provider-Specific Hints

Treat these as tendencies, not absolute rankings:

- `Claude Fable 5`: strongest fit when temporal reasoning and high-consequence analytical rigor dominate
- `Claude Opus 4.8`: strong fit when rule fidelity and heavy reasoning matter, especially if the task also touches implementation
- `Claude Sonnet 4.6`: strong fit for daily finance research and long-context document analysis
- `GPT-5.5`: strong fit when structured output integrity and exact machine-readable formats dominate
- `Gemini 3.1 Pro`: strong fit when the task is primarily about holding and searching extremely large evidence sets
