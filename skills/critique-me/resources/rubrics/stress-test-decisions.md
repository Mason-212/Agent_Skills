# Rubric: stress-test decisions

Apply to **stated** commitments, predictions, feasibility claims, causal stories, and scope/non-goals. Ignore filler unless it contains a hidden bet.

## Checklist

1. **Load-bearing bets** — List the few decisions the artifact actually rests on (not every bullet).
2. **Evidence fit** — For each bet: does the strength of the language match the strength of evidence (metrics, prior art, spikes, citations)?
3. **Failure scenarios** — What concrete situations break the approach (load, partial outage, bad data, adversary, org change)?
4. **Hidden quant claims** — Latency, cost, scale, “enough for MVP” — are numbers, bounds, or measurement plans present?
5. **Kill criteria** — What observation would **falsify** or downgrade this approach? If none, flag it.
6. **Overconfidence** — “Obviously”, “best practice”, “industry standard” without context → ask what would make it **false here**.

## Output discipline

- One primary finding per issue; optional one-line “see also” to **blind-spots** if the real issue is an unstated dependency.
