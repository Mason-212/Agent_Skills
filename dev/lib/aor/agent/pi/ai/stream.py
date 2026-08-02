"""Public stream entrypoints.

Python port of vendor/pi-mono-upstream/packages/ai/src/stream.ts.

`stream` / `stream_simple` resolve the provider via the registry and return an
`AssistantMessageEventStream`. `complete` / `complete_simple` are convenience
wrappers that await the stream's final result.

Unlike pi-ai (where the provider modules are imported for side effects in
`stream.ts`), we import providers at the package level in
`agent.pi.ai/__init__.py` and `agent.pi.ai/providers/__init__.py`.
Importing this module directly is safe but does not force provider registration.
"""

from __future__ import annotations

from .event_stream import AssistantMessageEventStream
from .registry import get_api_provider
from .types import (
    AssistantMessage,
    Context,
    Model,
    SimpleStreamOptions,
    StreamOptions,
)


def _resolve(api: str):
    provider = get_api_provider(api)
    if provider is None:
        raise LookupError(f"No API provider registered for api: {api!r}")
    return provider


async def stream(
    model: Model,
    context: Context,
    options: StreamOptions | None = None,
) -> AssistantMessageEventStream:
    """Start a streaming call with the full (non-simple) options surface."""
    return await _resolve(model.api).stream(model, context, options)


async def complete(
    model: Model,
    context: Context,
    options: StreamOptions | None = None,
) -> AssistantMessage:
    """Start a stream and await its final AssistantMessage."""
    s = await stream(model, context, options)
    return await s.result()


async def stream_simple(
    model: Model,
    context: Context,
    options: SimpleStreamOptions | None = None,
) -> AssistantMessageEventStream:
    """Simple streaming entrypoint (port of streamSimple).

    Accepts the unified `reasoning` / `thinking_budgets` options. Providers map
    these onto their native reasoning/thinking knobs:

    - Anthropic (messages API): `reasoning` selects a built-in default budget,
      `thinking_budgets[level]` overrides it and becomes
      `thinking.budget_tokens`.
    - Google Gemini: same pattern, becoming
      `generationConfig.thinkingConfig.thinkingBudget`.
    - OpenAI `/v1/responses`: `reasoning` maps to `reasoning.effort`
      (minimal/low/medium/high). The Responses API does not take a numeric
      budget, so `thinking_budgets` is ignored for this provider.
    - Gateway: forwards whatever the underlying provider supports.
    """
    return await _resolve(model.api).stream_simple(model, context, options)


async def complete_simple(
    model: Model,
    context: Context,
    options: SimpleStreamOptions | None = None,
) -> AssistantMessage:
    s = await stream_simple(model, context, options)
    return await s.result()


__all__ = ["complete", "complete_simple", "stream", "stream_simple"]
