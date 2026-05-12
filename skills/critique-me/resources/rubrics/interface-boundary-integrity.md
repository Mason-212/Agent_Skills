# Rubric: interface and boundary integrity

Apply this rubric when reviewing public APIs, framework contracts, lifecycle flows, and type/runtime boundaries.

## Level 1 - Universal contract checks

Use these on every critique, regardless of domain.

1. **Truthfulness** - Do types, docs, and tests match runtime behavior?
2. **Single authority** - Are critical invariants enforced in one place (framework/base), not by convention?
3. **Symmetry** - Do paired operations provide equivalent guarantees (`run/resume`, `open/close`, `create/update`)?
4. **Closure** - Can callers stay within the intended public interface without reaching into internals?
5. **Totality** - Are all meaningful states represented and handled explicitly?
6. **Enforcement over guidance** - Are guarantees implemented in code rather than left as "remember to..." instructions?

## Level 2 - Boundary-specific probes

Run probes that match the artifact. Example mismatch to explicitly detect: a framework advertises
`run/resume` symmetry but `run` returns an envelope while `resume` returns raw internals.

### API boundary

- Is there one canonical entry point per mode?
- Do all entry points return consistent envelope/shape guarantees?
- Do any paths bypass standard validation/context/result shaping?

### Type/runtime boundary

- Are there `Any` annotations where runtime is stricter?
- Do protocol/interface signatures describe the real behavior contract?
- Are static contracts aligned with runtime validators/schemas?

### Lifecycle/state boundary

- Who owns state transitions/flags? Is ownership centralized?
- Are lifecycle operations idempotent by construction?
- If cleanup fails, is system state still safe?

### Continuation boundary

- Can continuation flows pause more than once?
- Is context reconstructable across continuation/resume?
- Are start/resume semantics envelope-consistent?

### Testing boundary

- Are boundary-level behaviors tested (not just helpers)?
- Is each state variant covered (success, pause, fail, invalid)?
- Are there negative tests proving invariant enforcement?

## Scoring and evidence

Score each Level 1 item and each applicable Level 2 boundary:

- **0 = strong** (no material issues)
- **1 = concern** (improvement needed)
- **2 = must-fix** (contract mismatch, abstraction leak, or unsafe invariant)

Decision rule:

- If **any** applicable section scores **2**, the overall critique outcome is **must-fix**.
- If no section scores 2 but **two or more** applicable sections score **1**, escalate overall to **must-fix**.
- Otherwise overall outcome is **later**.

Every finding must include:

- **claim**
- **why it matters**
- **evidence** (`path:line` or quoted text)

## Automatic must-fix triggers

Escalate to **must-fix** when any of these are present:

- public API contract differs from runtime behavior
- callers must use internals to complete a documented flow
- paired APIs have inconsistent guarantees that can corrupt caller assumptions

## Output discipline

- Use this as the **primary rubric** for contract drift, boundary leakage, and interface mismatch.
- Prefer the smallest framework-level change that makes misuse impossible by construction.
