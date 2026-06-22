"""Platform-level tool response contract for domain packs.

Tool responses injected into the LLM context MUST use the preview + output_path
shape defined here rather than returning full inference payloads.  Returning the
full payload wastes ~400 tokens per call on raw data the LLM cannot reason over.

The outer contract (status / output_path / preview) is fixed. The ``preview`` dict
MUST contain a ``"type"`` discriminator key that identifies the ML problem type
("forecast", "classification", "anomaly", …). The ``preview`` dict contains
ML problem-specific output summaries (e.g., per-series forecast trends). Optional
``extra`` fields (passed to ``build_tool_response``) are for cross-cutting scalar
metadata like ``num_series`` or ``horizon`` that apply to all series in the response.
Each pack owns the preview structure for its problem type.

Platform contract
-----------------
Every successful tool response must be a JSON object with:

    {
        "status":      "success",
        "output_path": "<session_id>/<filename>",   # relative, never absolute
        "preview": {
            "type": "<problem_type>",               # discriminator — required
            ...                                     # pack-specific scalar fields
        }
    }

Usage — pack author builds the preview dict, then calls ``build_tool_response``:

    from agent.packs.tool_response import build_tool_response

    preview = {
        "type": "forecast",
        "revenue": {
            "q50_first": 148.2,
            "q50_last":  175.4,
            "q50_trend": "upward",
            "q50_range": [139.4, 182.1],
        },
    }
    response = build_tool_response(
        session_id=ctx.session_id,
        output_filename="forecast.json",
        preview=preview,
        extra={"num_series": 1, "horizon": 12},
    )
    return AgentToolResult(content=[TextContent(type="text", text=json.dumps(response))])
"""

from __future__ import annotations

import json
import logging
import re
from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator

logger = logging.getLogger(__name__)


class ToolResponsePreview(BaseModel):
    """Preview must contain a type discriminator and optional problem-specific fields.

    The ``type`` field discriminates between problem types (forecast, classification, etc.).
    Additional fields are problem-specific and defined by domain packs.
    """

    type: str = Field(..., description="Problem type discriminator (forecast, classification, etc.)")

    model_config = {"extra": "allow"}  # Allow pack-specific fields

    @field_validator("type")
    @classmethod
    def validate_type_string(cls, v: Any) -> str:
        if not v or not isinstance(v, str):
            raise ValueError(f"type must be non-empty string, got {type(v).__name__}")
        return v


class ToolResponse(BaseModel):
    """Immutable tool response for LLM context injection.

    Enforces the platform contract: status, output_path, and preview are required.
    Additional fields can be added via the ``extra`` dict during construction.
    """

    status: Literal["success"] = "success"
    output_path: str = Field(..., pattern=r"^[^/]")  # Must not start with /
    preview: ToolResponsePreview

    model_config = {"extra": "allow", "frozen": True}  # Allow extra fields, prevent mutation

    @field_validator("output_path")
    @classmethod
    def validate_path_safety(cls, v: str) -> str:
        if v.startswith("/"):
            raise ValueError(f"output_path must be relative, got: {v}")
        # Note: .. traversal is validated before construction in build_tool_response()
        # This validator only checks the final concatenated path starts correctly
        return v


def build_tool_response(
    *,
    session_id: str,
    output_filename: str,
    preview: dict | ToolResponsePreview,
    extra: dict | None = None,
) -> dict:
    """Build the standard tool response envelope for LLM injection.

    Args:
        session_id:       The session ID from ``PackExecutionContext.session_id``.
        output_filename:  Filename of the artifact written to the workspace
                          (e.g. ``"forecast.json"``).  Must not be a full path.
        preview:          Pack-specific preview dict or ToolResponsePreview instance.
                          MUST contain a ``"type"`` key with a string discriminator
                          (e.g. ``"forecast"``).
        extra:            Optional additional top-level scalar fields to merge
                          into the response (e.g. ``{"num_series": 1, "horizon": 12}``).
                          Keys ``"status"`` and ``"output_path"`` are reserved and
                          will be overwritten if present in ``extra``.

    Returns:
        A dict ready to be ``json.dumps``-ed into a ``TextContent`` response.
        The dict is derived from a validated ToolResponse Pydantic model for type safety.

    Raises:
        ValueError: If ``preview`` is missing the ``"type"`` discriminator, or if
                    ``output_filename`` looks like an absolute path, or if
                    ``session_id`` is empty or contains unsafe characters, or if
                    validation fails for any field.
    """
    # Validate session_id with strict whitelist: alphanumeric + hyphen/underscore, max 64 chars
    if not session_id or not isinstance(session_id, str):
        logger.error(
            "build_tool_response validation failed: invalid session_id "
            "[session=%r type=%s]",
            session_id,
            type(session_id).__name__,
        )
        raise ValueError(
            f"session_id must be a non-empty string. Got: {session_id!r}"
        )
    # '@' is permitted to support tenant/org-prefixed session IDs (e.g. "tenant@org-session"),
    # consistent with _SESSION_ID_SAFE_CHARS in context.py.
    if not re.match(r'^[a-zA-Z0-9_@-]{1,64}$', session_id):
        logger.error(
            "build_tool_response validation failed: session_id contains invalid characters or exceeds length "
            "[session=%s len=%d]",
            session_id,
            len(session_id),
        )
        raise ValueError(
            f"session_id must match pattern ^[a-zA-Z0-9_@-]{{1,64}}$ (alphanumeric, hyphen, underscore, '@'; max 64 chars). "
            f"Got: {session_id!r}"
        )

    # Validate output_filename before concatenation
    if output_filename.startswith("/"):
        logger.error(
            "build_tool_response validation failed: absolute path in output_filename "
            "[session=%s file=%s]",
            session_id,
            output_filename,
        )
        raise ValueError(
            f"output_filename must be a relative filename, not an absolute path. Got: {output_filename!r}"
        )
    if ".." in output_filename.split("/"):
        logger.error(
            "build_tool_response validation failed: path traversal in output_filename "
            "[session=%s file=%s]",
            session_id,
            output_filename,
        )
        raise ValueError(
            f"output_filename must not contain '..' path traversal components. Got: {output_filename!r}"
        )

    # Convert preview dict to ToolResponsePreview if needed
    if isinstance(preview, dict):
        try:
            preview_model = ToolResponsePreview(**preview)
        except Exception as exc:
            logger.error(
                "build_tool_response validation failed: invalid preview structure "
                "[session=%s file=%s]: %s",
                session_id,
                output_filename,
                exc,
            )
            raise ValueError(f"Invalid preview structure: {exc}") from exc
    else:
        preview_model = preview

    # Build ToolResponse with validation
    try:
        data = {
            "output_path": f"{session_id}/{output_filename}",
            "preview": preview_model,
            **(extra or {}),
        }
        response_model = ToolResponse(**data)
    except Exception as exc:
        logger.error(
            "build_tool_response validation failed [session=%s file=%s]: %s",
            session_id,
            output_filename,
            exc,
        )
        raise ValueError(f"Invalid tool response: {exc}") from exc

    # Return as dict for JSON serialization - validate JSON-serializability
    result_dict = response_model.model_dump(mode="json", exclude_none=True)
    try:
        json.dumps(result_dict)
    except TypeError as exc:
        logger.error(
            "build_tool_response: preview contains non-JSON-serializable values [session=%s file=%s]: %s",
            session_id,
            output_filename,
            exc,
        )
        raise ValueError(
            f"Preview contains non-JSON-serializable values (datetime, bytes, custom objects). "
            f"All preview fields must be JSON-safe. Error: {exc}"
        ) from exc
    return result_dict


