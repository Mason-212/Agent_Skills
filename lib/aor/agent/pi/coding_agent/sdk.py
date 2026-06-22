"""Public SDK entry points.

Python port of `vendor/pi-mono-upstream/packages/coding-agent/src/core/sdk.ts`.
Keep the surface tiny:

- `create_agent_session(...)` — construct an `AgentSession` from simple args.
- `run_once(prompt, ...)` — single-shot convenience wrapper.
- `stream(prompt, ...)` — event generator for custom UIs.

Live-credential integration tests live alongside the ai-distilled tests.
"""

from __future__ import annotations

from typing import AsyncIterator

from ..ai.types import AssistantMessage, Model
from ..core.types import AgentEvent
from .agent_session import AgentSession, AgentSessionOptions
from .defaults import DEFAULT_THINKING_LEVEL, ThinkingLevel
from .extensions import Extension, load_extensions


def create_agent_session(
    *,
    model: Model,
    cwd: str | None = None,
    include_pi_tools: bool = True,
    thinking_level: ThinkingLevel = DEFAULT_THINKING_LEVEL,
    custom_system_prompt: str | None = None,
    append_system_prompt: str | None = None,
    extensions: list[Extension] | None = None,
    extension_paths: list[str] | None = None,
    skill_paths: list[str] | None = None,
    include_default_skills: bool = True,
    include_global_context: bool = True,
    extra_context_paths: list[str] | None = None,
    sessions_dir: str | None = None,
    api_key: str | None = None,
) -> AgentSession:
    """Build a fully-wired `AgentSession`.

    `extensions` takes precedence over `extension_paths`. When
    `extension_paths` is provided, it is passed through `load_extensions`
    and the resulting `extensions` list is merged.
    """
    exts: list[Extension] = list(extensions or [])
    if extension_paths:
        res = load_extensions(extension_paths)
        exts.extend(res.extensions)
    options = AgentSessionOptions(
        model=model,
        cwd=cwd,
        include_pi_tools=include_pi_tools,
        thinking_level=thinking_level,
        custom_system_prompt=custom_system_prompt,
        append_system_prompt=append_system_prompt,
        extensions=exts,
        skill_paths=list(skill_paths or []),
        include_default_skills=include_default_skills,
        include_global_context=include_global_context,
        extra_context_paths=list(extra_context_paths or []),
        sessions_dir=sessions_dir,
        api_key=api_key,
    )
    return AgentSession(options)


async def run_once(
    prompt: str,
    *,
    model: Model,
    **kwargs,
) -> AssistantMessage:
    """Create a session, run one prompt, return the last assistant message."""
    session = create_agent_session(model=model, **kwargs)
    try:
        return await session.run(prompt)
    finally:
        await session.shutdown()


async def stream(
    prompt: str,
    *,
    model: Model,
    **kwargs,
) -> AsyncIterator[AgentEvent]:
    """Yield the raw `AgentEvent` stream for a single prompt.

    The generator terminates when the underlying ``session.run`` finishes
    (success or failure). If ``run`` raises, the exception is re-raised
    to the consumer of the generator after cleanup so failures cannot be
    swallowed silently. A sentinel ``None`` is always enqueued when the
    runner exits, which guarantees the consumer cannot deadlock on
    ``queue.get()`` even if no ``agent_end`` event was ever emitted.
    """
    import asyncio

    session = create_agent_session(model=model, **kwargs)
    queue: asyncio.Queue[AgentEvent | None] = asyncio.Queue()
    runner_exc: BaseException | None = None

    def _on_event(event: AgentEvent) -> None:
        queue.put_nowait(event)

    unsubscribe = session.agent.subscribe(_on_event)

    async def _runner() -> None:
        nonlocal runner_exc
        try:
            await session.run(prompt)
        except asyncio.CancelledError:
            raise
        except BaseException as exc:  # noqa: BLE001
            runner_exc = exc
        finally:
            queue.put_nowait(None)

    task = asyncio.create_task(_runner())

    try:
        while True:
            event = await queue.get()
            if event is None:
                break
            yield event
    finally:
        unsubscribe()
        if not task.done():
            task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass
        await session.shutdown()

    if runner_exc is not None:
        raise runner_exc


__all__ = ["create_agent_session", "run_once", "stream"]
