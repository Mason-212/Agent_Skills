# Reasoning Techniques in the Think Framework

## Overview

This document catalogs all reasoning techniques used in the think skill, organized by the step where they're applied, with their philosophical foundations and purposes.

---

## Framework Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              USER QUERY                                     │
└────────────────────────────────┬────────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  STEP 1: BUILD STRUCTURE                                                    │
│  ─────────────────────────                                                  │
│  Goal: Discover or construct the mental model                               │
│                                                                              │
│  Techniques:                                                                 │
│  • Abductive Reasoning (inference to best explanation)                      │
│  • Causal Mechanism Identification (mechanism over correlation)             │
│  • Variable Identification (systems thinking)                               │
│  • Hypothesis Formation (scientific method)                                 │
│                                                                              │
│  [Parsimony implicit: Don't add unnecessary variables from start]           │
└────────────────────────────────┬────────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  STEP 2: VALIDATE  ◄───────────────── CRITICAL GATE                         │
│  ─────────────────                                                          │
│  Goal: Test if model explains evidence and is internally consistent         │
│                                                                              │
│  Current Techniques:                                                         │
│  • Evidence Hierarchy (primary > secondary sources)                         │
│  • Correspondence Testing (model matches reality?)                          │
│  • Internal Consistency Check (logical coherence)                           │
│  • Explanatory Scope (explains all key observations?)                       │
│                                                                              │
│  [EXPLORATION - FAIL FAST CHECKS:]                                          │
│  • Mechanistic Depth Probing (PRIMARY) - If shallow, STOP                   │
│  • Evidence Weighting (PRIMARY) - If all weak, STOP                         │
│                                                                              │
│  → GATE: Only proceed to Step 3 if model has depth + solid evidence         │
└────────────────────────────────┬────────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  STEP 3: TEST WITH COUNTEREXAMPLES                                          │
│  ──────────────────────────────                                             │
│  Goal: Stress-test model to find weaknesses, boundaries                     │
│                                                                              │
│  Current Techniques:                                                         │
│  • Missing Variable Testing (diagnostic falsification)                      │
│  • Contradiction Testing (Popperian falsification)                          │
│  • Boundary Analysis (scope definition)                                     │
│  • Assumption Reversal (dialectical method)                                 │
│  • Alternative Explanations (inference competition)                         │
│                                                                              │
│  [EXPLORATION: Analogical Reasoning (PRIMARY)]                              │
│  • Use historical precedents as ready-made counterexamples                  │
└────────────────────────────────┬────────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  STEP 4: COMPRESS                                                           │
│  ─────────────────                                                          │
│  Goal: Distill model to essential structure                                 │
│                                                                              │
│  Current Techniques:                                                         │
│  • Invariant Extraction (structural realism)                                │
│  • Simplification (Occam's Razor, implicit)                                 │
│  • Causal Core Identification (mechanism focus)                             │
│  • Pattern Abstraction (generalization)                                     │
│                                                                              │
│  [EXPLORATION: Parsimony Testing (PRIMARY)]                                 │
│  • Explicitly remove variables that don't earn complexity cost              │
└────────────────────────────────┬────────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  STEP 5: EXPAND FOR USER CONTEXT                                            │
│  ─────────────────────────────────                                          │
│  Goal: Decompress to answer user's specific question                        │
│                                                                              │
│  Techniques:                                                                 │
│  • Contextual Application (pragmatic epistemology)                          │
│  • Decompression (reverse compression with constraints)                     │
│  • Assumption Surfacing (transparency)                                      │
│  • Action Translation (practical reasoning)                                 │
└────────────────────────────────┬────────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  STEP 6: VERIFY (Independent Validation Only)                               │
│  ───────────────                                                            │
│  Goal: Test if reasoning is accurate vs internally consistent but wrong     │
│                                                                              │
│  Current Techniques (6 methods):                                            │
│  1. Consequence Testing (deductive logic) - HIGHEST PRIORITY                │
│  2. Temporal Consistency (inductive pattern)                                │
│  3. Calculation Verification (correspondence theory)                        │
│  4. Adversarial Review (dialectical method)                                 │
│  5. Cross-Source Triangulation (coherence theory)                           │
│  6. Predictive Testing (Popperian falsification)                            │
│                                                                              │
│  Note: Step 6 should NOT be first time checking mechanistic depth,          │
│        evidence strength, or parsimony (caught in Steps 2-4).               │
└────────────────────────────────┬────────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                  OUTPUT: ANALYSIS + CONFIDENCE ASSESSMENT                   │
└─────────────────────────────────────────────────────────────────────────────┘

CROSS-CUTTING PRINCIPLES (apply to all steps):
─────────────────────────────────────────────
• Mechanism Over Correlation
• Evidence Hierarchy (primary > secondary)
• Explicit Uncertainty
• Scope Definition
• Falsifiability
• FAIL FAST: Catch errors early before building on flawed foundations
• LOW-COST EXPLORATION: Early steps (1-3) prioritize cheap methods to expand search space
```

---

## Control Flow: What Happens When Checks Fail?

### The Lineage Problem

**Challenge**: The framework appears linear (Steps 1→2→3→4→5→6), but what happens when a check fails?

**Example failure scenarios:**
- Step 2 Mechanistic Depth check: Model is shallow (only explains at Level 1-2)
- Step 2 Evidence Weighting check: All evidence is Weak, no Strong evidence
- Step 3 Counterexample: Model contradicts key observation
- Step 4 Parsimony: Model has 8 variables but only 2 are load-bearing

**Key Problem**: Agent doesn't have explicit decision tree tracking. How does it know:
- Which alternative paths to explore?
- What it already tried and failed?
- Why previous attempts failed?

### Solution: Iterative Refinement with Explicit Alternatives

The framework should be **iterative, not strictly linear**:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    ITERATIVE CONTROL FLOW                                   │
└─────────────────────────────────────────────────────────────────────────────┘

USER QUERY
    │
    ▼
STEP 1: BUILD STRUCTURE
    │
    │ Generate 2-3 candidate models (LOW COST)
    │ Use abductive reasoning, analogical reasoning for alternatives
    │
    ▼
STEP 2: VALIDATE ◄──────────── GATE 1: Fundamental Checks
    │                           │
    │ Check each candidate:     │
    │ • Mechanistic Depth       │
    │ • Evidence Weighting      │
    │                           │
    ├─ PASS → Proceed to Step 3 │
    │                           │
    └─ FAIL → Generate alternative models
                │
                ├─ Why did it fail?
                │  • Shallow mechanism → Need deeper causal chain
                │  • Weak evidence → Need different data sources
                │  • Missing variable → What's omitted?
                │
                ├─ Constraint for next iteration:
                │    "Previous model: [X]. Failed because: [Y]. Try: [Z]"
                │
                ├─ Generate new candidate using constraint
                │
                └─ Return to STEP 1 (max 3 iterations)
                   If all candidates fail → Report to user with uncertainties

STEP 3: TEST WITH COUNTEREXAMPLES ◄──────────── GATE 2: Stress Tests
    │                                            │
    │ Apply counterexamples + analogical tests   │
    │                                            │
    ├─ PASS → Proceed to Step 4                 │
    │                                            │
    └─ FAIL (contradiction found) → Refine model
                │
                ├─ Minor refinement? → Add missing variable, adjust scope
                │                      Stay in Step 3, iterate
                │
                └─ Major failure? → Return to Step 1 with new constraint
                                    "Model contradicted by [observation]"

STEP 4: COMPRESS
    │
    │ Parsimony Testing
    │
    └─ If model won't compress → Too complex, return to Step 1
       "Model has [N] variables but only [M] are load-bearing. Simplify."

STEPS 5-6: EXPAND + VERIFY
    │
    └─ If verification fails → Report uncertainty, don't force wrong answer
```

### Explicit Alternative Generation Strategy

**When a check fails, agent should:**

#### 1. Diagnose WHY it failed

```
STEP 2 FAILURE EXAMPLES:

Mechanistic Depth Check:
└─ Diagnosis: "Model stops at Level 1: 'NVDA margins high because demand high'
              No explanation for WHY demand is high or sustainable"
   Constraint: "Need model that explains demand at 3+ causal levels"
   Alternative: "Demand → AI scaling laws → Winner-take-most dynamics → 
                Enterprise differentiation value"

Evidence Weighting Check:
└─ Diagnosis: "Only Weak evidence (NVDA earnings call mentions power). 
              No independent confirmation"
   Constraint: "Need Strong evidence from independent sources"
   Alternative: "Check power supplier earnings (Vertiv), hyperscaler CapEx,
                utility grid data"
```

#### 2. Generate alternatives using systematic methods

**Method 1: Analogical Reasoning**
- Previous model failed → Check historical parallels
- Example: "Cisco 1999 bottleneck → What happened when it resolved?"
- Use historical outcomes to generate alternative models

**Method 2: Inversion**
- Take failed model and invert key assumption
- Example: Model: "Power bottleneck extends moat" → Failed
- Alternative: "Power bottleneck THREATENS moat (delays revenue, opens competitive window)"

**Method 3: Variable Substitution**
- Keep structure, change key variable
- Example: Model: "NVDA benefits from power bottleneck" → Shallow
- Alternative: "NVDA benefits from CUDA software lock-in (power is distraction)"

**Method 4: Scope Narrowing**
- Original model too broad → Narrow to specific domain
- Example: Model: "NVDA will dominate AI" → Too vague
- Alternative: "NVDA captures 2026-2028 training bottleneck, inference market more competitive"

#### 3. Track failed paths (in working memory)

**Explicit tracking:**
```
Attempt 1: "Power bottleneck extends moat"
└─ Failed: Mechanistic Depth (stopped at Level 2)
   Learned: Need to explain WHY power bottleneck creates moat, not just assert it

Attempt 2: "Power bottleneck forces 800V co-engineering, which creates switching costs"
└─ Passed: Mechanistic Depth (reached Level 4)
   Passed: Evidence Weighting (Vertiv backlog confirms, Strong evidence)
   → Proceed to Step 3
```

**This prevents:**
- Retrying the same failed approach
- Forgetting why previous attempts failed
- Wasting effort on equivalent models

### Cost-Benefit by Step

| Step | Method Cost | Failure Cost | Strategy |
|------|-------------|--------------|----------|
| **Step 1-2** | LOW (generate models, quick checks) | LOW (caught early) | Try 2-3 alternatives, fail fast |
| **Step 3** | MEDIUM (counterexamples, historical research) | MEDIUM (invested some effort) | Iterate if minor fix, restart if major |
| **Step 4-5** | MEDIUM-HIGH (compression, expansion) | HIGH (significant effort invested) | Avoid reaching here with broken model |
| **Step 6** | HIGH (independent validation, multiple sources) | VERY HIGH (entire analysis wasted) | Should rarely fail if Gates 1-2 worked |

### Low-Cost Exploration Principle

**Early steps (1-3) should prioritize cheap methods to expand search space:**

**GOOD (low-cost exploration):**
```
Step 1: Generate 3 candidate models (5 min each)
  • Model A: Power bottleneck extends moat
  • Model B: CUDA lock-in is primary moat
  • Model C: Hyperscaler CapEx sustains demand

Step 2: Quick checks on each (2 min each)
  • Model A: Mechanistic Depth = Level 2 → Shallow, reject
  • Model B: Mechanistic Depth = Level 4 → Deep, keep
  • Model C: Evidence = All Weak → Reject

Step 3: Invest in testing Model B deeply
  • Historical counterexamples (15 min)
  • Boundary conditions (10 min)

Total: 41 minutes, found robust model
```

**BAD (expensive single-path):**
```
Step 1: Build one model (10 min)
  • Model: Power bottleneck extends moat

Steps 2-5: Elaborate this model (60 min)
  • Detailed validation, counterexamples, compression, expansion

Step 6: Verification fails (15 min)
  • Mechanistic depth is shallow (should have caught in Step 2)

Total: 85 minutes, failed, must restart
```

**Key Insight**: Cheap exploration early (parallel candidates) > Expensive refinement of single path

### When to Stop Iterating

**Stop and report uncertainty if:**
1. **3 iterations exhausted**: Tried 3+ alternative models, all fail critical checks
2. **Contradictory evidence**: Strong evidence for AND against model (honest uncertainty)
3. **Insufficient data**: Can't gather Strong evidence, only Weak available
4. **High complexity**: Model requires >5 load-bearing variables (might be irreducible complexity)

**Don't force a confident answer when:**
- Evidence is genuinely weak
- Multiple competing models explain observations equally well
- Key data is unavailable or unreliable

**Report structure when stopping:**
```
"Explored 3 models:
 1. Power bottleneck (failed: shallow mechanism)
 2. CUDA lock-in (partial: explains margins, not demand)
 3. Hyperscaler CapEx (failed: weak evidence only)

Current assessment: MEDIUM-LOW confidence
Best partial model: CUDA lock-in explains pricing power
Missing: Clear explanation for demand sustainability
Uncertainty: Whether hyperscaler CapEx will sustain 2027+"
```

### Implementation Note: Tracking Decision Lineage

**Default approach** (as of Aug 2026): **Experiment Notebook for all /think queries**

**Rationale**: Framework is under active development. Logging enables:
- Identify where reasoning succeeds/fails
- Tune technique thresholds (e.g., "Is Level 3 depth sufficient?")
- Calibrate evidence weighting criteria
- Meta-learning from patterns across queries

---

#### Robust Logging: Event-Stream Architecture

**Challenge**: LLMs don't have explicit DAG workflow orchestration. How do we log:
- Iterative loops (Attempt 1 → fails → Attempt 2)
- Backtracking (Step 3 fails → return to Step 1)
- Parallel exploration (testing 3 models concurrently in reasoning)
- Non-linear control flow

**Solution**: **Append-only event stream** (JSONL format)

---

#### Event-Stream Pattern

**Key principles:**
1. **Append-only**: Never read-modify-write, only append new events
2. **Self-describing**: Each event is atomic, contains full context
3. **Order-preserving**: Timestamp + sequence number
4. **Workflow-agnostic**: Works with any control flow (loops, branches, DAG, non-DAG)

**File format**: JSONL (one JSON object per line)

**File location**: `skills/think/logs/YYYY-MM-DD-HHMMSS-{query-hash}.jsonl`

**Example log:**

```jsonl
{"event": "query_start", "timestamp": "2026-08-03T06:30:00Z", "seq": 1, "query": "What stock opportunities exist in August 2026?", "session_id": "abc123"}
{"event": "attempt_start", "seq": 2, "attempt": 1, "model_hypothesis": "Power bottleneck extends NVDA moat", "generation_method": "abductive_reasoning"}
{"event": "step_start", "seq": 3, "step": 1, "step_name": "build", "attempt": 1}
{"event": "model_built", "seq": 4, "attempt": 1, "structure": "Power bottleneck → Pricing power → Margin expansion", "variables": ["power_capacity", "gpu_demand", "pricing_power"], "time_spent_sec": 120}
{"event": "step_end", "seq": 5, "step": 1, "result": "complete", "attempt": 1}
{"event": "step_start", "seq": 6, "step": 2, "step_name": "validate", "attempt": 1}
{"event": "check_start", "seq": 7, "check": "mechanistic_depth", "attempt": 1}
{"event": "depth_level", "seq": 8, "level": 1, "question": "Why does power bottleneck create pricing power?", "answer": "Because GPUs need power", "attempt": 1}
{"event": "depth_level", "seq": 9, "level": 2, "question": "Why do GPUs need more power?", "answer": "Higher compute density", "attempt": 1}
{"event": "depth_stop", "seq": 10, "level": 2, "reason": "circular_reasoning", "attempt": 1}
{"event": "check_fail", "seq": 11, "check": "mechanistic_depth", "achieved_level": 2, "required_level": 3, "diagnosis": "Shallow - no explanation for WHY bottleneck creates moat, only THAT it does", "attempt": 1}
{"event": "step_end", "seq": 12, "step": 2, "result": "fail", "attempt": 1}
{"event": "attempt_end", "seq": 13, "attempt": 1, "result": "rejected", "reason": "mechanistic_depth_fail", "learned": "Need deeper causal chain explaining mechanism, not just correlation"}
{"event": "alternative_generation", "seq": 14, "method": "extend_mechanism", "constraint": "Previous model stopped at Level 2, need 3+ levels", "new_hypothesis": "Power bottleneck → 800V DC requirement → NVDA-Vertiv co-engineering → Switching costs"}
{"event": "attempt_start", "seq": 15, "attempt": 2, "model_hypothesis": "800V co-engineering creates technical moat", "generation_method": "extend_mechanism"}
{"event": "step_start", "seq": 16, "step": 2, "step_name": "validate", "attempt": 2}
{"event": "check_start", "seq": 17, "check": "mechanistic_depth", "attempt": 2}
{"event": "depth_level", "seq": 18, "level": 1, "question": "Why does power bottleneck matter?", "answer": "Data centers can't deploy GPUs without power infrastructure upgrades", "attempt": 2}
{"event": "depth_level", "seq": 19, "level": 2, "question": "Why do they need infrastructure upgrades?", "answer": "GPUs now require 800V DC architecture vs 400V legacy systems", "attempt": 2}
{"event": "depth_level", "seq": 20, "level": 3, "question": "Why does 800V create moat?", "answer": "NVDA co-engineers 800V systems with Vertiv, creating technical interdependence", "attempt": 2}
{"event": "depth_level", "seq": 21, "level": 4, "question": "Why is co-engineering valuable?", "answer": "Customer switching costs emerge from validated integrated systems", "attempt": 2}
{"event": "depth_level", "seq": 22, "level": 5, "question": "Why do switching costs extend moat?", "answer": "18-24 month re-validation cycle gives NVDA temporal advantage", "attempt": 2}
{"event": "check_pass", "seq": 23, "check": "mechanistic_depth", "achieved_level": 5, "assessment": "Deep causal understanding", "attempt": 2}
{"event": "check_start", "seq": 24, "check": "evidence_weighting", "attempt": 2}
{"event": "evidence_assessed", "seq": 25, "source": "Vertiv Q2 2026 earnings", "claim": "Power infrastructure demand growing", "direction": "supports", "strength": "strong", "independence": true, "rationale": "Independent supplier confirms infrastructure bottleneck", "attempt": 2}
{"event": "evidence_assessed", "seq": 26, "source": "NVDA earnings call", "claim": "Power constraints mentioned", "direction": "supports", "strength": "weak", "independence": false, "rationale": "Expected confirmation, company has incentive to emphasize", "attempt": 2}
{"event": "check_pass", "seq": 27, "check": "evidence_weighting", "strong_count": 1, "medium_count": 0, "weak_count": 1, "assessment": "Sufficient - at least one Strong independent source", "attempt": 2}
{"event": "step_end", "seq": 28, "step": 2, "result": "pass", "attempt": 2}
{"event": "step_start", "seq": 29, "step": 3, "step_name": "test", "attempt": 2}
{"event": "counterexample_test", "seq": 30, "type": "historical_analogy", "analogy": "Cisco 1999 networking bottleneck", "similarity": "Infrastructure constraint, dominant supplier", "difference": "Cisco lacked software moat, NVDA has CUDA", "lesson": "Bottleneck can last 3-5 years, but margins compress when resolved", "attempt": 2}
{"event": "step_end", "seq": 31, "step": 3, "result": "pass", "attempt": 2}
{"event": "attempt_end", "seq": 32, "attempt": 2, "result": "accepted", "reason": "Passed mechanistic_depth (Level 5), evidence_weighting (Strong), counterexample_test"}
{"event": "query_end", "seq": 33, "timestamp": "2026-08-03T06:45:00Z", "selected_attempt": 2, "total_attempts": 2, "total_time_sec": 900, "confidence": "high"}
```

---

#### Event Schema

**Core fields (all events):**
- `event`: Event type (see taxonomy below)
- `seq`: Monotonically increasing sequence number (prevents ordering ambiguity)
- `timestamp`: ISO 8601 timestamp (optional, seq is primary ordering)
- `attempt`: Which model iteration (1, 2, 3...)
- `step`: Which step in framework (1-6) if applicable

**Event Taxonomy:**

| Event Type | When | Key Fields |
|------------|------|------------|
| `query_start` | Begin /think | `query`, `session_id` |
| `attempt_start` | Begin new model | `attempt`, `model_hypothesis`, `generation_method` |
| `step_start` | Enter framework step | `step`, `step_name` |
| `check_start` | Begin verification check | `check` (e.g., "mechanistic_depth") |
| `check_pass` | Check succeeds | `check`, `assessment` |
| `check_fail` | Check fails | `check`, `diagnosis`, `achieved_level`, `required_level` |
| `depth_level` | Mechanistic depth level reached | `level`, `question`, `answer` |
| `depth_stop` | Depth check stops | `level`, `reason` |
| `evidence_assessed` | Evidence piece evaluated | `source`, `strength`, `independence` |
| `counterexample_test` | Counterexample applied | `type`, `result` |
| `step_end` | Exit framework step | `step`, `result` ("pass"/"fail") |
| `attempt_end` | Finish model evaluation | `attempt`, `result` ("accepted"/"rejected"), `reason`, `learned` |
| `alternative_generation` | Generate new model | `method`, `constraint`, `new_hypothesis` |
| `query_end` | Complete /think | `selected_attempt`, `total_attempts`, `confidence` |

---

#### Writing Pattern for Agent

**Simple append-only writes:**

```python
# Pseudocode for agent reasoning

# 1. Start query
append_event({"event": "query_start", "seq": next_seq(), "query": user_query})

# 2. Try first model
append_event({"event": "attempt_start", "seq": next_seq(), "attempt": 1, "model_hypothesis": "..."})

# 3. Mechanistic depth check
append_event({"event": "check_start", "seq": next_seq(), "check": "mechanistic_depth", "attempt": 1})

# Agent reasons through levels...
append_event({"event": "depth_level", "seq": next_seq(), "level": 1, "question": "...", "answer": "..."})
append_event({"event": "depth_level", "seq": next_seq(), "level": 2, "question": "...", "answer": "..."})
append_event({"event": "depth_stop", "seq": next_seq(), "level": 2, "reason": "circular_reasoning"})

# Check fails
append_event({"event": "check_fail", "seq": next_seq(), "check": "mechanistic_depth", "achieved_level": 2, "required_level": 3})

# Reject attempt
append_event({"event": "attempt_end", "seq": next_seq(), "attempt": 1, "result": "rejected", "reason": "mechanistic_depth_fail"})

# Generate alternative
append_event({"event": "alternative_generation", "seq": next_seq(), "method": "extend_mechanism", "new_hypothesis": "..."})

# Try second model
append_event({"event": "attempt_start", "seq": next_seq(), "attempt": 2, "model_hypothesis": "..."})

# ... continues ...
```

**Agent implementation:**
- Keep `seq` counter in memory (starts at 1)
- After each significant decision/check, append one event
- Use Write tool for new file, append mode for existing
- File path: Generate once at query start, reuse

---

#### Robustness Properties

**Why this works for non-DAG workflows:**

1. **No read-modify-write**: Append-only prevents corruption
2. **Self-contained events**: Each event has full context (attempt, step, check)
3. **Reconstructable**: Can rebuild decision tree from event sequence
4. **Handles loops**: Attempt 1 → fail → Attempt 2 → fail → Attempt 3 logged naturally
5. **Handles backtracking**: Step 3 fails → return to Step 1 evident from event sequence
6. **Handles concurrency**: If agent explores 3 models in parallel (in reasoning), events interleave naturally

**Example: Complex control flow**

```jsonl
{"event": "attempt_start", "seq": 10, "attempt": 1, "model_hypothesis": "A"}
{"event": "step_start", "seq": 11, "step": 3, "attempt": 1}
{"event": "counterexample_test", "seq": 12, "result": "contradiction_found", "attempt": 1}
{"event": "step_end", "seq": 13, "step": 3, "result": "fail", "attempt": 1}
{"event": "backtrack", "seq": 14, "from_step": 3, "to_step": 1, "reason": "Major contradiction, need new model"}
{"event": "attempt_end", "seq": 15, "attempt": 1, "result": "rejected"}
{"event": "attempt_start", "seq": 16, "attempt": 2, "model_hypothesis": "B"}
```

The event stream naturally captures non-linear flow.

---

#### Analysis and Debugging

**Post-hoc analysis** (after collecting logs from multiple queries):

```python
# Count how often each check fails
failures = [e for e in events if e["event"] == "check_fail"]
by_check = Counter(f["check"] for f in failures)
# Result: mechanistic_depth: 15, evidence_weighting: 8, ...

# Average attempts per query
queries = [e for e in events if e["event"] == "query_end"]
avg_attempts = mean(q["total_attempts"] for q in queries)
# Result: 2.3 attempts per query → Framework is iterating reasonably

# Which alternative generation methods work best?
alt_gens = [e for e in events if e["event"] == "alternative_generation"]
successes = [e for e in events if e["event"] == "attempt_end" and e["result"] == "accepted"]
# Join by attempt number to see which method led to accepted models

# Mechanistic depth distribution
depths = [e for e in events if e["event"] == "check_pass" and e["check"] == "mechanistic_depth"]
depth_levels = [d["achieved_level"] for d in depths]
# Result: median = 4, mean = 4.2 → Most models reach Level 4-5
```

**Debugging specific query:**

```python
# Why did Attempt 1 fail?
attempt_1_events = [e for e in events if e["attempt"] == 1]
failure = [e for e in attempt_1_events if e["event"] == "check_fail"][0]
# Result: {"check": "mechanistic_depth", "achieved_level": 2, "diagnosis": "..."}

# What did agent learn?
learned = [e for e in events if e["event"] == "attempt_end" and e["attempt"] == 1][0]["learned"]
# Result: "Need deeper causal chain explaining mechanism"
```

---

#### Human-Readable Summary (Optional)

**Also generate markdown summary** for human review:

File: `skills/think/logs/YYYY-MM-DD-HHMMSS-{query-hash}.md`

```markdown
# Think Framework Experiment Log

**Query**: What stock opportunities exist in August 2026?
**Session**: abc123
**Started**: 2026-08-03 06:30:00 AM
**Duration**: 15 minutes

---

## Attempt 1: Power Bottleneck Hypothesis

**Model**: "Power bottleneck extends NVDA moat"

### Step 2: Validate
- **Mechanistic Depth Check**: ❌ FAIL
  - Achieved Level: 2
  - Required Level: 3
  - Diagnosis: Shallow - no explanation for WHY bottleneck creates moat
  
**Decision**: REJECT

**Learned**: Need deeper causal chain explaining mechanism, not just correlation

---

## Attempt 2: 800V Co-Engineering Hypothesis

**Model**: "Power bottleneck → 800V DC requirement → NVDA-Vertiv co-engineering → Switching costs"

### Step 2: Validate
- **Mechanistic Depth Check**: ✅ PASS
  - Level 1: Data centers need power infrastructure upgrades
  - Level 2: GPUs require 800V DC vs 400V legacy
  - Level 3: NVDA co-engineers with Vertiv, technical interdependence
  - Level 4: Switching costs from validated systems
  - Level 5: 18-24 month re-validation extends moat
  - Assessment: Deep causal understanding

- **Evidence Weighting**: ✅ PASS
  - Vertiv Q2 2026 earnings: Backlog +24% (Strong, independent)
  - NVDA earnings call: Power mentioned (Weak, expected)
  - Assessment: Sufficient (1 Strong source)

### Step 3: Test with Counterexamples
- Historical analogy: Cisco 1999 networking bottleneck
  - Similarity: Infrastructure constraint, dominant supplier
  - Difference: Cisco lacked software moat, NVDA has CUDA
  - Lesson: Bottleneck can last 3-5 years, margins compress when resolved

**Decision**: ACCEPT

---

## Summary

**Selected Model**: Attempt 2 (800V Co-Engineering)
**Total Attempts**: 2
**Confidence**: High
**Key Success Factors**:
- Deep mechanistic understanding (Level 5)
- Strong independent evidence (Vertiv backlog)
- Historical validation (Cisco analogy)
```

**Generation**: Write markdown after query completes, by parsing JSONL events.

---

#### File Management

**Directory structure:**
```
skills/think/logs/
├── 2026-08-03-063000-nvda-stocks.jsonl
├── 2026-08-03-063000-nvda-stocks.md
├── 2026-08-03-070000-asylum-system.jsonl
├── 2026-08-03-070000-asylum-system.md
└── index.md  # Optional: List of all logs
```

**Naming convention:**
- `YYYY-MM-DD-HHMMSS`: Timestamp for uniqueness
- `{query-slug}`: First 3-4 words of query, kebab-case
- `.jsonl`: Machine-readable event stream
- `.md`: Human-readable summary

**Cleanup**: Periodically archive or delete old logs (keep last 30 days?)

---

### Agent Implementation Checklist

**At query start:**
1. Generate log file path: `skills/think/logs/2026-08-03-{time}-{slug}.jsonl`
2. Initialize seq counter: `seq = 1`
3. Write `query_start` event

**During reasoning:**
4. After each significant decision, append event with `seq++`
5. Keep log file path in context

**At query end:**
6. Write `query_end` event
7. Generate markdown summary (parse JSONL → markdown)
8. Report to user: "Logged decision process to {path}"

**Overhead**: ~5-10 Write tool calls per query (low, acceptable for tuning phase)
1. Attempt 2 fails (suggests complexity requires tracking)
2. User asks "how did you decide?"
3. Context window getting full
4. High-stakes decision (explicit verification needed)

---

## Current Techniques by Step

### Step 1: Build Structure

**Goal**: Discover or construct the mental model that explains the observations.

| Technique | Philosophical Foundation | Purpose | When to Apply |
|-----------|-------------------------|---------|---------------|
| **Abductive Reasoning** | C.S. Peirce (inference to best explanation) | Generate candidate explanatory models | When no model exists yet |
| **Causal Mechanism Identification** | Aristotelian causation | Distinguish correlation from causation | Always - avoid spurious patterns |
| **Variable Identification** | Systems thinking | Find relevant factors and relationships | When building model from scratch |
| **Hypothesis Formation** | Scientific method | Create testable structures | When observations need explanation |

**Output**: Candidate mental model(s)

**Example**:
- Observation: "NVDA stock at high valuation but margins increasing"
- Abduction: Generate explanations (AI demand surge? Supply constraint? Pricing power?)
- Mechanism: Identify causal chain (GPU bottleneck → pricing power → margin expansion)
- Model: "Sequential infrastructure bottlenecks drive NVDA pricing power"

---

### Step 2: Validate Structure

**Goal**: Test whether the model explains known evidence and has internal consistency.

| Technique | Philosophical Foundation | Purpose | When to Apply |
|-----------|-------------------------|---------|---------------|
| **Evidence Hierarchy** | Empirical epistemology | Prioritize primary sources over secondary | Always - establishes reliability |
| **Correspondence Testing** | Correspondence theory of truth | Check if model matches observable reality | Always - validate against data |
| **Internal Consistency Check** | Logical coherence | Ensure model doesn't contradict itself | Always - catch logical errors |
| **Explanatory Scope** | Philosophy of science | Verify model explains all key observations | When model seems incomplete |

**Output**: Validated or refined model

**Evidence Hierarchy** (strongest to weakest):
1. Primary sources (company filings, financial statements)
2. Direct measurements (earnings transcripts, guidance)
3. Independent analysis (supplier data, cross-industry signals)
4. Secondary commentary (analyst reports, news)
5. Speculation (social media, unverified claims)

**Example**:
- Model: "Power bottleneck extends NVDA moat"
- Evidence check: Does NVDA 10-Q confirm high margins? (Yes, 73% gross margin)
- Consistency: Does high margin contradict bottleneck? (No, bottleneck can enable pricing power)
- Scope: Does this explain customer advances? (Yes, customers pre-paying for scarce GPUs)

---

### Step 3: Test with Counterexamples

**Goal**: Stress-test the model to find weaknesses, missing variables, and boundaries.

| Technique | Philosophical Foundation | Purpose | When to Apply |
|-----------|-------------------------|---------|---------------|
| **Missing Variable Testing** | Diagnostic falsification | Expose incomplete models | Always - find gaps |
| **Contradiction Testing** | Popperian falsification | Find observations that break model | Always - test limits |
| **Boundary Analysis** | Scope definition | Identify where model doesn't apply | Always - define applicability |
| **Assumption Reversal** | Dialectical method | Test what happens if assumptions flip | When assumptions are critical |
| **Alternative Explanations** | Inference competition | Check if other models fit better | When confidence is uncertain |

**Three Types of Counterexamples**:

| Type | Purpose | Result |
|------|---------|--------|
| **Missing Variable** | Reveals incomplete model | Refine by adding variable |
| **Contradiction** | Shows model is false | Replace or major revision |
| **Boundary** | Shows scope limits | Define where model applies |

**Example**:
- Model: "Great companies make great investments"
- Missing variable: Great company at extreme valuation → poor returns (add Price variable)
- Contradiction: Monopoly that loses money (if sustained, model is wrong)
- Boundary: Model applies to long-term equity, not short-term options trading

---

### Step 4: Compress

**Goal**: Distill the model to its essential structure, removing unnecessary complexity.

| Technique | Philosophical Foundation | Purpose | When to Apply |
|-----------|-------------------------|---------|---------------|
| **Invariant Extraction** | Structural realism | Find what stays true across cases | Always - identify core pattern |
| **Simplification** | Occam's Razor (implicit) | Remove non-essential detail | Always - make model usable |
| **Causal Core Identification** | Mechanism focus | Keep only load-bearing variables | When model has many factors |
| **Pattern Abstraction** | Generalization | Extract transferable insight | When model should apply broadly |

**Compression Criteria**:
- Preserve explanatory power
- Maintain predictive capability
- Keep causal mechanisms
- Remove implementation details, examples, redundant factors

**Example**:
- Verbose: "NVDA benefits from AI demand growth driven by enterprises seeking competitive advantage through foundation models that require massive compute for training and inference, constrained by data center power capacity that takes 18-24 months to upgrade..."
- Compressed: "Sequential infrastructure bottlenecks (GPU supply → Power capacity) extend NVDA pricing power"
- Preserved: Causal mechanism (bottleneck → pricing power), temporal sequence
- Removed: Implementation details, obvious facts, redundant descriptions

---

### Step 5: Expand for User Context

**Goal**: Decompress the model to answer the user's specific question with appropriate detail.

| Technique | Philosophical Foundation | Purpose | When to Apply |
|-----------|-------------------------|---------|---------------|
| **Contextual Application** | Pragmatic epistemology | Tailor output to user's goal | Always - make useful |
| **Decompression** | Reverse compression | Unpack compressed model with constraints | Always - provide sufficient detail |
| **Assumption Surfacing** | Transparency | Make implicit assumptions explicit | When assumptions matter for decision |
| **Action Translation** | Practical reasoning | Convert model to decisions/plans | When user needs action, not just understanding |

**Expansion Triggers** (when to go deeper):
- User's goal requires specific detail
- Decision has high stakes
- Assumptions need clarification
- Edge cases matter for user's situation

**Example**:
- Compressed model: "Sequential bottlenecks extend NVDA pricing power"
- User context: "Should I invest in NVDA?"
- Expansion: Unpack valuation (Forward PE 15.57 vs historical 20-30), risk factors (AMD competition, CapEx reversal), time horizon (bottleneck may last 3-5 years based on infrastructure lead times), position sizing (high conviction but concentrated risk)

---

### Step 6: Verify

**Goal**: Test whether the reasoning from Steps 1-5 is accurate vs internally consistent but wrong.

| Technique | Philosophical Foundation | Purpose | When to Apply |
|-----------|-------------------------|---------|---------------|
| **Consequence Testing** | Deductive logic | Test independent predictions from model | Always (highest priority) |
| **Temporal Consistency** | Inductive pattern recognition | Verify patterns across time periods | Always - catch one-time noise |
| **Calculation Verification** | Correspondence theory | Reproduce key numbers from raw sources | For critical quantitative claims |
| **Adversarial Review** | Dialectical method | Build strongest counter-thesis | High stakes or controversial claims |
| **Cross-Source Triangulation** | Coherence theory | Verify claims across independent sources | For critical assumptions |
| **Predictive Testing** | Popperian falsification | Make falsifiable future predictions | When possible to test later |

#### Method 1: Consequence Testing (Highest Priority)

**Process**:
1. Generate 3-5 independent predictions from your model
2. Test against sources you haven't used yet
3. Threshold: <60% pass rate = weak model

**Example**:
- Model: Power bottleneck extends NVDA moat
- Prediction 1: Power suppliers (Vertiv) should show growing backlog
- Test: Check Vertiv Q2 2026 earnings
- Result: ✅ Backlog +24% YoY → Model confirmed

#### Method 2: Temporal Consistency

**Process**:
1. Check if key patterns hold across 3+ time periods
2. One period = noise; three periods = signal

**Example**:
- Metric: NVDA gross margins
- Check: Q2 2026 (73%), Q1 2026 (72%), Q4 2025 (70%), Q3 2025 (68%)
- Result: ✅ Consistent upward trend, not one-time spike

#### Method 3: Calculation Verification

**Process**:
1. For critical metrics, pull raw financial statements
2. Recalculate key numbers yourself
3. Flag >10% discrepancies

**Example**:
- Claim: Forward PE = 15.57
- Verify: Price $200.75 / Analyst consensus FY2027 EPS $12.89 = 15.57
- Result: ✅ Calculation matches

#### Method 4: Adversarial Review

**Process**:
1. Build the strongest possible counter-thesis (steel-man, not straw-man)
2. Apply same rigor: gather evidence, test consequence predictions
3. Honest assessment: Which explains observations better?

**Example**:
- Bull: Power bottleneck extends moat
- Bear: Power bottleneck delays revenue, competitive window opens
- Test both: Which has more supporting evidence?

#### Method 5: Cross-Source Triangulation

**Process**:
1. Identify critical claims
2. Verify each from 2+ structurally different sources
3. Investigate discrepancies

**Example**:
- Claim: Data center power capacity is binding constraint
- Source 1: NVDA investor commentary
- Source 2: Hyperscaler CapEx breakdowns
- Source 3: Power equipment supplier earnings
- Source 4: Utility grid expansion timelines

#### Method 6: Predictive Testing

**Process**:
1. Make specific, falsifiable predictions
2. Wait for new data
3. Check if predictions hold

**Example**:
- Prediction: If power bottleneck is real, Q3 2026 gross margins ≥70%
- Wait for Q3 earnings
- Check: Did prediction hold?

**Output**: Confidence assessment (High/Medium/Low) + identified uncertainties

---

## Technique Summary Table

| Step | Primary Techniques | Philosophical Roots | Key Output |
|------|-------------------|---------------------|------------|
| **1. Build** | Abductive reasoning, Causal mechanism ID | C.S. Peirce, Aristotle | Candidate model(s) |
| **2. Validate** | Evidence hierarchy, Correspondence testing | Empiricism, Correspondence theory | Validated model |
| **3. Test** | Counterexamples (3 types), Alternative explanations | Popper, Dialectics | Refined model with boundaries |
| **4. Compress** | Invariant extraction, Simplification | Structural realism, Occam's Razor | Essential structure |
| **5. Expand** | Contextual application, Decompression | Pragmatism | User-specific answer |
| **6. Verify** | Consequence testing, Temporal checks, Adversarial review | Multiple traditions | Confidence assessment |

---

## Cross-Cutting Principles

These principles apply across all steps:

### 1. Mechanism Over Correlation

**Foundation**: Aristotelian causation

**Principle**: Prefer causal explanations over statistical patterns.

**Example**:
- ❌ "NVDA stock goes up when headlines mention AI" (correlation)
- ✅ "NVDA captures value because GPUs solve AI compute bottleneck" (mechanism)

### 2. Evidence Hierarchy

**Foundation**: Empirical epistemology

**Principle**: Primary sources > Independent verification > Secondary commentary

**Example**:
- Tier 1: NVDA 10-Q financial statements
- Tier 2: Supplier earnings (Vertiv, TSMC)
- Tier 3: Analyst reports
- Tier 4: News articles
- Tier 5: Social media speculation

### 3. Explicit Uncertainty

**Foundation**: Bayesian epistemology (qualitative)

**Principle**: Surface assumptions and confidence limits explicitly.

**Example**:
- ✅ "If power bottleneck resolves faster than expected (12 months vs 36 months), thesis breaks"
- ❌ "NVDA will definitely succeed"

### 4. Scope Definition

**Foundation**: Philosophy of science (scope conditions)

**Principle**: Every model has boundaries. Define them.

**Example**:
- "This model applies to long-term equity investing (3+ years), not short-term trading"
- "Assumes hyperscaler CapEx remains >$600B annually"

### 5. Falsifiability

**Foundation**: Popperian philosophy of science

**Principle**: Good models make predictions that can be proven wrong.

**Example**:
- ✅ "If Q3 margins drop below 60%, pricing power thesis is wrong"
- ❌ "NVDA will do well in the long run" (not falsifiable)

---

## Exploration: New Techniques Under Evaluation

The following four techniques are **under evaluation** for integration into the framework. They prioritize qualitative/structural reasoning to avoid numerical hallucination risks.

### Placement Analysis: "Fail Fast" Architecture

**Critical Principle**: Catch reasoning errors EARLY before building on flawed foundations. Don't wait until Step 6 to discover the model is shallow, overcomplicated, or built on weak evidence.

**Revised Placement Strategy:**

```
┌─────────────────────────────────────────────────────────────────────────────┐
│             EXPLORATION TECHNIQUES: FAIL-FAST PLACEMENT                     │
└─────────────────────────────────────────────────────────────────────────────┘

                    STEP 1: BUILD
                         │
                         │ [Parsimony Check: Don't add unnecessary variables]
                         │
                         ▼
                    STEP 2: VALIDATE ◄───────── CRITICAL GATE
                         │
                         │ [Mechanistic Depth: PRIMARY]
                         │  → If shallow (Level 1-2 only), STOP and refine
                         │
                         │ [Evidence Weighting: PRIMARY]
                         │  → If all evidence is Weak, STOP and gather better data
                         │
                         ▼
                    STEP 3: TEST
                         │
                         │ [Analogical Reasoning: PRIMARY]
                         │  → Historical counterexamples provide rich stress tests
                         │
                         ▼
                    STEP 4: COMPRESS
                         │
                         │ [Parsimony Testing: PRIMARY]
                         │  → Remove variables that don't earn their complexity cost
                         │
                         ▼
                    STEP 5: EXPAND
                         │
                         │
                         ▼
                    STEP 6: VERIFY ◄──────── FINAL CHECKS ONLY
                         │
                         │ • Consequence Testing (independent predictions)
                         │ • Temporal Consistency (pattern across time)
                         │ • Calculation Verification (reproduce numbers)
                         │ • Adversarial Review (steel-man opposition)
                         │ • Cross-Source Triangulation (multiple sources)
                         │ • Predictive Testing (falsifiable predictions)
                         │
                         │ [Step 6 should NOT be first time checking:]
                         │  ✗ Mechanistic depth (caught in Step 2)
                         │  ✗ Evidence strength (caught in Step 2)
                         │  ✗ Overcomplicated model (caught in Step 4)
                         │  ✗ Historical precedents (used in Step 3)
                         │
                         ▼
                    OUTPUT
```

**Revised Placements:**

| Technique | PRIMARY Placement | Why Early? | Step 6 Role? |
|-----------|------------------|------------|--------------|
| **Mechanistic Depth Probing** | **Step 2 (Validate)** | Catch shallow reasoning BEFORE building on it. If you can't explain mechanism at 3+ levels, model is suspect from the start. | Optional: Re-check if refined |
| **Evidence Weighting** | **Step 2 (Validate)** | Assess evidence strength as you validate. Don't build elaborate structures on weak foundations. If all evidence is "Weak", STOP. | Use for final confidence given cumulative evidence |
| **Parsimony Testing** | **Step 4 (Compress)** + Step 1 (implicit) | During compression, explicitly remove variables that don't earn their cost. Implicitly avoid unnecessary complexity in Step 1. | Optional: Verify simplification was sufficient |
| **Analogical Reasoning** | **Step 3 (Test)** | Historical failures provide ready-made counterexamples for stress testing. Learn from past mistakes BEFORE finalizing model. | Optional: Final sanity check vs precedents |

**Architectural Principle:**

```
┌─────────────────────────────────────────────────────────────┐
│  EARLY CHECKS (Steps 1-4): Catch fundamental errors          │
│  ────────────────────────────────────────────                │
│  • Mechanistic Depth (Step 2): Is reasoning deep or shallow? │
│  • Evidence Weighting (Step 2): Is foundation solid or weak? │
│  • Analogical Reasoning (Step 3): What do precedents teach?  │
│  • Parsimony Testing (Step 4): Is model lean or bloated?     │
│                                                               │
│  → FAIL FAST if checks fail. Don't proceed to Step 6.        │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│  LATE CHECKS (Step 6): Independent validation                │
│  ────────────────────────────────────────────                │
│  • Consequence Testing: Do predictions match unused sources? │
│  • Temporal Consistency: Does pattern hold across time?      │
│  • Calculation Verification: Can we reproduce key numbers?   │
│  • Cross-Source Triangulation: Do multiple sources confirm?  │
│                                                               │
│  → These catch subtle errors that early checks miss.         │
└─────────────────────────────────────────────────────────────┘
```

**Why This Matters:**

**BAD (current design):**
1. Step 1-2: Build shallow model (correlation without mechanism)
2. Step 3-4: Compress and refine the shallow model
3. Step 5: Expand with user context
4. Step 6: Mechanistic Depth check reveals model is shallow ← **Too late! Wasted effort.**

**GOOD (fail-fast design):**
1. Step 1-2: Build model + **Mechanistic Depth check immediately**
2. If shallow → STOP, refine mechanism, try again
3. If deep → Proceed to Step 3 with confidence
4. Step 6 focuses on independent validation, not catching fundamental flaws

**Cost-Benefit:**

| Technique | Overhead if applied early | Waste if error caught late | Net Benefit |
|-----------|-------------------------|---------------------------|-------------|
| Mechanistic Depth | Low (just ask "why?" 3-5 times) | High (entire Steps 3-6 wasted) | ✅ Apply early |
| Evidence Weighting | Low (assess as you gather) | High (building on weak evidence) | ✅ Apply early |
| Parsimony Testing | Medium (requires variable analysis) | Medium (overcomplicated models compress poorly) | ✅ Apply in Step 4 |
| Analogical Reasoning | Medium (requires historical research) | Medium (missing historical lessons) | ✅ Apply in Step 3 |

**Integration Strategy:**

1. **Phase 1**: Test each technique in its PRIMARY (early) placement
2. **Phase 2**: Evaluate if late (Step 6) application adds value
3. **Phase 3**: Decide final placement based on fail-fast principle

**Decision Criteria:**
- If technique catches **fundamental errors** → Must be early (Steps 1-4)
- If technique provides **independent validation** → Can be late (Step 6)
- If technique is **cheap to apply** → Apply early even if benefit is uncertain

---

### Exploration Method 1: Mechanistic Depth Probing

**Philosophical Foundation**: Aristotelian causation (multiple levels of explanation)

**Method**: "Can I explain this at 3+ levels of causation?"

**Purpose**: Distinguish deep causal understanding from surface correlation.

**Proposed Application**: Step 6 (Verify) as Method 7

**Process**:
1. State claim
2. Explain immediate cause (Level 1)
3. Explain cause of that cause (Level 2)
4. Explain root cause (Level 3+)
5. If you hit "I don't know" before Level 3, model is shallow

**Example (NVDA Power Bottleneck)**:
- **Claim**: NVDA benefits from data center power constraints
- **Level 1**: Data centers can't deploy GPUs without power upgrades
- **Level 2**: Modern GPUs draw 700W vs 300W previously
- **Level 3**: Larger models need more FLOPs, so designers prioritized compute over efficiency
- **Level 4**: Scaling laws show performance scales with compute
- **Level 5**: Winner-take-most dynamics make model quality worth power cost
- **Assessment**: ✅ Reached Level 5 → Deep understanding

**Red Flags**:
- Stopped at Level 1: "It just is" → Correlation without mechanism
- Circular reasoning: "A causes B because B requires A"
- Hand-waving: "Market dynamics" without specifics

**Evaluation Criteria**:
- Does it catch shallow reasoning that other methods miss?
- Is it practical to apply without excessive overhead?
- Does it improve model quality measurably?

---

### Exploration Method 2: Parsimony Testing (Explicit Occam's Razor)

**Philosophical Foundation**: Occam's Razor (principle of parsimony)

**Method**: "Does each additional variable earn its complexity cost?"

**Purpose**: Prevent overcomplicated models that overfit vs generalize poorly.

**Proposed Application**: Step 4 (Compress) as explicit check

**Process**:
1. List key variables in your model
2. For each variable: "If I removed this, would my model fail to explain key observations?"
3. If yes → Keep it (load-bearing)
4. If no → Remove it (decorative)
5. Check competing simpler models

**Example (NVDA Analysis)**:

**Full Model**:
```
NVDA value = GPU demand + Power bottleneck + 800V co-engineering + 
             CUDA moat + AI hype cycle + Liquid cooling + Edge AI + 
             Sovereign AI + Automotive recovery
```

**Parsimony Test**:
- Remove "Automotive recovery" → Model still explains margins/growth? YES → Remove
- Remove "AI hype cycle" → Model still explains demand? YES (demand is real CapEx) → Remove
- Remove "CUDA moat" → Model still explains 60%+ margins? NO → Keep
- Remove "800V co-engineering" → Model still explains moat extension? NO → Keep

**Simplified Model** (5 variables):
```
NVDA value = (GPU demand + Sovereign AI) + Power bottleneck + 
             800V co-engineering + CUDA moat
```

**Warning Signs**:
- "Kitchen sink" models: Adding every possible variable
- Can't explain why variable matters
- Correlation without mechanism

**Evaluation Criteria**:
- Does it reduce model complexity without losing predictive power?
- Does it improve clarity and falsifiability?
- Is it practical to apply systematically?

---

### Exploration Method 3: Evidence Weighting (Qualitative Bayesian)

**Philosophical Foundation**: Bayesian epistemology (without precise probabilities)

**Method**: "How much does this evidence shift my confidence, and why?"

**Purpose**: Explicitly reason about evidence strength without hallucinating precise numbers.

**Proposed Application**: Step 6 (Verify) as Method 8

**Process**:
1. Start with initial confidence (Low/Medium/High)
2. For each evidence piece, assess:
   - **Direction**: Supports or contradicts?
   - **Strength**: Strong / Medium / Weak
   - **Independence**: Redundant with prior evidence?
3. Update confidence based on cumulative pattern
4. Final confidence: Low/Medium/High (not a number)

**Evidence Strength Criteria**:

| Strength | Characteristics | Update Size |
|----------|----------------|-------------|
| **Strong** | Independent source confirms prediction; contradicts alternatives; high signal-to-noise; visible mechanism | Large |
| **Medium** | Partial independence; supports thesis but also consistent with alternatives; moderate noise | Medium |
| **Weak** | Same source as prior evidence; confirms what's known; high noise; could support multiple explanations | Small |

**Example (NVDA)**:

- **Start**: Medium confidence
- **Evidence 1**: Vertiv backlog +24% (Strong, independent) → **Medium-High**
- **Evidence 2**: NVDA mentions power in call (Weak, expected) → **Medium-High** (no change)
- **Evidence 3**: Margins hold 73% for 3 quarters (Strong, temporal) → **High**
- **Evidence 4**: Utility CapEx shows no acceleration (Medium contradiction) → **Medium-High**
- **Final**: Medium-High confidence

**Red Flags**:
- Counting evidence without weighing (quality > quantity)
- Ignoring independence (same source ≠ multiple confirmations)
- Treating weak evidence as strong
- Dismissing contradictions but embracing confirmations

**Evaluation Criteria**:
- Does it prevent overconfidence from weak evidence?
- Is it practical without precise probability estimates?
- Does it improve calibration vs current implicit method?

---

### Exploration Method 4: Analogical Reasoning

**Philosophical Foundation**: Inductive reasoning via pattern matching

**Method**: "What historical parallels exist, and where do they break down?"

**Purpose**: Learn from similar situations without assuming "this time is different" OR "history repeats exactly"

**Proposed Application**: Step 6 (Verify) as Method 9, or Step 3 (Test) for domain-specific counterexamples

**Process**:
1. Identify 2-3 historical analogies with structural similarities
2. Map similarities (what's the same?)
3. Map differences (what's different?)
4. Extract lessons: Which outcomes are likely vs unlikely?
5. **Critical**: Be explicit about where analogy breaks down

**Example (NVDA 2026)**:

#### Analogy 1: Cisco (1995-2000) - Networking Bottleneck

**Similarities**:
- Physical infrastructure bottleneck
- Single dominant supplier (60%+ share)
- Customers pre-paying for scarce equipment
- "Arms race" adoption dynamics

**Differences**:
- Cisco's moat was switching costs; NVDA's is CUDA (stickier)
- Networking commoditized via standards (IEEE); AI software is proprietary
- Cisco faced strong competition (Juniper, Nortel); AMD is weaker

**Lessons**:
- ✅ Bottleneck phase can last 3-5 years
- ✅ Margins >60% sustainable during bottleneck
- ⚠️ Risk: Margins compress rapidly when bottleneck resolves
- ❌ Unlike Cisco, CUDA creates software moat → May sustain longer

#### Analogy 2: Intel (1990-2005) - x86 Architecture Moat

**Similarities**:
- Software ecosystem lock-in (x86 vs CUDA)
- High switching costs
- 60%+ margins for 10+ years

**Differences**:
- Intel owned manufacturing; NVDA is fabless
- x86 was standardized ISA; CUDA is proprietary
- AMD eventually closed gap via TSMC manufacturing parity

**Lessons**:
- ✅ Software moats can last 10+ years
- ⚠️ Risk: Competitor closes gap via manufacturing access (TSMC serves everyone)
- ⚠️ Risk: Market saturation

#### Analogy 3: Cloud Infrastructure Build (2010-2018)

**Similarities**:
- Multi-year hyperscaler CapEx cycle
- Supplier concentration
- Market skepticism of CapEx sustainability

**Differences**:
- Cloud CapEx had clear unit economics ($/VM)
- AI CapEx is for product differentiation, ROI less proven
- Cloud standardized (Kubernetes); AI diverging (custom chips)

**Lessons**:
- ✅ CapEx cycles can sustain 8+ years
- ⚠️ Risk: Hyperscalers backward-integrate (AWS Graviton, Google TPU)
- ⚠️ Risk: If AI ROI doesn't materialize, cuts can be sudden

**Synthesis**:
- **Base case**: 3-5 year bottleneck (Cisco), CUDA moat sustains (Intel), CapEx elevated (Cloud)
- **Key risks**: Margin compression (Cisco), backward integration (Cloud), competitor catch-up (Intel)

**Red Flags**:
- Cherry-picking analogies that support thesis
- Ignoring disanalogies (differences often contain critical risks)
- "This time is different" without evidence
- "History repeats exactly" without acknowledging structural changes

**Evaluation Criteria**:
- Does it surface risks that forward-looking analysis misses?
- Are historical parallels actionable for current decisions?
- Does it avoid false pattern matching?

---

## Evaluation Framework for New Techniques

Each exploration method will be tested against:

### 1. Error Detection
- Does it catch reasoning errors that existing methods miss?
- What types of errors does it surface?

### 2. Practicality
- Can it be applied systematically without excessive overhead?
- Is it clear when to use it?

### 3. Robustness
- Does it avoid numerical hallucination risks?
- Is it qualitative/structural enough to be reliable?

### 4. Value-Add
- Does it improve model quality measurably?
- Is the improvement worth the additional complexity?

### 5. Integration
- Where in the 6-step process does it fit best?
- Does it complement or duplicate existing techniques?

---

## Testing Plan

**Phase 1: Individual Evaluation** (Current)
- Apply each method to 2-3 case studies (NVDA analysis, asylum system analysis, pre-med strategy)
- Document what each method caught that others missed
- Assess practicality and overhead

**Phase 2: Comparative Analysis**
- Compare error detection: Which methods caught which types of errors?
- Compare cost: Which methods required most tool calls/research?
- Compare reliability: Which methods avoided hallucination risks best?

**Phase 3: Integration Decision**
- For each method: Integrate, Modify, or Reject
- If integrated: Document in main SKILL.md
- If modified: Specify refinements needed
- If rejected: Document why and what it taught us

**Success Criteria**: A method should be integrated if it:
1. Catches errors that existing methods miss
2. Is practical to apply (clear trigger conditions)
3. Avoids numerical hallucination
4. Improves reasoning quality measurably (not just theoretically)

---

## Design Philosophy

### Qualitative Over Quantitative

**Principle**: When in doubt, reason structurally rather than numerically.

**Rationale**: LLMs are better at pattern recognition and logical reasoning than precise numerical estimation. Forcing precise probabilities or percentages risks hallucination.

**Examples**:
- ✅ "Strong evidence" vs "Weak evidence"
- ❌ "70% probability" vs "30% probability"
- ✅ "Pattern holds across 3+ periods"
- ❌ "Correlation coefficient = 0.87"

### Mechanism Over Numbers

**Principle**: Understand why something works, not just that it correlates.

**Examples**:
- ✅ "Power bottleneck creates GPU deployment constraint → pricing power → margin expansion"
- ❌ "NVDA margins correlate 0.9 with AI mentions in earnings calls"

### Low-Cost Exploration Early

**Principle**: Early steps (1-3) should generate multiple alternatives cheaply. Late steps (4-6) refine the best candidate deeply.

**Rationale**: Better to test 3 models at 10 minutes each (30 min, find best) than elaborate 1 model for 90 minutes and discover it's flawed.

**Cost structure:**
```
CHEAP (do early, do often):
• Generate alternative models (Step 1): 5-10 min each
• Quick depth checks (Step 2): 2-5 min per model
• Abductive reasoning, analogy generation

MEDIUM (do for promising candidates):
• Historical counterexamples (Step 3): 10-20 min
• Evidence gathering (Step 2): 15-30 min
• Assumption reversal testing

EXPENSIVE (do once for validated model):
• Comprehensive verification (Step 6): 30-60 min
• Temporal consistency across years
• Multiple independent source triangulation
```

**Examples**:
- ✅ Generate 3 models → Quick check each → Invest in best one
- ❌ Generate 1 model → Fully elaborate → Discover it's shallow

### Fail Fast

**Principle**: Catch fundamental errors in Steps 1-3 before investing in Steps 4-6.

**Examples**:
- ✅ Step 2: Mechanistic Depth check reveals shallow reasoning → Stop, try alternative
- ❌ Step 6: After full analysis, discover mechanism was shallow all along

### Explicit Over Implicit

**Principle**: Make reasoning transparent. Surface assumptions, confidence, and limitations.

**Examples**:
- ✅ "This model assumes hyperscaler CapEx >$600B; if CapEx drops 20%, thesis breaks"
- ❌ "NVDA will do well"

### Falsifiable Over Vague

**Principle**: Good models make predictions that can be proven wrong.

**Examples**:
- ✅ "If Q3 margins <60%, pricing power thesis is falsified"
- ❌ "NVDA has a strong moat"

### Iterative Over Linear

**Principle**: The framework is iterative, not strictly linear. Failed checks trigger alternative generation, not blind forward progress.

**Examples**:
- ✅ Step 2 check fails → Generate alternative model → Retry Step 2
- ❌ Step 2 check fails → Ignore and proceed to Step 3 anyway

---

## Meta-Note: Limits of Verification

Even with extensive verification techniques, we cannot guarantee correctness. We can only:
- Reduce probability of major errors
- Make uncertainty explicit
- Catch data source bugs and confirmation bias
- Differentiate high-confidence from low-confidence claims

**The market/reality is the ultimate test.** Verification techniques improve reasoning, but external validation (predictions tested against future data) is what separates good models from lucky guesses.

**Humility is part of rigor.**
