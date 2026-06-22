"""Workflow node definitions and related policy protocols."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Protocol, runtime_checkable

from pydantic import BaseModel, ConfigDict, Field

from .executors import ExecutorAdapter
from .types import (
    NodeCategory,
    RouterDecision,
    RunState,
    StepResult,
    WorkflowAction,
    WorkflowDecision,
    WorkflowRequest,
)


@runtime_checkable
class WorkflowPolicy(Protocol):
    """Policy that decides what to do after a node finishes."""

    async def decide(
        self,
        node: WorkflowNode,
        result: StepResult,
        run_state: RunState,
    ) -> WorkflowDecision: ...


@runtime_checkable
class RouterPolicy(Protocol):
    """Policy that selects a registered workflow or asks for an interrupt."""

    async def route(
        self,
        request: WorkflowRequest,
        known_workflow_ids: Sequence[str],
    ) -> RouterDecision: ...


def _default_allowed_actions() -> frozenset[WorkflowAction]:
    return frozenset(
        {
            WorkflowAction.NEXT,
            WorkflowAction.RETRY,
            WorkflowAction.FAIL,
            WorkflowAction.INTERRUPT,
            WorkflowAction.COMPLETE,
        }
    )


class WorkflowNode(BaseModel):
    """Definition of one workflow node."""

    name: str
    executor: ExecutorAdapter
    allowed_next_nodes: tuple[str, ...] = ()
    allowed_actions: frozenset[WorkflowAction] = Field(default_factory=_default_allowed_actions)
    retry_limit: int = 0
    category: NodeCategory = NodeCategory.DETERMINISTIC
    description: str | None = None
    policy: WorkflowPolicy | None = None

    model_config = ConfigDict(arbitrary_types_allowed=True)
