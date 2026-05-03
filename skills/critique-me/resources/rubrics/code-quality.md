# Rubric: code quality

For **code in scope** (files read per `SKILL.md` caps, or snippets in the thread). This is **not** a full merge-bar review unless the user asks for that explicitly.

## Checklist

1. **Correctness** — Logic bugs, off-by-one, null/empty paths, error handling that drops context or swallows failures.
2. **APIs and boundaries** — Clear contracts; leakage of responsibilities; over-coupling.
3. **Readability** — Naming, structure, duplication; comments that only restate code.
4. **Security footguns** — Injection, secrets in code, unsafe deserialization, authz gaps when visible from snippet.
5. **Operability** — Logging/metrics hooks where failures would be opaque; config explosion.
6. **Consistency** — If repo context exists, flag clashes with nearby conventions **only** when you have seen those files.

## Output discipline

- Prefer **actionable** fixes over style nitpicks. Defer diff-wide security/regression bar to **git-review** / **pr-review-remote** when the user needs merge quality.
