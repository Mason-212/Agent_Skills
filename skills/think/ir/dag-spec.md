# Reasoning Framework: DAG Specification

## Overview

This document specifies the Directed Acyclic Graph (DAG) implementation of the reasoning framework. Each node represents a stage in the reasoning pipeline with defined inputs, outputs, validation gates, and failure behaviors.

## Purpose

The DAG provides a concrete implementation structure for the abstract reasoning framework. It defines:

- Node contracts (inputs/outputs)
- Validation gates (quality checks)
- Artifact schemas (data structures)
- Failure/retry behavior
- Branching conditions

---

## Pipeline Architecture

```
┌─────────────────┐
│  User Query     │
└────────┬────────┘
         │
         v
┌─────────────────┐
│ ClarifyObjective│
└────────┬────────┘
         │
         v
┌─────────────────┐
│CreateStructures │
└────────┬────────┘
         │
         v
┌─────────────────┐
│EvaluateStructures│
└────────┬────────┘
         │
         v
┌─────────────────┐
│ SelectStructure │
└────────┬────────┘
         │
         v
┌─────────────────┐
│DistillStructure│
└────────┬────────┘
         │
         v
┌─────────────────┐
│DetermineOutput  │
└────────┬────────┘
         │
    ┌────┴────┐
    v         v
┌────────┐ ┌────────┐
│Understand│ │ Action │
└────────┘ └────────┘
```

---

## Node Specifications

### Node 1: ClarifyObjective

**Purpose**: Understand what the user actually needs from their query.

**Inputs**:
- `user_query` (string): The user's question, statement, or request
- `context` (optional): Prior conversation context

**Outputs**:
```yaml
objective:
  intent: "understanding" | "action" | "both"
  domain: string              # e.g., "investing", "education", "strategy"
  stakes: "low" | "medium" | "high"
  complexity: "simple" | "moderate" | "complex"
  ambiguity: "clear" | "partially_ambiguous" | "highly_ambiguous"
  reframed_query: string     # Clarified version of user query
```

**Validation Gates**:
- Intent must be categorized
- Stakes and complexity must be assessed
- If ambiguity is "highly_ambiguous", may need to ask clarifying questions

**Failure Behavior**:
- If unable to categorize intent, default to "understanding"
- If unable to assess stakes, default to "high" (conservative approach)

---

### Node 2: CreateStructures

**Purpose**: Generate candidate mental models that could explain the domain.

**Inputs**:
- `objective` (from ClarifyObjective)
- `domain_knowledge` (optional): Relevant facts, observations, constraints

**Outputs**:
```yaml
candidate_structures:
  - id: string
    name: string
    description: string
    entities: [string]
    variables: [string]
    relationships: [string]
    mechanisms: [string]
    assumptions: [string]
    constraints: [string]
    predictions: [string]
    confidence: float          # 0.0 to 1.0
```

**Validation Gates**:
- Must generate at least 1 candidate structure
- Each structure must have defined entities, variables, and relationships
- Structures should be meaningfully different from each other

**Failure Behavior**:
- If no structures generated, create a simple linear causal model
- Minimum viable structure: 2 entities + 1 relationship

---

### Node 3: EvaluateStructures

**Purpose**: Apply validation, counterexamples, and scope analysis to each candidate.

**Inputs**:
- `candidate_structures` (from CreateStructures)
- `objective` (from ClarifyObjective)

**Outputs**:
```yaml
evaluated_structures:
  - structure_id: string
    validation:
      explains_observations: boolean
      predicts_outcomes: boolean
      improves_decisions: boolean
      evidence: [string]
    counterexamples:
      - type: "incomplete" | "contradictory" | "boundary"
        example: string
        diagnosis: string
        action: "refine" | "replace" | "narrow_scope"
    scope:
      applies_to: [string]
      does_not_apply_to: [string]
      required_assumptions: [string]
    quality_score: float       # 0.0 to 1.0
```

**Validation Gates**:
- Must test at least 2 counterexamples per structure
- Must define scope boundaries
- Quality score must be computed from validation + counterexample results

**Failure Behavior**:
- If all structures fail validation, return to CreateStructures
- If counterexample testing is inconclusive, flag for human review
- Maximum 3 iterations before proceeding with best-available structure

---

### Node 4: SelectStructure

**Purpose**: Choose the structure with best explanatory and predictive power.

**Inputs**:
- `evaluated_structures` (from EvaluateStructures)
- `objective` (from ClarifyObjective)

**Outputs**:
```yaml
selected_structure:
  structure_id: string
  structure: object           # Full structure object
  selection_rationale: string
  known_limitations: [string]
  competing_models: [string]  # IDs of strong alternatives
```

**Validation Gates**:
- Selected structure must have quality_score >= 0.5
- Must document why this structure was chosen over alternatives
- Must acknowledge known limitations

**Failure Behavior**:
- If no structure meets minimum quality threshold, flag high uncertainty
- If multiple structures are tied, select the simpler one (Occam's razor)

---

### Node 5: DistillStructure

**Purpose**: Compress structure to minimal useful form while preserving reasoning capability.

**Inputs**:
- `selected_structure` (from SelectStructure)
- `objective` (from ClarifyObjective)

**Outputs**:
```yaml
distilled_structure:
  compressed_form: string     # e.g., "Quality × Growth × Price × Risk"
  preserved_elements:
    - causal_mechanisms: [string]
    - key_variables: [string]
    - critical_assumptions: [string]
  hidden_complexity: [string] # What was compressed out
  expansion_triggers:         # When to expand
    - high_stakes: boolean
    - edge_case: boolean
    - precision_required: boolean
```

**Validation Gates**:
- Compressed form must be significantly shorter than expanded form
- Must preserve core predictive power
- Must document what complexity was hidden

**Failure Behavior**:
- If compression loses critical information, keep expanded form
- If structure is already minimal, pass through unchanged

---

### Node 6: DetermineOutput

**Purpose**: Decide between understanding output or action plan based on user intent.

**Inputs**:
- `objective` (from ClarifyObjective)
- `distilled_structure` (from DistillStructure)

**Outputs**:
```yaml
output_spec:
  type: "understanding" | "action" | "both"
  understanding_components:    # If type includes "understanding"
    - structure: boolean
    - mechanisms: boolean
    - assumptions: boolean
    - examples: boolean
    - limitations: boolean
  action_components:           # If type includes "action"
    - options: boolean
    - tradeoffs: boolean
    - risks: boolean
    - recommendations: boolean
    - monitoring_signals: boolean
```

**Validation Gates**:
- Output type must align with user intent from objective
- Required components must be selected

**Failure Behavior**:
- If intent unclear, default to "both"

---

### Branch A: Understanding Output

**Purpose**: Generate understanding-focused response.

**Inputs**:
- `output_spec` (from DetermineOutput)
- `distilled_structure` (from DistillStructure)
- `selected_structure` (from SelectStructure)

**Outputs**:
```yaml
understanding_output:
  structure:
    visual: string            # Diagram or text representation
    explanation: string
  mechanisms:
    - mechanism: string
      explanation: string
  assumptions:
    - assumption: string
      criticality: "low" | "medium" | "high"
  examples:
    - example: string
      demonstrates: string
  limitations:
    - limitation: string
      boundary: string
```

**Validation Gates**:
- Must explain core structure clearly
- Must surface critical assumptions
- Must define boundaries

---

### Branch B: Action Output

**Purpose**: Generate action-focused response.

**Inputs**:
- `output_spec` (from DetermineOutput)
- `distilled_structure` (from DistillStructure)
- `selected_structure` (from SelectStructure)

**Outputs**:
```yaml
action_output:
  options:
    - option: string
      pros: [string]
      cons: [string]
      required_resources: [string]
  recommended_action:
    action: string
    rationale: string
    based_on: string          # Which part of structure supports this
  risks:
    - risk: string
      likelihood: "low" | "medium" | "high"
      impact: "low" | "medium" | "high"
      mitigation: string
  monitoring_signals:
    - signal: string
      threshold: string
      action_if_triggered: string
```

**Validation Gates**:
- Must provide at least 2 options
- Must recommend specific action with clear rationale
- Must identify key risks

---

## Artifact Schemas

### Internal Reasoning Artifacts

These artifacts are generated during execution but may not be surfaced to the user:

```yaml
reasoning_trace:
  objective: object           # From ClarifyObjective
  candidate_structures: []    # From CreateStructures
  evaluated_structures: []    # From EvaluateStructures
  selected_structure: object  # From SelectStructure
  distilled_structure: object # From DistillStructure
  output_spec: object         # From DetermineOutput
  final_output: object        # Understanding or Action output
  
metadata:
  total_structures_considered: int
  structures_rejected: int
  validation_iterations: int
  expansion_triggered: boolean
  confidence: float
  uncertainty_flags: [string]
```

---

## Execution Rules

### Iteration Limits

- Maximum 3 iterations in CreateStructures → EvaluateStructures loop
- If no structure passes validation after 3 iterations, proceed with best-available and flag uncertainty

### Adaptive Depth

Adjust depth based on objective stakes:

- **Low stakes**: Single pass, minimal counterexample testing
- **Medium stakes**: Standard pipeline, 2-3 counterexamples per structure
- **High stakes**: Full evaluation, 5+ counterexamples, detailed scope analysis

### Early Exit Conditions

Exit pipeline early if:
- User query is simple and doesn't require structure building
- Existing validated structure can be reused
- User explicitly requests quick answer

### Quality Gates

At each node, check:
- Output meets specification
- Validation gates pass
- Confidence threshold met

If quality gates fail:
- Log failure reason
- Attempt recovery (retry, backtrack, or simplify)
- If recovery impossible, flag for human review

---

## Implementation Notes

1. **Flexibility over Rigidity**: The DAG is a template, not a straitjacket. Agents should adapt the pipeline when a better reasoning path exists.

2. **Preserve Principles**: Structure-first reasoning, reality calibration, and earned simplicity matter more than following the DAG exactly.

3. **Artifact Persistence**: Keep reasoning artifacts for debugging and improvement. They help calibrate future reasoning.

4. **Incremental Improvement**: Track which structures work in which domains to build domain-specific reasoning patterns over time.
