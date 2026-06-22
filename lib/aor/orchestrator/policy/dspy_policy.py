"""DSPy-backed routing and workflow policies."""

from __future__ import annotations

import asyncio
import contextvars
import os
import re
import threading
from collections.abc import Sequence
from contextlib import nullcontext
from typing import Any, Literal

import dspy
from pydantic import BaseModel, ConfigDict, Field

from ..context import WorkflowNodeExecutionContext
from ..node import WorkflowNode, WorkflowPolicy
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

# Serialises the SSL_CERT_FILE env-mutation window across threads so that
# concurrent DSPy calls cannot observe a bare environment (see class docstring
# on DSPyWorkflowDecisionPolicy for full explanation of the workaround).
_ssl_cert_lock = threading.Lock()


class DSPyLMConfig(BaseModel):
    """Configuration for binding a concrete DSPy LM instance."""

    model: str
    api_key: str
    model_type: Literal["chat", "text", "responses"] = "chat"
    temperature: float | None = None
    max_tokens: int | None = None
    cache: bool = True
    kwargs: dict[str, Any] = Field(default_factory=dict)

    model_config = ConfigDict(arbitrary_types_allowed=True)


class _RouterSignature(dspy.Signature):
    request: str = dspy.InputField(desc="The user's raw workflow request.")
    known_workflows: str = dspy.InputField(
        desc="A newline-delimited list of valid workflow ids. Choose only from this list."
    )
    destination: str = dspy.OutputField(
        desc="Return exactly one of: known_workflow, interrupt."
    )
    workflow_id: str = dspy.OutputField(
        desc="If destination=known_workflow, return exactly one valid workflow id from known_workflows. Otherwise leave blank."
    )
    confidence: str = dspy.OutputField(
        desc="Confidence score between 0 and 1 as a decimal string when possible."
    )
    interrupt: str = dspy.OutputField(
        desc="If destination=interrupt, provide a short clarification question or reason. Otherwise leave blank."
    )
    reason: str = dspy.OutputField(
        desc="Brief explanation for why that route was selected."
    )


_ROUTER_SIGNATURE = _RouterSignature.with_instructions(
    "Route the request to exactly one known workflow or choose interrupt. "
    "Do not invent workflow ids. "
    "If a workflow is selected, destination must be 'known_workflow' and workflow_id must be copied exactly from the provided known_workflows list. "
    "If the request is ambiguous or no workflow fits, destination must be 'interrupt'."
)


class DSPyWorkflowRouter:
    """Fuzzy ingress router that selects a workflow or requests an interrupt."""

    def __init__(
        self,
        *,
        use_chain_of_thought: bool = True,
        lm_config: DSPyLMConfig | None = None,
    ) -> None:
        self._lm = _build_dspy_lm(lm_config)
        self._module = (
            dspy.ChainOfThought(_ROUTER_SIGNATURE)
            if use_chain_of_thought
            else dspy.Predict(_ROUTER_SIGNATURE)
        )

    async def route(
        self,
        request: WorkflowRequest,
        known_workflow_ids: Sequence[str],
    ) -> RouterDecision:
        prediction = await _acall_with_optional_lm(
            self._module,
            self._lm,
            request=request.text,
            known_workflows=_format_known_workflows(known_workflow_ids),
        )
        raw_destination = _clean_text(getattr(prediction, "destination", None))
        raw_workflow_id = _clean_text(getattr(prediction, "workflow_id", None))
        destination = _normalize_router_destination(
            destination=raw_destination,
            workflow_id=raw_workflow_id,
            known_workflow_ids=known_workflow_ids,
        )
        if destination == RouteDestination.INTERRUPT.value:
            return RouterDecision(
                destination=RouteDestination.INTERRUPT,
                confidence=_safe_float(getattr(prediction, "confidence", None)),
                interrupt=_router_interrupt_payload(
                    request=request.text,
                    known_workflow_ids=known_workflow_ids,
                    raw_interrupt=_clean_text(getattr(prediction, "interrupt", None)),
                ),
                reason=_clean_text(getattr(prediction, "reason", None)),
            )
        if destination == RouteDestination.KNOWN_WORKFLOW.value:
            workflow_id = _resolve_known_workflow_id(
                destination=raw_destination,
                workflow_id=raw_workflow_id,
                known_workflow_ids=known_workflow_ids,
            )
            if workflow_id is None:
                return RouterDecision(
                    destination=RouteDestination.INTERRUPT,
                    confidence=0.0,
                    interrupt={
                        "kind": "workflow_selection",
                        "request": request.text,
                        "available_workflows": list(known_workflow_ids),
                    },
                    reason=(
                        "DSPy selected an unknown or ambiguous workflow "
                        f"(destination={raw_destination!r}, workflow_id={raw_workflow_id!r}); "
                        "asking for an explicit workflow selection"
                    ),
                )
            return RouterDecision(
                destination=RouteDestination.KNOWN_WORKFLOW,
                workflow_id=workflow_id,
                confidence=_safe_float(getattr(prediction, "confidence", None)),
                reason=_clean_text(getattr(prediction, "reason", None)),
            )
        return RouterDecision(
            destination=RouteDestination.INTERRUPT,
            confidence=_safe_float(getattr(prediction, "confidence", None)),
            interrupt={
                "kind": "workflow_selection",
                "request": request.text,
                "available_workflows": list(known_workflow_ids),
            },
            reason=_clean_text(getattr(prediction, "reason", None)),
        )


class DSPyWorkflowDecisionPolicy(WorkflowPolicy):
    """Bounded workflow decision policy using DSPy.

    **DSPy/LiteLLM SSL Bug Workaround:**

    When SSL_CERT_FILE environment variable is set (e.g., for internal service auth),
    LiteLLM (DSPy's underlying HTTP client) inherits it globally and uses it for ALL
    requests, including public APIs like OpenAI. This causes SSL verification failures:

    - SSL_CERT_FILE=/path/to/internal_ca.pem (for internal services)
    - DSPy makes OpenAI API call
    - LiteLLM tries to verify OpenAI's cert against internal_ca.pem → FAIL

    **Why configuration doesn't work:**
    - LiteLLM reads SSL_CERT_FILE from environment BEFORE checking kwargs
    - Passing ssl_verify=True or ssl_verify=certifi.where() has no effect
    - No way to override per-client when SSL_CERT_FILE is set globally

    **Workaround:**
    This policy temporarily clears SSL_CERT_FILE during DSPy calls, then restores it.
    Ugly but necessary until LiteLLM fixes per-client SSL configuration.

    **When this workaround can be removed:**
    - When LiteLLM adds proper per-client SSL override (ssl_verify takes precedence)
    - When switching to a different DSPy HTTP backend that respects ssl_verify
    - When using a proxy/gateway that doesn't require custom SSL_CERT_FILE
    """

    def __init__(
        self,
        *,
        use_chain_of_thought: bool = True,
        lm_config: DSPyLMConfig | None = None,
    ) -> None:
        self._lm = _build_dspy_lm(lm_config)
        self._module = (
            dspy.ChainOfThought(
                "node_name, latest_output, latest_summary, allowed_actions, allowed_next_nodes, history_summary -> action, next_node, interrupt, reason"
            )
            if use_chain_of_thought
            else dspy.Predict(
                "node_name, latest_output, latest_summary, allowed_actions, allowed_next_nodes, history_summary -> action, next_node, interrupt, reason"
            )
        )

    async def decide(
        self,
        node: WorkflowNode,
        result: StepResult,
        run_state: RunState,
    ) -> WorkflowDecision:
        # WORKAROUND: LiteLLM reads SSL_CERT_FILE globally and applies it to all
        # requests, including public APIs, causing SSL failures when a corporate CA
        # is set.  We must temporarily clear it during the DSPy call.
        #
        # The call runs in run_in_executor so that _ssl_cert_lock is held for the
        # entire duration (including the HTTP round-trip), preventing any concurrent
        # coroutine from observing a bare environment.  See class docstring for full
        # context and removal conditions.
        kwargs = {
            "node_name": node.name,
            "latest_output": str(result.output),
            "latest_summary": result.summary or "",
            "allowed_actions": ", ".join(sorted(action.value for action in node.allowed_actions)),
            "allowed_next_nodes": ", ".join(node.allowed_next_nodes),
            "history_summary": _history_summary(run_state),
        }
        lm = self._lm
        module = self._module
        ctx = contextvars.copy_context()

        def _call_in_ctx() -> Any:
            # dspy.context sets a contextvar; call module directly here so the
            # contextvar binding is visible to module — ctx.run() would restore
            # the copied context (without the LM) and override dspy.context's
            # binding, causing "No LM is loaded".
            with (dspy.context(lm=lm) if lm is not None else nullcontext()):
                return module(**kwargs)

        def _call_sync() -> Any:
            with _ssl_cert_lock:
                saved = os.environ.pop("SSL_CERT_FILE", None)
                try:
                    # ctx.run propagates the async caller's contextvars (e.g. trace
                    # IDs) into this executor thread.  The inner _call_in_ctx then
                    # applies the DSPy LM contextvar on top of that copy.
                    return ctx.run(_call_in_ctx)
                finally:
                    if saved is not None:
                        os.environ["SSL_CERT_FILE"] = saved

        prediction = await asyncio.get_event_loop().run_in_executor(None, _call_sync)

        action_name = str(getattr(prediction, "action", "")).strip().lower()
        try:
            action = WorkflowAction(action_name)
        except ValueError as exc:
            raise ValueError(
                f"DSPy policy returned unknown workflow action {action_name!r}"
            ) from exc
        return WorkflowDecision(
            action=action,
            next_node=_clean_text(getattr(prediction, "next_node", None)),
            reason=_clean_text(getattr(prediction, "reason", None)),
            interrupt=getattr(prediction, "interrupt", None),
        )


class DSPyOpenEndedRLMExecutor:
    """Executor for workflow nodes that delegate open-ended reasoning to DSPy's RLM."""

    def __init__(
        self,
        *,
        max_iterations: int = 8,
        lm_config: DSPyLMConfig | None = None,
    ) -> None:
        self._lm = _build_dspy_lm(lm_config)
        self._module = dspy.RLM(
            "request, history_summary -> answer",
            max_iterations=max_iterations,
        )

    async def execute(self, context: WorkflowNodeExecutionContext) -> StepResult:
        prediction = await _acall_with_optional_lm(
            self._module,
            self._lm,
            request=context.request.text,
            history_summary=_history_summary(context.run_state),
        )
        answer = getattr(prediction, "answer", None)
        return StepResult(
            status=StepStatus.SUCCESS,
            summary=str(answer) if answer is not None else None,
            output={
                "answer": answer,
                "trajectory": getattr(prediction, "trajectory", []),
                "final_reasoning": getattr(prediction, "final_reasoning", None),
            },
            diagnostics={"executor": "dspy_rlm"},
        )

def _history_summary(run_state: RunState) -> str:
    lines = [
        f"{record.node_name} attempt={record.attempt} status={record.result.status.value}"
        for record in run_state.step_history[-10:]
    ]
    return "\n".join(lines)


def _clean_text(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _safe_float(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _format_known_workflows(known_workflow_ids: Sequence[str]) -> str:
    return "\n".join(f"- {workflow_id}" for workflow_id in known_workflow_ids)


def _normalize_router_destination(
    *,
    destination: str | None,
    workflow_id: str | None,
    known_workflow_ids: Sequence[str],
) -> str:
    normalized_destination = _canonicalize_identifier(destination)
    if normalized_destination == _canonicalize_identifier(RouteDestination.INTERRUPT.value):
        return RouteDestination.INTERRUPT.value
    if normalized_destination == _canonicalize_identifier(RouteDestination.KNOWN_WORKFLOW.value):
        return RouteDestination.KNOWN_WORKFLOW.value
    if _resolve_known_workflow_id(
        destination=destination,
        workflow_id=workflow_id,
        known_workflow_ids=known_workflow_ids,
    ) is not None:
        return RouteDestination.KNOWN_WORKFLOW.value
    return RouteDestination.INTERRUPT.value


def _resolve_known_workflow_id(
    *,
    destination: str | None,
    workflow_id: str | None,
    known_workflow_ids: Sequence[str],
) -> str | None:
    normalized_known = {
        _canonicalize_identifier(known_workflow_id): known_workflow_id
        for known_workflow_id in known_workflow_ids
    }
    exact_matches = [
        normalized_known[_canonicalize_identifier(candidate)]
        for candidate in (workflow_id, destination)
        if candidate is not None and _canonicalize_identifier(candidate) in normalized_known
    ]
    if exact_matches:
        return exact_matches[0]
    return None


def _canonicalize_identifier(value: str | None) -> str:
    if value is None:
        return ""
    return re.sub(r"[^a-z0-9]+", "", value.strip().lower())


def _router_interrupt_payload(
    *,
    request: str,
    known_workflow_ids: Sequence[str],
    raw_interrupt: str | None,
) -> Any:
    if raw_interrupt and raw_interrupt.lower() not in {"no", "none", "n/a", "null"}:
        return raw_interrupt
    return {
        "kind": "workflow_selection",
        "request": request,
        "available_workflows": list(known_workflow_ids),
    }


def _build_dspy_lm(lm_config: DSPyLMConfig | None) -> Any | None:
    if lm_config is None:
        return None
    return dspy.LM(
        model=lm_config.model,
        model_type=lm_config.model_type,
        temperature=lm_config.temperature,
        max_tokens=lm_config.max_tokens,
        cache=lm_config.cache,
        api_key=lm_config.api_key,
        **lm_config.kwargs,
    )


async def _acall_with_optional_lm(module: Any, lm: Any | None, **kwargs: Any) -> Any:
    with (dspy.context(lm=lm) if lm is not None else nullcontext()):
        return await module.acall(**kwargs)
