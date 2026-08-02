# Think Skill Architecture

## For Users: Understanding How This Works

This document explains the architecture of the think skill - how the reasoning flow works and how domain-specific knowledge integrates.

---

## Core Philosophy

The think skill uses **compression and decompression** as its fundamental reasoning pattern:

1. **Build** a mental model (structure) that explains something
2. **Validate** it against reality
3. **Stress test** it with counterexamples
4. **Compress** it to essential insight
5. **Expand** it back out for your specific situation

This flow is **universal** - it works for any complex question, regardless of domain.

---

## The Two-Layer Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    CORE REASONING FLOW                      │
│                  (Compression/Decompression)                │
│                                                             │
│  1. Build Structure    → What mental model explains this?  │
│  2. Validate          → Does evidence support it?           │
│  3. Counterexamples   → What breaks it?                     │
│  4. Compress          → What's the essential insight?       │
│  5. Expand            → Apply to your specific case         │
└─────────────────────────────────────────────────────────────┘
                            ↑
                    Augmented by
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                   QUALITY PLUGINS                           │
│         (When domain-specific evaluation criteria exist)    │
│                                                             │
│  • Context on known structures (1-2 sentence summaries)     │
│  • Quality standards for evidence (evidence hierarchy)      │
│  • Common failure modes and red flags                       │
│  • Compression/expansion criteria                           │
│  • Verification methods                                     │
└─────────────────────────────────────────────────────────────┘
```

### Layer 1: Core Reasoning (Always Active)

The compression/decompression flow runs on **every** think skill query, regardless of domain.

**What it does**:
- Builds mental models from first principles
- Tests them against reality
- Finds their limitations
- Distills insights
- Applies them to your situation

**What it doesn't do**:
- Domain-specific checklists
- Rigid procedures
- Fixed templates

### Layer 2: Domain Plugins (When Available)

Domain plugins **augment** the core flow by providing:
- Known structures that work in this domain
- What "good evidence" looks like here
- Common ways reasoning fails
- When to go deep vs stay light

**Key**: Plugins provide **evaluation criteria compiled from expert knowledge**. They're self-contained - no runtime dependencies on external files.

---

## How Plugins Integrate at Each Step

### Step 1: Build Structure

**Core flow asks**: What mental model explains this?

**Plugin provides**:
- Context on known frameworks (brief summaries)
- Relevant structures experts use

**Example (Equity Investing)**:
- Core: "What makes a good investment?"
- Plugin: "Here are 5 known approaches: Value (buy undervalued, wait for mean reversion), Growth (buy exceptional companies, hold forever), Passive (broad indexing), Momentum (ride trends), Macro (uncorrelated portfolio)"
- Agent builds: Structure based on user context and these approaches

### Step 2: Validate

**Core flow asks**: Does evidence support this structure?

**Plugin provides**:
- Quality standards for evidence in this domain
- Evidence hierarchy (what sources to trust)
- Red flags that invalidate reasoning

**Example (Equity Investing)**:
- Core: "What evidence supports this thesis?"
- Plugin: "Audited financials > Management promises; Check RPO growth, gross margins"
- Agent validates: Using Tier 1 evidence standards from plugin

### Step 3: Counterexamples

**Core flow asks**: What breaks this structure?

**Plugin provides**:
- Domain-specific stress tests
- Common failure modes
- Known boundary conditions

**Example (Equity Investing)**:
- Core: "Under what conditions does this fail?"
- Plugin: "Test: What if CapEx reverses? What if bottleneck disappears?"
- Agent stress-tests: Using equity-specific counterfactuals from plugin

### Step 4: Compress

**Core flow asks**: What's the essential insight?

**Plugin provides**:
- What complexity must stay explicit in this domain
- What can safely be simplified
- Known compressed principles

**Example (Equity Investing)**:
- Core: "Distill to simplest useful form"
- Plugin: "Can't compress away: valuation, quality, timing, risk"
- Agent compresses: "Good business ≠ good investment without price/timing/risk"

### Step 5: Expand

**Core flow asks**: How does this apply to user's specific case?

**Plugin provides**:
- Verification methods (code to check claims)
- When to go deep vs stay light
- Monitoring signals

**Example (Equity Investing)**:
- Core: "Apply structure to Skynx"
- Plugin: "Pull 10-K data, verify RPO, check gross margins, map CapEx flow"
- Agent expands: With financial verification from plugin methods

---

## Why This Architecture?

### Problem It Solves

**Without this architecture**:
- Agent becomes checklist-follower
- Rigid procedures replace reasoning
- Can't adapt to novel situations
- Domain plugins become straitjackets

**With this architecture**:
- Core reasoning flow is universal and flexible
- Domain knowledge enhances rather than constrains
- Agent can reason about situations not in any plugin
- Natural degradation when plugins unavailable

### Key Properties

1. **Composable**: Core flow + any domain plugin(s)
2. **Graceful degradation**: Works without plugins (just less domain-specialized)
3. **Principle-based**: Not procedure-driven
4. **Extensible**: Add new domains without changing core

---

## Example: Investment Question Without Plugin

**Query**: "Should I invest in [Novel Technology Company]?"

**Without equity plugin**:
1. **Build**: Structure around risk/return, uncertainty, capital preservation
2. **Validate**: Look for evidence of business quality, market opportunity
3. **Counterexamples**: What if technology doesn't work? Market smaller than claimed?
4. **Compress**: "High uncertainty = smaller position or avoid until validation"
5. **Expand**: Based on available public information

**Result**: Sound general reasoning, but misses investing-specific rigor

---

## Example: Investment Question With Plugin

**Query**: "Should I invest in [Novel Technology Company]?"

**With equity plugin** (`quality/equity/taste.md`):
1. **Build**: Structure for what makes good investment
   - *Plugin provides*: Context on 5 approaches (brief summaries)
2. **Validate**: Check evidence quality
   - *Plugin provides*: "Audited financials > promises; look for RPO, backlog, gross margins"
3. **Counterexamples**: Stress test assumptions
   - *Plugin provides*: "What if bottleneck disappears? CapEx reverses? Moat weaker?"
4. **Compress**: Essential insight
   - *Plugin provides*: "Can't compress away: valuation, quality, timing, risk"
5. **Expand**: Verify with financial data
   - *Plugin provides*: "Pull 10-K, calculate RPO growth, verify CapEx linkage"

**Result**: Domain-expert level reasoning with verification

---

## How Quality Plugins Are Organized

### Plugin Structure

```
quality/{domain}/
└── taste.md           # Self-contained evaluation criteria
```

### What Goes in Plugins

**Evaluation criteria**:
- Universal quality standards for this domain
- Evidence hierarchy (what sources to trust)
- Common failure modes and red flags
- Verification methods (how to check claims)
- Compression/expansion criteria

**Context (brief summaries)**:
- Known approaches/frameworks (1-2 sentences each)
- When each works/fails

**What doesn't go in plugins**:
- Deep framework explanations (compile from sources, distill to essentials)
- External file references (plugins are self-contained)
- Rigid checklists (provide principles, not procedures)

---

## Current Available Plugins

### Equity Investing Domain

**Location**: `quality/equity/taste.md`

**Source knowledge** (compiled at authoring time):
- wiki-finance (investing approaches, four-lens framework)
- Investment books (Graham, Fisher, Bogle, etc.)
- Personal experience

**What it provides**:
- Context: 5 investing approaches (brief summaries)
- Universal standards: Evidence over narrative, falsifiable claims, scope boundaries
- Thinking patterns: Evidence hierarchy, scope testing, mechanism over correlation
- Verification methods: Code checks, cross-referencing, business flow analysis
- Counterfactuals: Assumption reversal, alternative explanations, boundary conditions
- Common failure modes: Narrative without evidence, circular reasoning, undefined scope
- Growth approach specifics: Quality indicators (RPO growth, gross margins, CapEx linkage), four-lens counterfactuals

**Self-contained**: No runtime dependencies on external files

---

## How Plugins Are Created

### Authoring Process

1. **Gather source knowledge**: Read wiki-finance, books, personal notes
2. **Distill to essentials**: Extract evaluation criteria, summarize approaches (1-2 sentences)
3. **Write self-contained plugin**: No external file references
4. **Plugin becomes frozen snapshot**: Update manually when source knowledge changes

**Example**: To create equity/taste.md:
- Read wiki-finance/topics/stocks/* (5 approaches, four-lens framework)
- Read investment books (Graham, Fisher, Bogle)
- Distill into evaluation criteria + brief context
- Result: Self-contained taste.md (no file:// references)

---

## How to Use This

### As a User

When you invoke the think skill (`/think [question]`), the agent:

1. **Always runs**: Core compression/decompression flow
2. **Detects domain**: If your question falls into a domain with plugins
3. **Loads plugin**: Reads self-contained evaluation criteria
4. **Augments flow**: Uses plugin standards at each reasoning step
5. **Stays transparent**: Shows you approach, assumptions, scope (not internal mechanics)

**You don't need to**:
- Specify which plugin to use (automatic)
- Know the internal flow (just ask your question)
- Request specific depth (agent adapts based on stakes)

**You can**:
- Explicitly request an approach: "Use Growth framework"
- Request depth: "Give me a quick sanity check" or "Full analysis"
- Override plugin: "Ignore the standard approach, I want..."

### As a Plugin Developer

To add a new domain:

1. Create `quality/{domain}/taste.md`
2. Gather source knowledge (external docs, books, experience)
3. Distill into self-contained plugin:
   - Quality standards (evidence hierarchy)
   - Common failure modes (red flags)
   - Verification methods
   - Brief context on known approaches (1-2 sentences)
4. No external file references (compile knowledge at authoring time)

**Test**: Does the plugin provide evaluation criteria that enhance compression/decompression without hijacking it?

---

## Evolution and Future

### Current State
- Core flow: Defined in `docs/framework.md`, `docs/principles.md`
- One quality plugin: Equity (self-contained evaluation criteria)
- Architecture: Compression/decompression with plugin augmentation

### Next Steps
- Add new domains: Engineering, Writing, Product (as needed)
- Refine integration: Learn what works as more plugins are added
- Keep plugins self-contained: Compile from sources, no runtime dependencies

### Design Principles
- Core flow should never change
- Plugins augment, never replace
- Graceful degradation always
- Principle-based over procedure-driven

---

## Philosophy

> "The compression/decompression flow is universal. Quality plugins make it sharper."

The think skill isn't about having the right checklist for every domain. It's about having a sound reasoning process that can integrate domain-specific evaluation criteria when available.

Without plugins: Sound general reasoning  
With plugins: Domain-expert reasoning with compiled quality standards

Both start from the same core flow. Plugins provide evaluation criteria, not the models themselves.
