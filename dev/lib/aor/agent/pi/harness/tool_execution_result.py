"""Structured tool-execution record and its LLM-facing projection.

See ``agent.pi.edc_harness.__init__`` for the architectural rationale and
``TODO.md`` in this package for the open design questions.
"""

from __future__ import annotations

import json
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from ..ai.types import TextContent, ToolResultMessage

ExecutionStatus = Literal["ok", "error", "timeout", "cancelled"]
"""Outcome of a tool invocation.

``ok`` maps to ``ToolResultMessage.is_error=False``; anything else maps to
``True``. The specific non-ok value is surfaced only in the projected text.
TODO: decide whether we need a richer taxonomy (e.g. ``retryable``,
``invalid_input``) before the first real consumer lands.
"""


class ArtifactRef(BaseModel):
    """Pointer to a file, blob, or structured payload produced by a tool.

    The full payload lives at ``uri``; the edc_harness intentionally keeps the
    body out of the transcript so large artifacts do not inflate the model's
    context window. ``preview`` is an optional short textual sample (e.g.
    first ~80 chars of a CSV, a description of an image) that is safe to
    include in the projection.

    TODO: URI scheme and lifecycle are left unspecified here. The edc_harness
    implementation will define (a) which schemes are valid (``s3://``,
    ``file://``, a repo-local URN, etc.), (b) whether URIs survive across
    runs, and (c) how content is fetched for verifier / evaluator use.
    """

    uri: str
    content_type: str = Field(validation_alias="contentType")
    size_bytes: int | None = Field(default=None, validation_alias="sizeBytes")
    preview: str | None = None

    model_config = ConfigDict(populate_by_name=True)


_DEFAULT_MAX_PREVIEW_CHARS = 2000
_TRUNCATION_SUFFIX = "... [truncated]"


class ToolExecutionResult(BaseModel):
    """Canonical structured record of a single tool invocation.

    Owned by the edc_harness / runtime layer. Constructed by whichever component
    actually executes a tool call. Verifiers, approval gates, evaluators,
    and the run store read from this object directly - they do not
    reconstruct structured data by parsing the LLM-facing projection.

    The compact LLM-facing message is obtained via :meth:`to_model_message`.

    Fields:

    - ``tool_call_id`` / ``tool_name``: identify which ``ToolCall`` this
      result answers. ``tool_call_id`` must round-trip unchanged so the
      provider layer can match it against the assistant's original request.
    - ``status``: see :data:`ExecutionStatus`.
    - ``structured_output``: arbitrary JSON-serializable payload the tool
      returned. Only a truncated JSON preview is projected.
    - ``artifacts``: references to out-of-band payloads; only URIs (and
      previews, when present) are projected.
    - ``metrics``: numeric tool-level telemetry (latency, token counts,
      result counts, ...). Projected as a short ``key: value`` list.
    - ``diagnostics``: human-readable notes, typically non-empty only on
      non-``ok`` status. Projected verbatim.
    - ``session_id``: opaque handle an executor may carry across retries.
      Not projected.
    - ``latency_ms``: end-to-end execution latency. Not projected by
      default.

    TODO: see ``TODO.md`` for the open design questions, especially around
    projection format, artifact previews, and error taxonomy.
    """

    tool_call_id: str = Field(validation_alias="toolCallId")
    tool_name: str = Field(validation_alias="toolName")
    status: ExecutionStatus = "ok"
    structured_output: Any | None = Field(
        default=None, validation_alias="structuredOutput"
    )
    artifacts: list[ArtifactRef] = Field(default_factory=list)
    metrics: dict[str, float] = Field(default_factory=dict)
    diagnostics: list[str] = Field(default_factory=list)
    session_id: str | None = Field(default=None, validation_alias="sessionId")
    latency_ms: float | None = Field(default=None, validation_alias="latencyMs")

    model_config = ConfigDict(populate_by_name=True)

    def to_model_message(
        self,
        timestamp: int,
        *,
        max_preview_chars: int = _DEFAULT_MAX_PREVIEW_CHARS,
    ) -> ToolResultMessage:
        """Render a compact, deterministic LLM-facing projection.

        The projection is intentionally small and text-only:

        1. A status line naming the tool and its outcome.
        2. Diagnostics (for non-``ok`` outcomes).
        3. A JSON preview of ``structured_output`` truncated to
           ``max_preview_chars``.
        4. Artifact URIs (with optional content-type and preview blurb).
        5. Metrics as ``key: value`` pairs.

        Fields that carry no signal for the LLM (``session_id``,
        ``latency_ms``) are intentionally omitted; they remain available to
        callers who hold the ``ToolExecutionResult`` directly.

        TODO: the exact wording is a first cut. We will likely revisit once
        real verifier / evaluator consumers exercise it. See ``TODO.md``.
        """
        parts: list[str] = []
        if self.status == "ok":
            parts.append(f"Tool '{self.tool_name}' completed successfully.")
        else:
            parts.append(f"Tool '{self.tool_name}' {self.status}.")
        if self.diagnostics:
            parts.append("Diagnostics:")
            parts.extend(f"- {d}" for d in self.diagnostics)
        if self.structured_output is not None:
            preview = _preview_json(self.structured_output, max_preview_chars)
            parts.append("Output:")
            parts.append(preview)
        if self.artifacts:
            parts.append("Artifacts:")
            for a in self.artifacts:
                line = f"- {a.uri} ({a.content_type}"
                if a.size_bytes is not None:
                    line += f", {a.size_bytes} bytes"
                line += ")"
                if a.preview:
                    line += f": {a.preview}"
                parts.append(line)
        if self.metrics:
            parts.append("Metrics:")
            for key in sorted(self.metrics):
                parts.append(f"- {key}: {self.metrics[key]}")
        text = "\n".join(parts)
        return ToolResultMessage(
            tool_call_id=self.tool_call_id,
            tool_name=self.tool_name,
            content=[TextContent(text=text)],
            is_error=self.status != "ok",
            timestamp=timestamp,
        )


def _preview_json(payload: Any, max_chars: int) -> str:
    """Dump ``payload`` as JSON and truncate to ``max_chars``.

    Falls back to ``repr`` with a note if the payload is not
    JSON-serializable, so a malformed tool output never raises out of the
    projection path.

    TODO: decide whether we prefer ``json.dumps(default=str)`` (lossy but
    always-succeeds) or a structured preview (e.g. first N keys only).
    """
    try:
        rendered = json.dumps(payload, sort_keys=True, default=str)
    except (TypeError, ValueError):
        rendered = f"[unserializable structured_output: {type(payload).__name__}]"
    if len(rendered) > max_chars:
        rendered = rendered[: max(0, max_chars - len(_TRUNCATION_SUFFIX))] + _TRUNCATION_SUFFIX
    return rendered
