"""Tool argument validation.

Python port of vendor/pi-mono-upstream/packages/ai/src/utils/validation.ts.

pi-ai uses AJV (JSON Schema validator) with `coerceTypes: true` and
`allErrors: true`. We use the `jsonschema` Python library with equivalent
semantics: collect all errors, coerce obvious type mismatches where safe,
preserve the original error shape so error messages line up with pi-ai's.

The behavioral contract tested in pi-ai's
test/anthropic-tool-name-normalization.test.ts and related suites:
- tool lookup by name; unknown tool raises ToolValidationError
- invalid arguments raise ToolValidationError with a multi-line message
  containing both the per-field errors and the received arguments JSON
- valid arguments are returned (optionally after best-effort coercion)
"""

from __future__ import annotations

import json
from typing import Any

from jsonschema import Draft202012Validator, FormatChecker

from .types import Tool, ToolCall


class ToolValidationError(ValueError):
    """Raised when tool arguments fail JSON-Schema validation.

    Message format is stable and matches pi-ai's AJV-derived message so test
    assertions can be shared. See pi-ai validation.ts line 81.
    """


def validate_tool_call(tools: list[Tool], tool_call: ToolCall) -> dict[str, Any]:
    """Find tool by name and validate; mirrors pi-ai validateToolCall."""
    tool = next((t for t in tools if t.name == tool_call.name), None)
    if tool is None:
        raise ToolValidationError(f'Tool "{tool_call.name}" not found')
    return validate_tool_arguments(tool, tool_call)


def validate_tool_arguments(tool: Tool, tool_call: ToolCall) -> dict[str, Any]:
    """Validate arguments against the tool's JSON Schema.

    Returns the arguments (best-effort coerced for simple type mismatches) on
    success. Raises ToolValidationError with a formatted, multi-line message
    on failure.
    """
    schema = tool.parameters or {}
    if not schema:
        return dict(tool_call.arguments)

    args = _deep_copy_json(tool_call.arguments)
    _coerce_types(args, schema)

    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    errors = sorted(validator.iter_errors(args), key=lambda e: list(e.absolute_path))
    if not errors:
        return args

    formatted = "\n".join(_format_error(err) for err in errors)
    received = json.dumps(tool_call.arguments, indent=2, sort_keys=False)
    raise ToolValidationError(
        f'Validation failed for tool "{tool_call.name}":\n{formatted}\n\n'
        f"Received arguments:\n{received}"
    )


def _format_error(err) -> str:
    path = ".".join(str(p) for p in err.absolute_path) or "root"
    if err.validator == "required":
        missing = err.message.split("'")[1] if "'" in err.message else err.message
        return f"  - {missing}: must have required property '{missing}'"
    return f"  - {path}: {err.message}"


def _deep_copy_json(value: Any) -> Any:
    return json.loads(json.dumps(value))


def _coerce_types(args: Any, schema: dict[str, Any]) -> None:
    """Best-effort type coercion matching AJV `coerceTypes: true` on scalars.

    Only coerces obvious, safe cases (string<->number, string<->bool, int<->float).
    Deeper coercion (arrays, nested objects) would require schema walking that
    AJV implements but that we intentionally keep simple here; tool authors
    should not rely on deep coercion.
    """
    if not isinstance(args, dict):
        return
    props = schema.get("properties", {})
    for key, prop_schema in props.items():
        if key not in args:
            continue
        value = args[key]
        expected = prop_schema.get("type")
        coerced = _coerce_scalar(value, expected)
        if coerced is not _SENTINEL:
            args[key] = coerced


class _Sentinel:
    pass


_SENTINEL = _Sentinel()


def _coerce_scalar(value: Any, expected: str | list[str] | None) -> Any:
    if expected is None or isinstance(expected, list):
        return _SENTINEL
    if expected == "number" or expected == "integer":
        if isinstance(value, bool):
            return _SENTINEL  # don't coerce bool->number
        if isinstance(value, str):
            try:
                return int(value) if expected == "integer" else float(value)
            except ValueError:
                return _SENTINEL
        if expected == "integer" and isinstance(value, float) and value.is_integer():
            return int(value)
        return _SENTINEL
    if expected == "string":
        if isinstance(value, (int, float)) and not isinstance(value, bool):
            return str(value)
        if isinstance(value, bool):
            return _SENTINEL
        return _SENTINEL
    if expected == "boolean":
        if isinstance(value, str):
            if value.lower() in ("true", "1"):
                return True
            if value.lower() in ("false", "0"):
                return False
        return _SENTINEL
    return _SENTINEL


__all__ = ["ToolValidationError", "validate_tool_arguments", "validate_tool_call"]
