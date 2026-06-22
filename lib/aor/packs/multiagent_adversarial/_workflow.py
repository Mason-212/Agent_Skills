"""Adversarial multi-agent workflow.

DAG shape:
    generate → verify → [COMPLETE | RETRY generate | FAIL if max_retries]

The generator produces an artifact from the user prompt. The verifier runs
a user-supplied Python script (verifier.py) that returns {"gate_passed": bool, "reason": str}.
AdversarialPolicy reads gate_passed and routes COMPLETE, RETRY, or FAIL.

If no verifier_script is provided, falls back to LLM-as-critic with an explicit warning.

WorkflowRequest.metadata fields:
    verifier_script (str): absolute path to verifier.py
    max_retries (int): maximum generator retries before FAIL (default 3)
    num_results (int): optional minimum number of results required in artifact
    max_cost_usd (float): optional cost budget in USD
    model (str): LLM model identifier (default "claude-sonnet-4-5-20250929")
    api_key (str): LLM API key (falls back to AOR_API_KEY env var)
"""

from __future__ import annotations

import json
import logging
import subprocess
import sys
import warnings
from pathlib import Path
from typing import Any

_log = logging.getLogger(__name__)

_GENERATOR_ROLE_PATH = Path(__file__).parent / "agents" / "generator" / "ROLE.md"
_CRITIC_ROLE_PATH = Path(__file__).parent / "agents" / "critic" / "ROLE.md"

_MEM_ARTIFACT = "artifact"
_MEM_CRITIQUE = "critique"
_MEM_ATTEMPT = "attempt"
_MEM_RUN_DIR = "run_dir"


class AdversarialWorkflowMixin:
    """Workflow nodes and WorkflowSpec wiring for AdversarialPack."""

    def _build_adversarial_workflow(self) -> Any:
        from orchestrator import WorkflowBuilder
        from orchestrator.executors import CallableExecutor
        from orchestrator.node import WorkflowNode

        return (
            WorkflowBuilder("adversarial")
            .add_node(WorkflowNode(
                name="generate",
                executor=CallableExecutor(self._node_generate),
                allowed_next_nodes=("verify",),
            ))
            .add_node(WorkflowNode(
                name="verify",
                executor=CallableExecutor(self._node_verify),
                allowed_next_nodes=("generate",),
                policy=AdversarialPolicy(),
            ))
            .set_start("generate")
            .build()
        )

    async def _node_generate(self, ctx: Any) -> Any:
        from agent.tracing import node_span
        from orchestrator.types import StepResult, StepStatus

        metadata = ctx.request.metadata
        prompt = metadata.get("prompt", ctx.request.text)
        prior_critique = ctx.run_state.working_memory.get(_MEM_CRITIQUE, "")
        attempt = ctx.run_state.working_memory.get(_MEM_ATTEMPT, 1)
        num_results = metadata.get("num_results")

        # Seed run_dir and termination params into working memory on first call
        if _MEM_RUN_DIR not in ctx.run_state.working_memory and metadata.get("_run_dir"):
            ctx.run_state.working_memory[_MEM_RUN_DIR] = metadata["_run_dir"]

        if attempt == 1:
            if "max_retries" not in ctx.run_state.working_memory:
                max_retries = metadata.get("max_retries")
                if max_retries is None:
                    raise ValueError(
                        "max_retries not provided in metadata. "
                        "The skill must ask the user for termination conditions before running."
                    )
                ctx.run_state.working_memory["max_retries"] = int(max_retries)
            if "max_cost_usd" not in ctx.run_state.working_memory and metadata.get("max_cost_usd") is not None:
                ctx.run_state.working_memory["max_cost_usd"] = float(metadata["max_cost_usd"])

        generator_system = _GENERATOR_ROLE_PATH.read_text()
        if num_results:
            generator_system += f"\n\nReturn exactly {num_results} results."

        user_prompt = prompt
        if prior_critique:
            user_prompt = (
                f"Original task:\n{prompt}\n\n"
                f"Prior feedback (attempt {attempt - 1}):\n{prior_critique}\n\n"
                "Revise your output addressing all points above."
            )

        with node_span("generate", attempt=attempt, prompt_length=len(user_prompt)) as span:
            artifact = await self._call_llm(
                system_prompt=generator_system,
                user_prompt=user_prompt,
                metadata=metadata,
            )
            span.set_attribute("aor.artifact_length", len(artifact))

        ctx.run_state.working_memory[_MEM_ARTIFACT] = artifact
        ctx.run_state.working_memory[_MEM_ATTEMPT] = attempt

        # Persist artifact to run dir
        run_dir = ctx.run_state.working_memory.get(_MEM_RUN_DIR)
        if run_dir:
            attempts_dir = Path(run_dir) / "attempts"
            attempts_dir.mkdir(parents=True, exist_ok=True)
            (attempts_dir / f"{attempt:03d}_artifact.txt").write_text(artifact)

        return StepResult(
            status=StepStatus.SUCCESS,
            summary=f"Attempt {attempt}: generated artifact ({len(artifact)} chars)",
            output={"artifact": artifact, "attempt": attempt},
        )

    async def _node_verify(self, ctx: Any) -> Any:
        from agent.tracing import node_span
        from orchestrator.types import StepResult, StepStatus

        metadata = ctx.request.metadata
        artifact = ctx.run_state.working_memory.get(_MEM_ARTIFACT, "")
        attempt = ctx.run_state.working_memory.get(_MEM_ATTEMPT, 1)
        verifier_script = metadata.get("verifier_script")
        run_dir = ctx.run_state.working_memory.get(_MEM_RUN_DIR)

        with node_span("verify", attempt=attempt, verifier_script=verifier_script or "llm_fallback") as span:
            if verifier_script and Path(verifier_script).exists():
                gate_passed, reason = self._run_verifier_script(verifier_script, artifact)
            else:
                if verifier_script:
                    warnings.warn(
                        f"verifier_script not found: {verifier_script}. "
                        "Falling back to LLM-as-critic. Results will be less reliable.",
                        stacklevel=2,
                    )
                else:
                    warnings.warn(
                        "No verifier_script provided. "
                        "Falling back to LLM-as-critic. Results will be less reliable.",
                        stacklevel=2,
                    )
                gate_passed, reason = await self._llm_critic_fallback(artifact, metadata)

            span.set_attribute("aor.gate_passed", gate_passed)
            span.set_attribute("aor.verifier_reason", reason[:500])

        ctx.run_state.working_memory[_MEM_CRITIQUE] = reason
        ctx.run_state.working_memory[_MEM_ATTEMPT] = attempt + 1

        # Persist verifier output to run dir
        if run_dir:
            attempts_dir = Path(run_dir) / "attempts"
            attempts_dir.mkdir(parents=True, exist_ok=True)
            verifier_out = {"gate_passed": gate_passed, "reason": reason, "attempt": attempt}
            (attempts_dir / f"{attempt:03d}_verifier_output.json").write_text(
                json.dumps(verifier_out, indent=2)
            )

        return StepResult(
            status=StepStatus.SUCCESS,
            summary=f"Gate {'PASSED' if gate_passed else 'FAILED'}: {reason[:120]}",
            output={
                "gate_passed": gate_passed,
                "verifier_reason": reason,
                "artifact": artifact,
            },
        )

    def _run_verifier_script(self, script_path: str, artifact: str) -> tuple[bool, str]:
        """Run verifier.py in a subprocess, passing artifact via stdin."""
        try:
            result = subprocess.run(
                [sys.executable, script_path],
                input=artifact,
                capture_output=True,
                text=True,
                timeout=30,
            )
            if result.returncode != 0:
                return False, f"Verifier exited {result.returncode}: {result.stderr[:300]}"
            parsed = json.loads(result.stdout.strip())
            return bool(parsed.get("gate_passed", False)), parsed.get("reason", result.stdout)
        except subprocess.TimeoutExpired:
            return False, "Verifier script timed out after 30s"
        except (json.JSONDecodeError, Exception) as exc:
            return False, f"Verifier script error: {exc}"

    async def _llm_critic_fallback(self, artifact: str, metadata: dict) -> tuple[bool, str]:
        """LLM-as-critic fallback. Only used when no verifier script is available."""
        critic_system = _CRITIC_ROLE_PATH.read_text()
        verification_criteria = metadata.get(
            "verification_criteria",
            "The artifact must be correct, complete, and well-structured.",
        )
        user_prompt = (
            f"Artifact to evaluate:\n{artifact}\n\n"
            f"Verification criteria:\n{verification_criteria}"
        )
        raw = await self._call_llm(
            system_prompt=critic_system,
            user_prompt=user_prompt,
            metadata=metadata,
        )
        try:
            cleaned = raw.strip()
            if cleaned.startswith("```"):
                cleaned = "\n".join(cleaned.split("\n")[1:])
                cleaned = cleaned.rsplit("```", 1)[0].strip()
            result = json.loads(cleaned)
            return bool(result.get("gate_passed", False)), result.get("critique", raw)
        except (json.JSONDecodeError, AttributeError):
            return False, raw

    async def _call_llm(self, *, system_prompt: str, user_prompt: str, metadata: dict) -> str:
        """Call the LLM via agent.pi.ai and return the text response.

        Provider/model/api_key are resolved from lib/aor/.env via agent.config.
        Values in metadata act as per-call overrides (used in tests).
        """
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


class AdversarialPolicy:
    """Route verify output: COMPLETE on gate_passed, RETRY generate, or FAIL after max_retries."""

    async def decide(self, node: Any, result: Any, run_state: Any) -> Any:
        from agent.tracing import policy_span
        from orchestrator.types import WorkflowAction, WorkflowDecision

        output = result.output or {}
        gate_passed = output.get("gate_passed", False)
        attempt = run_state.working_memory.get(_MEM_ATTEMPT, 1)

        max_retries = run_state.working_memory.get("max_retries")
        if max_retries is None:
            raise ValueError(
                "max_retries not set in working_memory. "
                "The skill must collect this from the user before running."
            )

        if gate_passed:
            decision = WorkflowDecision(action=WorkflowAction.COMPLETE)
        elif attempt - 1 >= max_retries:
            decision = WorkflowDecision(
                action=WorkflowAction.FAIL,
                reason=f"Gate failed after {max_retries} attempts. Last reason: {output.get('verifier_reason', '')[:200]}",
            )
        else:
            decision = WorkflowDecision(action=WorkflowAction.NEXT, next_node="generate")

        with policy_span(
            "adversarial",
            attempt=attempt,
            max_retries=max_retries,
            gate_passed=gate_passed,
        ) as span:
            span.set_attribute("aor.action", decision.action.value)
            if decision.next_node:
                span.set_attribute("aor.next_node", decision.next_node)
            if decision.reason:
                span.set_attribute("aor.reason", decision.reason[:500])

        return decision
