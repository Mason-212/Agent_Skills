"""Workflow execution context types."""

from __future__ import annotations

from .types import RunState, WorkflowRequest


class WorkflowNodeExecutionContext:
    """Concrete node execution context used by runtime and adapters."""

    def __init__(
        self,
        *,
        workflow_id: str,
        node_name: str,
        attempt: int,
        request: WorkflowRequest,
        run_state: RunState,
    ) -> None:
        self.workflow_id = workflow_id
        self.node_name = node_name
        self.attempt = attempt
        self.request = request
        self.run_state = run_state
