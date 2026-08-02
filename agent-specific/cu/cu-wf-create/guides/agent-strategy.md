# Agent Strategy

When to create custom agents vs reuse generic agents.

## Default: Custom Agents Per Workflow

cu-wf-create generates custom agents by default because:

1. **Domain-specific systemPrompts** — Each workflow needs tailored instructions
2. **Tool requirements vary** — Different workflows need different tool sets
3. **Self-contained workflows** — Portable, self-documenting

## Agent Naming Convention

**Pattern:** `<workflow-slug>_<role>`

**Examples:**
- `branch-quality-check_analyzer`
- `branch-quality-check_reporter`
- `test-fixer_detector`
- `test-fixer_fixer`
- `test-fixer_verifier`

## Common Roles

- `_analyzer` — Analyzes/checks (read-only)
- `_fixer` — Repairs issues (writes code)
- `_reporter` — Writes reports/documentation
- `_verifier` — Validates prior work
- `_coordinator` — Orchestrates sub-tasks
- `_fetcher` — Retrieves data (API calls)
- `_processor` — Transforms data
- `_notifier` — Sends notifications

## Agent YAML Template

```yaml
name: <workflow-slug>_<role>
description: <What this agent does>
archetype: <developer|reviewer|writer|other>
model: <sonnet|opus|haiku>

systemPrompt: |
  <Detailed instructions for this agent>
  
  <What to do>
  <What to output>
  <How to handle errors>

allowedTools:
  - Bash
  - Read
  - Write
  - <other tools>

outputs:
  <output-name>:
    description: <What this output contains>
    required: true
    kind: <json|string|file>
```

## Tool Selection by Role

**Analyzer (read-only):**
- Bash (run tests/lint)
- Read
- Grep

**Fixer (writes code):**
- Bash
- Read
- Edit
- Write

**Reporter (writes docs):**
- Read
- Write

**Fetcher (API calls):**
- Bash (curl, gh CLI)
- Write (save data)

**Notifier (external systems):**
- Bash (slack CLI, email)
- Read (get content to send)

## Model Selection

**Analyzer/Fixer (complex logic):**
- `model: sonnet` (balance of speed and capability)
- `model: opus` (for very complex analysis)

**Reporter/Notifier (simple formatting):**
- `model: haiku` (fast, cheap)
- `model: sonnet` (if needs judgment)

## When to Ask User

If workflow seems generic (could apply to many repos), ask:

> "Should I create custom agents or reuse generic agents (executor/reviewer) with workflow-specific prompts?"

Most workflows: custom agents (recommended)
Rare cases: generic agents with inline prompts
