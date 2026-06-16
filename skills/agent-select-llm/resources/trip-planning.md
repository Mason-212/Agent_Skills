## Trip Planning

Use this overlay for itinerary design, destination comparison, route planning, trip budgeting, and travel option synthesis.

## Domain Signals

- the user wants help planning a trip, comparing destinations, or building an itinerary
- the task mixes constraints like budget, travel time, pace, preferences, and logistics
- the answer may need to combine many options into a clean recommendation

## Decision Lenses

| Trip lens | What to evaluate | Critical failure state | Model tendency |
|---|---|---|---|
| `constraint-blending` | how many preferences and hard constraints must be balanced | the itinerary sounds good but violates budget, pace, or timing constraints | multi-constraint planning pushes toward stronger reasoning |
| `option-synthesis` | how many locations, routes, or trade-offs must be compared | the model over-focuses on one option and ignores better alternatives | larger option sets push toward stronger synthesis and context handling |
| `fact-sensitivity` | how much the answer depends on fresh or exact travel facts | the model gives plausible but stale guidance on schedules, policies, or availability | high fact sensitivity requires caveats and may reduce model differentiation |
| `presentation-needs` | whether the user wants a polished itinerary or raw trade-offs | the answer is accurate but hard to use | polished trip design often fits balanced, fluent models |
| `budget-pressure` | how strongly cost dominates the decision | the model optimizes for quality but ignores price discipline | stronger budget pressure favors cheaper/faster models for iterative comparison |

## Good Follow-up Questions

- "Is the priority budget, convenience, experience quality, or a balance?"
- "Are you comparing a few options, or planning a full itinerary with many moving parts?"
- "Do you need polished recommendations, or mainly a quick decision framework?"
- "How sensitive is this to fresh facts like schedules, openings, or current prices?"

## Recommendation Tendencies

- For multi-city or heavily constrained itineraries, prioritize reasoning and option synthesis.
- For casual trip brainstorming, a balanced fast model is usually enough.
- If the task depends on fresh facts, say that browsing or verification matters more than squeezing the last few percent out of model choice.
- For repeated what-if comparisons under a budget cap, speed and cost often matter more than maximum model size.

## Provider-Specific Hints

Treat these as tendencies, not absolute rankings:

- `Claude Sonnet 4.6`: strong default for fast, well-structured trip planning and iterative comparisons
- `Claude Fable 5` or `GPT-5.5`: stronger fit when itinerary constraints are unusually dense or optimization-heavy
- `Gemini 3.1 Pro`: useful when comparing a large amount of source material at once

If the user needs live travel facts, emphasize that browsing and source verification are more important than the exact model choice.
