# Equity Investing Quality Standards

## Purpose

This file defines quality standards for evaluating equity investment reasoning. Use these criteria to assess whether investment models and reasoning are sound.

---

## Context: Five Investing Approaches

Five core approaches exist in equity investing. Each works best in different market environments:

**Value (Graham)**: Buy undervalued assets with margin of safety, wait for mean reversion. Best in rising rates/inflation. Fails when rates stay low (value traps).

**Growth (Fisher)**: Buy exceptional fast-growing companies, hold long-term. Best in falling rates/tech booms. Fails when rates spike (distant cash flows discounted heavily).

**Passive (Bogle)**: Broad index fund, minimize fees, capture market returns. Best in steady bull markets. Fails in prolonged bear markets (no downside protection).

**Momentum (Lefèvre)**: Ride price trends, cut losses ruthlessly. Best in strong directional trends. Fails in choppy/mean-reverting markets.

**Macro (Dalio)**: Uncorrelated asset portfolio for all economic regimes. Best in geopolitical chaos/regime shifts. Fails in stable low-volatility environments.

**Note**: The specific approach matters less than applying rigorous quality standards to whatever approach is used.

---

## Tools Used

This section defines which data sources and tools to use for equity analysis, respecting rate limits and data quality hierarchy.

### Data Source Strategy

**For verified fundamentals (Tier 1 data):**

1. **yfinance (Yahoo Finance API)** (Primary - Generous limits)
   - Status: **Available via MCP** (`mcps/python/yfinance/`)
   - Use for: Real-time fundamentals (PE, forward PE, EPS, margins, revenue growth, analyst targets)
   - Rate limit: Much more generous than Alpha Vantage (no documented daily cap)
   - When: Primary source for current stock fundamentals

2. **SEC Edgar API** (Deep-dive - Unlimited)
   - Status: **Available via MCP** (`mcps/python/sec-edgar/`)
   - Use for: Audited financial statements from 10-K/10-Q, search for RPO/backlog disclosures, contract terms
   - Rate limit: Unlimited (with proper User-Agent)
   - When: Deep-dive verification, searching for specific disclosures in filings

3. **Alpha Vantage** (Fallback - 25 requests/day free tier)
   - Status: **Available via MCP**
   - Use for: Specialized data (technical indicators, commodities, economic data)
   - Rate limit: 25 requests/day on free tier
   - When: Fallback if yfinance fails, or for non-stock data

**For estimates and forward-looking data (Tier 2/3):**

4. **Web Search**
   - Use for: Forward PE estimates, analyst consensus, guidance, news
   - No rate limits
   - Always cite sources and mark as "estimated"

### Tool Selection Flow

**When analyzing stocks:**

```
Step 1: Define universe via web search (no rate limit)
  → "major semiconductor companies by market cap 2026"
  
Step 2: For 5-10 candidates, pull real-time fundamentals:
  → Use yfinance MCP (primary) - PE, margins, growth, analyst targets
  
Step 3: For top 2-3 deep-dive candidates, verify with SEC Edgar:
  → Pull 10-K data to verify revenue, margins, cash flow
  → Search filings for RPO/backlog disclosures
  → Check customer concentration, contract terms
  
Step 4: Fill gaps with web search:
  → Forward estimates beyond what yfinance provides
  → Qualitative factors, management commentary
  → Mark as "estimated" in verification section
```

### Rate Limit Management

**Best practices:**
- **Define universe first** via web search (free) before pulling data
- **Prioritize yfinance**: Pull real-time fundamentals for 5-10 stocks (generous limits)
- **Deep-dive with SEC Edgar**: Verify top 2-3 candidates with audited 10-K data, search for RPO/backlog
- **Note limitations**: Explicitly state data sources and confidence levels

**Example statement:**
```
"Analyzed 10 semiconductor stocks conceptually. Pulled real-time fundamentals 
for NVDA, AMD, MU, AMAT, LRCX (via yfinance MCP). Deep-dived NVDA and AMD 
via SEC Edgar 10-K: verified revenue growth, searched for RPO disclosures. 
TSM, INTC, QCOM assessed via web search estimates."
```

### What to Verify vs Estimate

**Always verify from Tier 1 sources (if analyzing deeply):**
- Trailing PE, EPS, revenue, margins
- Market cap, shares outstanding
- Historical financial statements
- Dividend history, splits

**Acceptable to estimate from Tier 2/3:**
- Forward PE (analyst consensus)
- Future earnings guidance
- CapEx projections
- Management targets
- Analyst price targets

**Never acceptable:**
- Made-up numbers
- Unsourced claims
- Conflating trailing (verified) with forward (estimated) without labeling

---

## Universal Quality Standards

These apply regardless of investing approach:

### 1. Evidence Over Narrative

**Hierarchy of trust**:
- **Tier 1** (Highest): Audited financial statements (10-K, 10-Q), contract disclosures (backlog, RPO), CapEx allocation data
- **Tier 2** (Verify): Management commentary, industry reports, competitor disclosures
- **Tier 3** (Low trust): Analyst pitches without data, forward guidance without contracts, media coverage, valuation multiples alone

**Standard**: If a thesis depends primarily on Tier 3 sources, flag it as speculative.

### 2. Falsifiable Claims

**Standard**: Structure reasoning so it can be proven wrong.

**Good**: "This thesis requires RPO to grow >20% annually for next 3 years"  
**Bad**: "Management has great vision" (unmeasurable, unfalsifiable)

### 3. Defined Scope

**Standard**: Specify where reasoning applies and where it doesn't.

**Questions**:
- What market conditions does this work in? (rates, volatility, economic cycle)
- What time horizon? (1 year, 5 years, 10+ years)
- Where does this fail?

### 4. Causal Mechanisms

**Standard**: Identify WHY something works, not just that it correlates.

**Weak**: "Stock X went up when rates fell, so it will repeat"  
**Strong**: "Stock X valuation depends on discounting distant cash flows. When rates fall, present value increases."

### 5. Explicit Assumptions

**Standard**: Surface critical assumptions that could break the thesis.

**Good**: "This assumes hyperscaler CapEx continues growing ~20% annually"  
**Bad**: Leaving assumptions implicit

---

## Thinking Patterns

### Pattern 1: Scope Testing

For any investment thesis, define boundaries:

**Where does this work?**
- Market conditions? (rising/falling rates, high/low volatility)
- Time horizon? (short/medium/long-term)
- Investor type? (active, passive, concentrated)

**Where does this fail?**
- What conditions break the thesis?
- Which environments favor alternatives?
- What assumptions are required?

**Why is this better than alternatives?**
- What edge does this provide vs other approaches?

### Pattern 2: Assumption Reversal

Identify the 1-2 critical assumptions, imagine they reverse completely. Does the thesis still work? If not, how fragile is it?

**Example**: Thesis assumes low rates persist → Test: What if rates spike 200bps?

### Pattern 3: Alternative Explanations

Generate 2-3 competing causal models for the same observation. Determine which model makes the most testable predictions.

**Example**: Stock up 50% → Could be: (a) fundamental improvement, (b) sector rotation, (c) short squeeze. Which predicts next quarter?

---

## Verification Methods

### Method 1: Write Code to Check Claims

Pull financial data programmatically (yfinance, SEC Edgar API). Calculate metrics from raw data. Backtest assumptions over historical periods.

**Use cases**:
- Verify "RPO growing faster than revenue" with 10-K data
- Calculate gross margin trends
- Test CapEx correlations
- Backtest signals over different regimes

### Method 2: Cross-Reference Sources

Check multiple company filings in the same supply chain. Verify hyperscaler CapEx guidance from multiple quarters. Compare segment reporting across competitors.

**Red flag**: If only one source mentions a claim, it may not be real.

### Method 3: Business Flow Analysis

Map customer workflow and integration points. Identify qualification cycles and regulatory barriers. Assess switching costs. Estimate time-to-replicate for competitors.

**Standard**: Strong moats have measurable barriers (5+ year qualification, regulatory protection, patent depth). Weak moats lack concrete obstacles.

---

## Common Failure Modes

### Red Flag 1: Narrative Without Evidence

Compelling story with no audited proof in financial statements.

**Test**: Can you verify the core claim in 10-K/10-Q? If not, it's speculation.

**Example**: "AI infrastructure boom" → Check: Are equipment suppliers showing backlog growth?

### Red Flag 2: Extrapolation Without Mechanism

Past performance projected forward without explaining WHY it should continue.

**Test**: What mechanism drives continued performance? Can that mechanism break?

**Example**: "Stock up 100% last year, will repeat" → Why? What changed fundamentally?

### Red Flag 3: Undefined Scope

Claim works "always" or "never" without boundary conditions.

**Test**: In which market conditions would this fail? If answer is "none," it's over-confident.

**Example**: "Growth stocks always outperform" → False. They underperform in high-rate regimes.

### Red Flag 4: Circular Reasoning

Success depends on the thesis working (tautology).

**Test**: Does return depend on fundamentals or just sentiment/multiple expansion?

**Example**: "Stock will go up because people will buy it" → Circular. What fundamental change drives buying?

### Red Flag 5: Untestable Claims

Success criteria can't be measured or falsified.

**Test**: What specific outcome would prove this wrong? If none, it's not falsifiable.

**Example**: "Management has great vision" → How do you measure vision? What outcome disproves it?

---

## Growth Approach Specifics (Four-Lens Framework)

When using Growth approach, additional quality indicators apply:

### Quality Indicator 1: Contracted Backlog Growth

**Check**: RPO (Remaining Performance Obligations) growing faster than revenue

**Verify**:
1. Read 10-K/10-Q footnotes for RPO disclosure
2. Calculate RPO growth rate vs Revenue growth rate
3. Check if RPO > annual revenue (multi-year visibility)

**Threshold**: RPO growing >30% faster than revenue = strong demand validation

### Quality Indicator 2: Gross Margin Resilience

**Check**: Gross margins stable or expanding during capacity constraints

**Verify**:
1. Track gross margin % over past 8 quarters
2. Compare to industry peers
3. Check if margins held/expanded as backlog grew

**Threshold**: Stable/expanding margins during backlog growth = real pricing power

### Quality Indicator 3: CapEx Linkage Directness

**Check**: Direct CapEx flow from hyperscalers/enterprises to company's products

**Verify**:
1. Identify hyperscaler CapEx guidance from their 10-Ks
2. Map company's product to specific CapEx line items
3. Cross-reference management commentary across quarters

**Threshold**: Company explicitly named in customer CapEx disclosures > 1+ steps removed

### Quality Indicator 4: Qualification Cycle Duration

**Check**: Time required for new competitor to pass customer certification

**Verify**: Research industry standards, check regulatory filings, review industry reports

**Threshold**: 3+ year qualification = strong moat; <1 year = weak moat

### Growth-Specific Counterfactuals

**Bottleneck Disappears**: What if the physical constraint is solved/bypassed? Research alternative solutions, monitor if demand shifts.

**CapEx Reverses**: What if hyperscalers cut spending? Monitor quarterly CapEx guidance from MSFT, GOOGL, AMZN, META.

**Moat Weaker Than Claimed**: What if competitors replicate faster? Track competitor qualification progress, customer backward integration.

**Validation Misleading**: What if backlog doesn't convert to revenue? Read contract footnotes for cancelation clauses, check RPO vs deferred revenue trends.

### Growth-Specific Failure Modes

**Thematic Exposure Without Bottleneck**: Company claims "AI exposure" but doesn't solve specific physical constraint.

**Indirect CapEx Linkage**: Three+ steps removed from actual spending (too indirect).

**Software-Only Moat**: Advantage is purely software with no physical/regulatory barriers (easily replicable).

**Backlog Without Context**: Company reports "record backlog" but doesn't disclose contract terms or cancelability.

**Valuation-Dependent Thesis**: Return depends on multiple expansion, not fundamental delivery.

---

## Expansion Triggers

Go deeper when:

1. **High stakes**: Position size would be >5% of portfolio
2. **Counterparty risk**: Thesis depends on specific customer/partner quality
3. **Edge cases**: Situation near boundary conditions
4. **Conflicting evidence**: Multiple sources contradict each other
5. **High uncertainty**: Causal mechanism unclear

**Expand into**:
- Detailed financial modeling (segment-level, scenario analysis)
- Supply chain mapping (dependencies)
- Competitive dynamics (barriers to entry, switching costs)
- Management track record (capital allocation history)
- Industry structure (oligopoly, commodity, winner-take-all)

---

## Philosophy

> "Quality in equity reasoning means: Evidence-based, mechanistic, falsifiable, scope-aware, and verification-backed."

These standards apply regardless of which investing approach is used. The goal is to evaluate whether the reasoning process is sound, not to prescribe which approach to use.

**Good investment reasoning**:
- Builds causal models (not just correlations)
- Tests against evidence (Tier 1 sources)
- Defines scope (where it works/fails)
- Makes falsifiable claims
- Surfaces assumptions
- Identifies failure modes

**Weak investment reasoning**:
- Relies on narratives without evidence
- Extrapolates without mechanism
- Makes unfalsifiable claims
- Hides assumptions
- Ignores boundary conditions
