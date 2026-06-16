## Coding

Use this overlay for implementation, debugging, refactoring, code review assistance, tests, and structured code generation.

## Domain Signals

- the user wants code written, changed, explained, or debugged
- a repo, file, stack trace, API, schema, or test suite is in scope
- the output may need exact syntax, exact edits, or structured patches

## Decision Lenses

| Coding lens | What to evaluate | Critical failure state | Model tendency |
|---|---|---|---|
| `codebase-scope` | whether the task touches one file, several files, or a large repo | the model solves only the local symptom and misses surrounding dependencies | broader scope pushes toward stronger repo-aware models |
| `debugging-ambiguity` | how much root-cause reasoning is needed | the model patches surface errors without identifying the true cause | high ambiguity pushes toward stronger reasoning models |
| `change-breadth` | whether this is a tiny edit, a feature, or a refactor | the model updates one part but leaves interfaces inconsistent | broad changes push toward stronger multi-file performers |
| `output-rigidity` | how exact the output must be | malformed JSON, invalid syntax, broken patches, wrong schema | rigid contracts favor models dependable on structured output |
| `iteration-speed` | whether the user wants many quick loops | the model is good but too slow or costly for repeated tries | high iteration pressure favors faster and cheaper models |

## Good Follow-up Questions

- "Is this a single-file change, or does it touch multiple files and interfaces?"
- "Do you need deep debugging, or mostly straightforward implementation?"
- "Does the output need strict JSON, exact patches, or another hard contract?"
- "Is this a quick iteration loop or a high-stakes change where reliability matters more than speed?"

## Recommendation Tendencies

- For broad repo work, tricky refactors, or ambiguous debugging, prefer the strongest reasoning and multi-file coding models available.
- For everyday coding, UI work, API wiring, and fast iteration, prefer the fastest strong coding model that is still reliable.
- For extraction, schema transforms, codegen with strict JSON, or typed contracts, prefer models that are dependable on structured output.
- If the task is small and repeated many times, bias toward `balanced` or `minimize-latency` rather than always choosing the biggest model.

## Provider-Specific Hints

Treat these as tendencies, not absolute rankings:

- `Claude Fable 5` or `Claude Opus 4.8`: strongest fit when reasoning depth and multi-file consistency dominate
- `Claude Sonnet 4.6`: strong default for daily coding with better speed-value balance
- `GPT-5.5`: strong option when strict structured output or schema fidelity dominates
- `Gemini 3.1 Pro`: useful when coding work is coupled to very large context ingestion
