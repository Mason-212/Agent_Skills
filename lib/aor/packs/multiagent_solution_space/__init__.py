"""Solution-space exploration multi-agent pack.

Fans out N domain-specific explorer agents in sequence, then synthesizes
the best answer. Domains are specified at runtime via WorkflowRequest.metadata.

Usage:
    from pathlib import Path
    from lib.aor.packs.multiagent_solution_space import create_pack
    from orchestrator.types import WorkflowRequest

    pack = create_pack(
        workspace_dir=Path("/tmp/aor_solution_space"),
        domains=["fintech", "healthcare", "energy"],
    )
    await pack.open()
    outcome = await pack.run_direct(WorkflowRequest(
        text="What are the best investment opportunities right now?",
        metadata={
            "domains": ["fintech", "healthcare", "energy"],
            "model": "claude-sonnet-4-5-20250929",
            "api_key": "...",
        }
    ))
    print(outcome.result.output["synthesis"])
    await pack.close()
"""

from __future__ import annotations

from pathlib import Path

from agent.packs.base import BoundDomainPack, ExecutionContext, PackDescriptor, PackResult
from agent.packs.orchestrator import PackWorkflowOrchestrator

from ._workflow import SolutionSpaceWorkflowMixin


class SolutionSpacePack(SolutionSpaceWorkflowMixin, BoundDomainPack):
    """Fan-out N domain explorers then synthesize findings."""

    def __init__(self, workspace_dir: Path, *, domains: list[str]) -> None:
        super().__init__(workspace_dir=workspace_dir)
        self._domains = domains
        self._orchestrator: PackWorkflowOrchestrator | None = None

    @property
    def descriptor(self) -> PackDescriptor:
        return PackDescriptor(
            id="multiagent_solution_space",
            name="Multi-Agent Solution Space",
            version="0.1.0",
            description="Fan-out N domain explorers, synthesize the best answer.",
        )

    async def _open_impl(self) -> None:
        from agent import config as aor_config
        if not aor_config._loaded:
            aor_config.load()

        workflow = self._build_solution_space_workflow(self._domains)
        self._orchestrator = PackWorkflowOrchestrator(workflow)

    async def _close_impl(self) -> None:
        self._orchestrator = None

    def get_workflow_wrapper(self) -> PackWorkflowOrchestrator:
        if self._orchestrator is None:
            raise RuntimeError("SolutionSpacePack not open — call open() first")
        return self._orchestrator

    def build_result(self, orchestrator_output: object, context: ExecutionContext) -> PackResult:
        return PackResult(
            pack_id=self.descriptor.id,
            request_id=context.request_id,
            output=orchestrator_output,
        )


def create_pack(
    workspace_dir: Path,
    *,
    domains: list[str],
) -> SolutionSpacePack:
    return SolutionSpacePack(workspace_dir=workspace_dir, domains=domains)
