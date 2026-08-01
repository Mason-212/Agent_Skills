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
├── SKILL.md                      # Main agent instructions
├── README.md                     # This file
├── docs/
│   ├── framework.md             # Core framework documentation
│   ├── principles.md            # Evolution and key principles
│   └── quality.md               # Quality principles (taste and judgment)
├── ir/
│   └── dag-spec.md              # DAG specification for reasoning process
├── evals/
│   ├── ai_education.md          # Example: AI and education query
│   ├── investing.md             # Example: Investment analysis
│   └── switzerland.md           # Example: Switzerland success analysis
└── extensions/                   # Personal calibration (optional)
    └── domains/                  # Domain-specific quality standards
        └── investing/            # Equity investing operational guidance
            ├── README.md         # Framework-agnostic patterns
            ├── growth.md         # Growth approach procedures
            └── ...               # Other approach procedures
```

## Quick Reference

### Reasoning Pipeline

1. **Clarify Objective** - What does the user need? Understanding or action?
2. **Create Structures** - Build candidate mental models
3. **Evaluate Structures** - Validate, test counterexamples, define scope
4. **Select Structure** - Choose model with best explanatory power
5. **Distill Structure** - Compress while preserving reasoning capability
6. **Determine Output** - Understanding vs action plan
7. **Deliver Result** - Provide validated response

### Key Principles

- **Simplicity must be earned** through validation
- **Reality is the calibration mechanism**, not elegance
- **Compress only after evaluation** to avoid slogans
- **Expand selectively** based on stakes and complexity
- **Separate facts from interpretation** to surface assumptions

## Documentation

- **[docs/framework.md](docs/framework.md)** - Comprehensive framework specification including philosophy, terminology, evaluation methods, and reasoning principles
- **[docs/principles.md](docs/principles.md)** - Evolution of the framework from compression/decompression to full reasoning system, with stress testing methodology
- **[docs/quality.md](docs/quality.md)** - Quality principles for reasoning: taste (recognizing excellence) and judgment (decisions under uncertainty)
- **[ir/dag-spec.md](ir/dag-spec.md)** - Implementation specification with node contracts, validation gates, and artifact schemas

## Evaluation Examples

- **[evals/ai_education.md](evals/ai_education.md)** - Worked example: "If AI makes everyone capable of learning faster, why will some people still outperform others?"
- **[evals/investing.md](evals/investing.md)** - Worked example: Identifying good investments with reasonable risk
- **[evals/switzerland.md](evals/switzerland.md)** - Worked example: Understanding Switzerland's success through structured analysis

## Personal Extensions

The `extensions/` directory allows you to add domain-specific operational guidance that augments the universal framework with your personal taste and judgment.

### Two-Layer Architecture

**Universal Framework** (skills/think/):
- Structure and principles for reasoning (docs/)
- DAG specification for implementation (ir/)
- Evaluation examples (evals/)

**Personal Extensions** (extensions/domains/):
- Operational guidance: HOW to apply frameworks rigorously
- Verification methods: HOW to check claims with code
- Counterfactual techniques: HOW to stress-test reasoning
- Failure mode detection: HOW to identify weak reasoning

**External Knowledge** (e.g., wiki-finance):
- Domain knowledge: WHAT approaches exist
- Framework definitions: WHEN to use each approach
- Quality standards: WHY approaches work in certain conditions

Extensions reference external knowledge bases for framework details, then provide operational guidance on how to apply them.

**Example**: `extensions/domains/investing/` references wiki-finance for investing approaches, then provides verification methods and counterfactual patterns that work across all approaches. Approach-specific operational procedures are in subdirectories (e.g., `growth.md`, `value.md`).

This is where YOU bring taste and judgment to the agentic experience.

## Philosophy

The goal is not to maximize answer generation. It is to improve the quality of reasoning that produces those answers.

> "Build, test, compress, and apply internal structures that help humans understand reality and make better decisions."
