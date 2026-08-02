# pi.harness — open design questions

This package shipped as a minimum-viable contract to respond to a PR comment
about the boundary between `pi.ai` (provider SDK / transcript) and the
runtime / harness layer that owns structured tool-execution bookkeeping.

The public shape is intentionally narrow and is expected to change before
the first external consumer (verifier, approval gate, evaluator) lands. The
list below captures the non-obvious decisions still owed.

## 1. Package naming

- `pi.harness` is a placeholder. Alternatives: `pi.runtime`, `pi.harness`,
  `pi.runner`. The top-level plan for `pi/` envisions two peer subpackages
  alongside `pi/ai/`; pick the name that best fits the other peer.
- Decision owner: @tomchang (this repo).

## 2. `ToolExecutionResult` field set

Currently shipped: `tool_call_id`, `tool_name`, `status`,
`structured_output`, `artifacts`, `metrics`, `diagnostics`, `session_id`,
`latency_ms`.

- Missing but likely-needed: `started_at` / `finished_at` timestamps (ISO-8601
  vs. epoch ms — both have callers), `tool_version`, `exit_code` (subprocess
  tools), `stdout` / `stderr` capture (or deliberately artifacted), `env_hash`
  for reproducibility, `parent_call_id` for tool-of-tools chains.
- Decision: land these once the first executor tells us what it captures,
  rather than speculatively.

## 3. `ExecutionStatus` taxonomy

Currently: `"ok" | "error" | "timeout" | "cancelled"`.

- Do we need `invalid_input` (pre-execution schema rejection) vs. `error`
  (in-execution failure)?
- Do we need `retryable` / `fatal` distinction, or is that an `is_retryable`
  bool alongside `status`?
- Verifier / approval-gate policies may want finer-grained signals. Revisit
  when those consumers exist.

## 4. `ArtifactRef` URI contract

`ArtifactRef.uri` is a free-form string today.

- Which schemes are valid? (`s3://`, `file://`, `abfss://`, a repo-local URN?)
- Lifetime guarantees: does a URI outlive a single run? A single worker?
- Who fetches the content? Verifier-side fetcher, harness-side fetcher, or
  lazy resolver injected at projection time?
- Content addressing: do we want a `sha256` field for audit?
- Decision owner: @tomchang, in conjunction with the run-store design.

## 5. Projection format

`to_model_message` produces a plain-text block with labeled sections.

- Should we also support a JSON-block projection for providers that can
  consume structured tool results natively (e.g. Anthropic accepts a list
  of `tool_result.content` blocks, not just a string)? That would require
  pi.ai widening `ToolResultContentBlock` — punted today, but revisit once
  we see real demand.
- Section ordering is heuristic. If we ever want a canonical form (e.g. for
  hashing transcripts), pin a formal grammar.
- `max_preview_chars` default is 2000. No evidence this is the right number;
  calibrate once we see real artifact sizes.

## 6. `structured_output` serialization

- `json.dumps(default=str)` is lossy but always-succeeds. If we pick
  strict serialization instead, tool authors must pre-serialize — good
  discipline but more friction.
- Should there be a hard upper bound on `structured_output` size at
  *ingest* time (guard against pathological tool returns), separate from
  the projection truncation?

## 7. Construction discipline

No enforcement today that callers construct `ToolResultMessage` only via
`ToolExecutionResult.to_model_message`. Options:

- Lint rule / repo convention only.
- Runtime guard: `ToolResultMessage.__init__` inspects caller frame — too
  magic.
- Private-suffixed constructor plus a public builder on `ToolExecutionResult`.

Prefer the convention route until we see divergence.

## 8. Async projection

`to_model_message` is sync. If artifact previews ever need to be fetched
lazily (e.g. pull first 2 KB from S3), this becomes `async`. Either keep it
sync and require callers to pre-populate `preview`, or add a separate
`async def to_model_message_async(...)`.

## 9. Relationship to pi-ai upstream

Upstream pi-ai carries a `details: any` passthrough on its tool-result
message. We explicitly diverge:

- No `details` on `pi.ai.ToolResultMessage`.
- Structured state lives on `pi.harness.ToolExecutionResult` and is only
  projected down.

If upstream later codifies a richer tool-result shape, we may wire through
structured blocks in `pi.ai` itself. For now, the port stays narrow.

## 10. Spec

A full written spec belongs at `specs/pi-harness/tool-execution-result.spec.md`
(not yet written). This file is a working TODO, not a replacement.
