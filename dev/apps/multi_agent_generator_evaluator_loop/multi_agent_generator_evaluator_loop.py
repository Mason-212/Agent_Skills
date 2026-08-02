"""Streamlit conductor: implementor → evaluator → human gate (Pattern C)."""

from __future__ import annotations

import time
import uuid
from pathlib import Path

import streamlit as st

from agent_runner import (
    AgentResult,
    PendingAgent,
    default_model,
    default_timeout_s,
    find_cursor_agent,
    spawn_cursor_agent,
)
from prompts import (
    evaluator_prompt,
    implementor_prompt,
    rubric_line_from_selection,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
APP_DIR = Path(__file__).resolve().parent
RUNS_DIR = APP_DIR / "runs"

RUBRIC_OPTIONS = [
    (1, "stress-test-decisions — Stress-test decisions"),
    (2, "blind-spots — Blind spots and coverage"),
    (3, "anti-ai-slop — Anti–AI slop (substance / value density)"),
    (4, "code-quality — Code quality"),
    (5, "ml-design — ML design"),
]

DEFAULT_GOAL = "Find weather in Moraga, CA f"
DEFAULT_DOD = (
    "1. Produce a 7-row daily forecast for **Moraga, CA**.\n"
    "2. Each row includes: date, temperature (high/low), wind speed (max).\n"
    "3. Output is visible as a saved artifact (e.g. `forecast.md`) in the run folder.\n"
)


def _checkpoint(label: str) -> None:
    """Append a timestamped line (only on user-driven actions; safe across reruns)."""
    ts = time.strftime("%Y-%m-%d %H:%M:%S")
    cps: list[str] = st.session_state.setdefault("_checkpoints", [])
    cps.append(f"{ts}  {label}")
    if len(cps) > 80:
        del cps[:-80]


def _pending_elapsed_s() -> float:
    started = float(st.session_state.get("_pending_started", 0.0))
    if started <= 0:
        return 0.0
    return max(0.0, time.monotonic() - started)


def _phase_seconds() -> dict[str, float]:
    return st.session_state.setdefault("_phase_seconds", {})


def _record_phase_duration(kind: str, seconds: float) -> None:
    secs = _phase_seconds()
    secs[kind] = float(seconds)


def _read_log_tail(path: Path | None, *, max_bytes: int = 48_000) -> str:
    if path is None or not path.is_file():
        return "(log file not available yet — subprocess may still be starting)"
    data = path.read_bytes()
    if len(data) > max_bytes:
        return (
            "…[truncated; showing tail]\n"
            + data[-max_bytes:].decode("utf-8", errors="replace")
        )
    return data.decode("utf-8", errors="replace")


def _render_agent_logs_panel(run_dir: Path) -> None:
    log_dir = run_dir / "logs"
    if not log_dir.is_dir():
        st.caption("No `logs/` folder yet.")
        return
    files = sorted(log_dir.glob("*.log"))
    if not files:
        st.caption("`logs/` has no `.log` files yet.")
        return
    st.markdown("#### Agent logs (`logs/*.log`)")
    tabs = st.tabs([p.name for p in files])
    for tab, path in zip(tabs, files):
        with tab:
            try:
                st.code(path.read_text(encoding="utf-8", errors="replace"), language="text")
            except OSError as e:
                st.error(str(e))


def _ensure_runs_dir() -> None:
    RUNS_DIR.mkdir(parents=True, exist_ok=True)


def _write_loop_manifest(
    *,
    run_dir: Path,
    max_iterations: int,
    current_iteration: int,
    rubric_ids: list[int],
    workspace: Path,
) -> None:
    preset = "all" if sorted(set(rubric_ids)) == [1, 2, 3, 4, 5] else ",".join(
        str(x) for x in sorted(set(rubric_ids))
    )
    paths = [
        run_dir / "goal.md",
        run_dir / "dod.md",
        run_dir / "reasoning.md",
        run_dir / "plan.md",
        run_dir / f"critique-iter-{current_iteration}.md",
        workspace,
    ]
    lines = [
        f"max_iterations: {max_iterations}",
        f"current_iteration: {current_iteration}",
        f'rubric_preset: "{preset}"',
        "artifact_paths:",
    ]
    for p in paths:
        lines.append(f"  - {p}")
    (run_dir / "loop.yml").write_text("\n".join(lines) + "\n", encoding="utf-8")


def _init_session_defaults() -> None:
    if "workspace" not in st.session_state:
        st.session_state.workspace = str(REPO_ROOT)
    if "max_iter" not in st.session_state:
        st.session_state.max_iter = 3
    if "rubric_ids" not in st.session_state:
        st.session_state.rubric_ids = [1, 2, 3]
    if "goal_text" not in st.session_state:
        st.session_state.goal_text = DEFAULT_GOAL
    if "dod_text" not in st.session_state:
        st.session_state.dod_text = DEFAULT_DOD
    if "extra_scan" not in st.session_state:
        st.session_state.extra_scan = ""
    if "verify_cmd" not in st.session_state:
        st.session_state.verify_cmd = ""
    if "run_dir" not in st.session_state:
        st.session_state.run_dir = None
    if "iteration" not in st.session_state:
        st.session_state.iteration = 1
    if "workflow_step" not in st.session_state:
        st.session_state.workflow_step = "setup"
    if "exit_reason" not in st.session_state:
        st.session_state.exit_reason = None
    if "last_impl" not in st.session_state:
        st.session_state.last_impl = None
    if "last_eval" not in st.session_state:
        st.session_state.last_eval = None


def _log_agent_output(run_dir: Path, name: str, result: AgentResult) -> None:
    log_dir = run_dir / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    body = f"returncode={result.returncode}\n\n--- stdout ---\n{result.stdout}\n\n--- stderr ---\n{result.stderr}\n"
    (log_dir / name).write_text(body, encoding="utf-8")


def _list_artifact_markdown(run_dir: Path) -> list[Path]:
    if not run_dir.exists():
        return []
    return sorted(run_dir.glob("*.md"))


def _pending_agent_busy() -> bool:
    h: PendingAgent | None = st.session_state.get("_pending_agent")
    return h is not None and h.thread is not None and h.thread.is_alive()


def _apply_pending_completion() -> None:
    """Apply finished background agent to session + disk (implement or evaluate)."""
    h: PendingAgent = st.session_state._pending_agent
    kind: str = st.session_state._pending_kind
    res = h.result or AgentResult(1, "", "missing result")
    run_dir = st.session_state.run_dir
    assert run_dir is not None
    ws = Path(st.session_state.workspace)
    it = st.session_state.iteration

    if kind == "implement":
        _record_phase_duration("implement", _pending_elapsed_s())
        _checkpoint(
            f"CP3: Implementer finished (exit {res.returncode}) → evaluate step "
            "(latency is mostly inside cursor-agent before this line)"
        )
        st.session_state._last_implementer_prompt = st.session_state.get("_pending_prompt", "")
        st.session_state.last_impl = res
        if not res.stdout and not res.stderr:
            # UI run: primary logs were streamed to file.
            live = st.session_state.get("_pending_live_log")
            if live:
                try:
                    txt = Path(live).read_text(encoding="utf-8", errors="replace")
                except OSError:
                    txt = ""
                _log_agent_output(
                    run_dir,
                    f"implementer-iter-{it}.log",
                    AgentResult(res.returncode, txt, ""),
                )
            else:
                _log_agent_output(run_dir, f"implementer-iter-{it}.log", res)
        else:
            _log_agent_output(run_dir, f"implementer-iter-{it}.log", res)
        _write_loop_manifest(
            run_dir=run_dir,
            max_iterations=st.session_state.max_iter,
            current_iteration=it,
            rubric_ids=st.session_state.rubric_ids,
            workspace=ws,
        )
        if res.returncode != 0:
            st.session_state._flash_agent_error = f"Implementer exit code {res.returncode}"
        if not (run_dir / "reasoning.md").exists():
            st.session_state.workflow_step = "artifact_gate"
        else:
            st.session_state.workflow_step = "evaluate"
    elif kind == "evaluate":
        _record_phase_duration("evaluate", _pending_elapsed_s())
        _checkpoint(
            f"CP5: Evaluator finished (exit {res.returncode}) → human gate "
            "(latency is mostly inside cursor-agent before this line)"
        )
        st.session_state._last_evaluator_prompt = st.session_state.get("_pending_prompt", "")
        st.session_state.last_eval = res
        if not res.stdout and not res.stderr:
            live = st.session_state.get("_pending_live_log")
            if live:
                try:
                    txt = Path(live).read_text(encoding="utf-8", errors="replace")
                except OSError:
                    txt = ""
                _log_agent_output(
                    run_dir,
                    f"evaluator-iter-{it}.log",
                    AgentResult(res.returncode, txt, ""),
                )
            else:
                _log_agent_output(run_dir, f"evaluator-iter-{it}.log", res)
        else:
            _log_agent_output(run_dir, f"evaluator-iter-{it}.log", res)
        crit = run_dir / f"critique-iter-{it}.md"
        if not crit.exists() and res.stdout.strip():
            crit.write_text(
                "<!-- Written from stdout fallback; agent did not create file -->\n\n"
                + res.stdout,
                encoding="utf-8",
            )
            st.session_state._flash_agent_warn = (
                "Evaluator did not create the critique file; saved stdout as fallback."
            )
        if res.returncode != 0:
            st.session_state._flash_agent_error = f"Evaluator exit code {res.returncode}"
        _write_loop_manifest(
            run_dir=run_dir,
            max_iterations=st.session_state.max_iter,
            current_iteration=it,
            rubric_ids=st.session_state.rubric_ids,
            workspace=ws,
        )
        st.session_state.workflow_step = "human_gate"


def _handle_pending_agent_early_exit() -> bool:
    """
    While cursor-agent runs in a background thread, refresh ~1/s so the UI is not frozen.
    When the thread finishes, apply results and rerun once.
    Returns True if main() should return immediately (rerun scheduled).
    """
    h: PendingAgent | None = st.session_state.get("_pending_agent")
    if h is None or h.thread is None:
        return False

    if h.thread.is_alive():
        timeout_s = float(st.session_state.get("_pending_timeout", default_timeout_s()))
        elapsed = time.monotonic() - float(st.session_state.get("_pending_started", 0))
        kind = st.session_state.get("_pending_kind", "agent")
        st.info(
            f"**cursor-agent is running** ({kind}, {elapsed:.0f}s elapsed; timeout {timeout_s:.0f}s). "
            "This page auto-refreshes about once per second. "
            "Artifact tabs below update when the agent writes files on disk."
        )
        if elapsed >= 20:
            st.markdown(
                "- If the live log stays header-only after ~20s: run `cursor-agent status` in a terminal.\n"
                "- If auth is OK: reduce **Workspace root** (smaller folder), switch `CURSOR_AGENT_MODEL`, or increase `CURSOR_AGENT_TIMEOUT`.\n"
                "- If the agent never writes `reasoning.md`: it’s not following the prompt; use the **Artifact gate** retry."
            )
        rd = st.session_state.get("run_dir")
        if rd is not None:
            with st.expander("Live run folder (markdown preview)", expanded=True):
                _render_live_run_folder(Path(rd))
        live_log = st.session_state.get("_pending_live_log")
        if live_log is not None:
            with st.expander("Live cursor-agent stream log", expanded=True):
                st.caption(
                    "Interleaved stdout/stderr as the CLI prints it. "
                    "Use checkpoints in the sidebar to see when each phase started and ended."
                )
                st.code(_read_log_tail(Path(live_log)), language="text")
        if h.proc is not None and elapsed > timeout_s:
            try:
                h.proc.kill()
            except ProcessLookupError:
                pass
        time.sleep(0.4)
        st.rerun()
        return True

    _apply_pending_completion()
    st.session_state._pending_agent = None
    st.session_state.pop("_pending_kind", None)
    st.session_state.pop("_pending_started", None)
    st.session_state.pop("_pending_timeout", None)
    st.session_state.pop("_pending_live_log", None)
    st.session_state.pop("_pending_prompt", None)
    st.rerun()
    return True


def _render_markdown_files(run_dir: Path) -> None:
    files = _list_artifact_markdown(run_dir)
    if not files:
        st.info("No markdown artifacts in the run folder yet.")
        return
    tabs = st.tabs([p.name for p in files])
    for tab, path in zip(tabs, files):
        with tab:
            try:
                st.markdown(path.read_text(encoding="utf-8"))
            except OSError as e:
                st.error(str(e))


def _render_live_run_folder(run_dir: Path, *, max_chars: int = 12_000) -> None:
    """Show run_dir files while cursor-agent is still running (updates each refresh)."""
    if not run_dir.is_dir():
        st.warning("Run folder does not exist yet.")
        return
    all_files = sorted(run_dir.iterdir(), key=lambda p: p.name)
    st.caption(
        "Markdown tabs below update as the agent writes files. Until `reasoning.md` exists you usually "
        "only see `goal.md` / `dod.md` from setup."
    )
    md_files = [p for p in all_files if p.suffix.lower() == ".md"]
    other = [p for p in all_files if p.suffix.lower() != ".md"]
    if other:
        st.caption("Other files: " + ", ".join(p.name for p in other))
    if not md_files:
        st.info("No `.md` files in the run folder yet (agent may not have started writing).")
        return
    tabs = st.tabs([p.name for p in md_files])
    for tab, path in zip(tabs, md_files):
        with tab:
            try:
                text = path.read_text(encoding="utf-8")
                if len(text) > max_chars:
                    st.markdown(text[:max_chars] + "\n\n… *(truncated for preview)*")
                else:
                    st.markdown(text)
            except OSError as e:
                st.error(str(e))


def main() -> None:
    st.set_page_config(page_title="Generator / evaluator loop", layout="wide")
    _init_session_defaults()
    _ensure_runs_dir()

    st.title("Multi-agent generator / evaluator loop")
    st.caption(
        "Separate headless `cursor-agent` runs per step. Artifacts live under each run folder."
    )

    if _handle_pending_agent_early_exit():
        return

    if w := st.session_state.pop("_flash_agent_warn", None):
        st.warning(w)
    if e := st.session_state.pop("_flash_agent_error", None):
        st.error(e)

    agent_path = find_cursor_agent()
    if not agent_path:
        st.warning(
            "`cursor-agent` not found on PATH. Install: https://cursor.com/install "
            "or set `CURSOR_AGENT_CMD`. Runs will fail until it is available."
        )
    else:
        st.success(f"Found agent: `{agent_path}` (model `{default_model()}`, timeout {default_timeout_s()}s)")

    with st.sidebar:
        st.header("Run parameters")
        st.session_state.workspace = st.text_input(
            "Workspace root (code edits)",
            value=st.session_state.workspace,
            help="Repository root or subproject where the implementer should apply changes.",
        )
        st.session_state.max_iter = int(
            st.number_input("Max iterations (N)", min_value=1, max_value=50, value=int(st.session_state.max_iter))
        )
        default_labels = [lbl for n, lbl in RUBRIC_OPTIONS if n in st.session_state.rubric_ids]
        picked = st.multiselect(
            "Critique-me rubrics",
            options=[lbl for _, lbl in RUBRIC_OPTIONS],
            default=default_labels or [RUBRIC_OPTIONS[0][1], RUBRIC_OPTIONS[1][1], RUBRIC_OPTIONS[2][1]],
            help="Maps to critique-me menu 1–5; all five → `Rubrics: all`.",
        )
        id_by_label = {lbl: n for n, lbl in RUBRIC_OPTIONS}
        st.session_state.rubric_ids = sorted({id_by_label[l] for l in picked}) if picked else [1, 2, 3]

        st.session_state.extra_scan = st.text_area(
            "Extra paths for evaluator (optional)",
            value=st.session_state.extra_scan,
            height=68,
            help="Additional roots or files the evaluator should consider (same 20-file / depth-2 caps).",
        )
        st.session_state.verify_cmd = st.text_input(
            "Optional verification shell command",
            value=st.session_state.verify_cmd,
            help="e.g. `pytest -q` from workspace — manual Run only; not auto-DoD.",
        )
        if st.session_state.verify_cmd.strip() and st.button("Run verification command"):
            import subprocess

            try:
                proc = subprocess.run(
                    st.session_state.verify_cmd.strip(),
                    shell=True,
                    cwd=st.session_state.workspace,
                    capture_output=True,
                    text=True,
                    timeout=300,
                )
                st.code((proc.stdout or "") + (proc.stderr or ""), language="text")
                st.write(f"Exit code: `{proc.returncode}`")
            except subprocess.TimeoutExpired:
                st.error("Verification timed out (300s).")
            except Exception as e:
                st.exception(e)

        with st.expander("Why is this slow?"):
            st.markdown(
                """
`cursor-agent` is a **full coding agent** (planning, tools, repo context) — not a single LLM reply.
A “simple” goal can still take minutes because of model latency, tool rounds, and how much of the
workspace it inspects.

**Faster runs:** set a **smaller workspace** (a subfolder) for tiny tasks; set `CURSOR_AGENT_MODEL`
to a faster tier if your CLI supports it (`cursor-agent --list-models`). Timeout: `CURSOR_AGENT_TIMEOUT`.
"""
            )

        with st.expander("Workflow checkpoints (latency trace)"):
            cps: list[str] = st.session_state.get("_checkpoints") or []
            if not cps:
                st.caption(
                    "Timestamps appear when you **Initialize run** and start each agent. "
                    "Compare CP2→CP3 and CP4→CP5 to see how long implementer vs evaluator took."
                )
            else:
                st.code("\n".join(cps), language="text")
            secs = st.session_state.get("_phase_seconds") or {}
            if secs:
                st.caption(
                    "Durations (computed from CP start→finish): "
                    + ", ".join(f"{k}={v:.0f}s" for k, v in secs.items())
                )
            if st.button("Clear checkpoint history"):
                st.session_state.pop("_checkpoints", None)
                st.session_state.pop("_phase_seconds", None)
                st.rerun()

    run_dir: Path | None = st.session_state.run_dir
    step = st.session_state.workflow_step

    if step == "setup":
        st.subheader("Checkpoint 0 — Goal & definition of done")
        st.caption("Edit defaults below, then **Initialize run**.")
        st.session_state.goal_text = st.text_area("goal.md", value=st.session_state.goal_text, height=160)
        st.session_state.dod_text = st.text_area("dod.md", value=st.session_state.dod_text, height=200)

        if st.button("Initialize run", type="primary"):
            if not st.session_state.goal_text.strip() or not st.session_state.dod_text.strip():
                st.error("Goal and DoD must be non-empty.")
            else:
                run_id = uuid.uuid4().hex[:12]
                run_dir = RUNS_DIR / f"run_{run_id}"
                run_dir.mkdir(parents=True, exist_ok=True)
                (run_dir / "goal.md").write_text(st.session_state.goal_text.strip() + "\n", encoding="utf-8")
                (run_dir / "dod.md").write_text(st.session_state.dod_text.strip() + "\n", encoding="utf-8")
                st.session_state.run_dir = run_dir
                st.session_state.iteration = 1
                st.session_state.workflow_step = "implement"
                st.session_state.exit_reason = None
                st.session_state.last_impl = None
                st.session_state.last_eval = None
                _checkpoint(
                    "CP1: Run initialized — goal.md & dod.md written (disk); next: implementer"
                )
                ws = Path(st.session_state.workspace)
                _write_loop_manifest(
                    run_dir=run_dir,
                    max_iterations=st.session_state.max_iter,
                    current_iteration=st.session_state.iteration,
                    rubric_ids=st.session_state.rubric_ids,
                    workspace=ws,
                )
                st.rerun()

    elif step == "done":
        st.subheader("Run finished")
        st.write(st.session_state.exit_reason or "Exited.")
        if run_dir:
            st.markdown(f"**Run folder:** `{run_dir}`")
            _render_markdown_files(run_dir)
            _render_agent_logs_panel(run_dir)
        if st.button("Start new run"):
            st.session_state.run_dir = None
            st.session_state.workflow_step = "setup"
            st.session_state.iteration = 1
            st.session_state.exit_reason = None
            st.rerun()

    else:
        assert run_dir is not None
        ws = Path(st.session_state.workspace)
        it = st.session_state.iteration
        rubric_line = rubric_line_from_selection(st.session_state.rubric_ids)

        st.subheader(f"Iteration {it} / {st.session_state.max_iter}")
        st.markdown(f"**Run folder:** `{run_dir}`")

        if step == "implement":
            st.markdown(
                "### Checkpoint 2 — Implementer (most wall time is usually inside `cursor-agent` here)"
            )
            busy = _pending_agent_busy()
            if busy:
                st.caption("Finish the in-flight `cursor-agent` run before starting another.")
            _render_agent_logs_panel(run_dir)
            if st.button(
                "Run implementer",
                type="primary",
                disabled=not agent_path or busy,
            ):
                prompt = implementor_prompt(
                    run_dir=run_dir,
                    workspace=ws,
                    iteration=it,
                    repo_root=REPO_ROOT,
                )
                log_dir = run_dir / "logs"
                log_dir.mkdir(parents=True, exist_ok=True)
                live = log_dir / f"live-implement-iter-{it}.log"
                live.write_text(
                    "# Live cursor-agent stream\n\n"
                    "# (Pre-created by Streamlit so the UI can show it immediately.)\n"
                    "# If this stays empty, the subprocess may not have started or it hasn't printed yet.\n\n",
                    encoding="utf-8",
                )
                _checkpoint(
                    "CP2: Implementer subprocess starting (watch live stream log + CP3 when it ends)"
                )
                st.session_state._pending_live_log = live
                st.session_state._pending_prompt = prompt
                st.session_state._pending_agent = spawn_cursor_agent(
                    cwd=ws, prompt=prompt, stream_log=live
                )
                st.session_state._pending_kind = "implement"
                st.session_state._pending_started = time.monotonic()
                st.session_state._pending_timeout = float(default_timeout_s())
                st.rerun()

        elif step == "artifact_gate":
            st.markdown("### Artifact gate — implementer did not produce required artifacts")
            st.error(
                "**`reasoning.md` is missing.** The implementer is required to write it early. "
                "Review the live log and prompt below, then retry or abort."
            )
            _render_markdown_files(run_dir)
            _render_agent_logs_panel(run_dir)
            with st.expander("Implementer prompt (what was sent)", expanded=False):
                st.code(st.session_state.get("_last_implementer_prompt", st.session_state.get("_pending_prompt", "")), language="text")

            c1, c2 = st.columns(2)
            with c1:
                if st.button("Retry implementer (same iteration)", type="primary", disabled=not agent_path or _pending_agent_busy()):
                    prompt = implementor_prompt(
                        run_dir=run_dir,
                        workspace=ws,
                        iteration=it,
                        repo_root=REPO_ROOT,
                    )
                    log_dir = run_dir / "logs"
                    log_dir.mkdir(parents=True, exist_ok=True)
                    live = log_dir / f"live-implement-iter-{it}.log"
                    live.write_text(
                        "# Live cursor-agent stream\n\n"
                        "# (Retry; pre-created by Streamlit.)\n\n",
                        encoding="utf-8",
                    )
                    _checkpoint("CP2: Implementer retry starting (artifact gate)")
                    st.session_state._pending_live_log = live
                    st.session_state._pending_prompt = prompt
                    st.session_state._pending_agent = spawn_cursor_agent(
                        cwd=ws, prompt=prompt, stream_log=live
                    )
                    st.session_state._pending_kind = "implement"
                    st.session_state._pending_started = time.monotonic()
                    st.session_state._pending_timeout = float(default_timeout_s())
                    st.rerun()
            with c2:
                if st.button("Abort run"):
                    st.session_state.workflow_step = "done"
                    st.session_state.exit_reason = f"Aborted: implementer did not produce reasoning.md (iter {it})."
                    st.rerun()

        elif step == "evaluate":
            st.markdown(
                "### Checkpoint 3 — Artifacts after implementer & evaluator prep "
                "(CP2→CP3 = implementer duration)"
            )
            if not (run_dir / "reasoning.md").exists():
                st.warning(
                    "No **`reasoning.md`** in the run folder — the implementer may not have written "
                    "artifacts there yet. Check **Agent logs** below; the prompt "
                    "requires `reasoning.md`, but the agent must follow it."
                )
            _render_markdown_files(run_dir)
            _render_agent_logs_panel(run_dir)

            st.markdown(
                "### Checkpoint 3b — Evaluator (CP4→CP5 = evaluator duration; separate agent context)"
            )
            busy = _pending_agent_busy()
            if busy:
                st.caption("Finish the in-flight `cursor-agent` run before starting another.")
            if st.button(
                "Run evaluator",
                type="primary",
                disabled=not agent_path or busy,
            ):
                prompt = evaluator_prompt(
                    run_dir=run_dir,
                    workspace=ws,
                    iteration=it,
                    repo_root=REPO_ROOT,
                    rubric_line=rubric_line,
                    extra_scan_paths=st.session_state.extra_scan,
                )
                log_dir = run_dir / "logs"
                log_dir.mkdir(parents=True, exist_ok=True)
                live = log_dir / f"live-evaluate-iter-{it}.log"
                live.write_text(
                    "# Live cursor-agent stream\n\n"
                    "# (Pre-created by Streamlit so the UI can show it immediately.)\n"
                    "# If this stays empty, the subprocess may not have started or it hasn't printed yet.\n\n",
                    encoding="utf-8",
                )
                _checkpoint(
                    "CP4: Evaluator subprocess starting (watch live stream log + CP5 when it ends)"
                )
                st.session_state._pending_live_log = live
                st.session_state._pending_prompt = prompt
                st.session_state._pending_agent = spawn_cursor_agent(
                    cwd=ws, prompt=prompt, stream_log=live
                )
                st.session_state._pending_kind = "evaluate"
                st.session_state._pending_started = time.monotonic()
                st.session_state._pending_timeout = float(default_timeout_s())
                st.rerun()

        elif step == "human_gate":
            st.markdown(
                "### Checkpoint 4 — Human gate (CP4→CP5 already recorded; review & continue or exit)"
            )
            st.success(
                f"Iteration **{it}** complete. Review outputs below, then choose what to do next."
            )

            # Make the decision gate explicit: show the evaluator's critique first,
            # then artifacts + logs, then a required human decision.
            crit = run_dir / f"critique-iter-{it}.md"
            if crit.exists():
                with st.expander("Evaluator critique (critique-iter-*.md)", expanded=True):
                    st.markdown(crit.read_text(encoding="utf-8", errors="replace"))
            else:
                st.warning(
                    f"Missing evaluator critique file: `{crit.name}`. Check logs below."
                )

            with st.expander("Artifacts (run folder .md files)", expanded=True):
                _render_markdown_files(run_dir)

            with st.expander("Logs (runs/.../logs/*.log)", expanded=True):
                _render_agent_logs_panel(run_dir)

            # Required human decision
            st.markdown("#### Human decision (required)")
            can_continue = it < st.session_state.max_iter
            default_choice = "stop" if not can_continue else "continue"
            choice = st.radio(
                "What next?",
                options=[
                    ("continue", "Continue to next iteration"),
                    ("done", "Stop (DoD satisfied)"),
                    ("stop", "Stop (abort / not worth continuing)"),
                ],
                format_func=lambda x: x[1],
                index=0 if default_choice == "continue" else (1 if default_choice == "done" else 2),
                horizontal=False,
            )[0]

            if not can_continue:
                st.info(
                    "Max iterations reached. You can still stop (done/abort), but you cannot continue."
                )

            action_label = {
                "continue": "Apply decision: continue",
                "done": "Apply decision: done",
                "stop": "Apply decision: abort",
            }[choice]

            if st.button(action_label, type="primary"):
                if choice == "continue":
                    if not can_continue:
                        st.error("Cannot continue: max iterations reached.")
                    else:
                        st.session_state.iteration = it + 1
                        st.session_state.workflow_step = "implement"
                        st.session_state.last_impl = None
                        st.session_state.last_eval = None
                        _write_loop_manifest(
                            run_dir=run_dir,
                            max_iterations=st.session_state.max_iter,
                            current_iteration=st.session_state.iteration,
                            rubric_ids=st.session_state.rubric_ids,
                            workspace=ws,
                        )
                        st.rerun()
                elif choice == "done":
                    st.session_state.workflow_step = "done"
                    st.session_state.exit_reason = (
                        f"User marked DoD satisfied after iteration {it}."
                    )
                    st.rerun()
                else:
                    st.session_state.workflow_step = "done"
                    st.session_state.exit_reason = f"User aborted after iteration {it}."
                    st.rerun()


if __name__ == "__main__":
    main()
