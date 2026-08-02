"""Solution-space exploration multi-agent workflow.

DAG shape:
    spawn → [explore_<domain_0>, explore_<domain_1>, ..., explore_<domain_N-1>] → synthesize

spawn fans out to one explore node per domain using LangGraph Send.
Each explore node runs a fresh AgentSession scoped to its domain.
synthesize reads all findings from working_memory and produces a ranked recommendation.

WorkflowRequest fields:
    text (str): the question each explorer answers
    metadata.domains (list[str]): domain names to explore (e.g. ["fintech", "healthcare"])
    metadata.prompt (str): optional alternative prompt (defaults to request.text)
    metadata.model (str): LLM model ID
    metadata.provider (str): LLM provider
    metadata.api_key (str): API key (falls back to AOR_API_KEY env var)
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

_log = logging.getLogger(__name__)

_EXPLORER_ROLE_PATH = Path(__file__).parent / "agents" / "explorer" / "ROLE.md"
_SYNTHESIZER_ROLE_PATH = Path(__file__).parent / "agents" / "synthesizer" / "ROLE.md"
_MEM_FINDINGS = "findings"


class SolutionSpaceWorkflowMixin:
    """Workflow nodes and WorkflowSpec wiring for SolutionSpacePack."""

    def _build_solution_space_workflow(self, domains: list[str]) -> Any:
        from orchestrator import WorkflowBuilder
        from orchestrator.executors import CallableExecutor
        from orchestrator.node import WorkflowNode

        builder = WorkflowBuilder("solution_space")

        # spawn node fans out to all explore nodes
        explore_node_names = tuple(f"explore_{d}" for d in domains)
        builder.add_node(WorkflowNode(
            name="spawn",
            executor=CallableExecutor(self._node_spawn),
            allowed_next_nodes=explore_node_names,
        ))

        for domain in domains:
            builder.add_node(WorkflowNode(
                name=f"explore_{domain}",
                executor=CallableExecutor(self._make_explorer_node(domain)),
                allowed_next_nodes=("synthesize",),
            ))

        builder.add_node(WorkflowNode(
            name="synthesize",
            executor=CallableExecutor(self._node_synthesize),
            allowed_next_nodes=(),
        ))

        builder.set_start("spawn")
        return builder.build()

    def _node_spawn(self, ctx: Any) -> Any:
        from orchestrator.types import StepResult, StepStatus

        metadata = ctx.request.metadata
        domains = metadata.get("domains", [])
        if not domains:
            return StepResult(
                status=StepStatus.FAILURE,
                output={"error": "metadata.domains must be a non-empty list"},
            )
        ctx.run_state.working_memory[_MEM_FINDINGS] = {}
        ctx.run_state.working_memory["domains"] = domains
        return StepResult(
            status=StepStatus.SUCCESS,
            summary=f"Spawning {len(domains)} explorer(s): {', '.join(domains)}",
            output={"domains": domains},
        )

    def _make_explorer_node(self, domain: str):
        async def _node(ctx: Any) -> Any:
            from orchestrator.types import StepResult, StepStatus

            metadata = ctx.request.metadata
            question = metadata.get("prompt", ctx.request.text)
            explorer_system = _EXPLORER_ROLE_PATH.read_text()

            user_prompt = f"Domain: {domain}\n\nQuestion: {question}"
            from agent.tracing import node_span
            with node_span(f"explore_{domain}", domain=domain, prompt_length=len(user_prompt)) as span:
                finding = await self._call_llm(
                    system_prompt=explorer_system,
                    user_prompt=user_prompt,
                    metadata=metadata,
                )
                span.set_attribute("aor.finding_length", len(finding))

            findings: dict = dict(ctx.run_state.working_memory.get(_MEM_FINDINGS, {}))
            findings[domain] = finding
            ctx.run_state.working_memory[_MEM_FINDINGS] = findings

            return StepResult(
                status=StepStatus.SUCCESS,
                summary=f"{domain}: {finding[:120]}",
                output={"domain": domain, "finding": finding},
            )
        _node.__name__ = f"_node_explore_{domain}"
        return _node

    async def _node_synthesize(self, ctx: Any) -> Any:
        from orchestrator.types import StepResult, StepStatus

        metadata = ctx.request.metadata
        findings: dict = ctx.run_state.working_memory.get(_MEM_FINDINGS, {})
        question = metadata.get("prompt", ctx.request.text)

        if not findings:
            return StepResult(
                status=StepStatus.FAILURE,
                output={"error": "No findings to synthesize"},
            )

        findings_text = "\n\n".join(
            f"## {domain}\n{finding}" for domain, finding in findings.items()
        )
        user_prompt = (
            f"Original question: {question}\n\n"
            f"Domain findings:\n\n{findings_text}\n\n"
            "Rank these findings and produce a final recommendation."
        )

        synthesizer_system = _SYNTHESIZER_ROLE_PATH.read_text()
        from agent.tracing import node_span
        with node_span("synthesize", domain_count=len(findings), prompt_length=len(user_prompt)) as span:
            synthesis = await self._call_llm(
                system_prompt=synthesizer_system,
                user_prompt=user_prompt,
                metadata=metadata,
            )
            span.set_attribute("aor.synthesis_length", len(synthesis))

        return StepResult(
            status=StepStatus.SUCCESS,
            summary=synthesis[:200],
            output={
                "synthesis": synthesis,
                "findings": findings,
                "domains": list(findings.keys()),
            },
        )

    async def _call_llm(self, *, system_prompt: str, user_prompt: str, metadata: dict) -> str:
        from agent import config as aor_config
        from agent.pi.ai import Context, UserMessage, complete_simple
        from agent.pi.ai.models_catalog.catalog import get_model
        from agent.pi.ai.types import SimpleStreamOptions, TextContent
        from agent.tracing import llm_span

        if not aor_config._loaded:
            aor_config.load()

        provider = metadata.get("provider", aor_config.PROVIDER)
        model_id = metadata.get("model", aor_config.MODEL)
        api_key = metadata.get("api_key", aor_config.API_KEY)

        model = get_model(provider, model_id)
        if model is None:
            raise ValueError(f"Model {provider}/{model_id} not found in catalog")

        context = Context(
            system_prompt=system_prompt,
            messages=[UserMessage(content=user_prompt, timestamp=0)],
        )
        options = SimpleStreamOptions(api_key=api_key) if api_key else None

        with llm_span(provider=provider, model=model_id, prompt_length=len(user_prompt)) as span:
            response = await complete_simple(model, context, options)
            text = " ".join(
                block.text for block in getattr(response, "content", [])
                if isinstance(block, TextContent)
            ).strip()
            span.set_attribute("aor.response_length", len(text))

        return text
