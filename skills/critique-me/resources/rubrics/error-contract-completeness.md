# Rubric: error contract completeness

Apply when code documents specific exception types, error envelopes, or error-handling contracts for callers.

## Core question

For every **public function** or **interface boundary**: does the runtime *always* raise exactly the documented exception type across all reachable failure paths — including partial-success paths that the happy path never exercises?

## Checklist

1. **Documented-vs-runtime exception gap** — For each documented exception type (`raises X`), enumerate every throw site (direct `raise`, re-raise, nested call). Are there paths where a *different* exception escapes instead?
   - Example trigger: function documents `CatalogLoadError` but a response-body read can throw `botocore.exceptions.BotoCoreError` or `socket.timeout` before the `except` clause.

2. **Partial-success escape hatches** — Operations with multiple phases (connect → read → parse → validate) often catch early-phase errors but leave later-phase exceptions unwrapped.
   - Probe: "After `get_object()` succeeds, what can `response['Body'].read()` throw?"

3. **Type coercion / attribute access before validation** — Code that calls `.lower()`, `.strip()`, or `["key"]` on untrusted data before type-checking it (`isinstance(data, dict)`) lets `AttributeError`/`TypeError` escape the documented error envelope.
   - Probe: "What happens if the input is `[]`, `123`, `null`, or a string instead of the expected dict?"

4. **Nullable field access** — Fields documented as optional but accessed without a null guard raise `AttributeError` at runtime despite the caller being promised a clean error type.
   - Probe: "Every `.get()` result that is then attribute-accessed without a guard."

5. **Fallthrough on schema drift** — When a structural invariant is violated (e.g., no recognized field column), does the code silently produce a partial result or correctly raise / log and skip?

6. **Boundary input validation completeness** — For every numeric or structural parameter accepted by a public function:
   - Is negative/zero/NaN explicitly rejected with a clear `ValueError`?
   - Is the check at the public entry point (not buried in a helper called later)?
   - Probe: negative `top_k`, negative slice index, `NaN` weight, non-dict row in a list.

## Output discipline

- For each gap: **documented contract → actual runtime behavior → evidence (path:line)**.
- Mark **must-fix** when the escaped exception breaks a caller's `try/except` block written against the documented type.
- This is distinct from `interface-boundary-integrity` (which checks API shape/symmetry); this rubric focuses on **exception semantics** and **input rejection**.
