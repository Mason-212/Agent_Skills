# Rubric: blind spots and coverage

Apply to **what is missing** from the frame: whole concern classes, stakeholders, or lifecycle not discussed.

## Checklist

1. **Assumption inventory** — What must be true for the plan to work but is never named?
2. **Stakeholders** — Who owns, operates, pays for, or is harmed by this? Who is not in the room?
3. **Lifecycle** — Deploy, rollback, migration, deprecation, on-call, observability, cost at steady state?
4. **Security / privacy / abuse** — When relevant: data handling, authz, threat model, compliance—even one sentence of “not considered” is a finding if stakes warrant it.
5. **Edge cases** — Empty inputs, retries, duplicates, clock skew, human error paths.
6. **Alternatives** — Credible options never mentioned; “only possible shape” without justification.

## Output discipline

- Primary home when the doc is **silent** on a concern class. If the doc **asserts** something weakly, that is **stress-test** first; use blind spots for **omission**.
