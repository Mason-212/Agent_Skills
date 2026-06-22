"""Role-based multi-agent pack.

N agents with defined roles collaborate in a fixed sequence. Each agent reads the
full conversation thread and appends its response. Role sequence and role definitions are
configurable at create_pack() time.

Usage:
    from pathlib import Path
    from lib.aor.packs.multiagent_roles import create_pack
    from orchestrator.types import WorkflowRequest

    pack = create_pack(workspace_dir=Path("/tmp/aor_roles"))
    await pack.open()
    outcome = await pack.run_direct(WorkflowRequest(
        text="Build a CLI tool that formats JSON files in place",
        metadata={
            "model": "claude-sonnet-4-5-20250929",
            "api_key": "...",
        }
    ))
    for entry in outcome.result.output["thread"]:
        print(f"## {entry['role']}")
        print(entry["content"])
    await pack.close()
"""

from __future__ import annotations

from pathlib import Path

from agent.packs.base import BoundDomainPack, ExecutionContext, PackDescriptor, PackResult
from agent.packs.orchestrator import PackWorkflowOrchestrator

from ._workflow import DEFAULT_ROLES, RolesWorkflowMixin


class RolesPack(RolesWorkflowMixin, BoundDomainPack):
    """Role-based multi-agent collaboration pack."""

    def __init__(self, workspace_dir: Path, *, role_sequence: list[str] | None = None) -> None:
        super().__init__(workspace_dir=workspace_dir)
        self._role_sequence = role_sequence or DEFAULT_ROLES
        self._orchestrator: PackWorkflowOrchestrator | None = None

    @property
    def descriptor(self) -> PackDescriptor:
        return PackDescriptor(
            id="multiagent_roles",
            name="Multi-Agent Roles",
            version="0.1.0",
            description="Role-based collaboration: each agent plays a role in a fixed sequence.",
        )

    async def _open_impl(self) -> None:
        from agent import config as aor_config
        if not aor_config._loaded:
            aor_config.load()

        workflow = self._build_roles_workflow(self._role_sequence)
        self._orchestrator = PackWorkflowOrchestrator(workflow)

    async def _close_impl(self) -> None:
        self._orchestrator = None

    def get_workflow_wrapper(self) -> PackWorkflowOrchestrator:
        if self._orchestrator is None:
            raise RuntimeError("RolesPack not open — call open() first")
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
    role_sequence: list[str] | None = None,
) -> RolesPack:
    return RolesPack(workspace_dir=workspace_dir, role_sequence=role_sequence)
