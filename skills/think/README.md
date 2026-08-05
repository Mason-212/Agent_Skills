# Think: Reasoning Framework Skill

A structured reasoning framework for building, validating, and applying mental models to complex questions and decisions.

## What This Skill Does

The `think` skill helps AI agents move beyond simple fact retrieval to construct robust internal structures (mental models) that:

- **Explain** observations and phenomena
- **Predict** outcomes under different conditions
- **Guide** decisions with explicit tradeoffs
- **Transfer** knowledge across situations

Instead of treating answers as collections of facts, this framework treats them as expressions of underlying structures that have been validated against reality.

## When to Use This Skill

Use `think` when:
- A question requires structured analysis, not just facts
- Multiple approaches exist with significant trade-offs
- Assumptions must be made explicit
- Decision stakes are high
- A compressed principle needs validation
- The user wants understanding, not just answers

Skip this skill for:
- Simple factual queries
- Straightforward tasks with obvious solutions
- Low-stakes, single-path problems

## Core Concepts

### Structure-First Reasoning

Answers emerge from underlying structures, not fact collections:

```
Observation → Underlying Structure → Prediction/Decision/Action
```

### Three-Phase Evaluation

1. **Validation**: Does the structure explain evidence and predict outcomes?
2. **Counterexamples**: Test with three types:
   - Missing variable → Refine the model
   - Contradiction → Replace the model  
   - Boundary → Define scope
3. **Scope Analysis**: Where does/doesn't the structure apply?

### Distillation and Expansion

- **Distillation**: Compress to smallest useful form while preserving reasoning capability
- **Expansion**: Recover hidden complexity when stakes require precision

### Output Types

- **Understanding**: Structure, mechanisms, assumptions, limitations, examples
- **Action**: Options, tradeoffs, risks, recommendations, monitoring signals

## Directory Structure

```
skills/think/
├── SKILL.md                      # Main agent instructions (compression/decompression flow)
├── README.md                     # This file
├── docs/
│   ├── README.md                # Doc index — boundaries and reading order
│   ├── architecture.md          # HOW: two-layer design + plugins (START HERE for users)
│   ├── framework.md             # WHAT: concepts and terminology
│   ├── principles.md            # WHY: design evolution
│   ├── reasoning-techniques.md  # WHICH: techniques, fail-fast, logging schema
│   └── quality.md               # Taste and judgment
├── ir/
│   └── dag-spec.md              # DAG specification for reasoning process
├── test_cases/
│   ├── ai_education.md          # Example: AI and education query
│   ├── investing.md             # Example: Investment analysis
│   └── switzerland.md           # Example: Switzerland success analysis
└── quality/                      # Quality standards by domain (evaluation criteria)
    └── equity/                   # Equity investing
        └── taste.md              # Compiled evaluation criteria
```

## Quick Reference

### Core Reasoning Flow

```
Build → Validate → Test → Compress → Expand → Verify
```

Domain plugins augment each step when available. Technique details: [`docs/reasoning-techniques.md`](docs/reasoning-techniques.md).

### Key Principles

- **Simplicity must be earned** through validation
- **Reality is the calibration mechanism**, not elegance
- **Compress only after evaluation** to avoid slogans
- **Expand selectively** based on stakes and complexity
- **Separate facts from interpretation** to surface assumptions

## Documentation

**Index**: **[docs/README.md](docs/README.md)** — which doc to read for what.

| Doc | Role |
|-----|------|
| [architecture.md](docs/architecture.md) | **START HERE** (users) — plugins + two-layer design |
| [framework.md](docs/framework.md) | Concepts, terminology, counterexample types |
| [principles.md](docs/principles.md) | Why the framework evolved |
| [reasoning-techniques.md](docs/reasoning-techniques.md) | Techniques per step, fail-fast, logging |
| [quality.md](docs/quality.md) | Taste and judgment |
| [learning-to-do.md](docs/learning-to-do.md) | Execution gaps and fixes |
| [ir/dag-spec.md](ir/dag-spec.md) | Formal pipeline contracts |

## Evaluation Examples

- **[test_cases/ai_education.md](test_cases/ai_education.md)** - Worked example: "If AI makes everyone capable of learning faster, why will some people still outperform others?"
- **[test_cases/investing.md](test_cases/investing.md)** - Worked example: Identifying good investments with reasonable risk
- **[test_cases/switzerland.md](test_cases/switzerland.md)** - Worked example: Understanding Switzerland's success through structured analysis

## Architecture

Two-layer design (core flow + optional domain plugins): see **[docs/architecture.md](docs/architecture.md)**. Equity example plugin: `quality/equity/taste.md`.

## Philosophy

The goal is not to maximize answer generation. It is to improve the quality of reasoning that produces those answers.

> "Build, test, compress, and apply internal structures that help humans understand reality and make better decisions."
