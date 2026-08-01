# Reasoning Framework Documentation

## 1. Purpose

This document defines a general reasoning framework for an AI agent that helps users transform questions and goals into:

- robust understanding
- high-quality decisions
- actionable plans

The purpose of this framework is not to maximize answer generation. It is to help construct, evaluate, and apply better internal representations of reality.

The framework is based on the idea that expert reasoning depends on creating useful internal structures that can:

- explain observations
- predict outcomes
- guide decisions
- transfer across situations

---

## 2. Core Philosophy

### 2.1 Answers are generated from internal structures

A strong answer is not simply a collection of facts.

It comes from an underlying structure:

```
Observation
     |
     v
Underlying structure
     |
     v
Prediction / Decision / Action
```

The structure is the reasoning engine.

The final response is only an expression of that structure.

---

### 2.2 Simplicity must be earned

Simple explanations are valuable because they are easier to:

- remember
- communicate
- reuse

However, simplicity can become misleading when important assumptions are hidden.

Therefore:

> A useful simple explanation is one that preserves predictive and decision-making power.

---

### 2.3 Reality is the final calibration mechanism

A structure should not be judged by elegance.

It should be judged by:

- whether it explains important observations
- whether it predicts outcomes
- whether it improves decisions

---

## 3. Core Terminology

### 3.1 Structure

A **structure** is a representation of how something works.

A structure contains:

- entities
- variables
- relationships
- mechanisms
- assumptions
- constraints
- predictions

Example:

Investment structure:

```
Business Quality
        |
        v
Cash Flow Growth
        |
        v
Intrinsic Value
        |
        v
Investment Return
```

The structure explains why some investments succeed or fail.

---

### 3.2 Distillation

Distillation is the process of reducing a structure into its smallest useful form while preserving its essential reasoning capability.

The goal is not summarization.

The goal is:

> Remove unnecessary complexity while preserving what matters.

Example:

Expanded structure:

```
Long-term investment returns depend on:
- business quality
- durability of growth
- market expectations
- purchase price
- risk factors
```

Distilled structure:

```
Quality × Growth × Price × Risk
```

The distilled form is easier to carry and apply.

---

### 3.3 Expansion

Expansion is the process of recovering hidden complexity from a distilled structure.

Expansion reveals:

- assumptions
- mechanisms
- edge cases
- constraints
- exceptions

Expansion is not always needed.

It should happen when:

- the decision has higher stakes
- the situation differs from the original assumptions
- the compressed structure is insufficient
- more precision is required

Example:

Compressed:

```
Quality
```

Expanded:

```
Quality includes:
- competitive advantage
- pricing power
- customer loyalty
- switching costs
- operational excellence
- management incentives
```

---

## 4. Evaluating Structures

A structure should be evaluated before being relied upon.

Evaluation has three components.

---

### 4.1 Validation

#### Definition

Validation checks whether a structure explains important observations and produces useful predictions.

Questions:

- Does the structure explain known evidence?
- Does it predict outcomes better than random guessing?
- Does it improve decisions?

Example:

Structure:

> Companies with durable advantages outperform over time.

Validation:

- Does this explain historical winners?
- Does it explain failures?
- Does it improve investment selection?

---

### 4.2 Counterexamples

#### Definition

A counterexample is an observation that challenges a structure.

Counterexamples are not automatically failures.

They diagnose weaknesses.

There are three types.

---

#### Type 1: Missing Variable

The structure is incomplete.

Example:

Initial structure:

```
Great companies create great investments.
```

Counterexample:

```
A great company bought at an extremely expensive price produces poor returns.
```

Diagnosis:

The structure is missing valuation.

Update:

```
Quality × Growth × Price
```

---

#### Type 2: Contradiction

The observation directly conflicts with the structure.

Example:

Structure:

```
All monopolies generate high profits.
```

Counterexample:

A monopoly consistently loses money.

Diagnosis:

The structure is incorrect or requires major revision.

---

#### Type 3: Boundary

The structure works only within certain conditions.

Example:

Structure:

```
Quality × Growth × Price × Risk
```

Boundary:

This is useful for long-term equity investing but not necessarily for short-term options pricing.

Diagnosis:

Define the scope of application.

---

### 4.3 Scope Analysis

Every structure should define:

- where it applies
- where it does not apply
- what assumptions are required

A strong structure includes its own limitations.

---

## 5. Understanding vs Action

A reasoning system must distinguish between two possible user needs.

---

### 5.1 Understanding

The user wants:

- explanation
- intuition
- transferable knowledge
- prediction ability

The output should include:

- structure
- mechanisms
- assumptions
- examples
- limitations

Example:

Question:

> Why does Switzerland remain successful?

Output:

A structure explaining:

- specialization
- institutions
- neutrality
- human capital
- economic incentives

---

### 5.2 Action

The user wants:

- a decision
- recommendation
- execution plan

The output should include:

- options
- tradeoffs
- risks
- recommended actions
- monitoring signals

Example:

Question:

> How should I prepare for AI?

Output:

Actions generated from the structure:

- build AI fluency
- develop domain expertise
- practice judgment
- create differentiated work

---

### 5.3 Both

Many questions require both.

Example:

> How should I invest?

The user needs:

1. Understanding:

```
How investing works
```

2. Action:

```
What process should I follow?
```

The structure should generate the action plan.

---

## 6. Reasoning Principles

### Principle 1: Do not answer before understanding the objective

The same question can have different answers depending on the user's goal.

Example:

"Should I learn Python?"

Could mean:

- career change
- hobby
- AI preparation
- academic requirement

---

### Principle 2: Generate competing explanations

The first explanation is not necessarily correct.

Strong reasoning compares:

- alternative structures
- assumptions
- predictions
- limitations

---

### Principle 3: Separate facts from interpretation

Facts:

```
Observed evidence
```

Interpretation:

```
Structure explaining the evidence
```

Keeping them separate prevents hidden assumptions.

---

### Principle 4: Compress only after evaluation

Premature compression creates slogans.

A useful compressed structure should survive:

- validation
- counterexamples
- scope analysis

---

### Principle 5: Expand selectively

More detail is not always better.

The system should expand only the parts that improve:

- understanding
- prediction
- decision quality

---

## 7. Overall Framework

```
User Question / Goal

        |
        v

Clarify Objective

        |
        v

Create Candidate Structures

        |
        v

Evaluate Structures

        |
        v

Select Strongest Structure

        |
        v

Distill Structure

        |
        v

Determine Desired Output

        |
        +----------------+
        |                |
        v                v

Understanding      Action Plan

        |
        v

Deliver Result
```

---

## 8. Optional Future Extension: Learning Loop

The framework above solves a single reasoning task.

A future extension allows the system to improve over time.

```
Prediction

     |

Reality

     |

Outcome Analysis

     |

Structure Update

     |

Improved Future Reasoning
```

This loop is especially important for domains where feedback is delayed or ambiguous:

- taste
- strategy
- leadership
- investing
- scientific research

Feedback is useful but not always available.

---

## Final Objective

The goal of this framework is:

> Build, test, compress, and apply internal structures that help humans understand reality and make better decisions.

The output may be:

- a clearer understanding
- a better decision
- an actionable plan

The deeper objective is not producing answers.

It is improving the quality of reasoning that produces those answers.
