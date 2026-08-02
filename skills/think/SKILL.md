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

## Purpose

Apply the compression/decompression reasoning flow to construct, validate, and apply robust mental models that:
- Explain observations
- Predict outcomes
- Guide decisions
- Transfer across situations

---

## Core Instruction: The Reasoning Flow

Follow this five-step flow for every think skill query. This is **universal** - it works regardless of domain.

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

### Step 2: Validate Structure

**What**: Test whether the structure explains observations and predicts outcomes.

**How**:
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

**How**: Apply three types of counterexamples:

1. **Missing Variables**: What factors did you not consider?
   - Effect: Refine the model to include them
   
2. **Contradictions**: What observations contradict the model?
   - Effect: Replace or fundamentally revise the model
   
3. **Boundary Conditions**: Where does the model stop working?
   - Effect: Define scope explicitly

**Output**: Refined model with known limitations and scope

**Quality plugin augmentation** (if available):
- Apply domain-specific stress tests (counterfactuals distilled from expert knowledge)
- Test approach-specific failure modes

---

### Step 4: Compress

**What**: Distill the structure to its essential insight.

**How**:
- Remove complexity while preserving reasoning capability
- Keep causal mechanisms visible
- Simplicity must be *earned* through validation
- Don't compress into slogans or oversimplifications

**Output**: Compressed principle that captures the validated structure

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

**Quality plugin augmentation** (if available):
- Use verification methods (code to check claims, data validation, cross-referencing)
- Determine depth based on stakes and domain standards

---

### Step 6: Verify Framework Effectiveness (Required)

**What**: Test whether your reasoning is accurate vs internally consistent but wrong.

**Why**: Steps 1-5 can produce internally coherent analysis that fails externally through confirmation bias, hallucinated mechanisms, or blind spots. Step 6 catches these errors.

**How**: Apply three verification methods:

#### 1. Counterfactual Testing (Highest Priority)

**Method**: "If my model is TRUE, what ELSE must be observable?"

**Process**:
- Generate 3-5 independent predictions from your model
- Check predictions against sources you haven't used yet
- Look for evidence that SHOULD exist if model is correct
- Threshold: If <60% of predictions hold, model is weak

**Example (Power bottleneck thesis)**:
- Prediction 1: Power suppliers (Vertiv) should show order backlogs
- Prediction 2: Hyperscaler CapEx should remain >$600B
- Prediction 3: Data center construction timelines lengthening
- Prediction 4: Utility CapEx spiking

**Output**: Independent confirmation or refutation of key claims

---

#### 2. Adversarial Review (Steel-Man Opposition)

**Method**: "Build the strongest possible counter-thesis and test THAT"

**Process**:
- State your thesis clearly
- Build the BEST counter-argument (not a strawman)
- Apply same rigor: gather evidence, test counterfactuals
- Honest adjudication: Which explains observations better?

**Example (NVDA bull vs bear)**:
- Bull: Power bottleneck extends moat, Forward PE 15.57 cheap
- Bear: AMD reaches parity, FCF pressure forces CapEx cuts, margins compress
- Test both → Bull stronger near-term, bear credible medium-term

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
- **High**: 3/3 methods pass, counterfactuals hold (>60%), multiple independent sources
- **Medium**: 2/3 methods pass, some counterfactuals fail, limited sources
- **Low**: <2/3 methods pass, most counterfactuals fail, single source only

**Red flags (reasoning may be wrong)**:
- <60% of counterfactual predictions hold
- Bull and bear cases equally strong (high uncertainty)
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
- Apply generic counterfactuals (assumption reversal, alternative explanations, boundary conditions)
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
- **Reality-tested**: Tests structures against evidence and counterexamples
- **Explicit assumptions**: Makes hidden assumptions visible
- **Bounded scope**: Defines where reasoning applies and where it breaks
- **Adaptive rigor**: Goes deep when stakes are high, stays light when appropriate

**Not** about following procedures perfectly. It's about producing sound reasoning through the compression/decompression flow.

---

## Supporting Resources

**Framework documentation** (`docs/`):
- `framework.md` - Core concepts and terminology
- `principles.md` - Evolution of the approach
- `quality.md` - What excellence looks like
- `architecture.md` - How plugins integrate with core flow (for users)
- `learning-to-do.md` - Common execution gaps and how to fix them
- `dag-spec.md` - Formal reasoning pipeline specification

**Evaluation examples** (`evals/`):
- `ai_education.md` - AI and education analysis
- `investing.md` - Investment decision framework
- `switzerland.md` - Switzerland success analysis

**Domain plugins** (`quality/`):
- `equity/` - Equity investing quality standards
  - `taste.md` - Compiled evaluation criteria from expert knowledge

---

## Remember

The five-step compression/decompression flow is universal and always applies:

1. Build Structure
2. Validate
3. Counterexamples
4. Compress
5. Expand

Domain plugins make this flow **sharper** in specialized domains, but they never replace it.
