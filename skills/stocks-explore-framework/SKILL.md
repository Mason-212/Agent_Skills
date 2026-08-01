---
name: stocks-explore-framework
description: Explore public equities through a four-lens framework focused on bottlenecks, CapEx, moats, and backlog validation. Use when the user wants stock ideas, equity research, market opportunities, or a Socratic stock-analysis workflow.
---

# Stocks Explore Framework

## When to Use

- User asks for stock market opportunities, equity ideas, or public-company research
- User wants to analyze a sector by following capital flows instead of predicting short-term price moves
- User wants a Socratic, interactive workflow that surfaces candidate stocks through evidence
- User wants to compare infrastructure, industrial, energy, or AI-adjacent companies using a repeatable framework

## Core Principle

Instead of guessing where a stock's price will go tomorrow, focus on how corporate money is flowing today.

Treat the conversation as a research process, not a prediction contest. Prefer evidence from filings, earnings calls, investor presentations, backlog disclosures, and contract language over narratives.

## Interaction Style

- Be Socratic and interactive
- Ask one focused question at a time when discovery is still needed
- Challenge weak assumptions politely and ask for receipts
- Separate `hypothesis`, `evidence`, and `open questions`
- Do not present speculative claims as facts
- Do not give personalized financial advice; frame output as research ideas and risks to investigate

## Default Workflow

### 1. Frame the Hunt

Start by narrowing the search:

- Which sector, theme, or demand wave is expanding right now?
- What time horizon matters: near-term trade, 1-to-3-year thesis, or longer-duration compounder?
- Is the user looking for large-cap stability, mid-cap leverage, or small-cap optionality?

If the user gives little context, default to structural themes with visible corporate spending, physical constraints, and auditable demand.

### 2. Run the Four Lenses

Use all four lenses in order. Do not skip the validation lens just because the story sounds strong.

#### Lens 1: The Friction Lens

In the stock market, friction is where the highest margins live. When an entire fast-growing industry encounters a structural wall, the few specialized companies capable of clearing that wall gain immense pricing power.

Ask:

_What physical or resource bottleneck is currently preventing a booming sector from scaling further?_

Look for:

- Bottlenecks in power, grid access, transformers, cooling, permitting, interconnection, water, or specialized manufacturing capacity
- Evidence of pricing power, lead-time expansion, constrained supply, or resilient gross margins
- Companies facilitating Bring-Your-Own-Power (BYOP), onsite generation, micro-grids, industrial gas turbines, and high-voltage electrical architectures

#### Lens 2: The Shift Lens

Corporate management can say whatever they want in press releases, but CapEx never lies. When the largest, most cash-rich enterprises in the world collectively dump hundreds of billions into a specific bucket, it creates a massive demand wave that rolls downhill into the broader supply chain.

Ask:

_Which secondary or tertiary suppliers are the direct, un-bypassable beneficiaries of massive corporate spending cycles?_

Look for:

- Clear linkage to major enterprise or hyperscaler capital expenditure
- Suppliers that benefit from physical layout changes in spending, not just top-line theme exposure
- Liquid cooling infrastructure, specialized industrial real estate, heavy mechanical engineering, and other scale-out enablers
- Reported jumps in capital investment, plant utilization, booked orders, or management commentary tied to the spending wave

#### Lens 3: The Edge Lens

Trillion-dollar tech giants can build almost any software tool they want, given enough software engineers and time. However, they cannot easily replicate decades of heavy manufacturing precision, specialized metallurgy, or heavily protected industrial intellectual property.

Ask:

_Which mid- or large-cap specialists own an operational, regulatory, or hardware niche so deep that the market leaders are forced to buy from them?_

Look for:

- Operational, regulatory, or hardware niches that are hard to replicate
- Specialized factories, long qualification cycles, utility relationships, compliance barriers, or patent depth
- Choke points such as advanced grid components, transformers, central busways, precision timing, or custom electrical hardware
- R&D intensity, certification barriers, installed base advantages, and customer stickiness

#### Lens 4: The Validation Lens

The final lens filters out speculative story-stocks from legitimate growth compounders. Before deploying your money, find hard, audited proof that customers are signed to legally binding contracts.

Ask:

_Does the company's financial disclosure show accelerating contract backlog growth that outpaces its current revenue recognition?_

Look for:

- Remaining Performance Obligations (RPO), backlog, booked-but-not-billed demand, or equivalent contracted revenue disclosures
- Long-term Power Purchase Agreements (PPAs), capacity leases, or take-or-pay contracts
- Multi-year backlog supported by credit-worthy counterparties
- Evidence that forward revenue is becoming mathematically locked in rather than merely forecast

### 3. Score the Candidates

For each company, rate:

- `Friction`: How severe is the bottleneck, and how directly does the company monetize it?
- `Shift`: How tightly is the company tied to a real CapEx wave?
- `Edge`: How hard is the company to bypass or replicate?
- `Validation`: How much of future revenue is contractually supported?
- `Risk`: What could break the thesis?

Prefer companies that score well on at least three lenses and pass the validation lens with documented evidence.

### 4. Produce a Shortlist

Return a ranked shortlist with:

- Ticker and company name
- One-sentence thesis
- Which lens or lenses make it attractive
- What in the financials or disclosures supports the idea
- Key disconfirming risks
- What to verify next before acting

If evidence is weak, say the name is only a watchlist candidate, not a validated opportunity.

## What to Scan in Financials

- Gross margin stability or expansion during capacity shortages
- CapEx, Property, Plant & Equipment, and capacity-expansion commentary
- Backlog, RPO, bookings, book-to-bill, and contract duration
- Customer concentration and counterparty quality
- Segment reporting that isolates exposure to the target theme
- Risk factors that could impair the bottleneck thesis

## Equity Framework Summary

| Lens | Market Focus | What to Scan in Financials | Structural Theme |
|---|---|---|---|
| 1. Friction | Speed-to-Power Bottlenecks | Pricing power and gross margin stability | Onsite generation / Grid enablers |
| 2. Shift | Tracing the $750B CapEx | Massive YoY jumps in Property, Plant & Equipment | Liquid cooling and industrial scale-out |
| 3. Edge | Un-replicable Physical IP | High R&D-to-sales ratios, deep patent moats | High-voltage architectures and custom hardware |
| 4. Validation | Multi-year Backlogs | Exploding RPO relative to recognized revenue | Hyperscaler take-or-pay long-term leases |

## Response Template

Use this format by default:

```markdown
## Theme
[Demand wave or bottleneck]

## Socratic question
[Single best next question]

## Candidate shortlist
| Company | Ticker | Lens fit | Evidence | Key risk |
|---|---|---|---|---|
| ... | ... | ... | ... | ... |

## Best opportunity now
- Thesis:
- Why this company:
- What the receipts say:
- What could break:

## What to verify next
- [Next filing, metric, or contract proof to inspect]
```

## Guardrails

- Prefer primary sources when available
- Distinguish confirmed facts from thematic inference
- Do not claim a company is a winner unless the disclosures support it
- If backlog, RPO, or contractual evidence is missing, explicitly downgrade confidence
- If the thesis depends mainly on valuation, momentum, or macro calls, say that this framework has limited edge there
