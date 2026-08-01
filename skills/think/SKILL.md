---
name: think
description: Apply a structured reasoning framework to complex questions, statements, decisions, and planning tasks by building, validating, and applying mental models.
---

# Reasoning Framework Skill

## When to Use

Use this skill when:
- The user asks a complex question requiring structured analysis
- A decision has multiple approaches with significant trade-offs
- You need to build and validate a mental model before answering
- The user wants understanding, not just facts
- The stakes are high and assumptions must be made explicit
- A compressed statement or principle needs stress testing

Do not use for:
- Simple factual queries
- Straightforward implementation tasks
- Questions with obvious single answers

## Purpose

Apply the Reasoning Framework to complex questions, statements, decisions, and planning tasks.

This skill helps you construct, validate, and apply robust internal structures (mental models) that:
- Explain observations
- Predict outcomes
- Guide decisions
- Transfer across situations

## Instructions

The framework provides **principles and tools** for rigorous reasoning, not a rigid procedure. Apply judgment about what's needed.

### Core Principles (Always Apply)

1. **Structure-first reasoning**: Build mental models that explain mechanisms, not just list facts
2. **Reality-based calibration**: Test structures against evidence and counterexamples
3. **Earned simplicity**: Compress only after validation
4. **Explicit scope**: Define where reasoning applies and where it doesn't
5. **Separate facts from interpretation**: Surface assumptions

### Available Tools (Use as Needed)

**Framework documentation** (`docs/`):
- `framework.md` - Core concepts and terminology
- `principles.md` - Evolution of the approach
- `quality.md` - What excellence looks like
- `dag-spec.md` - Formal reasoning pipeline (if you need structure)

**Domain-specific operational guidance** (`extensions/domains/`):
- Verification methods (how to check claims with code/data)
- Counterfactual patterns (how to stress-test reasoning)
- Quality indicators (what excellence looks like in specific domains)
- Failure modes (red flags to watch for)

**Evaluation examples** (`evals/`):
- Worked examples showing the principles in action

### When to Go Deep vs Stay Light

**Go deep when**:
- Stakes are high (major decision, significant investment, irreversible action)
- Multiple valid approaches exist with real trade-offs
- Assumptions are hidden or unclear
- The user explicitly wants structured analysis
- Domain has specialized operational guidance available

**Stay light when**:
- Query is straightforward with obvious answer
- Stakes are low
- User wants quick guidance, not exhaustive analysis
- Your natural reasoning is already sound

### Adaptive Approach for Investing Domain

When you detect an investing question:

1. **Read wiki-finance** to understand available approaches (Value, Growth, Passive, Momentum, Macro)
2. **Have a conversation** to understand context (not interrogate with checklist):
   - What's the situation? (market conditions, time horizon, goals)
   - What approach makes sense given their context?
   - How much depth do they want?
3. **Load relevant operational guidance** if needed:
   - `extensions/domains/investing/README.md` - Framework-agnostic patterns
   - `extensions/domains/investing/{approach}.md` - Approach-specific procedures
4. **Use the tools that fit**:
   - High-stakes concentrated bet → Full four-lens scan with verification
   - Quick sanity check → Apply failure modes and red flags only
   - Portfolio allocation question → Different framework entirely

**Key**: The operational guidance is a **toolbox**, not a **script**. Use what's needed for the situation.

## Key Framework Concepts

These concepts support the principles above. Reference when needed:

### Structure
A mental model representing how something works:
- Entities and variables
- Relationships and mechanisms
- Assumptions and constraints
- Predictions

### Evaluation Approaches
1. **Validation**: Does this explain observations and predict outcomes?
2. **Counterexamples**: Three types:
   - Missing variable → Refine the model
   - Contradiction → Replace the model
   - Boundary → Narrow the scope
3. **Scope Analysis**: Where does/doesn't this apply?

### Distillation vs Expansion
- **Distillation**: Remove complexity while preserving reasoning capability
- **Expansion**: Recover hidden assumptions when stakes require it

### Output Types
- **Understanding**: Structure, mechanisms, assumptions, limitations
- **Action**: Options, tradeoffs, risks, recommendations, monitoring signals

## Quality Criteria

Good reasoning demonstrates:
- **Structure over facts**: Builds models that explain mechanisms, not just lists information
- **Reality-tested**: Tests structures against evidence and counterexamples
- **Explicit assumptions**: Makes hidden assumptions visible
- **Bounded scope**: Defines where reasoning applies and where it breaks
- **Adaptive rigor**: Goes deep when stakes are high, stays light when appropriate

**Not** about following procedures perfectly. It's about producing sound reasoning that helps the user understand or decide well.

## Transparency Without Overnarration

**Be explicit about**:
- **Approach**: Which framework/lens you're using and why it fits
  - Good: "I'll analyze this as a Growth investment through the four-lens framework since you're looking at structural bottlenecks"
  - Bad: "Now I'm reading the framework documentation and will apply steps 1-7"
  
- **Key assumptions**: Surface critical assumptions that could break
  - Good: "This assumes hyperscaler CapEx continues growing ~20% annually"
  - Bad: "I'm now applying assumption validation from section 3.2.1"

- **Scope boundaries**: Where reasoning applies and where it doesn't
  - Good: "This framework works best for 3-5 year structural themes, less useful for short-term trading"
  - Bad: "According to the scope analysis criteria in Pattern C"

- **Limitations**: What you don't know or can't verify
  - Good: "I can't verify the qualification cycle duration without industry-specific sources"
  - Bad: "Per the validation checklist, item 4 is incomplete"

**Stay quiet about**:
- Reading documentation or loading extensions
- Which internal tools/patterns you're applying
- Step numbers or procedure names
- Mechanical aspects of the framework

**Format for clean transparency**:
- Use section headers that signal structure naturally ("Evidence", "Risks", "When This Fails")
- Lead with "Here's my approach: ..." when approach choice matters
- Embed assumptions and limitations naturally in the flow
- Show your reasoning path through clear structure, not narration

## Examples

See `evals/` directory for worked examples:
- `ai_education.md` - AI and education analysis
- `investing.md` - Investment decision framework
- `switzerland.md` - Switzerland success analysis

## Domain-Specific Extensions

The `extensions/domains/` directory contains operational guidance for applying the framework rigorously in specific domains.

**Available domains**:
- `investing/` - Equity investing with framework-agnostic patterns and approach-specific procedures (Growth, Value, Momentum, Passive, Macro)

**When to use**: Load domain extensions when you detect the query falls into a calibrated domain. The extensions provide:
- Verification methods (how to check claims with code/data)
- Counterfactual patterns (how to stress-test reasoning)
- Quality indicators (what excellence looks like in this domain)
- Failure modes (red flags to watch for)

**Integration**: Domain extensions augment the universal framework with domain-specific rigor. Use them when the situation warrants - they're tools to enhance reasoning, not requirements to follow mechanically.
