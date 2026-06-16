## Example 1: Everyday Coding

**User request**

> Which model should I use to add a new API endpoint and wire the frontend form to it?

**Suggested handling**

Because this is coding and likely medium scope, first infer:

- domain: `coding`
- likely goal: `balanced`
- likely execution scope: `medium`

One good follow-up:

> Is this mostly straightforward implementation, or does it touch several files and tricky business logic?

If the user says it is straightforward and they want fast iteration:

```markdown
Primary model: Claude Sonnet 4.6

Why:
- The task is coding-focused but not unusually deep or risky
- Fast iteration matters more than maximum reasoning depth
- It should handle normal API and UI wiring well without the cost of a heavier model

Fallback for speed/cost: GPT-5.5 — good if strict structured output or schema-heavy codegen matters
Fallback for max capability: Claude Opus 4.8 — use if the work expands into a broader refactor

Decision lenses:
- reasoning-depth: medium
- context-load: medium
- constraint-strictness: medium
- output-contract: medium
- execution-scope: medium
- latency-sensitivity: high
- budget-sensitivity: medium
- task-criticality: medium
```

## Example 2: Agentic Repo Refactor

**User request**

> I want to use Cursor Agent to refactor a repo-wide auth flow across backend, middleware, and UI. Which model should I pick?

**Suggested handling**

Infer:

- domain: `agentic-work` plus `coding`
- likely goal: `maximize-performance`
- execution scope: `broad`

One good follow-up:

> Is this a high-stakes refactor where a missed dependency is expensive, or are you okay with a faster workhorse and more review?

If the user says missed dependencies are expensive:

```markdown
Primary model: Claude Fable 5

Why:
- The task is broad, cross-file, and dependency-heavy
- Long-horizon state retention matters across planning, edits, and verification
- A missed dependency in auth flow changes is expensive

Fallback for speed/cost: Claude Sonnet 4.6 — use if you need a cheaper workhorse and can review more aggressively
Fallback for max capability: Claude Opus 4.8 — also a strong fit for heavy multi-file agentic implementation

Decision lenses:
- reasoning-depth: high
- context-load: high
- constraint-strictness: high
- output-contract: medium
- execution-scope: broad
- latency-sensitivity: low
- budget-sensitivity: low
- task-criticality: high
```

## Example 3: Finance Planning

**User request**

> I need a model for retirement planning scenarios with taxes, Roth conversions, and 30-year projections. I care more about being right than being cheap.

**Suggested handling**

Infer:

- domain: `finance-planning`
- goal: `maximize-performance`
- temporal math and rule fidelity: `high`

Minimal follow-up:

> Will the model also need to read lots of filings or source material, or is the main challenge the long-horizon planning logic itself?

If the user says the main challenge is the multi-step planning logic:

```markdown
Primary model: Claude Fable 5

Why:
- The task has high temporal reasoning load across long projections
- Tax-aware logic raises constraint strictness and consequence of subtle mistakes
- You explicitly care more about analytical quality than cost

Fallback for speed/cost: Claude Sonnet 4.6 — acceptable for lighter exploratory finance work
Fallback for max capability: Claude Opus 4.8 — strong alternative when the task also includes implementation or stricter policy-heavy reasoning

Decision lenses:
- reasoning-depth: high
- context-load: medium
- constraint-strictness: high
- output-contract: medium
- execution-scope: medium
- latency-sensitivity: low
- budget-sensitivity: low
- task-criticality: high
```

## Example 4: Trip Planning

**User request**

> Help me pick a model for planning a 10-day Japan trip for two people with a budget cap, two cities, and a moderate pace.

**Suggested handling**

Infer:

- domain: `trip-planning`
- likely goal: `balanced`
- constraint blending: `medium` to `high`

One good follow-up:

> Do you mainly want a polished itinerary fast, or a deeper optimization pass across lots of options and trade-offs?

If the user wants a polished answer fast:

```markdown
Primary model: Claude Sonnet 4.6

Why:
- The task has multiple constraints, but not enough complexity to require the heaviest model by default
- Speed and answer quality both matter for itinerary iteration
- A balanced fast model is usually the best value for trip planning

Fallback for speed/cost: GPT-5.5 — reasonable when the output format matters more than deep synthesis
Fallback for max capability: Claude Fable 5 — use if the itinerary becomes unusually optimization-heavy

Decision lenses:
- reasoning-depth: medium
- context-load: medium
- constraint-strictness: medium
- output-contract: low
- execution-scope: medium
- latency-sensitivity: high
- budget-sensitivity: medium
- task-criticality: low

Open uncertainty: If the plan depends on live schedules or pricing, browsing and source verification matter more than model choice alone.
```
