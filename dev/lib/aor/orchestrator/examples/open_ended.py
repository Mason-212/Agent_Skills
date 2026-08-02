"""Open-ended workflow examples."""

from __future__ import annotations

from collections.abc import Awaitable, Callable

from ..graph import WorkflowBuilder, WorkflowSpec
from ..node import WorkflowNode
from ..policy import (
    DSPyLMConfig,
    DSPyOpenEndedRLMExecutor,
    RouteRule,
    RuleBasedRouterPolicy,
)
from ..types import NodeCategory


def build_open_ended_assistance_workflow(
    *,
    workflow_id: str = "open_ended_assistance",
    max_iterations: int = 8,
    dspy_lm_config: DSPyLMConfig | None = None,
) -> WorkflowSpec:
    """Build a fallback workflow backed by DSPy's RLM."""

    return (
        WorkflowBuilder(
            workflow_id,
            description="Open-ended assistance workflow backed by DSPy RLM",
        )
        .add_node(
            WorkflowNode(
                name="assist",
                executor=DSPyOpenEndedRLMExecutor(
                    max_iterations=max_iterations,
                    lm_config=dspy_lm_config,
                ),
                category=NodeCategory.AGENT_LOOP,
                description=(
                    "Fallback assistance node for requests that do not fit "
                    "another rigid workflow."
                ),
            )
        )
        .set_start("assist")
        .build()
    )


def build_open_ended_router(
    *,
    workflow_id: str = "open_ended_assistance",
    predicate: Callable[[str], bool] | Callable[[str], Awaitable[bool]] | None = None,
    reason: str | None = None,
) -> RuleBasedRouterPolicy:
    """Build a router that sends matched requests to the open-ended workflow.

    The default predicate matches all requests, which makes this helper useful as a
    final fallback after more specific workflow routes have already been checked.
    """

    return RuleBasedRouterPolicy(
        [
            RouteRule(
                workflow_id=workflow_id,
                predicate=predicate or (lambda _request: True),
                reason=reason or "Matched the open-ended assistance fallback workflow",
            )
        ]
    )
