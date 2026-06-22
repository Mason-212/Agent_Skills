"""Unit tests for multiagent_adversarial pack.

Tests workflow topology and node logic without making real LLM calls.
The verifier is a Python script run in a subprocess; tests use real temp scripts.
"""

import json
import sys
import textwrap
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from orchestrator.types import StepResult, StepStatus, WorkflowRequest
from packs.multiagent_adversarial import create_pack, _next_run_dir
from packs.multiagent_adversarial._workflow import AdversarialPolicy


# ── Pack instantiation ────────────────────────────────────────────────────────

def test_create_pack_auto_run_dir() -> None:
    pack = create_pack()
    assert pack._run_dir.exists()
    assert pack._run_dir.parent == Path("/tmp/aor_runs")
    assert not pack.is_open


def test_create_pack_explicit_run_dir(tmp_path: Path) -> None:
    pack = create_pack(run_dir=tmp_path)
    assert pack._run_dir == tmp_path
    assert pack.descriptor.id == "multiagent_adversarial"


@pytest.mark.asyncio
async def test_open_close(tmp_path: Path) -> None:
    pack = create_pack(run_dir=tmp_path)
    await pack.open()
    assert pack.is_open
    await pack.close()
    assert not pack.is_open


def test_workflow_topology(tmp_path: Path) -> None:
    pack = create_pack(run_dir=tmp_path)
    spec = pack._build_adversarial_workflow()
    assert "generate" in spec.nodes
    assert "verify" in spec.nodes
    assert spec.start_node == "generate"
    assert "verify" in spec.nodes["generate"].allowed_next_nodes
    assert "generate" in spec.nodes["verify"].allowed_next_nodes


def test_next_run_dir_increments() -> None:
    d1 = _next_run_dir()
    d2 = _next_run_dir()
    assert d1.exists()
    assert d2.exists()
    assert d1 != d2


# ── Verifier script ───────────────────────────────────────────────────────────

def test_run_verifier_script_pass(tmp_path: Path) -> None:
    script = tmp_path / "verifier.py"
    script.write_text(textwrap.dedent("""\
        import sys, json
        artifact = sys.stdin.read()
        passed = "AAPL" in artifact
        print(json.dumps({"gate_passed": passed, "reason": "found ticker" if passed else "missing ticker"}))
    """))
    pack = create_pack(run_dir=tmp_path)
    passed, reason = pack._run_verifier_script(str(script), "AAPL is a great stock")
    assert passed is True
    assert "ticker" in reason


def test_run_verifier_script_fail(tmp_path: Path) -> None:
    script = tmp_path / "verifier.py"
    script.write_text(textwrap.dedent("""\
        import sys, json
        artifact = sys.stdin.read()
        print(json.dumps({"gate_passed": False, "reason": "missing ticker"}))
    """))
    pack = create_pack(run_dir=tmp_path)
    passed, reason = pack._run_verifier_script(str(script), "no ticker here")
    assert passed is False
    assert reason == "missing ticker"


def test_run_verifier_script_bad_exit(tmp_path: Path) -> None:
    script = tmp_path / "verifier.py"
    script.write_text("import sys; sys.exit(1)")
    pack = create_pack(run_dir=tmp_path)
    passed, reason = pack._run_verifier_script(str(script), "anything")
    assert passed is False
    assert "Verifier exited" in reason


def test_run_verifier_script_bad_json(tmp_path: Path) -> None:
    script = tmp_path / "verifier.py"
    script.write_text("print('not json')")
    pack = create_pack(run_dir=tmp_path)
    passed, reason = pack._run_verifier_script(str(script), "anything")
    assert passed is False
    assert "error" in reason.lower()


# ── Node: generate ────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_generate_node_stores_artifact(tmp_path: Path) -> None:
    pack = create_pack(run_dir=tmp_path)
    ctx = MagicMock()
    ctx.request.text = "Find a good stock"
    ctx.request.metadata = {"provider": "x", "model": "x", "api_key": "x", "_run_dir": str(tmp_path), "max_retries": 3}
    ctx.run_state.working_memory = {}

    with patch.object(pack, "_call_llm", new=AsyncMock(return_value="Buy AAPL")):
        result = await pack._node_generate(ctx)

    assert result.status == StepStatus.SUCCESS
    assert ctx.run_state.working_memory["artifact"] == "Buy AAPL"
    # attempt file written
    assert (tmp_path / "attempts" / "001_artifact.txt").read_text() == "Buy AAPL"


@pytest.mark.asyncio
async def test_generate_node_includes_prior_critique(tmp_path: Path) -> None:
    pack = create_pack(run_dir=tmp_path)
    ctx = MagicMock()
    ctx.request.text = "Find a good stock"
    ctx.request.metadata = {"provider": "x", "model": "x", "api_key": "x", "max_retries": 3}
    ctx.run_state.working_memory = {"critique": "Missing P/E ratio", "attempt": 2, "max_retries": 3}

    captured_prompt: list[str] = []

    async def fake_llm(*, system_prompt: str, user_prompt: str, metadata: dict) -> str:
        captured_prompt.append(user_prompt)
        return "AAPL with P/E 28"

    with patch.object(pack, "_call_llm", new=fake_llm):
        await pack._node_generate(ctx)

    assert "Missing P/E ratio" in captured_prompt[0]


# ── Node: verify ─────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_verify_node_uses_script(tmp_path: Path) -> None:
    script = tmp_path / "verifier.py"
    script.write_text(textwrap.dedent("""\
        import sys, json
        artifact = sys.stdin.read()
        print(json.dumps({"gate_passed": True, "reason": "all good"}))
    """))
    pack = create_pack(run_dir=tmp_path)
    ctx = MagicMock()
    ctx.request.metadata = {"verifier_script": str(script), "provider": "x", "model": "x", "api_key": "x"}
    ctx.run_state.working_memory = {"artifact": "AAPL recommendation", "attempt": 1, "run_dir": str(tmp_path)}

    result = await pack._node_verify(ctx)

    assert result.status == StepStatus.SUCCESS
    assert result.output["gate_passed"] is True
    assert result.output["verifier_reason"] == "all good"
    assert (tmp_path / "attempts" / "001_verifier_output.json").exists()


@pytest.mark.asyncio
async def test_verify_node_warns_and_falls_back_when_no_script(tmp_path: Path) -> None:
    pack = create_pack(run_dir=tmp_path)
    ctx = MagicMock()
    ctx.request.metadata = {"provider": "x", "model": "x", "api_key": "x"}
    ctx.run_state.working_memory = {"artifact": "AAPL", "attempt": 1}

    with patch.object(pack, "_llm_critic_fallback", new=AsyncMock(return_value=(True, "ok"))):
        import warnings
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            result = await pack._node_verify(ctx)
            assert any("Falling back to LLM-as-critic" in str(warning.message) for warning in w)

    assert result.output["gate_passed"] is True


# ── AdversarialPolicy ─────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_policy_raises_if_max_retries_missing() -> None:
    policy = AdversarialPolicy()
    node = MagicMock()
    result = StepResult(status=StepStatus.SUCCESS, output={"gate_passed": False, "verifier_reason": "bad"})
    run_state = MagicMock()
    run_state.working_memory = {"attempt": 2}  # no max_retries

    with pytest.raises(ValueError, match="max_retries not set"):
        await policy.decide(node, result, run_state)


@pytest.mark.asyncio
async def test_policy_complete_on_gate_passed() -> None:
    policy = AdversarialPolicy()
    node = MagicMock()
    result = StepResult(status=StepStatus.SUCCESS, output={"gate_passed": True, "verifier_reason": "ok"})
    run_state = MagicMock()
    run_state.working_memory = {"attempt": 2, "max_retries": 3}

    from orchestrator.types import WorkflowAction
    decision = await policy.decide(node, result, run_state)
    assert decision.action == WorkflowAction.COMPLETE


@pytest.mark.asyncio
async def test_policy_retry_on_gate_failed() -> None:
    policy = AdversarialPolicy()
    node = MagicMock()
    result = StepResult(status=StepStatus.SUCCESS, output={"gate_passed": False, "verifier_reason": "fix it"})
    run_state = MagicMock()
    run_state.working_memory = {"attempt": 2, "max_retries": 3}

    from orchestrator.types import WorkflowAction
    decision = await policy.decide(node, result, run_state)
    assert decision.action == WorkflowAction.NEXT
    assert decision.next_node == "generate"


@pytest.mark.asyncio
async def test_policy_fail_after_max_retries() -> None:
    policy = AdversarialPolicy()
    node = MagicMock()
    result = StepResult(status=StepStatus.SUCCESS, output={"gate_passed": False, "verifier_reason": "still bad"})
    run_state = MagicMock()
    run_state.working_memory = {"attempt": 4, "max_retries": 3}

    from orchestrator.types import WorkflowAction
    decision = await policy.decide(node, result, run_state)
    assert decision.action == WorkflowAction.FAIL
