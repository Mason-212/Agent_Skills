"""Pack workflow wrappers for domain pack execution.

Two concrete classes serve different use cases:

- PackWorkflowWrapper  — wraps a plain async callable (simple packs, tests)
- PackWorkflowOrchestrator — wraps an orchestrator WorkflowSpec via
                              WorkflowRuntime (multi-node graph workflows)

Both expose the same interface: run(request) and resume(checkpoint, response).

Pack-layer outcome types
------------------------
``run_direct()`` / ``resume_direct()`` return a discriminated union at the
**pack layer**, distinct from the internal orchestrator ``WorkflowOutcome``:

- ``WorkflowCompleted`` — workflow reached a terminal success; carry ``result``
  (a ``PackResult``).
- ``WorkflowPaused`` — workflow hit an interrupt and is waiting for human input;
  carry ``checkpoint`` and ``interrupts``. This is **expected control flow**, not
  an error — APM tooling, retry decorators, and exception handlers will not see
  it as a failure.
- ``WorkflowFailedError`` (exception) — workflow reached a terminal failure;
  this truly is an unexpected error and maps naturally to ``raise``.

Caller pattern (flat loop, no nested try/except)::

    outcome = await pack.run_direct(request)
    while isinstance(outcome, WorkflowPaused):
        response = await ask_user(outcome.interrupts)
        outcome = await pack.resume_direct(outcome.checkpoint, response, request)
    # outcome is now WorkflowCompleted
    result = outcome.result
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Callable

if TYPE_CHECKING:
    from agent.packs.base import PackResult
    from orchestrator import (  # type: ignore[import]
        WorkflowCheckpointHandle,
        WorkflowExecutionResult,
        WorkflowSpec,
    )
    from orchestrator.context import WorkflowNodeExecutionContext  # type: ignore[import]
    from orchestrator.types import StepResult  # type: ignore[import]


# ---------------------------------------------------------------------------
# Pack-layer outcome types (public API of run_direct / resume_direct)
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class WorkflowCompleted:
    """Returned by ``run_direct`` / ``resume_direct`` when the workflow
    reaches a terminal success state.

    Attributes:
        result: The ``PackResult`` built by ``build_result()``.
    """

    result: "PackResult"


@dataclass(frozen=True)
class WorkflowPaused:
    """Returned by ``run_direct`` / ``resume_direct`` when the workflow
    reaches an interrupt point and is waiting for human (or system) input.

    This is **expected control flow** in human-in-the-loop workflows — it is
    not an error. APM tooling and retry decorators never see it because it is
    a return value, not an exception.

    Pass ``checkpoint`` to ``pack.resume_direct()`` to continue the workflow.

    Attributes:
        pack_id: ID of the pack whose workflow paused.
        checkpoint: Opaque handle required by ``resume_direct()``.
        interrupts: Tuple of interrupt payloads emitted by the paused node
                   (e.g. approval requests, clarification prompts).
    """

    pack_id: str
    checkpoint: "WorkflowCheckpointHandle"
    interrupts: tuple[Any, ...]


# Public alias for callers that want to annotate the union explicitly.
WorkflowDirectOutcome = WorkflowCompleted | WorkflowPaused


# ---------------------------------------------------------------------------
# Internal orchestrator-layer types (not part of the pack public API)
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class Completed:
    """Internal: orchestrator terminal result — successful completion."""

    output: Any


@dataclass(frozen=True)
class Paused:
    """Internal: orchestrator terminal result — interrupt awaiting resume()."""

    checkpoint: "WorkflowCheckpointHandle"
    interrupts: tuple[Any, ...]


@dataclass(frozen=True)
class Failed:
    """Internal: orchestrator terminal result — failed run."""

    payload: Any
    reason: str | None = None


WorkflowOutcome = Completed | Paused | Failed


# ---------------------------------------------------------------------------
# Exception — only for true failure (not for pause)
# ---------------------------------------------------------------------------

class WorkflowFailedError(RuntimeError):
    """Raised by ``run_direct`` / ``resume_direct`` when the workflow reaches
    a terminal failure state.

    A failed workflow is a genuine error — the workflow could not complete and
    no result is available. This maps naturally to ``raise``.

    ``WorkflowPaused`` (a paused workflow) is **not** an exception — it is
    expected control flow returned as a value. See module docstring.

    Example::

        outcome = await pack.run_direct(request)
        while isinstance(outcome, WorkflowPaused):
            response = await ask_user(outcome.interrupts)
            outcome = await pack.resume_direct(outcome.checkpoint, response, request)
        result = outcome.result   # WorkflowCompleted

        # Failed workflows surface here:
        except WorkflowFailedError as e:
            logger.error("workflow failed: %s — payload: %s", e.reason, e.payload)
            raise

    Attributes:
        pack_id: ID of the pack whose workflow failed.
        payload: Final output from the failed workflow node (may be None).
        reason: Human-readable failure reason, or None if not recorded.
    """

    def __init__(self, pack_id: str, payload: Any, reason: str | None) -> None:
        self.pack_id = pack_id
        self.payload = payload
        self.reason = reason
        reason_str = f": {reason}" if reason else ""
        super().__init__(f"Pack '{pack_id}': workflow failed{reason_str}")


class PackWorkflowWrapper:
    """Wraps a plain async callable as a pack workflow.

    Use this for simple packs or tests where the entire workflow
    logic lives in a single async function.

    Example:
        async def my_workflow(request: dict) -> dict:
            return {"result": compute(request["data"])}

        wrapper = PackWorkflowWrapper(my_workflow)
        output = await wrapper.run(request)
    """

    def __init__(self, workflow_fn: Callable[[Any], Any]):
        """Initialize wrapper with workflow function.

        Args:
            workflow_fn: Async function that takes a request and returns
                        the final output dict.

        Raises:
            TypeError: If workflow_fn is not an async function.
        """
        if not asyncio.iscoroutinefunction(workflow_fn):
            raise TypeError(
                f"workflow_fn '{getattr(workflow_fn, '__name__', repr(workflow_fn))}' "
                "must be an async function. Use 'async def' to define it."
            )
        self._workflow_fn = workflow_fn

    async def run(self, request: Any) -> Any:
        """Execute workflow and return final output.

        Args:
            request: Workflow request passed directly to workflow_fn.

        Returns:
            Whatever workflow_fn returns.
        """
        return await self._workflow_fn(request)

    @property
    def supports_resume(self) -> bool:
        """Plain callable workflows do not support interrupt/resume."""
        return False

    async def resume(self, checkpoint: Any, response: Any) -> Any:
        """Not supported for plain callable workflows.

        Raises:
            NotImplementedError: Always. Use PackWorkflowOrchestrator
                for workflows that require interrupt/resume support.
        """
        raise NotImplementedError(
            "resume() is not supported for plain callable workflows. "
            "Use PackWorkflowOrchestrator with a WorkflowSpec for interrupt/resume support."
        )


class PackWorkflowOrchestrator:
    """Wraps an orchestrator WorkflowSpec via WorkflowRuntime.

    Use this for multi-node graph workflows built with WorkflowBuilder.
    Supports both run() and resume() via WorkflowRuntime's checkpoint system.

    Example:
        from orchestrator import WorkflowBuilder, CallableExecutor, WorkflowNode

        workflow = (
            WorkflowBuilder("my_workflow")
            .add_node(WorkflowNode(name="step1", executor=CallableExecutor(handler1), allowed_next_nodes=("step2",)))
            .add_node(WorkflowNode(name="step2", executor=CallableExecutor(handler2), allowed_next_nodes=()))
            .set_start("step1")
            .build()
        )
        return PackWorkflowOrchestrator(workflow)
    """

    def __init__(self, workflow: "WorkflowSpec"):
        """Initialize with a compiled WorkflowSpec.

        Args:
            workflow: WorkflowSpec from WorkflowBuilder.build(). The spec
                     is validated on construction.
        """
        from langgraph.checkpoint.memory import InMemorySaver  # type: ignore[import]

        self._workflow = workflow
        # Shared checkpointer kept alive across run() → resume() turns.
        # WorkflowRuntime uses InMemorySaver by default, but that saver is
        # private to each runtime instance — constructing a new runtime per
        # call (needed for on_progress wrapping) would discard the paused
        # checkpoint state. By owning the saver here and injecting it into
        # every runtime, checkpoint state persists for the lifetime of this
        # orchestrator regardless of how many runtimes are constructed.
        self._checkpointer = InMemorySaver()

    @property
    def supports_resume(self) -> bool:
        """Graph workflows support interrupt/resume via WorkflowRuntime checkpoints."""
        return True

    async def run(
        self,
        request: Any,
        *,
        on_progress: Callable[[str], None] | None = None,
    ) -> WorkflowOutcome:
        """Execute the workflow graph and return a status-discriminated outcome.

        Args:
            request: WorkflowRequest passed to the runtime.
            on_progress: Optional callback called with the node name each time a
                node begins execution. Use for real-time UI updates (e.g. Streamlit
                ``st.status()`` via ``run_in_thread``). Called synchronously from
                within the async workflow execution — keep it fast and non-blocking.

        Returns:
            Completed(output), Paused(checkpoint, interrupts), or Failed(payload, reason).

        Raises:
            RuntimeError: If runtime returns a non-terminal status.
        """
        from orchestrator import WorkflowRuntime  # type: ignore[import]

        workflow = (
            _wrap_workflow_with_progress(self._workflow, on_progress)
            if on_progress is not None
            else self._workflow
        )
        runtime = WorkflowRuntime(workflow, checkpointer=self._checkpointer)
        result = await runtime.run(request)
        return self._extract_output(result)

    async def resume(
        self,
        checkpoint: "WorkflowCheckpointHandle",
        response: Any,
        *,
        on_progress: Callable[[str], None] | None = None,
    ) -> WorkflowOutcome:
        """Resume a paused workflow from a checkpoint.

        Args:
            checkpoint: WorkflowCheckpointHandle returned by a previous
                       run that ended in an interrupt.
            response: User or system response to the interrupt.
            on_progress: Optional callback called with the node name each time a
                node begins execution. Mirrors ``run()`` — wire the same callback
                for consistent streaming across initial run and resume turns.

        Returns:
            Completed(output), Paused(checkpoint, interrupts), or Failed(payload, reason).

        Raises:
            RuntimeError: If runtime returns a non-terminal status.
        """
        from orchestrator import WorkflowRuntime  # type: ignore[import]

        workflow = (
            _wrap_workflow_with_progress(self._workflow, on_progress)
            if on_progress is not None
            else self._workflow
        )
        runtime = WorkflowRuntime(workflow, checkpointer=self._checkpointer)
        result = await runtime.resume(checkpoint, response)
        return self._extract_output(result)

    @staticmethod
    def _extract_output(result: "WorkflowExecutionResult") -> WorkflowOutcome:
        """Map runtime status to an explicit terminal workflow outcome."""
        from orchestrator import WorkflowStatus  # type: ignore[import]

        match result.status:
            case WorkflowStatus.COMPLETED:
                return Completed(output=result.run_state.final_output)
            case WorkflowStatus.PAUSED:
                if result.checkpoint is None:
                    raise RuntimeError(
                        "Workflow runtime reported PAUSED status but returned a null "
                        "checkpoint handle. This is a bug in the underlying "
                        "WorkflowRuntime implementation — a correctly implemented "
                        "runtime must always attach a non-null checkpoint when it "
                        "pauses so that the caller can resume the workflow.\n\n"
                        "Diagnostic info:\n"
                        f"  run_id    : {getattr(result, 'run_id', '<unknown>')}\n"
                        f"  interrupts: {getattr(result, 'interrupts', '<unknown>')}\n"
                        f"  run_state : {getattr(result, 'run_state', '<unknown>')}\n\n"
                        "Resolution: inspect the WorkflowRuntime that produced this "
                        "result and ensure it sets `checkpoint` before returning a "
                        "PAUSED status. The workflow cannot be resumed from this "
                        "execution; it must be restarted."
                    )
                return Paused(
                    checkpoint=result.checkpoint,
                    interrupts=tuple(result.interrupts) if result.interrupts else (),
                )
            case WorkflowStatus.FAILED:
                return Failed(
                    payload=result.run_state.final_output,
                    reason=PackWorkflowOrchestrator._failure_reason(result),
                )
            case WorkflowStatus.RUNNING:
                raise RuntimeError("workflow returned without reaching a terminal state")

        raise RuntimeError(f"workflow returned unknown status: {result.status!r}")

    @staticmethod
    def _failure_reason(result: "WorkflowExecutionResult") -> str | None:
        """Best-effort extraction of failure reason from runtime event log."""
        for event in reversed(result.run_state.event_log):
            if event.type == "workflow_failed":
                payload_reason = event.payload.get("reason")
                if isinstance(payload_reason, str):
                    return payload_reason
                return event.message
        return None


class _ProgressWrappingExecutor:
    """Executor adapter that calls on_progress(node_name) before delegating.

    Wraps the original node executor so that the callback fires at node-entry
    time (synchronously, before the executor runs). Kept private — callers use
    ``PackWorkflowOrchestrator.run(on_progress=...)`` instead.
    """

    def __init__(
        self,
        node_name: str,
        inner: Any,
        on_progress: Callable[[str], None],
    ) -> None:
        self._node_name = node_name
        self._inner = inner
        self._on_progress = on_progress

    async def execute(self, context: "WorkflowNodeExecutionContext") -> "StepResult":
        self._on_progress(self._node_name)
        return await self._inner.execute(context)


def _wrap_workflow_with_progress(
    workflow: "WorkflowSpec",
    on_progress: Callable[[str], None],
) -> "WorkflowSpec":
    """Return a shallow copy of *workflow* where every node executor fires on_progress first.

    Uses Pydantic ``model_copy(update=...)`` on both ``WorkflowNode`` and ``WorkflowSpec``
    so that any fields added to those models in future edc_orchestrator versions are
    preserved automatically — only ``executor`` is overridden per node.

    The original spec stored on the orchestrator is never mutated, ensuring correctness
    when ``run()`` is called concurrently with different ``on_progress`` callbacks.
    """
    wrapped_nodes = {
        name: node.model_copy(
            update={"executor": _ProgressWrappingExecutor(name, node.executor, on_progress)}
        )
        for name, node in workflow.nodes.items()
    }
    return workflow.model_copy(update={"nodes": wrapped_nodes})
