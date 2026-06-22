"""Base routing and workflow policies."""

from __future__ import annotations

import inspect
from collections.abc import Awaitable, Callable, Sequence

from pydantic import BaseModel, ConfigDict

from ..node import WorkflowNode
from ..types import (
    RouteDestination,
    RouterDecision,
    RunState,
    StepResult,
    StepStatus,
    WorkflowAction,
    WorkflowDecision,
    WorkflowRequest,
)


class DefaultWorkflowPolicy:
    """Deterministic default policy used when a node does not define one."""

    async def decide(
        self,
        node: WorkflowNode,
        result: StepResult,
        run_state: RunState,
    ) -> WorkflowDecision:
        attempt = run_state.node_attempts.get(node.name, 0)

        if result.status == StepStatus.INTERRUPT:
            return WorkflowDecision(
                action=WorkflowAction.INTERRUPT,
                reason="Node requested interrupt",
                interrupt=result.interrupt,
            )

        if result.status == StepStatus.FAILURE:
            if result.retryable and attempt <= node.retry_limit:
                return WorkflowDecision(
                    action=WorkflowAction.RETRY,
                    reason="Retryable node failure",
                )
            return WorkflowDecision(
                action=WorkflowAction.FAIL,
                reason="Node reported failure",
                final_output=result.output,
            )

        if node.allowed_next_nodes:
            return WorkflowDecision(
                action=WorkflowAction.NEXT,
                next_node=node.allowed_next_nodes[0],
                reason="Single allowed next node",
            )

        return WorkflowDecision(
            action=WorkflowAction.COMPLETE,
            reason="No remaining next nodes",
            final_output=result.output,
        )


class RouteRule(BaseModel):
    """One deterministic routing rule."""

    workflow_id: str
    predicate: Callable[[str], bool] | Callable[[str], Awaitable[bool]]
    reason: str | None = None

    model_config = ConfigDict(arbitrary_types_allowed=True)


class RuleBasedRouterPolicy:
    """Deterministic ingress router for registered workflows."""

    def __init__(self, rules: Sequence[RouteRule]) -> None:
        self._rules = list(rules)

    async def route(
        self,
        request: WorkflowRequest,
        known_workflow_ids: Sequence[str],
    ) -> RouterDecision:
        for rule in self._rules:
            outcome = rule.predicate(request.text)
            if inspect.isawaitable(outcome):
                matched = await outcome
            else:
                matched = outcome
            if matched:
                if rule.workflow_id not in known_workflow_ids:
                    return RouterDecision(
                        destination=RouteDestination.INTERRUPT,
                        confidence=0.0,
                        interrupt={
                            "kind": "workflow_selection",
                            "request": request.text,
                            "available_workflows": list(known_workflow_ids),
                        },
                        reason=(
                            f"Rule matched unknown workflow {rule.workflow_id!r}; "
                            "asking for an explicit workflow selection"
                        ),
                    )
                return RouterDecision(
                    destination=RouteDestination.KNOWN_WORKFLOW,
                    workflow_id=rule.workflow_id,
                    confidence=1.0,
                    reason=rule.reason or f"Rule matched workflow {rule.workflow_id!r}",
                )
        return RouterDecision(
            destination=RouteDestination.INTERRUPT,
            confidence=0.0,
            interrupt={
                "kind": "workflow_selection",
                "request": request.text,
                "available_workflows": list(known_workflow_ids),
            },
            reason="No deterministic workflow route matched",
        )
