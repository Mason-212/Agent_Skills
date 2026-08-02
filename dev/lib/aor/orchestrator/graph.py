"""Workflow graph specifications."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, model_validator

from .node import WorkflowNode
from .policy.base import DefaultWorkflowPolicy


class WorkflowValidationError(ValueError):
    """Raised when a workflow spec or policy output is invalid."""


class WorkflowSpec(BaseModel):
    """Complete workflow definition."""

    workflow_id: str
    start_node: str
    nodes: dict[str, WorkflowNode]
    description: str | None = None

    model_config = ConfigDict(arbitrary_types_allowed=True)

    @model_validator(mode="after")
    def _validate_model(self) -> WorkflowSpec:
        self.validate_spec()
        return self

    def validate_spec(self) -> None:
        if self.start_node not in self.nodes:
            raise WorkflowValidationError(
                f"Workflow {self.workflow_id!r} start node {self.start_node!r} is missing"
            )
        for node_name, node in self.nodes.items():
            if node_name != node.name:
                raise WorkflowValidationError(
                    f"Workflow {self.workflow_id!r} stores node {node.name!r} under "
                    f"mismatched key {node_name!r}"
                )
            for next_node in node.allowed_next_nodes:
                if next_node not in self.nodes:
                    raise WorkflowValidationError(
                        f"Node {node_name!r} references unknown next node {next_node!r}"
                    )
            if node.policy is None:
                node.policy = DefaultWorkflowPolicy()


class WorkflowBuilder:
    """Convenience builder for workflow specs."""

    def __init__(self, workflow_id: str, *, description: str | None = None) -> None:
        self._workflow_id = workflow_id
        self._description = description
        self._nodes: dict[str, WorkflowNode] = {}
        self._start_node: str | None = None

    def add_node(
        self,
        node: WorkflowNode,
    ) -> WorkflowBuilder:
        self._nodes[node.name] = node
        return self

    def set_start(self, name: str) -> WorkflowBuilder:
        self._start_node = name
        return self

    def build(self) -> WorkflowSpec:
        if self._start_node is None:
            raise WorkflowValidationError("Workflow must define an explicit start node via set_start()")
        spec = WorkflowSpec(
            workflow_id=self._workflow_id,
            description=self._description,
            start_node=self._start_node,
            nodes=self._nodes,
        )
        spec.validate_spec()
        return spec


class WorkflowRegistry:
    """Simple registry for known workflows."""

    def __init__(self) -> None:
        self._workflows: dict[str, WorkflowSpec] = {}

    def register(self, workflow: WorkflowSpec) -> None:
        workflow.validate_spec()
        self._workflows[workflow.workflow_id] = workflow

    def get(self, workflow_id: str) -> WorkflowSpec:
        if workflow_id not in self._workflows:
            raise WorkflowValidationError(f"Unknown workflow {workflow_id!r}")
        return self._workflows[workflow_id]

    def workflow_ids(self) -> list[str]:
        return sorted(self._workflows)
