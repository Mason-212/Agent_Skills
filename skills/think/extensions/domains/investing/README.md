# Domain: Equity Investing (Operational Guidance)

## Purpose

Framework-agnostic thinking patterns, verification methods, and failure mode identification for stock reasoning.

This directory provides **operational guidance** on HOW to apply investing frameworks rigorously. For knowledge about WHAT approaches exist and WHEN to use them, see wiki-finance.

**Knowledge base**: [wiki-finance/topics/stocks/investing-approaches.md](file:///Users/chang/Documents/dev/git/wikis/wiki-finance/wiki/topics/stocks/investing-approaches.md)  
**Fallback**: https://github.com/thomaschangsf/wiki-finance/blob/main/wiki/topics/stocks/investing-approaches.md

*Note: If local file:// path fails, agent should print warning and use GitHub link.*

---

## Quality Principles Across All Approaches

### Universal Standards

These apply regardless of whether you're using Value, Growth, Passive, Momentum, or Macro approaches:

- **Evidence over narrative**: Primary sources (10-Ks, CapEx data) > Secondary sources (analyst reports) > Narratives (media hype)
- **Audited data over promises**: Financial statements > Management guidance
- **Falsifiable claims**: Structure reasoning so it can be proven wrong
- **Defined scope**: Specify where reasoning applies and where it doesn't
- **Explicit assumptions**: Surface hidden assumptions that could break

### Approach Selection

To choose which investing approach to use:

**See**: [wiki-finance: investing-approaches](file:///Users/chang/Documents/dev/git/wikis/wiki-finance/wiki/topics/stocks/investing-approaches.md)  
**Fallback**: https://github.com/thomaschangsf/wiki-finance/blob/main/wiki/topics/stocks/investing-approaches.md

---

## Thinking Patterns (Framework-Agnostic)

### Pattern 1: Evidence Hierarchy

When evaluating any investment claim, trust sources in this order:

**Tier 1 (Highest trust)**:
- Audited financial statements (10-K, 10-Q)
- Contract disclosures (backlog, RPO, long-term agreements)
- CapEx allocation data

**Tier 2 (Verify independently)**:
- Management commentary (earnings calls, investor presentations)
- Industry reports (cross-reference multiple sources)
- Competitor disclosures

**Tier 3 (Low trust)**:
- Analyst narrative pitches without data
- Forward guidance without contractual support
- Media coverage and social sentiment
- Valuation arguments based on multiples alone

**Application**: Always start with Tier 1 sources. If a thesis depends primarily on Tier 3 sources, flag it as speculative.

---

### Pattern 2: Scope Testing

For any investment thesis, explicitly define boundaries:

**Questions to ask**:
1. **Where does this work?**
   - What market conditions? (rising rates, falling rates, high volatility, etc.)
   - What time horizon? (1 year, 5 years, 10+ years)
   - What investor type? (active, passive, concentrated, diversified)

2. **Where does this fail?**
   - What conditions would break the thesis?
   - Which market environments favor alternatives?
   - What assumptions are required?

3. **What makes this better than alternatives?**
   - Why this approach vs others in current environment?
   - What edge does this provide?

**Application**: Before accepting any reasoning, map it to conditions where it works and explicitly state where it doesn't.

---

### Pattern 3: Mechanism Over Correlation

Don't confuse correlation with causation. Always identify the causal mechanism.

**Weak reasoning** (correlation): "Stock X went up when rates fell, so it will go up next time rates fall."

**Strong reasoning** (mechanism): "Stock X's valuation depends on discounting distant cash flows. When rates fall, the present value of those cash flows increases, creating upward pressure on price."

**Application**: For any claim, ask "What is the causal mechanism?" If you can't articulate it, the claim is likely pattern-matching without understanding.

---

## Verification Methods

### Verification 1: Write Code to Check Claims

**When to use**: Analyzing financial metrics, testing correlations, backtesting strategy assumptions.

**How**:
- Pull financial data programmatically (yfinance, SEC Edgar API)
- Calculate metrics from raw data (don't trust pre-calculated numbers)
- Backtest assumptions over historical periods
- Verify relationships hold across multiple companies/sectors

**Where code lives**: `wiki-finance/sources/investing/tools/`

**Example use cases**:
- Verify "RPO growing faster than revenue" with actual 10-K data
- Calculate gross margin trends across supply chain
- Test correlation between CapEx announcements and supplier backlog
- Backtest momentum signals over different market regimes

---

### Verification 2: Cross-Reference Sources

**When to use**: Validating narratives about bottlenecks, CapEx flows, or industry dynamics.

**How**:
- Check multiple company filings in the same supply chain
- Verify hyperscaler CapEx guidance from multiple quarterly reports
- Compare segment reporting across competitors
- Cross-reference industry reports with company disclosures

**Example workflow** (for bottleneck claims):
1. Identify claimed bottleneck (e.g., "data center power constraints")
2. Check multiple electrical equipment suppliers' 10-Ks for backlog growth
3. Verify hyperscaler CapEx guidance mentions power infrastructure
4. Look for third-party industry reports confirming constraint

**Red flag**: If only one source mentions the bottleneck, it may not be real.

---

### Verification 3: Business Flow Analysis

**When to use**: Testing if competitive advantage is real or easily replicable.

**How**:
- Map customer workflow and integration points
- Identify qualification cycles and regulatory barriers
- Assess switching costs and vendor lock-in
- Estimate time-to-replicate for competitors

**Example questions**:
- How long does it take to certify a new supplier? (qualification cycle)
- What regulatory approvals are required? (barriers to entry)
- What would it cost a customer to switch providers? (switching costs)
- Could a competitor acquire the capability through acquisition?

**Application**: Strong moats have measurable barriers (5+ year qualification, regulatory protection, patent depth). Weak moats lack these concrete obstacles.

---

## Counterfactuals and Stress Tests

### Generic Counterfactual Patterns (All Approaches)

#### Pattern A: Assumption Reversal
**Question**: What if the core assumption breaks?

**How to apply**:
1. Identify the 1-2 critical assumptions
2. Imagine they reverse completely
3. Does the thesis still work? If not, how fragile is it?

**Example**: Thesis assumes low rates persist → Test: What if rates spike 200bps?

---

#### Pattern B: Alternative Explanations
**Question**: What else could explain the same observations?

**How to apply**:
1. State the observed phenomenon
2. Generate 2-3 competing causal models
3. Determine which model makes the most testable predictions

**Example**: Stock went up 50% → Could be: (a) fundamental improvement, (b) sector rotation, (c) short squeeze. Which model predicts next quarter's behavior?

---

#### Pattern C: Boundary Conditions
**Question**: In what market conditions does this fail?

**How to apply**:
1. Map approach to economic regimes (growth/recession, high/low rates, high/low vol)
2. Identify regimes where approach underperforms
3. Check if we're entering one of those regimes

**Example**: Value investing underperforms in low-rate tech booms → Are we in one now?

---

## Common Failure Modes (Approach-Agnostic)

### Red Flag 1: Narrative Without Evidence
**What it is**: Compelling story with no audited proof in financial statements.

**Test**: Can you verify the core claim in 10-K/10-Q? If not, it's speculation.

**Example**: "AI infrastructure boom" → Check: Are equipment suppliers showing backlog growth?

---

### Red Flag 2: Extrapolation Without Mechanism
**What it is**: Past performance projected forward without explaining WHY it should continue.

**Test**: What mechanism drives continued performance? Can that mechanism break?

**Example**: "Stock up 100% last year, will repeat" → Why? What changed fundamentally?

---

### Red Flag 3: Undefined Scope
**What it is**: Claim works "always" or "never" without boundary conditions.

**Test**: In which market conditions would this fail? If answer is "none," it's over-confident.

**Example**: "Growth stocks always outperform" → False. They underperform in high-rate regimes.

---

### Red Flag 4: Circular Reasoning
**What it is**: Success depends on the thesis working (tautology).

**Test**: Does return depend on fundamentals or just sentiment/multiple expansion?

**Example**: "Stock will go up because people will buy it" → Circular. What fundamental change drives buying?

---

### Red Flag 5: Untestable Claims
**What it is**: Success criteria can't be measured or falsified.

**Test**: What specific outcome would prove this wrong? If none, it's not falsifiable.

**Example**: "Management has great vision" → How do you measure vision? What outcome disproves it?

---

## Expansion Triggers

When to dig deeper and expand analysis (applies to all approaches):

1. **High stakes**: Position size would be meaningful (>5% of portfolio)
2. **Counterparty risk**: Thesis depends on specific customer/partner quality
3. **Edge cases**: Situation near boundary conditions of framework
4. **Conflicting evidence**: Multiple sources contradict each other
5. **High uncertainty**: Causal mechanism unclear or disputed

**What to expand into**:
- Detailed financial modeling (segment-level, scenario analysis)
- Supply chain mapping (who depends on whom)
- Competitive dynamics (barriers to entry, switching costs)
- Management track record (capital allocation history)
- Industry structure analysis (oligopoly, commodity, winner-take-all)

---

## Integration with Think Skill

When using think skill for stock analysis:

### Step 1: Clarify Objective
- Is user looking for new ideas (discovery) or validating existing thesis (evaluation)?
- Which investing approach are they using? (or should they use based on current environment?)

### Step 2: Reference Knowledge Base
- Load relevant framework from wiki-finance
- Understand approach-specific quality standards

### Step 3: Apply Thinking Patterns
- Evidence hierarchy: What sources support the claim?
- Scope testing: Where does this work and fail?
- Mechanism identification: What's the causal chain?

### Step 4: Run Verification Methods
- Code: Pull financial data to verify claims
- Cross-reference: Check multiple sources
- Business flow: Map competitive dynamics

### Step 5: Execute Counterfactuals
- Generic: Assumption reversal, alternative explanations, boundary conditions
- Approach-specific: Based on framework being used (see approach-specific files)

### Step 6: Check Failure Modes
- Scan for red flags (narrative without evidence, circular reasoning, etc.)
- Flag any that apply

### Step 7: Determine Output
- Understanding: Explain the causal mechanism and evidence
- Action: Score against framework criteria, recommend watchlist or position

---

## Approach-Specific Operational Files

For operational guidance specific to each investing approach, see:

- **[growth.md](./growth.md)** - Four-lens framework operational procedures
- **[value.md](./value.md)** - Value investing counterfactuals and verification patterns
- **[momentum.md](./momentum.md)** - Momentum approach operational guidance
- **[passive.md](./passive.md)** - Passive indexing verification patterns
- **[macro.md](./macro.md)** - Macro approach operational procedures

Each approach-specific file contains:
- Approach-specific counterfactuals and stress tests
- Verification patterns unique to that approach
- Quality indicators specific to that philosophy
- Integration guidance with the think skill

---

## Philosophy

> "The knowledge of WHAT approaches exist lives in wiki-finance. The operational guidance on HOW to apply them rigorously lives here."

This directory provides thinking patterns, verification methods, and failure mode detection that work across all investing approaches.

For approach-specific knowledge (what makes a good Value stock vs Growth stock), see wiki-finance.

For verification code implementations, see wiki-finance/sources/investing/tools/.

**Quality in reasoning means**: Evidence-based, mechanistic, falsifiable, scope-aware, and verification-backed.
