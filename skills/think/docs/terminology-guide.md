# Terminology Guide: Counterexamples vs Consequence Testing

## Purpose

This guide clarifies the distinction between **Counterexamples** (Step 3) and **Consequence Testing** (Step 6) in the think skill, and distinguishes both from the ML/RL use of "counterfactuals."

---

## Three Distinct Concepts

### 1. Counterexamples (Step 3: Stress Testing)

**Definition**: Observations that challenge or stress-test a model to expose weaknesses.

**Purpose**: Diagnostic testing to find missing variables, contradictions, or boundary conditions.

**Three Types**:
- **Missing Variable**: Model is incomplete → Refine it
- **Contradiction**: Model is false → Replace it
- **Boundary**: Model works here but not there → Define scope

**Example**:
- Model: "Great companies make great investments"
- Counterexample: Great company at extreme valuation → poor returns
- Diagnosis: Missing variable (valuation) → Refine to "Quality × Growth × Price"

**When to Use**: After building initial structure in Steps 1-2, before compressing.

---

### 2. Consequence Testing (Step 6: Verification)

**Definition**: "If my model is TRUE, what ELSE must be observable?" Generate independent predictions and test them against unused sources.

**Purpose**: Verify that the model's logical consequences match independent evidence.

**Process**:
1. Generate 3-5 predictions from your model
2. Check predictions against NEW sources (not used in Steps 1-5)
3. Threshold: <60% pass rate = weak model

**Example**:
- Model: NVDA benefits from power bottleneck
- Consequence: Power suppliers should show growing backlog
- Test: Check Vertiv Q2 2026 earnings (independent source)
- Result: ✅ Vertiv backlog +24% YoY → Model confirmed

**When to Use**: After completing Steps 1-5, to verify the entire analysis.

**Key Difference from Step 3**: Consequence testing uses INDEPENDENT SOURCES you haven't consulted yet. Counterexamples use logic and known examples to stress-test structure.

---

### 3. Counterfactuals (ML/RL Definition)

**Definition**: "What would happen if agent chose action B instead of A?"

**Purpose**: Off-policy evaluation, causal inference, credit assignment in reinforcement learning.

**Example**:
- Agent chose action A, got reward R
- Counterfactual: What reward would agent get if it chose action B?
- Use: Estimate value of unchosen actions, debug policy decisions

**NOT used in think skill**: The think skill doesn't evaluate alternative actions an agent could have taken. It tests whether a model's predictions match reality.

---

## Quick Reference Table

| Term | Step | Question | Purpose |
|------|------|----------|---------|
| **Counterexamples** | 3 | What breaks this model? | Stress-test structure, find weaknesses |
| **Consequence Testing** | 6 | If true, what else is observable? | Verify model against independent sources |
| **Counterfactuals (ML)** | N/A | What if action B was chosen? | Off-policy RL evaluation |

---

## Common Confusion Points

### "Aren't these all the same?"

**No.** They serve different purposes:
- **Counterexamples** = Stress testing using logic/known examples
- **Consequence Testing** = Verification using independent new evidence
- **Counterfactuals (ML)** = Alternative action evaluation in RL

### "Why rename from 'Counterfactual Testing' to 'Consequence Testing'?"

**Reason**: "Counterfactual" has a specific meaning in ML/RL (alternative actions). Using it for "deductive prediction testing" creates confusion.

**Better name**: "Consequence Testing" clearly describes what we do: test the observable consequences of a model.

---

## Usage Guidelines

### When to apply Counterexamples (Step 3):
- After building structure in Steps 1-2
- To expose missing variables, contradictions, boundary conditions
- Use logic, domain knowledge, and known examples

### When to apply Consequence Testing (Step 6):
- After completing Steps 1-5 (entire analysis)
- To verify the model matches independent reality
- Use NEW sources you haven't consulted yet
- Threshold: <60% pass = model is weak

### Domain plugins enhance both:
- Equity plugin provides **growth-specific counterexamples** (Step 3): "What if bottleneck disappears?"
- Same plugin informs **consequence test selection** (Step 6): "Check power supplier earnings"

---

## Historical Note

Earlier versions of the think skill documentation used "Counterfactual Testing" for Step 6. This was renamed to "Consequence Testing" in August 2026 to:
1. Avoid confusion with ML/RL counterfactuals
2. More accurately describe the verification method
3. Improve clarity and consistency across documentation
