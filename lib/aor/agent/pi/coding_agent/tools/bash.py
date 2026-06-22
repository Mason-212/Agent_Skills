"""`bash` tool — run a shell command and stream tail-truncated output.

Python port of `coding-agent/src/core/tools/bash.ts`. Implements:

- Streaming via asyncio subprocess; emits partial results to `on_update`.
- Timeout via `asyncio.wait_for` on the read loop, killing the process tree.
- Tail truncation: keeps the last DEFAULT_MAX_BYTES/DEFAULT_MAX_LINES.
- Spills full output to a temp file when truncated.
"""

from __future__ import annotations

import asyncio
import os
import secrets
import signal as signalmod
import sys
import tempfile
from collections import deque
from dataclasses import dataclass, field
from typing import Any, Awaitable, Callable

from ...ai.types import TextContent
from ...core.types import AgentTool, AgentToolResult, AgentToolUpdateCallback
from .truncate import (
    DEFAULT_MAX_BYTES,
    DEFAULT_MAX_LINES,
    TruncationResult,
    format_size,
    truncate_tail,
)

BashToolInput = dict[str, Any]


@dataclass
class BashToolDetails:
    truncation: TruncationResult | None = None
    full_output_path: str | None = None


@dataclass
class BashSpawnContext:
    command: str
    cwd: str
    env: dict[str, str] = field(default_factory=dict)


BashSpawnHook = Callable[[BashSpawnContext], BashSpawnContext]


@dataclass
class BashOperations:
    """Pluggable command execution (override for SSH-style remote exec)."""

    exec: Callable[[str, str, dict[str, Any]], Awaitable[dict[str, Any]]]


def _get_temp_path() -> str:
    return os.path.join(tempfile.gettempdir(), f"pi-bash-{secrets.token_hex(8)}.log")


def _safe_unlink(path: str | None) -> None:
    if not path:
        return
    try:
        os.unlink(path)
    except OSError:
        pass


def _get_shell_config() -> tuple[str, list[str]]:
    if sys.platform == "win32":
        sh = os.environ.get("COMSPEC", "cmd.exe")
        return sh, ["/c"]
    sh = os.environ.get("SHELL", "/bin/bash")
    return sh, ["-c"]


def _get_shell_env() -> dict[str, str]:
    return dict(os.environ)


async def _kill_process_tree(pid: int, sig: int = signalmod.SIGTERM) -> None:
    try:
        if sys.platform == "win32":
            # Windows has no SIGKILL; SIGTERM is the strongest signal we can
            # send through ``os.kill`` without escalating to TerminateProcess.
            os.kill(pid, signalmod.SIGTERM)
        else:
            os.killpg(os.getpgid(pid), sig)
    except (ProcessLookupError, PermissionError):
        pass


async def _terminate_with_escalation(
    process: asyncio.subprocess.Process,
    *,
    grace: float = 0.5,
) -> None:
    """SIGTERM the process group, wait briefly, then SIGKILL if still alive.

    Without this escalation a process that ignores SIGTERM (``trap '' TERM``)
    keeps the bash tool blocked forever on ``process.wait()``.
    """
    if process.returncode is not None:
        return
    await _kill_process_tree(process.pid, signalmod.SIGTERM)
    try:
        await asyncio.wait_for(process.wait(), timeout=grace)
        return
    except asyncio.TimeoutError:
        pass
    if sys.platform != "win32":
        await _kill_process_tree(process.pid, signalmod.SIGKILL)
    try:
        await asyncio.wait_for(process.wait(), timeout=grace)
    except asyncio.TimeoutError:
        # Last resort: leave the (likely zombie) process behind. We've already
        # tried the strongest signal the OS allows from userland.
        pass


async def _default_exec(command: str, cwd: str, options: dict[str, Any]) -> dict[str, Any]:
    on_data: Callable[[bytes], None] = options["on_data"]
    timeout: float | None = options.get("timeout")
    sig = options.get("signal")
    env = options.get("env") or _get_shell_env()
    if not os.path.isdir(cwd):
        raise FileNotFoundError(
            f"Working directory does not exist: {cwd}\nCannot execute bash commands."
        )

    shell, args = _get_shell_config()
    process = await asyncio.create_subprocess_exec(
        shell,
        *args,
        command,
        cwd=cwd,
        env=env,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        stdin=asyncio.subprocess.DEVNULL,
        preexec_fn=os.setsid if sys.platform != "win32" else None,
    )

    timed_out = {"value": False}

    async def _abort_watch() -> None:
        if not sig:
            return
        await sig.wait()
        await _terminate_with_escalation(process)

    async def _pump(stream: asyncio.StreamReader) -> None:
        while True:
            chunk = await stream.read(4096)
            if not chunk:
                return
            on_data(chunk)

    async def _run() -> int | None:
        assert process.stdout is not None and process.stderr is not None
        await asyncio.gather(_pump(process.stdout), _pump(process.stderr))
        return await process.wait()

    abort_task = asyncio.create_task(_abort_watch()) if sig else None
    try:
        if timeout and timeout > 0:
            try:
                code = await asyncio.wait_for(_run(), timeout=timeout)
            except asyncio.TimeoutError:
                timed_out["value"] = True
                await _terminate_with_escalation(process)
                raise RuntimeError(f"timeout:{timeout}") from None
        else:
            code = await _run()
    finally:
        if abort_task:
            abort_task.cancel()

    if sig and sig.aborted:
        raise RuntimeError("aborted")
    if timed_out["value"]:
        raise RuntimeError(f"timeout:{timeout}")
    return {"exit_code": code}


default_bash_operations = BashOperations(exec=_default_exec)


_BASH_PARAMS_SCHEMA = {
    "type": "object",
    "properties": {
        "command": {"type": "string", "description": "Bash command to execute"},
        "timeout": {"type": "integer", "description": "Timeout in seconds (optional)"},
    },
    "required": ["command"],
}


def create_bash_tool(
    cwd: str,
    *,
    operations: BashOperations | None = None,
    command_prefix: str | None = None,
    spawn_hook: BashSpawnHook | None = None,
) -> AgentTool:
    ops = operations or default_bash_operations

    def _resolve_spawn(command: str) -> BashSpawnContext:
        ctx = BashSpawnContext(command=command, cwd=cwd, env=_get_shell_env())
        return spawn_hook(ctx) if spawn_hook else ctx

    async def execute(
        _tool_call_id: str,
        args: dict[str, Any],
        signal=None,
        on_update: AgentToolUpdateCallback | None = None,
    ) -> AgentToolResult:
        command = args["command"]
        timeout = args.get("timeout")
        if command_prefix:
            command = f"{command_prefix}\n{command}"
        ctx = _resolve_spawn(command)

        chunks: deque[bytes] = deque()
        chunks_bytes = 0
        total_bytes = 0
        max_chunks_bytes = DEFAULT_MAX_BYTES * 2
        temp_path: str | None = None
        temp_file = None

        def _on_data(data: bytes) -> None:
            nonlocal chunks_bytes, total_bytes, temp_path, temp_file
            total_bytes += len(data)
            if total_bytes > DEFAULT_MAX_BYTES and temp_path is None:
                temp_path = _get_temp_path()
                temp_file = open(temp_path, "wb")
                for c in chunks:
                    temp_file.write(c)
            if temp_file is not None:
                temp_file.write(data)
            chunks.append(data)
            chunks_bytes += len(data)
            while chunks_bytes > max_chunks_bytes and len(chunks) > 1:
                removed = chunks.popleft()
                chunks_bytes -= len(removed)
            if on_update:
                full = b"".join(chunks).decode("utf-8", errors="replace")
                trunc = truncate_tail(full)
                on_update(
                    AgentToolResult(
                        content=[TextContent(type="text", text=trunc.content or "")],
                        details=BashToolDetails(
                            truncation=trunc if trunc.truncated else None,
                            full_output_path=temp_path,
                        ),
                    )
                )

        try:
            result = await ops.exec(
                ctx.command,
                ctx.cwd,
                {"on_data": _on_data, "signal": signal, "timeout": timeout, "env": ctx.env},
            )
            exit_code = result.get("exit_code")
        except RuntimeError as exc:
            if temp_file:
                temp_file.close()
            # The abort/timeout messages don't expose ``temp_path`` to the
            # caller in any actionable way, so the spill file would just
            # accumulate. Remove it best-effort.
            _safe_unlink(temp_path)
            temp_path = None
            full = b"".join(chunks).decode("utf-8", errors="replace")
            msg = str(exc)
            if msg == "aborted":
                output = (full + "\n\n" if full else "") + "Command aborted"
                raise RuntimeError(output) from None
            if msg.startswith("timeout:"):
                secs = msg.split(":", 1)[1]
                output = (full + "\n\n" if full else "") + f"Command timed out after {secs} seconds"
                raise RuntimeError(output) from None
            raise
        finally:
            if temp_file:
                temp_file.close()

        full = b"".join(chunks).decode("utf-8", errors="replace")
        truncation = truncate_tail(full)
        output_text = truncation.content or "(no output)"
        details: BashToolDetails | None = None
        if truncation.truncated:
            details = BashToolDetails(truncation=truncation, full_output_path=temp_path)
        else:
            # Output ended up small enough to fit in-memory; the spill file
            # (if any) is dead weight and would never be referenced by the
            # caller, so clean it up.
            _safe_unlink(temp_path)
            temp_path = None
            start = truncation.total_lines - truncation.output_lines + 1
            end = truncation.total_lines
            if truncation.last_line_partial:
                last_line = (full.split("\n")[-1] if full else "")
                size = format_size(len(last_line.encode("utf-8")))
                output_text += (
                    f"\n\n[Showing last {format_size(truncation.output_bytes)} of line "
                    f"{end} (line is {size}). Full output: {temp_path}]"
                )
            elif truncation.truncated_by == "lines":
                output_text += (
                    f"\n\n[Showing lines {start}-{end} of {truncation.total_lines}. "
                    f"Full output: {temp_path}]"
                )
            else:
                output_text += (
                    f"\n\n[Showing lines {start}-{end} of {truncation.total_lines} "
                    f"({format_size(DEFAULT_MAX_BYTES)} limit). Full output: {temp_path}]"
                )

        if exit_code not in (0, None):
            output_text += f"\n\nCommand exited with code {exit_code}"
            raise RuntimeError(output_text)

        return AgentToolResult(
            content=[TextContent(type="text", text=output_text)], details=details
        )

    return AgentTool(
        name="bash",
        label="bash",
        description=(
            "Execute a bash command in the current working directory. Returns stdout and "
            f"stderr. Output is truncated to last {DEFAULT_MAX_LINES} lines or "
            f"{DEFAULT_MAX_BYTES // 1024}KB. If truncated, full output is saved to a temp "
            "file. Optionally provide a timeout in seconds."
        ),
        parameters=_BASH_PARAMS_SCHEMA,
        execute=execute,
    )


__all__ = [
    "BashOperations",
    "BashSpawnContext",
    "BashSpawnHook",
    "BashToolDetails",
    "BashToolInput",
    "create_bash_tool",
    "default_bash_operations",
]
