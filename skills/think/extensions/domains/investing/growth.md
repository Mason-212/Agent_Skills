# Growth Approach - Operational Procedures

## Purpose

Operational guidance for applying Growth investing approach (Fisher philosophy), specifically the four-lens framework.

**Knowledge Base (WHAT)**: [wiki-finance: four-lens-equity-research](file:///Users/chang/Documents/dev/git/wikis/wiki-finance/wiki/topics/stocks/four-lens-equity-research.md)  
**Fallback**: https://github.com/thomaschangsf/wiki-finance/blob/main/wiki/topics/stocks/four-lens-equity-research.md

This file contains **HOW** to verify, stress test, and identify failure modes when using the four-lens framework.

---

## Approach-Specific Quality Indicators

### Quality Indicator 1: Contracted Backlog Growth
**What to check**: RPO (Remaining Performance Obligations) growing faster than revenue

**How to verify**:
1. Read 10-K/10-Q footnotes for RPO disclosure
2. Calculate: `RPO growth rate` vs `Revenue growth rate`
3. Check if RPO > annual revenue (indicates multi-year visibility)

**Code verification**: Pull financial data and calculate programmatically
```python
# wiki-finance/sources/investing/tools/verify_rpo_growth.py
```

**Quality threshold**: RPO growing >30% faster than revenue suggests strong demand validation

---

### Quality Indicator 2: Gross Margin Resilience
**What to check**: Gross margins stable or expanding during capacity constraints

**How to verify**:
1. Track gross margin % over past 8 quarters
2. Compare to industry peers during same period
3. Check if margins held or expanded as backlog grew

**Quality threshold**: Stable/expanding margins during backlog growth = real pricing power

---

### Quality Indicator 3: CapEx Linkage Directness
**What to check**: Direct CapEx flow from hyperscalers/enterprises to company's products

**How to verify**:
1. Identify hyperscaler CapEx guidance from their 10-Ks
2. Map company's product to specific CapEx line items
3. Cross-reference management commentary across multiple quarters

**Quality threshold**: Company explicitly named in customer CapEx disclosures > 1 step removed in supply chain

---

### Quality Indicator 4: Qualification Cycle Duration
**What to check**: Time required for new competitor to pass customer certification

**How to verify**:
1. Research industry qualification standards
2. Check regulatory filings for certification requirements
3. Interview suppliers or check industry reports

**Quality threshold**: 3+ year qualification = strong moat; <1 year = weak moat

---

## Approach-Specific Counterfactuals

### Counterfactual 1: Bottleneck Disappears
**Question**: What if the physical constraint is solved or bypassed?

**How to test**:
- Research alternative solutions (new technology, different architecture)
- Check if regulatory changes could remove the constraint
- Monitor if demand is shifting away from constrained resource

**Verification**:
- Track patent filings for alternative approaches
- Monitor industry conferences for new solutions
- Check if customers are exploring workarounds

**Disconfirming evidence**: Multiple credible alternatives gaining traction

---

### Counterfactual 2: CapEx Reverses
**Question**: What if hyperscalers cut spending or delay infrastructure build-out?

**How to test**:
- Monitor quarterly CapEx guidance from major spenders (MSFT, GOOGL, AMZN, META)
- Check for commentary about "cost discipline" or "optimization"
- Look for capacity oversupply signals

**Verification**:
- Track CapEx as % of revenue trends
- Monitor datacenter utilization rates
- Check if guidance is being revised downward

**Disconfirming evidence**: Two consecutive quarters of CapEx guidance cuts

---

### Counterfactual 3: Moat Weaker Than Claimed
**Question**: What if competitors can replicate the advantage faster than expected?

**How to test**:
- Track competitor filings for qualification progress
- Check customer CapEx for signs of backward integration
- Monitor new entrant announcements and funding rounds

**Verification**:
- Search for "qualified supplier" announcements
- Check if customers are building internal capabilities
- Monitor acquisition activity in the space

**Disconfirming evidence**: Competitor passes major customer qualification within 18 months

---

### Counterfactual 4: Validation Is Misleading
**Question**: What if backlog/RPO doesn't translate to actual profitable revenue?

**How to test**:
- Read contract footnotes for cancelation clauses
- Check if RPO growth is organic or acquisition-driven
- Analyze conversion of backlog to recognized revenue

**Verification**:
- Compare backlog burn rate to revenue recognition
- Check deferred revenue trends vs RPO
- Look for changes in payment terms or contract structure

**Disconfirming evidence**: RPO growing but deferred revenue flat or declining

---

## Financial Scan Checklist (Four-Lens Specific)

When screening a potential Growth investment through four-lens framework:

### Pre-Analysis (Before Deep Dive)
- [ ] Identified specific physical bottleneck (Friction)
- [ ] Mapped direct CapEx linkage (Shift)
- [ ] Researched qualification cycle duration (Edge)
- [ ] Located RPO/backlog disclosure in 10-K (Validation)

### Friction Lens Verification
- [ ] Physical bottleneck exists (not just narrative)
- [ ] Lead times are expanding (check management commentary)
- [ ] Pricing power evident (check gross margin trends)
- [ ] Constraint can't be quickly solved

### Shift Lens Verification
- [ ] Hyperscaler/enterprise CapEx guidance explicit
- [ ] Company products directly tied to that CapEx
- [ ] Multiple customers showing same spending pattern
- [ ] Management commentary confirms CapEx linkage

### Edge Lens Verification
- [ ] Qualification cycle duration documented (3+ years)
- [ ] Regulatory or physical barriers exist
- [ ] No credible competitors in qualification pipeline
- [ ] R&D spending or patent depth supports moat claim

### Validation Lens Verification
- [ ] RPO disclosed and growing faster than revenue
- [ ] Backlog growth >30% YoY
- [ ] Gross margins stable or expanding
- [ ] Contracted backlog > 1 year of revenue
- [ ] Counterparty quality is strong (credit-worthy customers)

### Scoring
- **4/4 lenses + strong validation**: High conviction candidate
- **3/4 lenses + moderate validation**: Moderate position size
- **2/4 lenses or weak validation**: Watchlist only

---

## Common Failure Modes (Growth-Specific)

### Red Flag 1: Thematic Exposure Without Bottleneck
**What it is**: Company claims "AI exposure" but doesn't solve a specific constraint

**Test**: Can you name the physical bottleneck? If not, it's a theme stock, not a bottleneck play.

**Example**: "We provide AI software tools" → What constraint does this solve that can't be solved by 100 other tools?

---

### Red Flag 2: Indirect CapEx Linkage
**What it is**: Three+ steps removed from actual spending

**Test**: Draw the flow: Hyperscaler → [Step 1] → [Step 2] → [Company]. If more than 2 arrows, it's too indirect.

**Example**: "Hyperscalers spend on datacenters → contractors → electrical distributors → component suppliers → [Company]" = 4 steps = too indirect

---

### Red Flag 3: Software-Only Moat
**What it is**: Advantage is purely software-based with no physical or regulatory barriers

**Test**: Could a well-funded competitor replicate this in 12 months? If yes, moat is weak.

**Example**: "Proprietary algorithm" → Unless patent-protected or requires decades of data, it's replicable

---

### Red Flag 4: Backlog Without Context
**What it is**: Company reports "record backlog" but doesn't disclose contract terms or cancelability

**Test**: Read footnotes. Are these firm orders or cancelable? What are payment terms?

**Example**: "Backlog up 200%" → But footnote says "subject to customer confirmation" = not real backlog

---

### Red Flag 5: Valuation-Dependent Thesis
**What it is**: Return depends on multiple expansion, not fundamental delivery

**Test**: If the stock traded sideways for 2 years but fundamentals delivered, would you be happy? If no, it's a valuation trade, not a growth investment.

**Example**: "Stock should trade at 50x because sector averages 45x" → Circular reasoning

---

## Expansion Triggers (Growth-Specific)

Dig deeper when:

1. **Qualification cycle claims are vague**: "Long qualification" without specific timeline
2. **CapEx linkage is indirect**: More than 2 steps from spending source
3. **Multiple competing bottlenecks exist**: Not clear which constraint is binding
4. **Backlog disclosure is incomplete**: Missing RPO, contract terms, or burn rate
5. **Moat depends on intangibles**: "Management quality" rather than physical/regulatory barriers

**What to do**: Expand verification using wiki-finance/sources/investing/tools/ scripts to pull financial data and stress test assumptions.

---

## Integration with Think Skill

When using think skill for Growth/four-lens analysis:

### Step 1: Clarify User Intent
- Are they evaluating a specific stock?
- Do they want to discover new ideas in a specific bottleneck?
- Are they stress testing an existing position?

### Step 2: Load Four-Lens Knowledge
**Read**: [wiki-finance: four-lens-equity-research](file:///Users/chang/Documents/dev/git/wikis/wiki-finance/wiki/topics/stocks/four-lens-equity-research.md)

### Step 3: Apply Framework Sequentially
1. **Friction**: Identify bottleneck
2. **Shift**: Verify CapEx linkage
3. **Edge**: Test moat durability
4. **Validation**: Demand financial proof

### Step 4: Run Growth-Specific Verifications
- Financial scan checklist (above)
- Pull 10-K data to verify RPO and gross margins
- Cross-reference hyperscaler CapEx guidance

### Step 5: Execute Growth-Specific Counterfactuals
- What if bottleneck disappears?
- What if CapEx reverses?
- What if moat is weaker than claimed?
- What if validation is misleading?

### Step 6: Check Growth-Specific Failure Modes
- Thematic exposure without bottleneck
- Indirect CapEx linkage
- Software-only moat
- Backlog without context
- Valuation-dependent thesis

### Step 7: Score and Recommend
- 4/4 lenses = High conviction
- 3/4 lenses = Moderate position
- 2/4 lenses = Watchlist only

---

## Philosophy

> "CapEx never lies. Management can say anything, but when hyperscalers commit hundreds of billions to infrastructure, that creates auditable, contractual demand."

Focus on evidence (CapEx flows, backlog data, audited financials) over narratives (management promises, analyst enthusiasm).

**Quality means**: Physical constraints + Direct CapEx flow + Un-replicable edge + Contractual validation.

Anything less is speculation.
