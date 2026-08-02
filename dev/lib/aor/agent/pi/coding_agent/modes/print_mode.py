"""Non-interactive "print" mode.

Python port of `vendor/pi-mono-upstream/packages/coding-agent/src/modes/print/print-mode.ts`
trimmed to the single responsibility of "run one prompt, print one result".
Two output formats:

- ``text`` (default): print the assistant's final text content.
- ``json``: print each `AgentEvent` as a JSON line. Useful for piping into
  other tools. Uses `model_dump(mode="json", by_alias=True)` to stay
  round-trippable.
"""

from __future__ import annotations

import asyncio
import json
import sys
from dataclasses import dataclass, field
from typing import IO, Literal

from pydantic import BaseModel

from ...ai.types import AssistantMessage, Model, TextContent
from ..sdk import create_agent_session

OutputFormat = Literal["text", "json"]


@dataclass
class PrintModeOptions:
    prompt: str
    model: Model
    cwd: str | None = None
    include_pi_tools: bool = True
    output_format: OutputFormat = "text"
    stream_events: bool = False
    extension_paths: list[str] = field(default_factory=list)
    skill_paths: list[str] = field(default_factory=list)
    api_key: str | None = None
    custom_system_prompt: str | None = None
    append_system_prompt: str | None = None


def _dump_event(event: object) -> str:
    if isinstance(event, BaseModel):
        return json.dumps(event.model_dump(mode="json", by_alias=True), ensure_ascii=False)
    return json.dumps({"event": repr(event)}, ensure_ascii=False)


async def run_print_mode(options: PrintModeOptions, *, out: IO[str] = sys.stdout) -> int:
    """Run a single prompt non-interactively. Returns the process exit code."""
    session = create_agent_session(
        model=options.model,
        cwd=options.cwd,
        include_pi_tools=options.include_pi_tools,
        extension_paths=options.extension_paths,
        skill_paths=options.skill_paths,
        api_key=options.api_key,
        custom_system_prompt=options.custom_system_prompt,
        append_system_prompt=options.append_system_prompt,
    )

    if options.stream_events and options.output_format == "json":
        def _listener(event: object) -> None:
            out.write(_dump_event(event) + "\n")
            out.flush()
        unsubscribe = session.agent.subscribe(_listener)
    else:
        unsubscribe = lambda: None  # noqa: E731

    try:
        last = await session.run(options.prompt)
    finally:
        unsubscribe()
        await session.shutdown()

    if options.output_format == "json":
        if not options.stream_events:
            out.write(_dump_event(last) + "\n")
    else:
        out.write(_extract_text(last) + "\n")
    out.flush()
    return 0


def _extract_text(message: AssistantMessage | None) -> str:
    if message is None:
        return ""
    parts: list[str] = []
    for block in message.content:
        if isinstance(block, TextContent) and block.text:
            parts.append(block.text)
    return "\n".join(parts)


def _sync_run(options: PrintModeOptions) -> int:
    return asyncio.run(run_print_mode(options))


__all__ = ["OutputFormat", "PrintModeOptions", "run_print_mode"]
