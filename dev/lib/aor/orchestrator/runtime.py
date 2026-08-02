"""LangGraph-backed workflow runtime."""

from __future__ import annotations

from typing import Any

from langgraph.checkpoint.memory import InMemorySaver
from langgraph.constants import END, START
from langgraph.graph import StateGraph
from langgraph.graph.state import CompiledStateGraph
from langgraph.types import Command, interrupt
from typing_extensions import TypedDict

from .checkpoint import WorkflowCheckpointHandle, workflow_config
from .context import WorkflowNodeExecutionContext
from .events import (
    decision_made,
    interrupt_requested,
    interrupt_resumed,
    step_finished,
    step_started,
    workflow_completed,
    workflow_failed,
)
from .graph import WorkflowSpec, WorkflowValidationError
from .node import WorkflowNode
from .types import (
    RunState,
    RuntimeEvent,
    StepRecord,
    StepResult,
    StepStatus,
    WorkflowAction,
    WorkflowDecision,
    WorkflowExecutionResult,
    WorkflowRequest,
    WorkflowStatus,
)


class _WorkflowState(TypedDict):
    run_state: dict[str, Any]
    active_node: str
    last_result: dict[str, Any] | None
    last_decision: dict[str, Any] | None
    terminal_status: str | None


class WorkflowRuntime:
    """Public workflow runtime hiding the internal LangGraph graph."""

    def __init__(
        self,
        workflow: WorkflowSpec,
        *,
        checkpointer: Any | None = None,
    ) -> None:
        self._workflow = workflow
        self._workflow.validate_spec()
        self._checkpointer = checkpointer or InMemorySaver()
        self._compiled = self._build_graph()

    async def run(
        self,
        request: WorkflowRequest,
        *,
        checkpoint: WorkflowCheckpointHandle | None = None,
        working_memory: dict[str, Any] | None = None,
    ) -> WorkflowExecutionResult:
        handle = checkpoint or WorkflowCheckpointHandle.new()
        run_state = RunState(
            workflow_id=self._workflow.workflow_id,
            request=request,
            working_memory=working_memory or {},
        )
        initial_state: _WorkflowState = {
            "run_state": _dump_run_state(run_state),
            "active_node": self._workflow.start_node,
            "last_result": None,
            "last_decision": None,
            "terminal_status": None,
        }
        await self._compiled.ainvoke(
            initial_state,
            workflow_config(handle),
        )
        return await self._result_from_checkpoint(handle)

    async def resume(
        self,
        checkpoint: WorkflowCheckpointHandle,
        response: Any,
    ) -> WorkflowExecutionResult:
        await self._compiled.ainvoke(
            Command(resume=response),
            workflow_config(checkpoint),
        )
        return await self._result_from_checkpoint(checkpoint)

    async def _execute_node(self, state: _WorkflowState) -> dict[str, Any]:
        run_state = _load_run_state(state["run_state"])
        active_node = state["active_node"]
        node = self._workflow.nodes[active_node]
        attempt = run_state.node_attempts.get(active_node, 0) + 1

        run_state = _append_event(run_state, step_started(active_node, attempt))
        context = WorkflowNodeExecutionContext(
            workflow_id=self._workflow.workflow_id,
            node_name=active_node,
            attempt=attempt,
            request=run_state.request,
            run_state=run_state,
        )
        try:
            result = await node.executor.execute(context)
        except Exception as exc:
            result = StepResult(
                status=StepStatus.FAILURE,
                summary=f"Executor raised {type(exc).__name__}: {exc}",
                diagnostics={
                    "exception_type": type(exc).__name__,
                    "exception_message": str(exc),
                    "raised": True,
                },
            )
        run_state = _record_result(run_state, active_node, attempt, result)
        run_state = _append_event(
            run_state,
            step_finished(active_node, attempt, result.status.value),
        )
        return {"run_state": _dump_run_state(run_state), "last_result": _dump_step_result(result)}

    async def _decide_next(self, state: _WorkflowState) -> dict[str, Any]:
        run_state = _load_run_state(state["run_state"])
        active_node = state["active_node"]
        node = self._workflow.nodes[active_node]
        result_data = state["last_result"]
        if result_data is None:
            raise WorkflowValidationError(
                f"Workflow {self._workflow.workflow_id!r} missing last_result before decision"
            )
        result = StepResult.model_validate(result_data)
        policy = node.policy
        if policy is None:
            raise WorkflowValidationError(f"Node {node.name!r} has no workflow policy")

        try:
            decision = await policy.decide(node, result, run_state)
            self._validate_decision(node, decision)
        except Exception as exc:
            decision = _policy_failure_decision(result, exc)

        run_state = _attach_decision(run_state, decision)
        run_state = _append_event(
            run_state,
            decision_made(active_node, decision.action.value, decision.next_node),
        )

        update: dict[str, Any] = {
            "run_state": _dump_run_state(run_state),
            "last_decision": _dump_workflow_decision(decision),
        }
        if decision.action == WorkflowAction.NEXT:
            update["active_node"] = decision.next_node
        elif decision.action == WorkflowAction.COMPLETE:
            final_output = (
                decision.final_output if decision.final_output is not None else result.output
            )
            run_state = run_state.model_copy(update={"final_output": final_output})
            run_state = _append_event(run_state, workflow_completed(final_output))
            update["run_state"] = _dump_run_state(run_state)
            update["terminal_status"] = WorkflowStatus.COMPLETED.value
        elif decision.action == WorkflowAction.FAIL:
            final_output = (
                decision.final_output if decision.final_output is not None else result.output
            )
            run_state = run_state.model_copy(update={"final_output": final_output})
            run_state = _append_event(run_state, workflow_failed(decision.reason))
            update["run_state"] = _dump_run_state(run_state)
            update["terminal_status"] = WorkflowStatus.FAILED.value
        elif decision.action == WorkflowAction.INTERRUPT:
            interrupt_value = decision.interrupt
            run_state = _append_event(
                run_state,
                interrupt_requested(active_node, interrupt_value),
            )
            update["run_state"] = _dump_run_state(run_state)
        return update

    async def _interrupt(self, state: _WorkflowState) -> dict[str, Any]:
        run_state = _load_run_state(state["run_state"])
        active_node = state["active_node"]
        decision_data = state["last_decision"]
        decision = (
            WorkflowDecision.model_validate(decision_data)
            if decision_data is not None
            else None
        )
        interrupt_value = decision.interrupt if decision is not None else None
        response = interrupt(interrupt_value)

        next_memory = dict(run_state.working_memory)
        interrupts = list(next_memory.get("interrupts", []))
        interrupts.append(
            {
                "node_name": active_node,
                "value": interrupt_value,
                "response": response,
            }
        )
        next_memory["interrupts"] = interrupts
        run_state = run_state.model_copy(update={"working_memory": next_memory})
        run_state = _append_event(
            run_state,
            interrupt_resumed(active_node, response),
        )
        return {"run_state": _dump_run_state(run_state), "last_decision": None}

    def _route_decision(self, state: _WorkflowState) -> str:
        decision_data = state.get("last_decision")
        if decision_data is None:
            raise WorkflowValidationError("Workflow state has no decision to route")
        decision = WorkflowDecision.model_validate(decision_data)
        if decision.action in {WorkflowAction.NEXT, WorkflowAction.RETRY}:
            return "execute"
        if decision.action == WorkflowAction.INTERRUPT:
            return "interrupt"
        return "end"

    def _build_graph(self) -> CompiledStateGraph:
        builder = StateGraph(_WorkflowState)
        builder.add_node("execute", self._execute_node)
        builder.add_node("decide", self._decide_next)
        builder.add_node("interrupt", self._interrupt)
        builder.add_edge(START, "execute")
        builder.add_edge("execute", "decide")
        builder.add_conditional_edges(
            "decide",
            self._route_decision,
            {
                "execute": "execute",
                "interrupt": "interrupt",
                "end": END,
            },
        )
        builder.add_edge("interrupt", "execute")
        return builder.compile(checkpointer=self._checkpointer)

    def _validate_decision(self, node: WorkflowNode, decision: WorkflowDecision) -> None:
        if decision.action not in node.allowed_actions:
            raise WorkflowValidationError(
                f"Node {node.name!r} policy returned disallowed action "
                f"{decision.action.value!r}"
            )
        if decision.action == WorkflowAction.NEXT and decision.next_node not in set(
            node.allowed_next_nodes
        ):
            raise WorkflowValidationError(
                f"Node {node.name!r} policy returned invalid next node "
                f"{decision.next_node!r}"
            )
        if decision.action == WorkflowAction.INTERRUPT and decision.interrupt is None:
            raise WorkflowValidationError(
                f"Node {node.name!r} policy returned interrupt action without an interrupt payload"
            )
    async def _result_from_checkpoint(
        self,
        checkpoint: WorkflowCheckpointHandle,
    ) -> WorkflowExecutionResult:
        snapshot = await self._compiled.aget_state(
            workflow_config(checkpoint, include_checkpoint_id=False)
        )
        values = snapshot.values
        if not isinstance(values, dict) or "run_state" not in values:
            raise WorkflowValidationError("Workflow snapshot missing run_state")
        run_state = values["run_state"]
        if not isinstance(run_state, RunState):
            run_state = RunState.model_validate(run_state)

        configurable = {}
        if snapshot.config is not None:
            configurable = dict(snapshot.config.get("configurable", {}))
        handle = WorkflowCheckpointHandle(
            thread_id=str(configurable.get("thread_id", checkpoint.thread_id)),
            checkpoint_id=(
                str(configurable["checkpoint_id"])
                if "checkpoint_id" in configurable
                else checkpoint.checkpoint_id
            ),
        )

        interrupts: tuple[Any, ...] = ()
        if values.get("terminal_status") == WorkflowStatus.FAILED.value:
            status = WorkflowStatus.FAILED
        elif values.get("terminal_status") == WorkflowStatus.COMPLETED.value or not snapshot.next:
            status = WorkflowStatus.COMPLETED
        elif snapshot.interrupts:
            interrupts = tuple(interrupt.value for interrupt in snapshot.interrupts)
            status = WorkflowStatus.PAUSED
        else:
            status = WorkflowStatus.RUNNING

        return WorkflowExecutionResult(
            status=status,
            checkpoint=handle,
            run_state=run_state,
            interrupts=interrupts,
        )


def _append_event(run_state: RunState, event: RuntimeEvent) -> RunState:
    return run_state.model_copy(update={"event_log": [*run_state.event_log, event]})


def _dump_run_state(run_state: RunState) -> dict[str, Any]:
    return run_state.model_dump(mode="json")


def _load_run_state(run_state: dict[str, Any] | RunState) -> RunState:
    if isinstance(run_state, RunState):
        return run_state
    return RunState.model_validate(run_state)


def _dump_step_result(result: StepResult) -> dict[str, Any]:
    return result.model_dump(mode="json")


def _dump_workflow_decision(decision: WorkflowDecision) -> dict[str, Any]:
    return decision.model_dump(mode="json")


def _record_result(
    run_state: RunState,
    node_name: str,
    attempt: int,
    result: StepResult,
) -> RunState:
    updated_attempts = dict(run_state.node_attempts)
    updated_attempts[node_name] = attempt
    updated_history = [
        *run_state.step_history,
        StepRecord(node_name=node_name, attempt=attempt, result=result),
    ]
    return run_state.model_copy(
        update={
            "node_attempts": updated_attempts,
            "step_history": updated_history,
            "artifacts": [*run_state.artifacts, *result.artifacts],
        }
    )


def _attach_decision(
    run_state: RunState,
    decision: WorkflowDecision,
) -> RunState:
    if not run_state.step_history:
        return run_state
    history = list(run_state.step_history)
    history[-1] = history[-1].model_copy(update={"decision": decision})
    return run_state.model_copy(update={"step_history": history})


def _policy_failure_decision(
    result: StepResult,
    exc: Exception,
) -> WorkflowDecision:
    return WorkflowDecision(
        action=WorkflowAction.FAIL,
        reason=f"Policy decision failed: {type(exc).__name__}: {exc}",
        final_output=result.output,
    )
