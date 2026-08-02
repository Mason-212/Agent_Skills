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
│   ├── architecture.md          # How it works (START HERE for users)
│   ├── framework.md             # Core framework documentation
│   ├── principles.md            # Evolution and key principles
│   └── quality.md               # Quality principles (taste and judgment)
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

### Core Reasoning Flow (Compression/Decompression)

1. **Build Structure** - Create mental model that explains the domain
2. **Validate** - Test against evidence and reality
3. **Counterexamples** - Stress-test to find limitations (missing variables, contradictions, boundaries)
4. **Compress** - Distill to essential insight
5. **Expand** - Apply to user's specific context

**Domain plugins augment each step** with specialized knowledge when available.

### Key Principles

- **Simplicity must be earned** through validation
- **Reality is the calibration mechanism**, not elegance
- **Compress only after evaluation** to avoid slogans
- **Expand selectively** based on stakes and complexity
- **Separate facts from interpretation** to surface assumptions

## Documentation

- **[docs/architecture.md](docs/architecture.md)** - **START HERE**: How the skill works - compression/decompression flow and how domain plugins integrate (for users)
- **[docs/framework.md](docs/framework.md)** - Comprehensive framework specification including philosophy, terminology, evaluation methods, and reasoning principles
- **[docs/principles.md](docs/principles.md)** - Evolution of the framework from compression/decompression to full reasoning system, with stress testing methodology
- **[docs/quality.md](docs/quality.md)** - Quality principles for reasoning: taste (recognizing excellence) and judgment (decisions under uncertainty)
- **[docs/learning-to-do.md](docs/learning-to-do.md)** - Common execution gaps and how to fix them (observed failures when applying the skill)
- **[ir/dag-spec.md](ir/dag-spec.md)** - Implementation specification with node contracts, validation gates, and artifact schemas

## Evaluation Examples

- **[test_cases/ai_education.md](test_cases/ai_education.md)** - Worked example: "If AI makes everyone capable of learning faster, why will some people still outperform others?"
- **[test_cases/investing.md](test_cases/investing.md)** - Worked example: Identifying good investments with reasonable risk
- **[test_cases/switzerland.md](test_cases/switzerland.md)** - Worked example: Understanding Switzerland's success through structured analysis

## Architecture: Core Flow + Domain Plugins

The think skill uses a **two-layer architecture**:

### Layer 1: Core Reasoning Flow (Universal)

The compression/decompression flow runs on **every** query:

```
Build Structure → Validate → Counterexamples → Compress → Expand
```

This flow is domain-agnostic and always active.

**Lives in**: `docs/framework.md`, `docs/principles.md`, `SKILL.md`

### Layer 2: Domain Plugins (When Available)

Domain plugins **augment** the core flow with specialized knowledge:

- Known structures in this domain
- Quality standards for evidence
- Common failure modes and stress tests
- Verification methods (code, data, cross-referencing)
- Compression/expansion criteria

**Lives in**: `quality/{domain}/`

**References**: External knowledge bases (e.g., wiki-finance) compiled into self-contained plugins at authoring time

### How They Work Together

```
Core Flow (Step 1: Build Structure)
    ↓
    ← Plugin injects: Context on known frameworks (1-2 sentence summaries)
    ↓
Core Flow (Step 2: Validate)
    ↓
    ← Plugin injects: Quality standards for evidence (evidence hierarchy)
    ↓
Core Flow (Step 3: Counterexamples)
    ↓
    ← Plugin injects: Domain-specific stress tests and failure modes
    ↓
[continues...]
```

**Key principle**: Plugins provide evaluation criteria compiled from expert knowledge. They're self-contained (no runtime dependencies on external files).

**See**: [docs/architecture.md](docs/architecture.md) for detailed explanation of how plugins integrate at each step.

### Example: Equity Investing Domain

**Plugin location**: `quality/equity/taste.md`

**Source knowledge** (compiled at authoring time): wiki-finance, investment books, personal experience

**How it augments**:
- Step 1 (Build): Provides context on 5 known approaches (Value, Growth, Passive, Momentum, Macro)
- Step 2 (Validate): Quality standards (evidence hierarchy, quality indicators)
- Step 3 (Counterexamples): Domain-specific stress tests, failure modes
- Step 4 (Compress): What complexity must stay explicit in investing
- Step 5 (Expand): Verification methods (pull 10-K data, calculate metrics)

## Philosophy

The goal is not to maximize answer generation. It is to improve the quality of reasoning that produces those answers.

> "Build, test, compress, and apply internal structures that help humans understand reality and make better decisions."
