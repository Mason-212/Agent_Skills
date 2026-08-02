# Learning to Do: Execution Gaps & Corrections

## Purpose

This document captures **how the think skill fails in practice** - not conceptual gaps in the framework, but execution failures when applying it. Each entry includes:

1. **The Gap**: What went wrong
2. **Example Prompt**: The actual user query
3. **What Happened**: How the agent executed
4. **Why It Failed**: Root cause analysis
5. **Correct Approach**: Step-by-step fix

---

## Gap 1: Search Space Premature Narrowing

### The Gap
When asked to analyze "companies" or "stocks" in a sector, agent narrows search space based on web search results rather than systematically defining the universe first.

### Example Prompt
```
User: "semiconductor companies stocks present good risk reward ratio today"
```

### What Happened
**Agent's execution:**
1. Web search: "semiconductor stocks forward PE ratio analyst estimates 2026"
2. Analyzed whatever appeared in results: NVDA, AMD, AMAT, MU, TXN
3. Concluded risk/reward assessment based on these 5 stocks
4. Never defined full semiconductor universe
5. Never explained selection criteria

**What was missing:**
- No systematic universe definition (GPU, Memory, Foundry, Equipment, Analog, Fabless segments)
- Missed major players: AVGO ($800B market cap, AI networking), ASML (EUV monopoly), QCOM (edge AI)
- Selection bias: Only analyzed stocks where forward PE data appeared in search results
- No explicit scope statement: "Focusing on AI-exposed semis >$100B market cap"

### Why It Failed

**Root causes:**

1. **Availability bias**: Web search results became the universe
   - Search query "semiconductor stocks forward PE" → Only returned stocks with prominent forward PE coverage
   - Created circular reasoning: Analyzed stocks with forward PE data, concluded forward PE matters

2. **No universe-first thinking**: Started analyzing before defining scope
   - Never asked: "What is the full set of semiconductor companies?"
   - Never segmented by sub-sector (GPU vs Memory vs Equipment have different cycle dynamics)

3. **Implicit filtering**: Agent made unstated decisions
   - Excluded companies without knowing they existed
   - User asked "semiconductor companies" (broad) → Agent gave 5-6 without explanation

4. **Search-driven vs. structure-driven**: Let tools determine scope rather than building structure first

### Correct Approach

**Step-by-step fix:**

#### Before Analysis: Define Universe

**1. Search for universe definition:**
```
Query: "major semiconductor companies by market cap 2026"
OR: "semiconductor industry segments companies 2026"
```

**2. Segment by relevant dimensions:**
```
Semiconductor Universe (by segment):
- GPU/AI Accelerators: NVDA, AMD
- CPUs: INTC, AMD
- Memory: MU, WDC, SKH
- Foundry: TSM, GFS, SMIC
- Equipment: AMAT, LRCX, KLAC, ASML
- Analog/Mixed Signal: TXN, ADI, MXIM
- Networking/Broadcom: AVGO
- Fabless Design: QCOM, MRVL, NXPI
```

**3. Apply explicit selection criteria:**
```
Filter by:
- Market cap > $50B (for liquidity)
- Direct AI exposure (narrows to GPU, Memory, Equipment)
- Data availability (Alpha Vantage coverage)
- Geographic focus (US-listed or ADRs)

Result: NVDA, AMD, MU, AVGO, AMAT, LRCX, ASML, TSM
```

**4. State scope explicitly to user:**
```
"Focusing on AI-exposed semiconductor stocks >$50B market cap with direct 
GPU, memory, or equipment exposure. This excludes analog (TXN, ADI) and 
mobile-focused (QCOM) which have different cycle dynamics."
```

#### During Analysis: Systematic Data Pull

**5. Pull fundamentals systematically:**
```python
# Pseudo-code for correct approach
universe = ["NVDA", "AMD", "MU", "AVGO", "AMAT", "LRCX", "ASML", "TSM"]

for symbol in universe:
    try:
        data = alpha_vantage.COMPANY_OVERVIEW(symbol)
        store(symbol, data.trailing_pe, data.forward_pe, data.margin)
    except RateLimit:
        note_limitation(symbol)
        
# Then web search to fill gaps for rate-limited stocks
```

**6. Build comparative table:**
```
| Stock | Segment    | Trailing PE | Forward PE | Rev Growth | Margin |
|-------|-----------|-------------|------------|------------|--------|
| NVDA  | GPU       | 29.8x       | 22.2x      | +85%       | 63%    |
| AMD   | GPU/CPU   | 158x (est)  | 68x (est)  | +40% (est) | ?      |
| MU    | Memory    | ?           | 11.8x (est)| ?          | ?      |
| AVGO  | Networking| ?           | ?          | ?          | 30% (est)|
...
```

**7. Analyze by segment:**
```
Risk/Reward by Segment:
- GPU: NVDA shows best profile (22x forward, 85% growth, margin resilient)
- Memory: MU cyclical upside if HBM supply tight (11.8x cheap but execution risk)
- Equipment: AMAT/LRCX lag chips by 6-12 months (40x+ valuation requires confirmation)
- Networking: AVGO underexplored in AI interconnect narrative
```

#### Key Principles

**Universe-first approach:**
1. **Define before filter**: Establish full universe before applying criteria
2. **Segment by structure**: Group by sub-sector, cycle dynamics, exposure type
3. **Explicit criteria**: State market cap, liquidity, exposure thresholds
4. **Acknowledge gaps**: Note companies excluded and why (data availability, rate limits, scope choice)

**Red flags you're doing it wrong:**
- ❌ Starting analysis immediately without universe definition
- ❌ Web search results become your universe
- ❌ Analyzing 3-5 companies without explaining why not 10-15
- ❌ No segmentation by sub-sector or cycle dynamics
- ❌ Selection criteria implicit/unstated

**Correct pattern:**
- ✅ Search for universe first: "major [sector] companies 2026"
- ✅ Segment: Map companies to sub-sectors
- ✅ Filter with explicit criteria: Market cap, exposure type, data availability
- ✅ State scope: "Focusing on X because Y, excluding Z"
- ✅ Pull data systematically across filtered universe
- ✅ Build comparative view before diving deep

---

## Gap 2: [Template for Future Gaps]

### The Gap
[Brief description of execution failure]

### Example Prompt
```
[Actual user query that triggered the gap]
```

### What Happened
[How agent actually executed]

### Why It Failed
[Root cause analysis]

### Correct Approach
[Step-by-step fix with examples]

---

## Usage Notes

**For agents:**
- Read this before applying think skill to complex queries
- Check: "Am I making any of these mistakes?"
- Correct course if you catch yourself in a known gap

**For users/developers:**
- Add new gaps as you observe execution failures
- Include actual examples (prompts, outputs)
- Focus on **how-to-do**, not **what-to-do** (framework is in SKILL.md)

**Distinction from other docs:**
- `SKILL.md`: What the framework is, when to use it
- `docs/framework.md`: Core concepts, philosophy
- `docs/principles.md`: Evolution, quality standards
- **`docs/learning-to-do.md`**: Execution failures and fixes (this document)

---

## Meta

Last updated: 2026-08-01  
Contributors: Observations from agent self-analysis during semiconductor stock analysis task
