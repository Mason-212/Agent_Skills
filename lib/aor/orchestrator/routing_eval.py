"""Routing evaluation helpers for demo workflows."""

from __future__ import annotations

import argparse
import asyncio
import json
from collections.abc import Sequence
from pathlib import Path

from pydantic import BaseModel, ConfigDict

from .config import load_orchestrator_config
from .examples import build_open_ended_router as build_analytics_router
from .node import RouterPolicy
from .policy import DSPyWorkflowRouter
from .types import RouteDestination, WorkflowRequest


class RoutingEvalCase(BaseModel):
    """One labeled routing example."""

    name: str
    request: WorkflowRequest
    expected_destination: RouteDestination
    expected_workflow_id: str | None = None

    model_config = ConfigDict(arbitrary_types_allowed=True)


class RoutingEvalResult(BaseModel):
    """Observed router output for one eval case."""

    name: str
    request_text: str
    expected_destination: RouteDestination
    actual_destination: RouteDestination
    expected_workflow_id: str | None = None
    actual_workflow_id: str | None = None
    passed: bool
    reason: str | None = None
    confidence: float | None = None


class RoutingEvalReport(BaseModel):
    """Aggregated routing evaluation report."""

    router_name: str
    known_workflow_ids: list[str]
    total_cases: int
    passed_cases: int
    accuracy: float
    results: list[RoutingEvalResult]


def build_demo_routing_eval_cases() -> list[RoutingEvalCase]:
    """Build labeled prompts for the demo workflow family."""

    return [
        RoutingEvalCase(
            name="forecast demand",
            request=WorkflowRequest(text="Forecast demand for next quarter by region."),
            expected_destination=RouteDestination.KNOWN_WORKFLOW,
            expected_workflow_id="forecast",
        ),
        RoutingEvalCase(
            name="forecast outlook",
            request=WorkflowRequest(text="Give me a sales outlook for the next six months."),
            expected_destination=RouteDestination.KNOWN_WORKFLOW,
            expected_workflow_id="forecast",
        ),
        RoutingEvalCase(
            name="causal impact",
            request=WorkflowRequest(text="Estimate the causal impact of the pricing change."),
            expected_destination=RouteDestination.KNOWN_WORKFLOW,
            expected_workflow_id="causal",
        ),
        RoutingEvalCase(
            name="causal driver",
            request=WorkflowRequest(text="What was the effect of the campaign on conversion?"),
            expected_destination=RouteDestination.KNOWN_WORKFLOW,
            expected_workflow_id="causal",
        ),
        RoutingEvalCase(
            name="classification score",
            request=WorkflowRequest(text="Build a classification score for churn risk."),
            expected_destination=RouteDestination.KNOWN_WORKFLOW,
            expected_workflow_id="regression_classification",
        ),
        RoutingEvalCase(
            name="regression fit",
            request=WorkflowRequest(text="Run a regression to predict renewal amount."),
            expected_destination=RouteDestination.KNOWN_WORKFLOW,
            expected_workflow_id="regression_classification",
        ),
        RoutingEvalCase(
            name="generic descriptive summary",
            request=WorkflowRequest(text="Summarize key insights from this dataset."),
            expected_destination=RouteDestination.INTERRUPT,
        ),
        RoutingEvalCase(
            name="generic dataset profile",
            request=WorkflowRequest(text="Profile the dataset and describe the main dimensions."),
            expected_destination=RouteDestination.INTERRUPT,
        ),
        RoutingEvalCase(
            name="nrr driver summary",
            request=WorkflowRequest(
                text="Our Q2 NRR dropped. Use Salesforce CRM data to explain the biggest drivers."
            ),
            expected_destination=RouteDestination.KNOWN_WORKFLOW,
            expected_workflow_id="nrr_deep_insight",
        ),
        RoutingEvalCase(
            name="ambiguous help",
            request=WorkflowRequest(text="Help me with this business problem."),
            expected_destination=RouteDestination.INTERRUPT,
        ),
        RoutingEvalCase(
            name="small talk",
            request=WorkflowRequest(text="Hi there, how are you today?"),
            expected_destination=RouteDestination.INTERRUPT,
        ),
    ]


async def evaluate_router(
    router_name: str,
    router: RouterPolicy,
    cases: Sequence[RoutingEvalCase],
    known_workflow_ids: Sequence[str],
) -> RoutingEvalReport:
    """Evaluate a router against labeled cases."""

    results: list[RoutingEvalResult] = []
    for case in cases:
        decision = await router.route(case.request, known_workflow_ids)
        passed = (
            decision.destination == case.expected_destination
            and decision.workflow_id == case.expected_workflow_id
        )
        results.append(
            RoutingEvalResult(
                name=case.name,
                request_text=case.request.text,
                expected_destination=case.expected_destination,
                actual_destination=decision.destination,
                expected_workflow_id=case.expected_workflow_id,
                actual_workflow_id=decision.workflow_id,
                passed=passed,
                reason=decision.reason,
                confidence=decision.confidence,
            )
        )

    passed_cases = sum(1 for result in results if result.passed)
    return RoutingEvalReport(
        router_name=router_name,
        known_workflow_ids=list(known_workflow_ids),
        total_cases=len(results),
        passed_cases=passed_cases,
        accuracy=(passed_cases / len(results)) if results else 0.0,
        results=results,
    )


def demo_workflow_ids() -> list[str]:
    """Return the known workflow ids used in the demo router eval."""

    return []


async def _run_cli() -> int:
    parser = argparse.ArgumentParser(description="Evaluate demo workflow routing.")
    parser.add_argument(
        "--router",
        choices=("deterministic", "dspy"),
        default="deterministic",
        help="Which router implementation to evaluate.",
    )
    parser.add_argument(
        "--config",
        default="config.local.json",
        help="Path to orchestrator config JSON for the DSPy router.",
    )
    parser.add_argument(
        "--chain-of-thought",
        action="store_true",
        help="Use DSPy ChainOfThought instead of Predict.",
    )
    args = parser.parse_args()

    known_workflow_ids = demo_workflow_ids()
    cases = build_demo_routing_eval_cases()

    if args.router == "deterministic":
        router = build_analytics_router()
    else:
        config = load_orchestrator_config(Path(args.config))
        router = DSPyWorkflowRouter(
            use_chain_of_thought=args.chain_of_thought,
            lm_config=config.dspy_lm,
        )

    report = await evaluate_router(args.router, router, cases, known_workflow_ids)
    print(json.dumps(report.model_dump(mode="json"), indent=2))
    return 0 if report.passed_cases == report.total_cases else 1


def main() -> int:
    return asyncio.run(_run_cli())


if __name__ == "__main__":
    raise SystemExit(main())
