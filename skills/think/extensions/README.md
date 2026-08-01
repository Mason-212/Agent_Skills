# Personal Extensions

This directory allows you to augment the universal reasoning framework with your personal taste and judgment.

## Purpose

The core framework (`docs/framework.md`, `docs/principles.md`) provides universal reasoning structure and principles. This is where **you** add domain-specific operational guidance calibrated from your experience.

## Relationship to External Knowledge Bases

Extensions provide **operational guidance** (HOW to apply frameworks rigorously), not **knowledge** (WHAT frameworks exist).

### Two-Layer Architecture

```
┌─────────────────────────────────────┐
│   External Knowledge Repositories   │  ← WHAT approaches exist
│   (e.g., wiki-finance)              │  ← WHEN to use each
│                                     │  ← WHY they work
└──────────────┬──────────────────────┘
               │ References
               ↓
┌─────────────────────────────────────┐
│   skills/think/extensions/domains   │  ← HOW to apply rigorously
│                                     │  ← HOW to verify claims
│                                     │  ← HOW to identify failures
└─────────────────────────────────────┘
```

**Example for investing**:
- **Wiki-finance** (`wiki-finance/topics/stocks/investing-approaches.md`): Documents 5 investing philosophies (Value, Growth, Passive, Momentum, Macro), when each works best, and what quality means in each
- **Extensions** (`extensions/domains/investing/`): Provides thinking patterns, verification methods, and counterfactual techniques that work across all approaches, with approach-specific operational procedures in subdirectories

### Cross-Repository References

Domain files in `extensions/domains/` may reference external knowledge bases using absolute file:// paths with GitHub fallbacks:

```markdown
See: [wiki-finance: investing-approaches](file:///path/to/wiki-finance/topics/stocks/investing-approaches.md)
Fallback: https://github.com/username/wiki-finance/blob/main/topics/stocks/investing-approaches.md
```

If local path fails, agents should print a warning and use the GitHub URL.

## What Goes Here

### Domain-Specific Quality Standards (`domains/`)

Define what "excellent" means in your domains:
- What makes good reasoning in investing vs engineering vs writing?
- What are red flags or common failure modes?
- What evidence do you trust in this domain?
- When do you expand vs compress?

### Your Calibrated Models

Mental models you've developed through experience:
- Patterns you've observed
- Predictions you've tested against reality
- Frameworks that have worked for you

### Personal Risk Tolerance

- When are stakes "high" vs "low" for you?
- How much validation do you require?
- What counterexamples matter most to you?

## How to Use

1. **Create a domain file or directory** in `domains/` (e.g., `investing/`, `engineering.md`)
2. **Define your standards** using the template structure
3. **Reference from prompts** when you want agents to apply your taste

Example prompts:
> "Use the think skill with my personal standards from extensions/domains/investing/"

> "Apply growth investing operational procedures from extensions/domains/investing/growth.md"

## Structure

```
extensions/
├── README.md              # This file
└── domains/
    ├── investing/         # Equity investing operational guidance
    │   ├── README.md      # Framework-agnostic patterns
    │   ├── growth.md      # Growth approach procedures
    │   ├── value.md       # Value approach procedures (stub)
    │   ├── momentum.md    # Momentum approach procedures (stub)
    │   ├── passive.md     # Passive approach procedures (stub)
    │   └── macro.md       # Macro approach procedures (stub)
    ├── engineering.md     # Your quality standards for code
    ├── writing.md         # Your quality standards for prose
    └── ...                # Add more as needed
```

## Domain Template

Each domain file should include:

```markdown
# Domain: [Name]

## Quality Standards

What constitutes excellent reasoning in this domain?

## Common Failure Modes

What are red flags or typical mistakes?

## Evidence Standards

What sources/evidence do you trust?

## Expansion Triggers

When should reasoning go deeper in this domain?

## Compression Criteria

When is simplification acceptable?

## Calibrated Models

Your experience-based frameworks for this domain.

## Examples

Good vs poor reasoning examples from your experience.
```

## Philosophy

> "Taste and judgment are what I bring to the agentic experience."

The framework provides structure. You provide the calibrated standards. Together they produce high-quality reasoning in your domains.
