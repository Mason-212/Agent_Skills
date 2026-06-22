"""agent.pi.edc_harness: runtime-layer contracts above agent.pi.ai.

This subpackage is the *canonical* home for tool-execution bookkeeping that
the LLM does not need to see in full. The boundary between ``pi.edc_harness``
and ``pi.ai`` is deliberate:

- :mod:`agent.pi.ai` is a narrow provider SDK. Its
  :class:`~agent.pi.ai.types.ToolResultMessage` is the compact transcript
  the LLM reads on its next turn; every provider adapter collapses it to
  wire-format text.
- :mod:`agent.pi.edc_harness` owns the full structured execution record -
  :class:`ToolExecutionResult` with artifacts, metrics, diagnostics, session
  handles, and exit status - plus a deterministic projection
  (:meth:`ToolExecutionResult.to_model_message`) that renders the compact
  ``ToolResultMessage`` the provider layer sends upstream.

Callers (tool runtimes, verifiers, approval gates, evaluators) should read
and write :class:`ToolExecutionResult`; only the projection step hands a
``ToolResultMessage`` to ``pi.ai``.

.. warning::
   This is an early contract. See ``TODO.md`` in this package for open
   design questions. Fields and projection format may change before the
   first external consumer lands.
"""

from __future__ import annotations

from .tool_execution_result import (
    ArtifactRef,
    ExecutionStatus,
    ToolExecutionResult,
)

__all__ = [
    "ArtifactRef",
    "ExecutionStatus",
    "ToolExecutionResult",
]
