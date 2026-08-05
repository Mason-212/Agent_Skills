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

## Logging (Active - Framework Tuning Phase)

**Status**: Logging is **enabled by default** while tuning the framework.

**What gets logged**:
- Decision lineage (attempts, checks, results)
- MCP calls (tool, inputs, outputs summary)
- Verification checks (pass/fail with reasoning)
- Alternative generation (why previous attempt failed)

**Log formats**:
- **JSONL** (`skills/think/logs/YYYY-MM-DD-HHMMSS-{query-slug}.jsonl`) - Machine-readable event stream
- **Markdown** (`skills/think/logs/YYYY-MM-DD-HHMMSS-{query-slug}.md`) - Human-readable with indents/prefixes

**User notification**: At start of session, inform user:
  "Logging session to skills/think/logs/2026-08-03-143000-stock-analysis.{jsonl,md}"

**MCP Usage**: Use the **log-agent** MCP (exact server id: `log-agent`):
- `create_log` - Initialize session
- `append_event` - Log each decision point (`event_data` arg, not `data`)
- `read_log` / `query_events` / `get_summary` / `aggregate_field` - Readback and stats

**Server id rules (do not guess):**
- Correct: `CallMcpTool(server="log-agent", ...)`
- Wrong: `user-log-agent`, `user_log_agent`, or any `user-*` prefix inferred from Cursor's on-disk `mcps/` folder
- The project `mcps/` folder names (`user-Atlassian`, etc.) are **not** authoritative server ids and may be stale
- Discover with `GetMcpTools(server="log-agent")` or `GetMcpTools(pattern="log-agent")`. If a guessed id fails, retry with pattern/catalog — do **not** treat a partial "Available servers: ..." error as proof the server is missing
- Confirm `serverStatus: "ready"` before logging; if unavailable, fall back to writing the same JSONL/markdown files directly and note the fallback in the session

## Purpose

Apply the compression/decompression reasoning flow to construct, validate, and apply robust mental models that:
- Explain observations
- Predict outcomes
- Guide decisions
- Transfer across situations

---

## Core Instruction: The Reasoning Flow

Follow this five-step flow for every think skill query. This is **universal** - it works regardless of domain.

## Iterative Refinement (Fail-Fast Architecture)

**Principle**: Catch errors early (Steps 2-4) before wasting effort on broken foundations.

**Attempt Loop** (max 3 attempts):

1. **Generate model** (Step 1)
2. **GATE 1: Step 2 Validate**
   - Mechanistic Depth check
   - Evidence Weighting check
   - If FAIL → Generate alternative, try again
   - If PASS → Proceed to Step 3

3. **GATE 2: Step 3 Test**
   - Counterexamples + Historical analogies
   - If major contradiction → Return to Step 1
   - If minor refinement → Adjust and continue

4. **Continue through Steps 4-6**

**Alternative Generation Methods** (when attempt fails):

1. **Extend Mechanism**: Add deeper causal levels (for shallow models)
2. **Inversion**: Flip key assumption (test opposite hypothesis)
3. **Variable Substitution**: Keep structure, change key variable
4. **Scope Narrowing**: Make model more specific (for overly broad models)

**Stopping Conditions**:
- ✅ Attempt passes all gates → Proceed with that model
- ❌ 3 attempts exhausted → Report uncertainty with partial results
- ❌ Contradictory evidence (Strong for AND against) → Report genuine uncertainty

**Example Flow**:
```
Attempt 1: "Power bottleneck extends moat"
  → Step 2: Mechanistic Depth FAIL (Level 2 only)
  → Generate alternative via "Extend Mechanism"

Attempt 2: "Power → 800V co-engineering → Switching costs → Moat"
  → Step 2: Mechanistic Depth PASS (Level 5)
  → Step 2: Evidence Weighting PASS (Strong: Vertiv backlog)
  → Continue to Step 3-6
  → Success!
```

**Logging**: All attempts logged with constraints for learning

---

## Logging Patterns (Instructions for Agent)

### Initialization Pattern (At Query Start)

After reading this SKILL.md, initialize logging:

1. Resolve MCP (before first write):
   - Server id is exactly `log-agent` (see **Server id rules** above)
   - Prefer `GetMcpTools(server="log-agent")` once per session to confirm schema/`ready`
   - Related equity MCPs use exact ids too: `yfinance`, `sec-edgar`, `Alpha Vantage` (space included)

2. Generate log file paths (absolute paths required by log-agent):
   - Base: `<repo>/skills/think/logs/YYYY-MM-DD-HHMMSS-{query-slug}`
   - JSONL: `{base}.jsonl`
   - Markdown: `{base}.md`
   - Ensure the `logs/` directory exists before `create_log`

3. Create log:
   ```
   CallMcpTool(server="log-agent", toolName="create_log",
               arguments={
                 "log_path": "{absolute_jsonl_path}",
                 "metadata": {
                   "query": "{user_query}",
                   "framework": "think-6step",
                   "session_id": "{generate_id}"
                 }
               })
   ```

4. Notify user: "Logging session to skills/think/logs/YYYY-MM-DD-HHMMSS-{query-slug}.{jsonl,md}"

---

### Step Logging Pattern

At each step (1-6), pass `event_data` (required arg name):

1. Log step start:
   ```
   CallMcpTool(server="log-agent", toolName="append_event",
               arguments={
                 "log_path": "{absolute_jsonl_path}",
                 "event_type": "step_start",
                 "event_data": {"step": 2, "step_name": "validate", "attempt": N}
               })
   ```

2. Log significant decisions/checks (same `append_event` shape):
   - Check starts: `event_type="check_start"`, `event_data={"check": "mechanistic_depth", "attempt": N}`
   - Check results: `event_type="check_pass"` or `"check_fail"`
   - Data gathered: `event_type="data_gathered"`
   - Verification exceptions: `event_type="verification_exception"`
   - Adversarial parity: `event_type="adversarial_parity_check"`
   - Temporal scope: `event_type="temporal_scope"`

3. Log step end:
   ```
   CallMcpTool(server="log-agent", toolName="append_event",
               arguments={
                 "log_path": "{absolute_jsonl_path}",
                 "event_type": "step_end",
                 "event_data": {"step": 2, "result": "pass", "attempt": N}
               })
   ```

---

### MCP Call Logging Pattern

Whenever using yfinance, sec-edgar, Alpha Vantage, or other MCPs — use each server's **exact** catalog id (`yfinance`, not `user-yfinance`):

1. Before call:
   ```
   CallMcpTool(server="log-agent", toolName="append_event",
               arguments={
                 "log_path": "{absolute_jsonl_path}",
                 "event_type": "mcp_call_start",
                 "event_data": {
                   "server": "yfinance",
                   "tool": "get_company_overview",
                   "input_args": {"symbol": "NVDA"},
                   "attempt": N
                 }
               })
   ```

2. After call:
   ```
   CallMcpTool(server="log-agent", toolName="append_event",
               arguments={
                 "log_path": "{absolute_jsonl_path}",
                 "event_type": "mcp_call_end",
                 "event_data": {
                   "server": "yfinance",
                   "tool": "get_company_overview",
                   "status": "success",
                   "output_summary": {
                     "Symbol": "NVDA",
                     "PERatio": 31.2,
                     "ForwardPE": 28.1,
                     "ProfitMargin": 0.63
                   },
                   "attempt": N
                 }
               })
   ```

**Note**: Log summary only (key fields), not full output

---

### Attempt Tracking Pattern

At attempt boundaries (same `append_event` / `event_data` shape):

1. Attempt start: `event_type="attempt_start"`, `event_data={"attempt": 1, "model_hypothesis": "...", "generation_method": "abductive_reasoning"}`

2. If attempt fails: `event_type="attempt_end"` with `result="rejected"`, then `event_type="alternative_generation"` with method/constraint/new_hypothesis

3. If attempt succeeds: `event_type="attempt_end"` with `result="accepted"`

---

### Finalization Pattern (At Query End)

1. Log query end: `event_type="query_end"`, `event_data={"selected_attempt": 2, "total_attempts": 2, "confidence": "high"}`

2. Generate markdown summary:
   - Prefer `CallMcpTool(server="log-agent", toolName="read_log" or "get_summary", ...)`
   - Format with numerical prefixes and indentation:
     ```
     1. Attempt 1: Power bottleneck hypothesis
        1.1 Step 2: Validate
            ❌ Mechanistic Depth: FAIL (Level 2, need 3+)
        1.2 Result: REJECTED
     2. Attempt 2: 800V co-engineering hypothesis
        2.1 Step 2: Validate
            ✅ Mechanistic Depth: PASS (Level 5)
        2.2 Result: ACCEPTED
     ```
   - Write markdown file at `{base}.md`

3. Report to user:
   ```
   "Session logged to skills/think/logs/2026-08-03-143000-stock-analysis.{jsonl,md}"
   ```

---

### Key Operating Principles

**1. Take action, don't interrogate**

Do NOT ask the user for publicly available information:
- Company information, financials, business models → Web search, SEC Edgar, financial APIs
- Industry dynamics, competitors, market data → Research tools
- Technical details, definitions, facts → Look them up

Only ask the user for:
- Personal preferences, constraints, goals (time horizon, risk tolerance, position size)
- Context you cannot infer (why interested, prior decisions, portfolio constraints)
- Choices between valid alternatives (which approach if genuinely unclear)

**Default behavior**: Start reasoning immediately with available information. Gather more data using tools as needed. Only stop to ask if you need user-specific input that cannot be obtained otherwise.

**Example - Good**:
- User: "Should I invest in Company X?"
- Agent: *Searches for Company X, pulls financials, researches industry, builds structure, then asks only about user's time horizon/goals if not already stated*

**Example - Bad**:
- User: "Should I invest in Company X?"
- Agent: "What does Company X do? What's their business model? Do you have their financials?"

---

### Step 1: Build Structure

**What**: Create a mental model that explains the domain or question.

**How**:
- Identify key entities, variables, and relationships
- Build causal mechanisms (not just correlations)
- Consider multiple candidate structures if unclear

**Output**: An internal mental model with clear components and mechanisms

**Quality plugin augmentation** (if available):
- Understand common structures experts use in this domain (distilled into plugin)
- Context on known frameworks/approaches (brief 1-2 sentence summaries)

---

### Step 2: Validate Structure (CRITICAL GATE)

**What**: Test whether the structure explains observations and is internally consistent.

**FAIL-FAST CHECKS** (Required):

#### Check 1: Mechanistic Depth Probing

**Method**: "Can I explain this at 3+ levels of causation?"

**Process**:
1. State your claim
2. Ask "Why?" and answer at each level:
   - Level 1: Immediate cause
   - Level 2: Cause of that cause  
   - Level 3+: Root cause
3. If you hit "I don't know" or circular reasoning before Level 3 → **FAIL**

**Logging**:
```
log: check_start (check="mechanistic_depth")
log: depth_level (level=1, question="...", answer="...")
log: depth_level (level=2, question="...", answer="...")
log: depth_stop (level=2, reason="circular_reasoning")
log: check_fail (check="mechanistic_depth", achieved_level=2, required_level=3)
```

**Example**:
- ❌ Shallow: "NVDA benefits from AI demand" (Level 1 only)
- ✅ Deep: "NVDA benefits because: Data centers need GPUs (L1) → Scaling laws require more compute (L2) → Winner-take-most dynamics justify compute cost (L3) → ..."

**If FAIL**: Generate alternative model with deeper mechanism. Max 3 attempts.

---

#### Check 2: Evidence Weighting

**Method**: "Is my evidence Strong, Medium, or Weak?"

**Criteria**:
- **Strong**: Independent source, confirms prediction, high signal-to-noise, visible mechanism
- **Medium**: Partial independence, consistent with alternatives, moderate noise
- **Weak**: Same source as prior, only confirms known facts, high noise

**Process**:
1. For each evidence piece, assess: Direction, Strength, Independence
2. If ALL evidence is Weak → **FAIL**
3. Need at least 1 Strong independent source to proceed

**Logging**:
```
log: evidence_assessed (source="...", strength="strong", independence=true, rationale="...")
log: check_pass (check="evidence_weighting", strong_count=1)
```

**If FAIL**: Gather better data sources before proceeding.

---

**Step 2 Gate Decision**:
- ✅ Both checks PASS → Proceed to Step 3
- ❌ Either check FAILS → Log failure, generate alternative (return to Step 1)

**How**: (existing validation content)
- Does it explain existing evidence?
- Does it make testable predictions?
- Is it consistent with known facts?
- Can you articulate the causal mechanism?

**Output**: Evidence that structure is sound (or identification of flaws)

**Quality plugin augmentation** (if available):
- Apply domain-specific quality standards (evidence hierarchy, what counts as good evidence)
- Check against known red flags and failure modes

---

### Step 3: Test with Counterexamples

**What**: Stress-test the structure to find limitations.

**How**: Apply three types + historical validation:

1. **Missing Variables**: What factors did you not consider?
   - Effect: Refine the model to include them
   
2. **Contradictions**: What observations contradict the model?
   - Effect: Replace or fundamentally revise the model
   
3. **Boundary Conditions**: Where does the model stop working?
   - Effect: Define scope explicitly

---

**NEW: Analogical Reasoning** (Historical Counterexamples)

**Method**: "What historical parallels exist, and where do they break down?"

**Process**:
1. Identify 2-3 historical analogies with structural similarities
2. Map similarities (what's the same?)
3. Map differences (what's different?)
4. Extract lessons: Which outcomes are likely vs unlikely?
5. **Critical**: Be explicit about where analogy breaks down

**Logging**:
```
log: counterexample_test (type="historical_analogy", analogy="Cisco 1999", 
     similarity="...", difference="...", lesson="...")
```

**Example (NVDA 2026)**:
- **Analogy**: Cisco 1999 networking bottleneck
- **Similarities**: Infrastructure bottleneck, dominant supplier, customer pre-payments
- **Differences**: Cisco lacked software moat (NVDA has CUDA), networking commoditized (AI software proprietary)
- **Lessons**: Bottleneck can last 3-5 years, but margins compress when resolved; NVDA's software moat may extend duration

**Red Flags**:
- Cherry-picking analogies that support thesis only
- Ignoring disanalogies (where it breaks down)
- "This time is different" without evidence

---

**Output**: Refined model with known limitations, scope, and historical risk patterns

**Quality plugin augmentation** (if available):
- Apply domain-specific stress tests (counterexamples distilled from expert knowledge)
- Test approach-specific failure modes

---

### Step 4: Compress

**What**: Distill the structure to its essential insight.

**How**:
- Remove complexity while preserving reasoning capability
- Keep causal mechanisms visible
- Simplicity must be *earned* through validation
- Don't compress into slogans or oversimplifications

---

**NEW: Parsimony Testing** (Explicit Occam's Razor)

**Method**: "Does each variable earn its complexity cost?"

**Process**:
1. List key variables in your model
2. For each: "If I removed this, would my model fail to explain key observations?"
3. If YES → Keep (load-bearing)
4. If NO → Remove (decorative)

**Logging**:
```
log: parsimony_test (variable="automotive_recovery", load_bearing=false, action="remove")
log: parsimony_test (variable="CUDA_moat", load_bearing=true, action="keep")
```

**Example**:
- Full model: GPU demand + Power bottleneck + 800V co-engineering + CUDA moat + AI hype + Automotive recovery
- Test: Remove "Automotive recovery" → Model still explains margins? YES → Remove
- Test: Remove "CUDA moat" → Model still explains 60%+ margins? NO → Keep
- Simplified: GPU demand + Power bottleneck + 800V co-engineering + CUDA moat

**Red Flag**: "Kitchen sink" models (adding every possible variable)

---

**Output**: Compressed principle that captures the validated structure with only load-bearing variables

**Quality plugin augmentation** (if available):
- Use domain-specific compression criteria (what complexity cannot be removed)
- Reference known compressed principles from domain

---

### Step 5: Expand for User Context

**What**: Apply the validated, compressed structure to the user's specific situation.

**How**:
- Recover necessary complexity for their case
- Surface assumptions specific to their context
- Define action steps or deeper understanding
- Specify monitoring signals or follow-up checks

**Output**: Understanding or action guidance tailored to user's situation

---

**Temporal Scoping** (Required when thesis is time-bounded):

If your model has expiration conditions or depends on a window of opportunity, structure output by time horizon:

**Format**:

1. **Near-term (0-12 months)**: [Confidence: HIGH/MEDIUM/LOW]
   - Key drivers: What makes the thesis valid now
   - Entry/recommendation: Specific action
   - Exit trigger: Specific signal or threshold (not vague "monitor")

2. **Medium-term (12-24 months)**: [Confidence: HIGH/MEDIUM/LOW]
   - Degradation factors: What starts to weaken the thesis
   - Position guidance: Hold / reduce / exit
   - Exit trigger: Specific threshold

3. **Long-term (24+ months)**: [Confidence: HIGH/MEDIUM/LOW]
   - Structural changes: What invalidates the thesis
   - Do NOT hold if: Explicit conditions

**Example (Power bottleneck thesis)**:
- Near-term (0-12 mo): HIGH — Vertiv order backlog visible, CapEx committed
  - Exit trigger: Q3 hyperscaler CapEx guidance cuts >15%
- Medium-term (12-24 mo): MEDIUM — Bottleneck persists but margin questions emerge
  - Exit trigger: Transformer lead times compress to <12 months
- Long-term (24+ mo): LOW — Supply chain resolves, margin compression likely
  - Do NOT hold if: AI commercial ROI unproven by Q4 2027

**Logging**:
```
append_event("temporal_scope", {
  "horizon": "near_term",
  "confidence": "high",
  "exit_trigger": "hyperscaler_capex_cut_15pct"
})
```

**Quality plugin augmentation** (if available):
- Use verification methods (code to check claims, data validation, cross-referencing)
- Determine depth based on stakes and domain standards

---

### Step 6: Verify Framework Effectiveness (Required)

**What**: Test whether your reasoning is accurate vs internally consistent but wrong.

**Why**: Steps 1-5 can produce internally coherent analysis that fails externally through confirmation bias, hallucinated mechanisms, or blind spots. Step 6 catches these errors.

**How**: Apply three verification methods:

#### 1. Consequence Testing (Highest Priority)

**Method**: "If my model is TRUE, what ELSE must be observable?"

**Note**: This is deductive prediction testing, not RL/ML counterfactuals (which ask "what if a different action was chosen?").

**Process**:
- Generate 3-5 independent predictions from your model
- Verify **ALL** predictions before proceeding (default: 100% completeness)
- Check predictions against sources you haven't used yet
- Look for evidence that SHOULD exist if model is correct

**Completeness Requirements**:

**Default: 100% verification required** — verify every prediction you generate.

**Exception (<100% allowed ONLY when)**:
1. Data is genuinely unavailable (proprietary, not yet released)
2. Data is cost-prohibitive (subscription beyond reasonable reach)
3. Prediction depends on a future event (cannot verify until it occurs)

**If <100% verified**:
- Document specific reason for each unverified prediction
- Assess: Is unverified prediction load-bearing? (thesis fails if false)
  - If YES → Lower confidence to LOW or mark as SPECULATIVE
  - If NO → Proceed but note limitation explicitly
- Mark thesis for follow-up verification when data becomes available

**Logging**:
```
append_event("verification_exception", {
  "prediction": "SMR_contract_acceleration",
  "reason": "proprietary_data",
  "load_bearing": false,
  "confidence_impact": "none"
})
append_event("verification_completeness", {
  "predictions_generated": 5,
  "verified": 4,
  "unverified": 1,
  "pass_rate": 0.8,
  "action": "proceed_with_documented_exception"
})
```

**Threshold**: If verified predictions <60%, model is weak regardless of exceptions.

**Example (Power bottleneck thesis)**:
- Prediction 1: Power suppliers (Vertiv) should show order backlogs → Verify
- Prediction 2: Hyperscaler CapEx should remain >$600B → Verify
- Prediction 3: Data center construction timelines lengthening → Verify
- Prediction 4: Utility CapEx spiking → Verify

**Output**: Independent confirmation or refutation of key claims

---

#### 2. Adversarial Review (Steel-Man Opposition) — Universal Parity

**Goal**: Test whether bull case is uniquely strong or just internally consistent.

**Method**: Generate counter-thesis and apply **identical rigor** to bull case.

---

**Step A: Generate Counter-Thesis (Generic Methods)**

Use ONE of these systematic generation methods:

1. **Inversion**: Flip your core claim
   - Bull: "X is undervalued" → Bear: "X is overvalued"
   - Bull: "Bottleneck persists 3-5 years" → Bear: "Bottleneck resolves in 12-18 months"

2. **Variable Substitution**: Keep structure, change key variable
   - Bull: "NVDA wins via CUDA moat" → Bear: "AMD wins via open ecosystem"

3. **Mechanism Reversal**: Reverse causal direction
   - Bull: "High demand drives scarcity" → Bear: "High prices destroy demand"

4. **Alternative Explanation**: Different mechanism explains same observations
   - Bull: "Margins high due to moat" → Bear: "Margins high due to temporary shortage"

**Output**: Explicit counter-thesis statement with clear mechanism

---

**Step B: Apply Parity Checklist (Universal Standards)**

Bull and Bear MUST both meet these thresholds:

- **Mechanistic Depth**: ≥3 levels of causal chain (Step 2 standard)
  - If bull reached Level 5, attempt Level 5 for bear
- **Evidence Quality**: ≥1 Strong independent source (Step 2 standard)
  - Gather NEW evidence for bear case (don't reuse bull sources saying "risks exist")
- **Consequence Testing**: 3+ predictions tested (Step 6.1 standard)
  - Generate bear-case predictions: "If bear case TRUE, what ELSE must be observable?"
- **Boundary Conditions**: Explicit scope (Step 3 standard)
  - When/where does bear case apply vs not apply?

**Logging**:
```
append_event("adversarial_parity_check", {
  "bull_mechanistic_depth": 5,
  "bear_mechanistic_depth": 5,
  "parity_met": true
})
append_event("adversarial_adjudication", {
  "bull_criteria_won": 2,
  "bear_criteria_won": 0,
  "tied": 2,
  "decision": "bull_stronger"
})
```

---

**Step C: Honest Adjudication (Scored, Not Narrative)**

Score both theses on identical rubric:

| Criterion | Bull Score | Bear Score | Winner |
|-----------|------------|------------|--------|
| Mechanistic Depth (1-5 levels) | ? | ? | ? |
| Evidence Strength (Strong source count) | ? | ? | ? |
| Consequence Tests Passed (%) | ? | ? | ? |
| Explains Contradictions? | ? | ? | ? |

**Decision Rules**:
- Bull wins 3/4 criteria → High confidence in bull case
- Bull wins 2/4 criteria → Medium confidence
- Tied or bear wins → Genuine uncertainty, report both theses

**Critical**: If you didn't gather bear-case evidence or test bear predictions, adjudication is INVALID (confirmation bias).

**Output**: Calibrated confidence with explicit risks and limitations

---

#### 3. Cross-Source Triangulation

**Method**: "Verify key claims from 2+ independent sources"

**Process**:
- Identify critical claims your thesis depends on
- Check each claim against multiple independent sources
- Sources should be structurally different (not correlated)
- If sources contradict, investigate discrepancy

**Example (Power bottleneck)**:
- Source 1: Industry reports (Gartner)
- Source 2: Power suppliers (Vertiv earnings)
- Source 3: Hyperscaler CapEx breakdowns
- Source 4: Utility grid expansion timelines
- All four confirm → High confidence

**Output**: Evidence quality assessment (strong vs weak vs unverified)

---

**Step 6 Output**: Confidence assessment with identified uncertainties

**Confidence levels**:
- **High**: 3/3 methods pass, 100% consequence verification (or documented non-load-bearing exceptions only), adversarial parity met and bull wins 3/4 criteria, multiple independent sources
- **Medium**: 2/3 methods pass, ≥80% consequence verification with documented exceptions, bull wins 2/4 adversarial criteria
- **Low**: <2/3 methods pass, <80% consequence verification, bear wins or ties adversarial adjudication, single source only, or load-bearing prediction unverified

**Red flags (reasoning may be wrong)**:
- <60% of verified consequence predictions hold
- Adversarial review is narrative-only (no bear evidence gathered)
- Bull and bear cases equally strong on scored adjudication (high uncertainty)
- Load-bearing prediction left unverified without documented reason
- Only one source supports key claim
- Sources contradict and discrepancy unexplained

**Note**: Steps 1-5 build the analysis. Step 6 verifies it's sound, not just coherent.

---

**Future enhancements (TODO)**:
- Calculation Verification: Reproduce key numbers from raw sources (catches data bugs)
- Predictive Testing: Make falsifiable predictions, check when new data arrives (tracks accuracy over time)

---

## Key Principles (Apply Throughout)

These principles guide the entire flow:

1. **Structure-first reasoning**: Build models that explain mechanisms, not just list facts
2. **Reality-based calibration**: Test structures against evidence and counterexamples
3. **Earned simplicity**: Compress only after validation
4. **Explicit scope**: Define where reasoning applies and where it doesn't
5. **Separate facts from interpretation**: Surface assumptions
6. **Take action, don't interrogate**: Gather publicly available information yourself; only ask users for personal context/preferences

---

## When to Go Deep vs Stay Light

**Go deep when**:
- Stakes are high (major decision, significant investment, irreversible action)
- Multiple valid structures exist with real trade-offs
- Assumptions are hidden or unclear
- The user explicitly wants structured analysis
- Domain has specialized guidance available

**Stay light when**:
- Query is straightforward with obvious structure
- Stakes are low
- User wants quick guidance, not exhaustive analysis
- Your natural reasoning already produces sound structure

**Adaptive rigor**: The flow stays the same, but depth at each step varies.

---

## Domain Plugin Integration

### How Plugins Work

Quality plugins **augment** the core flow by providing domain-specific evaluation criteria at each step. They don't replace the flow.

**Available plugins**: Check `quality/` directory

**Current domains**:
- `equity/` - Stock investing quality standards (compiled from expert knowledge)

### When Plugins Are Loaded

**Automatic detection**: If query falls into a domain with available plugins, load relevant guidance.

**What plugins provide**:
- **Tool/data source guidance**: Which APIs, MCPs, or data sources to use (respecting rate limits)
- Quality standards for evidence (evidence hierarchy)
- Common failure modes and red flags
- Verification methods (code, data checks, cross-referencing)
- Compression/expansion criteria
- Context on known approaches (distilled 1-2 sentence summaries)

**What plugins don't do**:
- Replace the five-step flow
- Provide rigid checklists
- Determine the reasoning path

### Example: Equity Investing Domain

When you detect an equity investing question:

**First: Read tool guidance**
- Check `quality/equity/taste.md` "Tools Used" section
- Follow data source priority: **yfinance (primary)** → Alpha Vantage (fallback) → SEC Edgar (deep-dive)
- yfinance has generous rate limits: Can pull 5-10 stocks per analysis

**Step 1 (Build Structure)**:
- Read `quality/equity/taste.md` for context on 5 known approaches (Value, Growth, Passive, Momentum, Macro)
- Have conversation with user to understand context (time horizon, goals, market conditions)
- Build structure for what makes a good investment

**Step 2 (Validate)**:
- Apply evidence hierarchy from plugin (audited financials > management promises)
- Use recommended tools: yfinance/Alpha Vantage for verified trailing metrics
- Check quality standards (falsifiable claims, defined scope, causal mechanisms)
- Use quality indicators if relevant approach identified (e.g., RPO growth for Growth approach)

**Step 3 (Counterexamples)**:
- Apply generic counterexamples (assumption reversal, alternative explanations, boundary conditions)
- Apply approach-specific stress tests if relevant (e.g., "What if CapEx reverses?" for Growth)
- Check common failure modes (narrative without evidence, circular reasoning, etc.)

**Step 4 (Compress)**:
- Use investing-specific compression criteria from plugin
- Keep explicit: valuation, quality, timing, risk
- Example: "Good business ≠ good investment without price/timing/risk"

**Step 5 (Expand)**:
- Follow tool strategy from plugin: Pull fundamentals for 5-10 stocks via yfinance MCP
- Use verification methods from plugin (pull 10-K data via SEC Edgar when needed)
- Determine depth based on stakes (concentrated bet vs quick sanity check)
- Apply relevant quality indicators
- Add "Data Sources & Verification" section per citation guidance

**Key**: Conversational, not interrogative. Ask intelligent questions to understand context, don't run through a checklist.

**Tool usage**: Use yfinance MCP as primary source (generous limits). Fall back to Alpha Vantage only if needed. Acknowledge gaps explicitly if data unavailable.

**Note**: The plugin provides evaluation criteria compiled from expert knowledge (wiki-finance, books, experience). It's self-contained - no runtime dependencies on external files.

---

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
- Use section headers that signal structure naturally ("Structure", "Evidence", "Risks", "When This Fails")
- Lead with "Here's my approach: ..." when approach choice matters
- Embed assumptions and limitations naturally in the flow
- Show your reasoning path through clear structure, not narration

---

## Data Citation & Verification

When your analysis relies on specific data points, provide a clean audit trail without cluttering the reasoning flow.

### During Analysis (Clean)
Use subtle inline markers for confidence level:
- No marker = verified/high confidence
- "(estimated)" = analyst consensus/projections
- "(guidance)" = management statements
- "(assumed)" = inference from available data

Example:
```
- NVDA trailing PE: 31.2x
- NVDA forward PE: ~28x (estimated)
- Revenue growth: 46% YoY
- Expected CapEx trends: +15-20% (guidance)
```

### At End (Full Verification Section)
Add a "Data Sources & Verification" section at the end with three parts:

**1. Verified Data** - Show how to reproduce:
```
Verified Data:
- Stock fundamentals: Alpha Vantage COMPANY_OVERVIEW for NVDA, AMD, INTC
  - Fields used: PERatio, EPS, MarketCapitalization, ProfitMargin
  - Reproduce: CallMcpTool(server="Alpha Vantage", toolName="COMPANY_OVERVIEW", symbol="NVDA")
```

**2. Estimated Data** - Provide search queries and sources:
```
Estimated Data:
- Forward P/E, analyst targets: Web search "NVDA analyst consensus 2026"
  - Sources: Reuters, Bloomberg, Seeking Alpha
- CapEx guidance: Web search "hyperscaler capex guidance 2026"
  - Sources: Company earnings calls, investor presentations
```

**3. Confidence Levels** - Be explicit:
```
Confidence:
- High: Trailing metrics from audited financials (PE, EPS, margins)
- Medium: Forward estimates from analyst consensus
- Low: Guidance subject to change (CapEx projections, management targets)
```

### Key Principles
- **Reproducible**: Show exact tool + parameters for verified data
- **Traceable**: Provide search queries (and URLs when available) for estimates
- **Honest**: Explicitly list what couldn't be verified or has low confidence
- **Non-intrusive**: Keep verification at the bottom so it doesn't disrupt reasoning flow

---

## Quality Criteria

Good reasoning demonstrates:
- **Structure over facts**: Builds models that explain mechanisms, not just lists information
- **Reality-tested**: Tests structures against evidence and counterexamples (Step 3 stress tests)
- **Explicit assumptions**: Makes hidden assumptions visible
- **Bounded scope**: Defines where reasoning applies and where it breaks
- **Adaptive rigor**: Goes deep when stakes are high, stays light when appropriate

**Not** about following procedures perfectly. It's about producing sound reasoning through the compression/decompression flow.

---

## Supporting Resources

**Framework documentation** (`docs/`):
- `README.md` - Doc index (boundaries and reading order)
- `architecture.md` - Two-layer design + plugins (users start here)
- `framework.md` - Concepts and terminology
- `principles.md` - Why the framework evolved
- `reasoning-techniques.md` - Techniques per step, fail-fast gates, logging schema
- `quality.md` - Taste and judgment
- `learning-to-do.md` - Execution gaps and fixes
- `../ir/dag-spec.md` - Formal pipeline contracts

**Evaluation examples** (`evals/`):
- `ai_education.md` - AI and education analysis
- `investing.md` - Investment decision framework
- `switzerland.md` - Switzerland success analysis

**Domain plugins** (`quality/`):
- `equity/` - Equity investing quality standards
  - `taste.md` - Compiled evaluation criteria from expert knowledge

---

## Remember

The six-step flow is universal and always applies:

1. Build Structure
2. Validate
3. Test (counterexamples)
4. Compress
5. Expand
6. Verify

Domain plugins make this flow **sharper** in specialized domains, but they never replace it. Technique catalog: `docs/reasoning-techniques.md`.
