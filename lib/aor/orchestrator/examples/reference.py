"""Reference workflow examples."""

from __future__ import annotations

from typing import Any, cast

from ..context import WorkflowNodeExecutionContext
from ..executors import CallableExecutor
from ..graph import WorkflowBuilder, WorkflowNode, WorkflowSpec
from ..policy.base import RouteRule, RuleBasedRouterPolicy
from ..types import (
    ArtifactRef,
    StepResult,
    StepStatus,
)


def build_reference_workflow() -> WorkflowSpec:
    async def collect_inputs(context: WorkflowNodeExecutionContext) -> StepResult:
        interrupts = context.run_state.working_memory.get("interrupts", [])
        if not interrupts:
            return StepResult(
                status=StepStatus.INTERRUPT,
                interrupt={"question": "Which workflow input should I use?", "options": ["known", "fallback"]},
            )
        return StepResult(
            status=StepStatus.SUCCESS,
            output={"selected_input": interrupts[-1]["response"]},
            artifacts=[ArtifactRef(kind="selection", uri="memory://selection")],
            summary="Collected workflow input",
        )

    async def finalize(context: WorkflowNodeExecutionContext) -> StepResult:
        latest = cast(dict[str, Any], context.run_state.step_history[-1].result.output or {})
        return StepResult(
            status=StepStatus.SUCCESS,
            output={"answer": f"Completed with input: {latest['selected_input']}"},
            summary="Finalized workflow answer",
        )

    return (
        WorkflowBuilder("reference_workflow", description="Reference clarify + finalize workflow")
        .add_node(
            WorkflowNode(
                name="collect_inputs",
                executor=CallableExecutor(collect_inputs),
                allowed_next_nodes=("finalize",),
            )
        )
        .add_node(WorkflowNode(name="finalize", executor=CallableExecutor(finalize)))
        .set_start("collect_inputs")
        .build()
    )


def build_reference_router() -> RuleBasedRouterPolicy:
    return RuleBasedRouterPolicy(
        [
            RouteRule(
                workflow_id="reference_workflow",
                predicate=lambda request: "known" in request.lower(),
                reason="Matched the reference workflow keyword",
            )
        ]
    )
