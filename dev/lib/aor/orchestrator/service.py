"""Top-level workflow orchestration service."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from .checkpoint import WorkflowCheckpointHandle
from .graph import WorkflowRegistry, WorkflowSpec, WorkflowValidationError
from .node import RouterPolicy
from .runtime import WorkflowRuntime
from .types import (
    OrchestratorExecutionResult,
    OrchestratorStatus,
    RouteDestination,
    RouterDecision,
    WorkflowExecutionResult,
    WorkflowRequest,
    WorkflowStatus,
)


class OrchestratorService:
    """Facade that routes requests into workflows and resumes paused runs."""

    def __init__(
        self,
        registry: WorkflowRegistry,
        router: RouterPolicy,
        *,
        runtime_factory: Callable[[WorkflowSpec], WorkflowRuntime] | None = None,
    ) -> None:
        self._registry = registry
        self._router = router
        self._runtime_factory = runtime_factory or WorkflowRuntime
        self._runtimes: dict[str, WorkflowRuntime] = {}
        self._workflow_by_thread_id: dict[str, str] = {}

    async def run(
        self,
        request: WorkflowRequest,
        *,
        working_memory: dict[str, Any] | None = None,
    ) -> OrchestratorExecutionResult:
        decision = await self._router.route(request, self._registry.workflow_ids())
        if decision.destination == RouteDestination.INTERRUPT:
            interrupts = (decision.interrupt,) if decision.interrupt is not None else ()
            return OrchestratorExecutionResult(
                status=OrchestratorStatus.ROUTING_INTERRUPT,
                router_decision=decision,
                interrupts=interrupts,
            )
        if decision.workflow_id is None:
            raise WorkflowValidationError(
                "Router selected a known workflow without providing workflow_id"
            )

        runtime = self._runtime_for(decision.workflow_id)
        workflow_result = await runtime.run(request, working_memory=working_memory)
        self._track_checkpoint(decision.workflow_id, workflow_result)
        return _wrap_workflow_result(
            workflow_id=decision.workflow_id,
            workflow_result=workflow_result,
            router_decision=decision,
        )

    async def resume(
        self,
        checkpoint: WorkflowCheckpointHandle,
        response: Any,
        *,
        workflow_id: str | None = None,
    ) -> OrchestratorExecutionResult:
        resolved_workflow_id = workflow_id or self._workflow_by_thread_id.get(
            checkpoint.thread_id
        )
        if resolved_workflow_id is None:
            raise WorkflowValidationError(
                "Cannot resume checkpoint without workflow_id. "
                "Pass workflow_id explicitly or resume using the same service instance."
            )

        runtime = self._runtime_for(resolved_workflow_id)
        workflow_result = await runtime.resume(checkpoint, response)
        self._track_checkpoint(resolved_workflow_id, workflow_result)
        return _wrap_workflow_result(
            workflow_id=resolved_workflow_id,
            workflow_result=workflow_result,
            router_decision=None,
        )

    def _runtime_for(self, workflow_id: str) -> WorkflowRuntime:
        if workflow_id not in self._runtimes:
            self._runtimes[workflow_id] = self._runtime_factory(
                self._registry.get(workflow_id)
            )
        return self._runtimes[workflow_id]

    def _track_checkpoint(
        self,
        workflow_id: str,
        workflow_result: WorkflowExecutionResult,
    ) -> None:
        thread_id = workflow_result.checkpoint.thread_id
        if workflow_result.status in {WorkflowStatus.PAUSED, WorkflowStatus.RUNNING}:
            self._workflow_by_thread_id[thread_id] = workflow_id
            return
        self._workflow_by_thread_id.pop(thread_id, None)


def _wrap_workflow_result(
    *,
    workflow_id: str,
    workflow_result: WorkflowExecutionResult,
    router_decision: RouterDecision | None,
) -> OrchestratorExecutionResult:
    return OrchestratorExecutionResult(
        status=OrchestratorStatus(workflow_result.status.value),
        workflow_id=workflow_id,
        router_decision=router_decision,
        workflow_result=workflow_result,
        interrupts=workflow_result.interrupts,
    )
