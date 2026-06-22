"""Provider registry.

Python port of vendor/pi-mono-upstream/packages/ai/src/api-registry.ts.

A provider is an async callable per API id. `stream` and `stream_simple` are
registered together so callers can choose the options surface they need.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Awaitable, Callable, Protocol

from .event_stream import AssistantMessageEventStream
from .types import (
    Context,
    Model,
    SimpleStreamOptions,
    StreamOptions,
)

StreamFunction = Callable[
    [Model, Context, "StreamOptions | None"],
    Awaitable[AssistantMessageEventStream],
]

SimpleStreamFunction = Callable[
    [Model, Context, "SimpleStreamOptions | None"],
    Awaitable[AssistantMessageEventStream],
]


class ApiProvider(Protocol):
    """Structural interface a provider module must satisfy."""

    api: str

    async def stream(
        self,
        model: Model,
        context: Context,
        options: StreamOptions | None = None,
    ) -> AssistantMessageEventStream: ...

    async def stream_simple(
        self,
        model: Model,
        context: Context,
        options: SimpleStreamOptions | None = None,
    ) -> AssistantMessageEventStream: ...


@dataclass
class _RegisteredProvider:
    api: str
    stream: StreamFunction
    stream_simple: SimpleStreamFunction
    source_id: str | None = None


_REGISTRY: dict[str, _RegisteredProvider] = {}


def register_api_provider(
    api: str,
    stream: StreamFunction,
    stream_simple: SimpleStreamFunction,
    *,
    source_id: str | None = None,
) -> None:
    """Register stream + stream_simple implementations for an API id.

    Mirrors pi-ai's `registerApiProvider` but takes callables directly rather
    than an object, which is friendlier for Python's module-level pattern.
    """
    _REGISTRY[api] = _RegisteredProvider(
        api=api,
        stream=_wrap_api_check(api, stream),
        stream_simple=_wrap_api_check(api, stream_simple),
        source_id=source_id,
    )


def get_api_provider(api: str) -> _RegisteredProvider | None:
    return _REGISTRY.get(api)


def get_api_providers() -> list[_RegisteredProvider]:
    return list(_REGISTRY.values())


def unregister_api_providers(source_id: str) -> None:
    for api in [api for api, p in _REGISTRY.items() if p.source_id == source_id]:
        del _REGISTRY[api]


def clear_api_providers() -> None:
    _REGISTRY.clear()


def _wrap_api_check(expected_api: str, fn):
    async def _checked(
        model: Model,
        context: Context,
        options=None,
    ) -> AssistantMessageEventStream:
        if model.api != expected_api:
            raise ValueError(
                f"Mismatched api: {model.api!r} expected {expected_api!r}"
            )
        return await fn(model, context, options)

    return _checked


__all__ = [
    "ApiProvider",
    "SimpleStreamFunction",
    "StreamFunction",
    "clear_api_providers",
    "get_api_provider",
    "get_api_providers",
    "register_api_provider",
    "unregister_api_providers",
]
