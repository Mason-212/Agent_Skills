"""Minimal async SSE parser.

Used by `gateway.py`, `anthropic.py`, and `openai_responses.py`. Gemini does
not use SSE (it emits a JSON array stream) and has its own parser inline.

Spec: https://developer.mozilla.org/en-US/docs/Web/API/Server-sent_events/Using_server-sent_events

Only the fields relevant to LLM streaming are surfaced: `event`, `data`.
Retry / id fields are ignored. Multi-line `data:` blocks are concatenated
with newlines per the spec. Empty lines terminate an event.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import AsyncIterator

import httpx


@dataclass
class SseEvent:
    event: str | None = None
    data: str = ""
    raw_lines: list[str] = field(default_factory=list)


async def iter_sse(response: httpx.Response) -> AsyncIterator[SseEvent]:
    """Parse an httpx streaming response into SSE events.

    The response must be opened with `stream=True` (i.e., via client.stream()).
    """
    buffer: list[str] = []
    event_name: str | None = None

    async for line in response.aiter_lines():
        if line == "":
            if buffer or event_name is not None:
                yield SseEvent(event=event_name, data="\n".join(buffer), raw_lines=list(buffer))
            buffer = []
            event_name = None
            continue
        if line.startswith(":"):
            continue
        if ":" in line:
            field_name, _, value = line.partition(":")
            if value.startswith(" "):
                value = value[1:]
        else:
            field_name, value = line, ""
        if field_name == "event":
            event_name = value
        elif field_name == "data":
            buffer.append(value)
        # Ignore id, retry, and unknown fields.

    if buffer or event_name is not None:
        yield SseEvent(event=event_name, data="\n".join(buffer), raw_lines=list(buffer))


__all__ = ["SseEvent", "iter_sse"]
