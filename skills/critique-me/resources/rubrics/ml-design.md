# Rubric: ML design

For ML-shaped designs: training/serving, data, labels, metrics, monitoring. Use together with **stress-test** and/or **blind-spots** for overlapping claims.

## Checklist

1. **Problem and metric** — Task definition, primary metric, business harm of wrong predictions; success threshold.
2. **Data** — Source, freshness, bias, PII, consent, label noise, train/serve skew.
3. **Leakage** — Temporal leakage, duplicate entities across splits, pipeline leakage.
4. **Baselines** — Simple/heuristic baselines before complex models; ablation story.
5. **Evaluation** — Offline protocol, holdout, variance; when offline fails to predict online.
6. **Serving** — Latency, cost, fallback, drift, monitoring, rollback, human review loops.
7. **Risk** — Failure modes specific to ML (silent degradation, feedback loops, adversarial inputs).

## Output discipline

- Tie ML findings to **evidence** in the artifact; do not invent dataset properties not stated.
