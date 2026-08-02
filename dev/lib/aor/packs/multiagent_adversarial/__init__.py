"""Adversarial multi-agent pack.

Generator produces an artifact; a verifier script evaluates it against a user-defined
quality gate. Loop retries up to max_retries times.

Each run is sandboxed under /tmp/aor_runs/aor_multiagent_adversarial_<N>_<timestamp>/.

Usage:
    from packs.multiagent_adversarial import create_pack
    from orchestrator.types import WorkflowRequest

    pack = create_pack()
    await pack.open()
    outcome = await pack.run_direct(WorkflowRequest(
        text="Find the best NASDAQ stock to buy",
        metadata={
            "verifier_script": "/tmp/aor_runs/.../verifier.py",
            "max_retries": 3,
            "model": "claude-sonnet-4-5-20250929",
            "api_key": "...",
        }
    ))
    print(outcome.result.output["artifact"])
    await pack.close()
"""

from __future__ import annotations

import datetime
import json
from pathlib import Path

from agent.packs.base import BoundDomainPack, ExecutionContext, PackDescriptor, PackResult
from agent.packs.orchestrator import PackWorkflowOrchestrator
from orchestrator.types import WorkflowRequest

from ._workflow import AdversarialWorkflowMixin

_RUNS_BASE = Path("/tmp/aor_runs")
_PACK_PREFIX = "aor_multiagent_adversarial"


def _next_run_dir() -> Path:
    """Create and return the next sequenced run directory."""
    _RUNS_BASE.mkdir(parents=True, exist_ok=True)
    existing = sorted(_RUNS_BASE.glob(f"{_PACK_PREFIX}_*"))
    run_number = len(existing) + 1
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    run_dir = _RUNS_BASE / f"{_PACK_PREFIX}_{run_number:03d}_{timestamp}"
    run_dir.mkdir(parents=True, exist_ok=True)
    return run_dir


class AdversarialPack(AdversarialWorkflowMixin, BoundDomainPack):
    """Generator/verifier loop pack with a user-supplied Python quality gate."""

    def __init__(self, run_dir: Path) -> None:
        super().__init__(workspace_dir=run_dir)
        self._run_dir = run_dir
        self._orchestrator: PackWorkflowOrchestrator | None = None

    @property
    def descriptor(self) -> PackDescriptor:
        return PackDescriptor(
            id="multiagent_adversarial",
            name="Multi-Agent Adversarial",
            version="0.2.0",
            description="Generator/verifier loop with a user-supplied Python quality gate.",
        )

    async def _open_impl(self) -> None:
        # Ensure config (and tracing) is initialized even if caller skips aor_config.load()
        from agent import config as aor_config
        if not aor_config._loaded:
            aor_config.load()

        workflow = self._build_adversarial_workflow()
        self._orchestrator = PackWorkflowOrchestrator(workflow)
        print(f"Run directory: {self._run_dir}", flush=True)

    async def _close_impl(self) -> None:
        self._orchestrator = None

    def get_workflow_wrapper(self) -> PackWorkflowOrchestrator:
        if self._orchestrator is None:
            raise RuntimeError("AdversarialPack not open — call open() first")
        return self._orchestrator

    def build_result(self, orchestrator_output: object, context: ExecutionContext) -> PackResult:
        output = orchestrator_output if isinstance(orchestrator_output, dict) else {}

        # Write final artifact and summary
        artifact = output.get("artifact", "")
        if artifact:
            (self._run_dir / "final_artifact.txt").write_text(artifact)

        summary = {
            "gate_passed": output.get("gate_passed", False),
            "verifier_reason": output.get("verifier_reason", ""),
            "attempts": output.get("attempts", 1),
            "run_dir": str(self._run_dir),
        }
        (self._run_dir / "run_summary.json").write_text(json.dumps(summary, indent=2))

        return PackResult(
            pack_id=self.descriptor.id,
            request_id=context.request_id,
            output={**output, "run_dir": str(self._run_dir)},
        )

    async def run_direct(self, request: "WorkflowRequest") -> object:  # type: ignore[override]
        """Inject run_dir into request metadata before delegating to orchestrator."""
        request.metadata.setdefault("_run_dir", str(self._run_dir))
        return await self.get_workflow_wrapper().run(request)


def create_pack(run_dir: Path | None = None) -> AdversarialPack:
    """Create an AdversarialPack with a sandboxed run directory.

    Args:
        run_dir: explicit run directory path. If None, auto-creates one under /tmp/aor_runs/.
    """
    if run_dir is None:
        run_dir = _next_run_dir()
    return AdversarialPack(run_dir=run_dir)
