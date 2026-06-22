"""Unit tests for multiagent_roles pack."""

import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from orchestrator.types import StepStatus
from packs.multiagent_roles import create_pack
from packs.multiagent_roles._workflow import DEFAULT_ROLES


def test_create_pack_default_roles(tmp_path: Path) -> None:
    pack = create_pack(workspace_dir=tmp_path)
    assert pack.descriptor.id == "multiagent_roles"
    assert pack._role_sequence == DEFAULT_ROLES


def test_create_pack_custom_roles(tmp_path: Path) -> None:
    pack = create_pack(workspace_dir=tmp_path, role_sequence=["architect", "dev"])
    assert pack._role_sequence == ["architect", "dev"]


def test_workflow_topology_default(tmp_path: Path) -> None:
    pack = create_pack(workspace_dir=tmp_path)
    spec = pack._build_roles_workflow(DEFAULT_ROLES)
    assert spec.start_node == "product_manager"
    assert "engineer" in spec.nodes["product_manager"].allowed_next_nodes
    assert "reviewer" in spec.nodes["engineer"].allowed_next_nodes
    assert spec.nodes["reviewer"].allowed_next_nodes == ()


def test_workflow_topology_custom(tmp_path: Path) -> None:
    pack = create_pack(workspace_dir=tmp_path, role_sequence=["a", "b", "c"])
    spec = pack._build_roles_workflow(["a", "b", "c"])
    assert spec.start_node == "a"
    assert "b" in spec.nodes["a"].allowed_next_nodes
    assert "c" in spec.nodes["b"].allowed_next_nodes
    assert spec.nodes["c"].allowed_next_nodes == ()


@pytest.mark.asyncio
async def test_role_node_appends_to_thread(tmp_path: Path) -> None:
    pack = create_pack(workspace_dir=tmp_path)
    node_fn = pack._make_role_node("engineer")

    ctx = MagicMock()
    ctx.request.text = "Build a CLI tool"
    ctx.request.metadata = {"provider": "x", "model": "x", "api_key": "x"}
    ctx.run_state.working_memory = {
        "thread": [{"role": "product_manager", "content": "Here is the spec."}]
    }

    with patch.object(pack, "_call_llm", new=AsyncMock(return_value="Here is the code.")):
        result = await node_fn(ctx)

    assert result.status == StepStatus.SUCCESS
    thread = ctx.run_state.working_memory["thread"]
    assert len(thread) == 2
    assert thread[1]["role"] == "engineer"
    assert thread[1]["content"] == "Here is the code."


@pytest.mark.asyncio
async def test_role_node_first_turn_no_thread(tmp_path: Path) -> None:
    pack = create_pack(workspace_dir=tmp_path)
    node_fn = pack._make_role_node("product_manager")

    ctx = MagicMock()
    ctx.request.text = "Build something"
    ctx.request.metadata = {"provider": "x", "model": "x", "api_key": "x"}
    ctx.run_state.working_memory = {}

    with patch.object(pack, "_call_llm", new=AsyncMock(return_value="Here is the PRD.")):
        result = await node_fn(ctx)

    assert result.status == StepStatus.SUCCESS
    thread = ctx.run_state.working_memory["thread"]
    assert thread[0]["role"] == "product_manager"
