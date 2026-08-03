# Step 6: Verify Framework Effectiveness (DRAFT)

**Status**: Experimental - Testing on NVDA case study (Aug 2026)

---

## Motivation

The five-step framework (Build → Validate → Test → Compress → Expand) can produce **internally consistent but externally wrong** reasoning through:
- Hallucinated causal mechanisms
- Confirmation bias in evidence selection
- Weak counterexample testing
- Data source errors
- Single-period noise mistaken for signal

**Step 6 adds systematic verification** to differentiate:
- **Accurate reasoning**: Multiple independent sources confirm, consequence tests hold, temporally consistent
- **Noisy data**: Single-period spike, doesn't hold across time
- **Hallucination**: Internally consistent but fails consequence tests

---

## The Verification Problem

**Example failure mode**:
1. **Step 1**: Build wrong causal model (hallucinate mechanism)
2. **Step 2**: Cherry-pick confirming evidence (confirmation bias)
3. **Step 3**: Test weak counterexamples that don't break it
4. **Step 4-5**: Compress and expand wrong model with high confidence
5. **Result**: Confident but incorrect analysis

**Key insight**: Internal consistency ≠ External validity

---

## Step 6: Verify Framework Effectiveness

### What
Test whether your reasoning is accurate vs internally consistent but wrong.

### How
Apply six verification methods to catch errors, noise, and hallucinations:

#### 1. Consequence Testing (Strongest)

**Method**: "If my model is TRUE, what ELSE must be observable?"

**Note**: This is deductive prediction testing, not RL/ML counterfactuals (which ask "what if I had chosen a different action?"). We test whether the model's logical consequences match independent evidence.

**Process**:
- Generate 3-5 independent predictions from your model
- Check predictions against sources you haven't used yet
- Look for evidence that SHOULD exist if model is correct
- Threshold: If <60% of predictions hold, model is weak

**Example (NVDA power bottleneck thesis)**:
- Prediction 1: Power infrastructure suppliers (Vertiv, Eaton) should show order backlogs → Check their 10-Qs
- Prediction 2: Data center construction timelines lengthening → Check REIT earnings calls
- Prediction 3: Utility CapEx spiking → Check utility company guidance
- Prediction 4: GPU inventory accumulating (can't deploy due to power) → Check NVDA inventory levels
- Prediction 5: Data center power capacity additions accelerating → Check industry reports

**Test**: If 3/5 predictions fail, power bottleneck thesis is weak or wrongly specified

**Why "Consequence Testing" not "Counterfactual"?** In ML/RL, counterfactuals mean "what would happen if agent chose action B instead of A?" This is different - we're testing whether observable consequences match our model's predictions.

---

#### 2. Temporal Consistency

**Method**: "Does this pattern hold across multiple time periods?"

**Process**:
- Check if key patterns hold across 3+ time periods (quarters/years)
- One quarter is noise; three quarters is signal
- Look for trend vs one-time event

**Example (NVDA margins)**:
- Q2 2026: Margins 73%
- Check Q1 2026, Q4 2025, Q3 2025, Q2 2025
- If margins were 60% → 58% → 61% → 73%, current 73% might be one-time spike
- If margins were 68% → 70% → 72% → 73%, this is consistent trend

**Red flag**: Pattern appears in one period, disappears in others

---

#### 3. Calculation Verification

**Method**: "Can I reproduce the key numbers from raw sources?"

**Process**:
- For critical metrics, don't trust parsed data alone
- Pull raw financial statements (10-K/10-Q line items)
- Recalculate key metrics yourself (PE, margins, growth rates)
- Check if your calculation matches reported numbers

**Example (NVDA Forward PE)**:
- yfinance reports: Forward PE = 15.57
- Verify: Pull analyst consensus Forward EPS estimates manually
- Calculate: Current Price ($200.75) / Forward EPS → Compare to 15.57
- If discrepancy >10%, investigate (data source error? stale data? wrong fiscal year?)

**Red flag**: Can't reproduce key numbers from raw sources

---

#### 4. Adversarial Review (Steel-Manning Opposition)

**Method**: "Build the strongest possible counter-thesis and test THAT"

**Process**:
- State your thesis clearly
- Build the **best possible counter-argument** (not a strawman)
- Apply same rigor to counter-thesis: gather evidence, test counterfactuals
- Honest assessment: Which explains observations better?

**Example (NVDA)**:
- **Bull thesis**: Power bottleneck extends NVDA moat through 800V co-engineering
- **Bear thesis**: Power bottleneck delays revenue 2+ years, competitive window opens for AMD/custom chips, margins compress as customers negotiate delays
- **Test both**: Which has more supporting evidence? Which makes better predictions?

**Red flag**: Bear case is equally strong as bull case → High uncertainty

---

#### 5. Cross-Source Triangulation

**Method**: "Verify key claims from 2+ independent sources"

**Process**:
- Identify critical claims your thesis depends on
- Check each claim against multiple independent sources
- Sources should be structurally different (company filings, competitor data, industry reports, supplier earnings)
- If sources contradict, investigate discrepancy

**Example (NVDA power bottleneck)**:
- Claim: "Data center power capacity is the binding constraint"
- Source 1: NVDA investor commentary
- Source 2: Hyperscaler (MSFT/GOOGL/AMZN) CapEx breakdowns
- Source 3: Data center REIT earnings calls
- Source 4: Utility company grid expansion timelines
- Source 5: Power equipment suppliers (Vertiv/Eaton) order books

**Red flag**: Only company mentions the claim; no independent confirmation

---

#### 6. Predictive Testing

**Method**: "Make falsifiable predictions about future data"

**Process**:
- Based on your model, predict specific outcomes for next quarter/year
- Make predictions falsifiable (specific thresholds, not vague)
- Wait for new data to arrive
- Check if predictions hold

**Example (NVDA)**:
- Prediction 1: If power bottleneck is real and extends moat, Q3 2026 gross margins should hold ≥70%
- Prediction 2: Customer advances should grow ≥15% QoQ (continued pre-payments)
- Prediction 3: RPO should stay low <5% of revenue (spot market dynamics persist)
- Prediction 4: Hyperscaler CapEx guidance for 2027 should remain >$600B (demand sustained)
- **Wait for Q3 earnings** → Check predictions

**This is how you separate good model from lucky guess.**

**Red flag**: Predictions consistently fail when new data arrives

---

## Output: Confidence Assessment

After applying verification methods, assign confidence levels:

**High Confidence** (4+ methods pass):
- Consequence tests hold (>60% of predictions confirmed)
- Temporal consistency (pattern holds 3+ periods)
- Can reproduce calculations from raw data
- Cross-source triangulation confirms key claims
- Made falsifiable predictions (if tested)

**Medium Confidence** (2-3 methods pass):
- Some consequence tests hold, some fail
- Temporal data limited or mixed
- Some sources confirm, others neutral/contradictory
- Could build equally strong counter-thesis

**Low Confidence** (<2 methods pass):
- Most consequence tests fail
- Single-period data only
- Can't reproduce calculations
- Only one source supports claim
- Strong counter-thesis exists

---

## Red Flags: Reasoning May Be Wrong

1. **<60% of consequence predictions hold** → Model is incomplete or wrong
2. **Temporal inconsistency** → Current period is noise, not signal
3. **Can't reproduce key calculations** → Data source error or parsing bug
4. **Bull case and bear case equally strong** → High uncertainty, need more data
5. **Sources contradict and discrepancy unexplained** → Core claim is suspect
6. **Predictions consistently fail** → Model doesn't match reality

---

## Integration with Five-Step Framework

**Step 6 is META-LEVEL**: It verifies the quality of your reasoning from Steps 1-5.

**Workflow**:
1. **Steps 1-5**: Build, validate, test, compress, expand (produce analysis)
2. **Step 6**: Verify the analysis using consequence tests, temporal checks, calculations, adversarial review
3. **Output**: Original analysis + confidence assessment + identified uncertainties

**Step 6 is NOT**:
- A replacement for Step 3 (counterexamples)
- Required for every query (use when stakes are high or uncertainty is high)
- A guarantee of correctness (only reduces error probability)

---

## When to Apply Step 6

**Always apply when**:
- High stakes (>5% portfolio allocation, major decision, irreversible action)
- Contradictory evidence emerged in Steps 1-5
- User explicitly asks to verify framework effectiveness
- Making predictions that will be tested later

**Can skip when**:
- Low stakes (exploratory question, sanity check)
- Framework is well-tested in this domain already
- Time/resource constraints
- Straightforward query with obvious structure

---

## Open Questions

1. **Threshold calibration**: Is 60% consequence test success the right bar? Need empirical testing.
2. **Verification cost**: Step 6 is expensive (more research, more tool calls). When is it worth it?
3. **Automated checks**: Can some verifications be automated (temporal consistency, calculation checks)?
4. **Cross-domain applicability**: Does Step 6 work the same for equity investing vs other domains?

---

## Testing Plan

**Next**: Apply Step 6 to NVDA analysis (Aug 2026) to:
- Test each verification method
- Identify what it catches that Steps 1-5 missed
- Calibrate confidence thresholds
- Refine the approach based on findings

**Success criteria**: Step 6 should catch errors, reduce hallucination risk, and provide honest confidence assessment without false precision.

---

## Meta-Note: Verification Limits

**Even with Step 6, we cannot guarantee correctness.** We can only:
- Reduce probability of major errors
- Make uncertainty explicit
- Catch data source bugs and confirmation bias
- Differentiate high-confidence from low-confidence claims

**The market is the ultimate test.** If NVDA predictions fail when Q3 earnings arrive, the model was wrong regardless of internal verification scores.

**Humility is part of rigor.**
