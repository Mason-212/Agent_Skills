---
name: agent-select-llm
description: Recommend the best available LLM for a task using domain-specific lenses and speed/cost/quality trade-offs. Use when the user asks which model to use, wants help picking a model, or describes a task with model trade-offs.
---

# Agent Select LLM

## When to Use

- The user asks which LLM or model they should use
- The user wants to choose between models for coding, agents, finance planning, trip planning, research, extraction, or similar tasks
- The user describes a task where trade-offs between quality, speed, context, and cost matter
- The user wants a primary recommendation plus practical fallbacks

## When Not to Use

- The user already named the exact model they want and is not asking for alternatives
- The task is really about prompt design, not model choice
- The user needs live benchmark validation or vendor pricing that is not already available in context

## Operating Principle

Do not recommend a model from generic reputation alone.

Route the decision through:

1. the task domain
2. the task shape
3. the user's optimization goal
4. the models the user can actually access

Use the shared rubric in [resources/shared-dimensions.md](resources/shared-dimensions.md) for every run. Then load the most relevant domain file:

- [resources/coding.md](resources/coding.md)
- [resources/agentic-work.md](resources/agentic-work.md)
- [resources/finance-planning.md](resources/finance-planning.md)
- [resources/trip-planning.md](resources/trip-planning.md)

If the task spans domains, combine at most two domain overlays plus the shared rubric.

## Selection Workflow

### 1. Detect the domain

Classify the request into the closest domain:

- `coding`
- `agentic-work`
- `finance-planning`
- `trip-planning`
- `mixed` or `unknown`

Infer the domain from the user's request, files in scope, repo context, and requested output.

### 2. Detect the task shape

Identify whether the user needs:

- quick chat or brainstorming
- document analysis
- structured extraction
- single-file coding
- multi-file or repo-aware work
- long-horizon agentic execution

This often matters as much as domain.

### 3. Infer the optimization goal

Resolve the user's goal into one of:

- `maximize-performance`
- `minimize-cost`
- `minimize-latency`
- `balanced`

If the user did not say, infer from the task:

- high-consequence work defaults toward `maximize-performance`
- iterative everyday work defaults toward `balanced`

### 4. Determine what is already known

Before asking questions, infer:

- available providers or model families
- whether long context is needed
- whether strict output is required
- whether subtle mistakes are expensive
- whether the task is broad and agentic or narrow and local

### 5. Ask only high-impact follow-ups

Ask at most 2-4 questions, only when missing information could change the result.

Good follow-ups:

- "Do you care more about top quality, speed, or cost?"
- "How much material does the model need to read at once?"
- "Does this require strict JSON, exact code edits, or another hard output contract?"
- "Is this a high-consequence task where a subtle error is expensive?"

Do not ask questions just to restate what is already obvious.

### 6. Apply the relevant overlay

Read the matching domain file and map the task to its domain lenses:

- coding: [resources/coding.md](resources/coding.md)
- agentic repo work: [resources/agentic-work.md](resources/agentic-work.md)
- finance planning: [resources/finance-planning.md](resources/finance-planning.md)
- trip planning: [resources/trip-planning.md](resources/trip-planning.md)

If the domain is `mixed`, use the two best-fitting overlays.

If the domain is `unknown`, stay with the shared rubric and say that the answer is based on general task shape rather than a domain-specific policy.

### 7. Recommend one primary model and fallbacks

Give:

- one primary recommendation
- one faster or cheaper fallback
- one stronger fallback when it is meaningfully different

Keep the rationale brief and tied to the task, not to broad benchmark mythology.

## Recommendation Format

Follow the format in [resources/shared-dimensions.md](resources/shared-dimensions.md).

By default:

```markdown
Primary model: [model]

Why:
- [task-specific reason]
- [task-specific reason]
- [task-specific reason]

Fallback for speed/cost: [model] — [one sentence]
Fallback for max capability: [model] — [one sentence, if useful]

Decision lenses:
- reasoning-depth: ...
- context-load: ...
- constraint-strictness: ...
- output-contract: ...
- execution-scope: ...
- latency-sensitivity: ...
- budget-sensitivity: ...
- task-criticality: ...

Open uncertainty: [only if needed]
```

## Important Constraints

- Recommend only from models the user can plausibly access, or state assumptions clearly.
- Do not claim universal rankings. Recommend for the current task shape.
- Prefer domain capability language over stale benchmark references.
- If model availability is unknown, say what assumption you are making.
- If the trade-off is close, say why two models are both reasonable.
- If the user wants a quick answer, give the recommendation first and keep the rest short.

## Examples

For worked examples, see [examples.md](examples.md).
