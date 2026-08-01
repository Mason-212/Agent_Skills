# Reasoning Framework: Evolution and Principles

## Context

We started by talking about **compression and decompression**, but through stress testing we ended up designing a **thinking framework** rather than just a prompt.

---

## The Evolution

### The original insight: Stereotypes (models) can be flawed

We began with the observation that experts naturally **compress** knowledge.

Examples:
- "Switzerland succeeds through specialization."
- "Quality × Growth × Price × Risk."
- "AI shifts the bottleneck from knowledge to judgment."

These are valuable because they are compact.

The problem is:

> A compressed model hides assumptions, mechanisms, and boundary conditions.

So we needed a way to **decompress** (validate) them.

---

### First flaw discovered

Our original prompt assumed:

> "The user already has a model."

But most people don't. They arrive with:
- a question
- a goal
- an observation
- confusion

So the process became:

> Discover the model first.

---

### Second flaw discovered

Not every user wants a model.

Sometimes they want:
> "What should I do?"
> "Help me understand."

So the framework evolved.

---

### The framework today

The goal is:

> **Help the user reach their goal by constructing, validating, and applying the minimum useful mental model.**

The model is **not** the output.

It is the engine that produces the output.

The output might be:
- understanding
- a decision
- an action plan
- a prediction

---

## How It Works

### Compression

Compression asks:

> **What is the simplest model that still predicts and explains reality?**

Good compression should preserve:
- causal mechanisms
- important variables
- assumptions
- predictive power

It removes:
- unnecessary detail
- examples
- implementation specifics

Compression is not summarization.

It is:

> **Finding the invariant structure.**

---

### Decompression

Decompression asks:

> **What complexity was hidden inside this simple model?**

It expands:
- assumptions
- edge cases
- mechanisms
- exceptions
- historical evidence
- competing explanations

The purpose is not to make the answer longer.

It is to know:

> **When will this model fail?**

---

### Stress Testing

Stress testing, model verification, happens throughout every stage of the pipeline, i.e., compression, decompression:

* **Compression**: Verify the model. "Can this model survive simplification?"
  - Does this explain the observations?
  - Are there simpler competing models?
  - What assumptions am I making?
  - Have I omitted an important variable?

* **Decompression**: Find the limits of the model; when does the model stop becoming sufficient?

This turned out to be the most important addition.

Every compressed model should answer:
- What evidence contradicts me?
- Where do I fail?
- What assumptions am I making?
- What variables did I ignore?
- What competing model explains the same facts?

Without stress testing: Compression becomes slogans.

With stress testing: Compression becomes robust mental models.

---

## 3 Types of Verification

### 1. Validation

Does this explain the known evidence?

**Example**: Can this investing model explain both successful and failed companies?

### 2. Falsification

What would prove this wrong?

**Example**: What would have to happen for my AI education model to fail?

### 3. Boundary analysis

Where should this model not be used?

**Example**: "Quality × Growth × Price × Risk" is useful for long-term equity investing but not for pricing short-term options.

---

## Counterexamples Are Different for Each Verification

| Counterexample type | Purpose | Result |
|---|---|---|
| **Incomplete** | Reveals a missing variable | Refine the model |
| **Contradictory** | Shows the model is false | Replace the model |
| **Boundary** | Shows where the model doesn't apply | Narrow the model's scope |

---

### Type 1: Validation

Counterexamples test whether the model has enough explanatory power.

**Example Model**:
> "Great companies make great investments."

**Counterexample**:
A great company purchased at an extremely high valuation produced poor returns.

**Question**:
> Does the model explain this?

If the answer is "yes" (because valuation was omitted), the model survives after refinement.

Here, the counterexample is **diagnostic**. It exposes a missing variable.

---

### Type 2: Falsification

Here the counterexample attacks the model directly.

**Example Model**:
> "Every monopoly produces high profits."

**Counterexample**:
A monopoly that consistently loses money.

If this really exists and cannot be explained away, the model is false.

This is a classic Popperian falsification.

---

### Type 3: Boundary Analysis

Here the counterexample isn't saying the model is wrong.

It's saying: "This model works here, but not there."

**Example Model**:
> "Quality × Growth × Price × Risk"

**Counterexample**:
It doesn't help price short-term options.

That doesn't invalidate the model. It defines its scope.

---

## Key Insights

1. **Models must be discovered, not assumed** - Users often arrive with questions, not models

2. **Stress testing is essential** - Without it, compression becomes slogans instead of robust structures

3. **Three verification types serve different purposes**:
   - Validation checks explanatory power
   - Falsification checks correctness
   - Boundary analysis checks scope

4. **Counterexamples are diagnostic tools**:
   - Incomplete → Missing variable → Refine
   - Contradictory → Model is false → Replace
   - Boundary → Scope limit → Narrow

5. **The model is the engine, not the output** - It generates understanding, decisions, or action plans
