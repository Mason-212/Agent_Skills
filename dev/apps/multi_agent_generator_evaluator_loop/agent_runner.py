"""Invoke headless cursor-agent for implementer / evaluator steps."""

from __future__ import annotations

import os
import shutil
import subprocess
import threading
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Sequence


@dataclass
class AgentResult:
    returncode: int
    stdout: str
    stderr: str


@dataclass
class PendingAgent:
    """Background `cursor-agent` process. Poll `thread.is_alive()`; then read `result`."""

    thread: threading.Thread | None = None
    proc: subprocess.Popen[str] | None = None
    result: AgentResult | None = None


def default_model() -> str:
    return os.environ.get("CURSOR_AGENT_MODEL", "gpt-5.4-high")


def default_timeout_s() -> int:
    return int(os.environ.get("CURSOR_AGENT_TIMEOUT", "600"))


def cursor_agent_binary() -> str:
    return os.environ.get("CURSOR_AGENT_CMD", "cursor-agent")


def find_cursor_agent() -> str | None:
    cmd = cursor_agent_binary()
    path = shutil.which(cmd)
    return path


def run_cursor_agent(
    *,
    cwd: Path,
    prompt: str,
    model: str | None = None,
    timeout_s: int | None = None,
) -> AgentResult:
    """
    Run `cursor-agent -p --force --trust` with the given prompt.

    Note: the Streamlit app uses `spawn_cursor_agent()` for non-blocking UI + streaming logs.
    Keep this helper for non-UI scripts/tests.
    """
    binary = find_cursor_agent()
    if not binary:
        return AgentResult(
            returncode=127,
            stdout="",
            stderr=f"Executable not found: {cursor_agent_binary()!r}. "
            "Install from https://cursor.com/install or set CURSOR_AGENT_CMD.",
        )

    m = model if model is not None else default_model()
    t = timeout_s if timeout_s is not None else default_timeout_s()
    args: Sequence[str] = [
        binary,
        "-p",
        "--force",
        "--trust",
        "--model",
        m,
        prompt,
    ]
    proc = subprocess.run(
        args,
        cwd=str(cwd),
        capture_output=True,
        text=True,
        timeout=t,
    )
    return AgentResult(
        returncode=proc.returncode,
        stdout=proc.stdout or "",
        stderr=proc.stderr or "",
    )


def _run_cursor_agent_worker(
    holder: PendingAgent,
    *,
    cwd: Path,
    prompt: str,
    model: str | None,
    timeout_s: int,
    stream_log: Path | None = None,
) -> None:
    binary = find_cursor_agent()
    if not binary:
        holder.result = AgentResult(
            returncode=127,
            stdout="",
            stderr=(
                f"Executable not found: {cursor_agent_binary()!r}. "
                "Install from https://cursor.com/install or set CURSOR_AGENT_CMD."
            ),
        )
        return

    m = model if model is not None else default_model()
    args: Sequence[str] = [
        binary,
        "-p",
        "--force",
        "--trust",
        "--model",
        m,
        prompt,
    ]

    # IMPORTANT: For UI usage we prefer streaming directly to a file (no pump threads),
    # because a stdout/stderr pumping loop can keep the worker thread alive even after
    # the subprocess exits (pipes/EOF timing), which makes the Streamlit UI "wait".
    lf = None
    try:
        popen_kw: dict[str, object]
        if stream_log is not None:
            stream_log.parent.mkdir(parents=True, exist_ok=True)
            # Append: the Streamlit UI pre-creates a header.
            lf = stream_log.open("a", encoding="utf-8")
            lf.write(
                f"\n# started {datetime.now(timezone.utc).isoformat()}Z\n\n"
            )
            lf.flush()
            popen_kw = {
                "args": args,
                "cwd": str(cwd),
                "stdout": lf,
                "stderr": subprocess.STDOUT,
                "text": True,
            }
        else:
            popen_kw = {
                "args": args,
                "cwd": str(cwd),
                "stdout": subprocess.PIPE,
                "stderr": subprocess.PIPE,
                "text": True,
            }
        if os.name != "nt":
            popen_kw["start_new_session"] = True
        holder.proc = subprocess.Popen(**popen_kw)
        rc: int | None
        try:
            rc = holder.proc.wait(timeout=timeout_s)
        except subprocess.TimeoutExpired:
            try:
                holder.proc.kill()
            except ProcessLookupError:
                pass
            holder.proc.wait()
            rc = holder.proc.returncode
            if lf is not None:
                lf.write("\n[stream: process killed after timeout]\n")
                lf.flush()

        if stream_log is not None:
            # UI path: return empty stdout/stderr; logs are in stream_log and will be copied
            # into implementer-iter-*.log / evaluator-iter-*.log by the Streamlit app anyway.
            holder.result = AgentResult(returncode=rc if rc is not None else 0, stdout="", stderr="")
        else:
            assert holder.proc.stdout is not None and holder.proc.stderr is not None
            stdout, stderr = holder.proc.communicate(timeout=1)
            holder.result = AgentResult(
                returncode=rc if rc is not None else 0,
                stdout=stdout or "",
                stderr=stderr or "",
            )
    except Exception as e:
        holder.result = AgentResult(1, "", str(e))
    finally:
        if lf is not None:
            lf.close()


def spawn_cursor_agent(
    *,
    cwd: Path,
    prompt: str,
    model: str | None = None,
    timeout_s: int | None = None,
    stream_log: Path | None = None,
) -> PendingAgent:
    """Start `cursor-agent` on a daemon thread (for Streamlit and other UIs that must not block)."""
    holder = PendingAgent()
    t_sec = int(timeout_s if timeout_s is not None else default_timeout_s())

    def target() -> None:
        _run_cursor_agent_worker(
            holder,
            cwd=cwd,
            prompt=prompt,
            model=model,
            timeout_s=t_sec,
            stream_log=stream_log,
        )

    th = threading.Thread(target=target, daemon=True)
    holder.thread = th
    th.start()
    return holder
