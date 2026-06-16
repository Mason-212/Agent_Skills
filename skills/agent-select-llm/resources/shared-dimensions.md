## Shared Decision Lenses

Use these lenses for every recommendation, regardless of domain. Treat them as the base routing rubric.

| Lens | What to evaluate | High-signal indicators | Typical recommendation effect |
|---|---|---|---|
| `reasoning-depth` | How much multi-step reasoning the task needs | long chains of logic, ambiguous debugging, simulation, synthesis, trade-off analysis | pushes toward stronger reasoning models |
| `context-load` | How much material the model must hold at once | long docs, many files, large repos, many options to compare | pushes toward stronger long-context models |
| `constraint-strictness` | How strictly the model must follow rules or policies | compliance, tax rules, rigid instructions, narrow acceptance criteria | favors models that are less likely to improvise |
| `output-contract` | How exact the output format must be | strict JSON, typed tables, code-only edits, reusable schemas | favors models that are dependable on structured output |
| `execution-scope` | How broad the task is operationally | single answer, single-file edit, multi-file refactor, long agent loop | favors models with stronger repo and agentic performance |
| `latency-sensitivity` | How much fast iteration matters | brainstorming, quick drafting, chatty back-and-forth, low stakes | favors faster and cheaper models |
| `budget-sensitivity` | How much usage cost matters | high-volume usage, repeated runs, exploratory work | favors lower-cost models |
| `task-criticality` | How expensive subtle mistakes would be | production changes, finance math, compliance, customer-facing decisions | favors more reliable models and more caveats |
| `availability` | What the user can actually use right now | current provider access, rate limits, throttling, allowed tools | narrows the candidate set before ranking |

## Optimization Modes

Infer the user's goal, then optimize accordingly:

- `maximize-performance`: best model for quality and reliability, cost secondary
- `minimize-cost`: cheapest model that is still fit for purpose
- `minimize-latency`: fastest strong-enough model for tight iteration loops
- `balanced`: strongest value across quality, speed, and cost

If the goal is not explicit, default to `balanced` for low-stakes work and `maximize-performance` for high-consequence work.

## How To Infer Missing Inputs

Prefer inference over extra questions.

Infer from:

- the user's wording
- the current repo or files in scope
- whether the task is planning, coding, extraction, research, or agentic execution
- whether the user is asking for one-shot output or repeated interactive help

Ask follow-up questions only when a missing input would materially change the recommendation.

## Follow-up Question Rules

- Ask at most 2-4 questions.
- Ask only high-leverage questions.
- Prefer multi-purpose questions like:
  - "Do you care more about top quality, speed, or cost?"
  - "How much material does the model need to read at once?"
  - "Does this need strict output like JSON or precise code changes?"
  - "Is this a high-consequence task where a subtle mistake is expensive?"
- Skip questions whose answer is already obvious from context.

## Recommendation Format

Use this format by default:

```markdown
Primary model: [model]

Why:
- [reason 1]
- [reason 2]
- [reason 3]

Fallback for speed/cost: [model] — [one sentence]
Fallback for max capability: [model] — [one sentence, if meaningfully different]

Decision lenses:
- reasoning-depth: low|medium|high
- context-load: low|medium|high
- constraint-strictness: low|medium|high
- output-contract: low|medium|high
- execution-scope: narrow|medium|broad
- latency-sensitivity: low|medium|high
- budget-sensitivity: low|medium|high
- task-criticality: low|medium|high

Open uncertainty: [only include when an unknown could change the answer]
```

## Important Constraints

- Do not pretend you know the user's available models if that was not established.
- If the provider or model list is unclear, ask once or state assumptions explicitly.
- Prefer capability-based reasoning over benchmark lore.
- Avoid absolute claims like "best model overall." Recommend for this task shape.
- If the task spans multiple domains, combine the shared rubric with the two most relevant domain overlays.
