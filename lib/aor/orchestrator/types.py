"""Public workflow contracts."""

from __future__ import annotations

from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from .checkpoint import WorkflowCheckpointHandle


class NodeCategory(StrEnum):
    """Supported workflow node categories."""

    DETERMINISTIC = "deterministic"
    SINGLE_TURN = "single_turn"
    AGENT_LOOP = "agent_loop"
    SUBGRAPH = "subgraph"


class StepStatus(StrEnum):
    """Normalized outcome of a workflow node execution."""

    SUCCESS = "success"
    FAILURE = "failure"
    INTERRUPT = "interrupt"


class WorkflowAction(StrEnum):
    """Actions a workflow policy may choose after a node finishes."""

    NEXT = "next"
    RETRY = "retry"
    FAIL = "fail"
    INTERRUPT = "interrupt"
    COMPLETE = "complete"


class WorkflowStatus(StrEnum):
    """Terminal and non-terminal workflow statuses."""

    COMPLETED = "completed"
    FAILED = "failed"
    PAUSED = "paused"
    RUNNING = "running"


class OrchestratorStatus(StrEnum):
    """Top-level orchestrator statuses."""

    COMPLETED = "completed"
    FAILED = "failed"
    PAUSED = "paused"
    RUNNING = "running"
    ROUTING_INTERRUPT = "routing_interrupt"


class RouteDestination(StrEnum):
    """Ingress router outcomes before workflow execution begins."""

    KNOWN_WORKFLOW = "known_workflow"
    INTERRUPT = "interrupt"


class ArtifactRef(BaseModel):
    """Workflow-visible artifact pointer."""

    kind: str
    uri: str
    metadata: dict[str, Any] = Field(default_factory=dict)


class WorkflowRequest(BaseModel):
    """Structured request passed through the workflow layer."""

    text: str
    metadata: dict[str, Any] = Field(default_factory=dict)
    artifacts: list[ArtifactRef] = Field(default_factory=list)
    constraints: dict[str, Any] = Field(default_factory=dict)

    model_config = ConfigDict(arbitrary_types_allowed=True)


class RuntimeEvent(BaseModel):
    """Structured event emitted during workflow execution."""

    type: str
    node_name: str | None = None
    attempt: int | None = None
    message: str | None = None
    payload: dict[str, Any] = Field(default_factory=dict)


class StepResult(BaseModel):
    """Normalized output from a workflow node or executor."""

    status: StepStatus
    output: Any | None = None
    summary: str | None = None
    retryable: bool = False
    artifacts: list[ArtifactRef] = Field(default_factory=list)
    diagnostics: dict[str, Any] = Field(default_factory=dict)
    interrupt: Any | None = None

    model_config = ConfigDict(arbitrary_types_allowed=True)


class WorkflowDecision(BaseModel):
    """Policy decision made after a node produces a `StepResult`."""

    action: WorkflowAction
    next_node: str | None = None
    reason: str | None = None
    interrupt: Any | None = None
    final_output: Any | None = None

    model_config = ConfigDict(arbitrary_types_allowed=True)


class StepRecord(BaseModel):
    """Execution record for one node attempt."""

    node_name: str
    attempt: int
    result: StepResult
    decision: WorkflowDecision | None = None

    model_config = ConfigDict(arbitrary_types_allowed=True)


class RunState(BaseModel):
    """Workflow-owned state kept independent from executor internals."""

    workflow_id: str
    request: WorkflowRequest
    working_memory: dict[str, Any] = Field(default_factory=dict)
    node_attempts: dict[str, int] = Field(default_factory=dict)
    step_history: list[StepRecord] = Field(default_factory=list)
    event_log: list[RuntimeEvent] = Field(default_factory=list)
    artifacts: list[ArtifactRef] = Field(default_factory=list)
    final_output: Any | None = None

    model_config = ConfigDict(arbitrary_types_allowed=True)


class RouterDecision(BaseModel):
    """Decision returned by the ingress router before a workflow begins."""

    destination: RouteDestination
    workflow_id: str | None = None
    confidence: float | None = None
    interrupt: Any | None = None
    reason: str | None = None


class WorkflowExecutionResult(BaseModel):
    """Result returned after starting or resuming a workflow."""

    status: WorkflowStatus
    checkpoint: WorkflowCheckpointHandle
    run_state: RunState
    interrupts: tuple[Any, ...] = ()

    model_config = ConfigDict(arbitrary_types_allowed=True)


class OrchestratorExecutionResult(BaseModel):
    """Result returned after routing and running or resuming a workflow."""

    status: OrchestratorStatus
    workflow_id: str | None = None
    router_decision: RouterDecision | None = None
    workflow_result: WorkflowExecutionResult | None = None
    interrupts: tuple[Any, ...] = ()

    model_config = ConfigDict(arbitrary_types_allowed=True)
