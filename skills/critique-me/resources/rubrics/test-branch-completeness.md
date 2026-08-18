# Rubric: test branch completeness

Apply when a test suite exists alongside the code under review. Goal: enumerate untested production branches — not just line coverage, but *semantic branch* coverage of the real runtime behaviors that callers depend on.

## Core question

For every **production code branch**, is there a test that *directly asserts* the expected output of that branch — not just exercises it incidentally as a side effect of a happy-path test?

## Checklist

1. **Scoring / ranking tier coverage** — When code has tiered scoring (score = 1.0 for tier A, 0.7 for tier B, 0.3 for tier C), each tier must have a test that asserts the exact expected score for a fixture designed to hit only that tier.
   - Probe: "Remove tier B's logic — does any test fail?"

2. **Parser / schema variant coverage** — When a parser supports multiple spellings of the same column (`"Label"` / `"Field Label"` / `"DMO Field Label"`), each alternate form must have at least one test asserting the parsed output is identical.
   - Probe: "Change the fixture to use an alternate column name — does any test catch it?"

3. **Configuration wiring** — When a function accepts non-default config (e.g., `recall_config`, `expansion_config`, `lexical_method`), is there a test that passes a non-default value and asserts it produces a different result from the default?
   - Probe: "Is non-default config ever exercised in the unit suite?"

4. **Lexical / tokenization edge cases** — Tokenizers that handle CamelCase, snake_case, stopwords, or separators must have direct unit tests for each transformation, not just end-to-end tests that happen to pass through them.

5. **FK / relationship branch coverage** — FK target identity, inbound vs outbound direction, PK exclusion — each must be directly asserted, not just present in a fixture that passes for unrelated reasons.
   - Probe: "Does any test verify the *names* of FK targets, not just their count?"

6. **Numeric boundary tests** — Every public numeric parameter (top_k, top_n, alpha, max_bridges) must have a test for:
   - The configured value producing a *different count or ordering* than the default (proves wiring)
   - Zero / negative values being rejected with the documented error type

7. **External service failure branches** — For code with S3/HTTP/LLM calls, are these failure branches covered?
   - Missing / malformed response body
   - Configured vs default credentials / region
   - Import unavailability (if a dep is declared optional)

8. **Shared-helper cross-module import** — If a private helper (`_tokenize`, `_normalize`) is imported from another module's private namespace, is the contract of that helper tested independently — not just through the importing module?

9. **LLM / external response parsing** — Malformed JSON, missing keys, wrong types, hallucinated values beyond the candidate pool — each must be directly exercised with a test that asserts safe degradation.

## Output discipline

- For each untested branch: **branch description → test that would catch a regression → evidence of absence** (grep or "no test in `test_X.py` exercises Y").
- Classify: **must-fix** if the branch is a documented production behavior that callers rely on (e.g., documented error type, score tier, config wiring). **Later** for purely internal helpers.
- Do not restate coverage percentages — focus on *semantic branch* gaps.
