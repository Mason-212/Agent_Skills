"""Unit tests for multiagent_solution_space pack."""

import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from orchestrator.types import StepStatus
from packs.multiagent_solution_space import create_pack


def test_create_pack(tmp_path: Path) -> None:
    pack = create_pack(workspace_dir=tmp_path, domains=["fintech", "healthcare"])
    assert pack.descriptor.id == "multiagent_solution_space"
    assert pack._domains == ["fintech", "healthcare"]


def test_workflow_topology(tmp_path: Path) -> None:
    domains = ["fintech", "healthcare", "energy"]
    pack = create_pack(workspace_dir=tmp_path, domains=domains)
    spec = pack._build_solution_space_workflow(domains)

    assert spec.start_node == "spawn"
    for domain in domains:
        node_name = f"explore_{domain}"
        assert node_name in spec.nodes
        assert "synthesize" in spec.nodes[node_name].allowed_next_nodes
    assert "synthesize" in spec.nodes
    assert spec.nodes["synthesize"].allowed_next_nodes == ()


def test_spawn_node_rejects_empty_domains(tmp_path: Path) -> None:
    pack = create_pack(workspace_dir=tmp_path, domains=[])

    ctx = MagicMock()
    ctx.request.metadata = {"domains": []}
    ctx.run_state.working_memory = {}

    result = pack._node_spawn(ctx)
    assert result.status == StepStatus.FAILURE


def test_spawn_node_initializes_findings(tmp_path: Path) -> None:
    pack = create_pack(workspace_dir=tmp_path, domains=["a", "b"])

    ctx = MagicMock()
    ctx.request.metadata = {"domains": ["a", "b"]}
    ctx.run_state.working_memory = {}

    result = pack._node_spawn(ctx)
    assert result.status == StepStatus.SUCCESS
    assert ctx.run_state.working_memory["findings"] == {}
    assert ctx.run_state.working_memory["domains"] == ["a", "b"]


@pytest.mark.asyncio
async def test_explorer_node_stores_finding(tmp_path: Path) -> None:
    pack = create_pack(workspace_dir=tmp_path, domains=["fintech"])
    node_fn = pack._make_explorer_node("fintech")

    ctx = MagicMock()
    ctx.request.text = "Best investment?"
    ctx.request.metadata = {"provider": "x", "model": "x", "api_key": "x"}
    ctx.run_state.working_memory = {"findings": {}}

    with patch.object(pack, "_call_llm", new=AsyncMock(return_value="Fintech is booming.")):
        result = await node_fn(ctx)

    assert result.status == StepStatus.SUCCESS
    assert ctx.run_state.working_memory["findings"]["fintech"] == "Fintech is booming."


@pytest.mark.asyncio
async def test_synthesize_node_fails_with_no_findings(tmp_path: Path) -> None:
    pack = create_pack(workspace_dir=tmp_path, domains=["a"])

    ctx = MagicMock()
    ctx.request.text = "Best?"
    ctx.request.metadata = {"provider": "x", "model": "x", "api_key": "x"}
    ctx.run_state.working_memory = {"findings": {}}

    result = await pack._node_synthesize(ctx)
    assert result.status == StepStatus.FAILURE


@pytest.mark.asyncio
async def test_synthesize_node_returns_synthesis(tmp_path: Path) -> None:
    pack = create_pack(workspace_dir=tmp_path, domains=["fintech", "healthcare"])

    ctx = MagicMock()
    ctx.request.text = "Best opportunities?"
    ctx.request.metadata = {"provider": "x", "model": "x", "api_key": "x"}
    ctx.run_state.working_memory = {
        "findings": {
            "fintech": "Strong growth in payments.",
            "healthcare": "AI diagnostics are promising.",
        }
    }

    with patch.object(pack, "_call_llm", new=AsyncMock(return_value="Fintech ranks #1.")):
        result = await pack._node_synthesize(ctx)

    assert result.status == StepStatus.SUCCESS
    assert result.output["synthesis"] == "Fintech ranks #1."
    assert "fintech" in result.output["findings"]
    assert "healthcare" in result.output["findings"]
