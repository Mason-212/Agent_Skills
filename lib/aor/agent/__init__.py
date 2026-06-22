"""agent: aor agent framework.

Today this package ships the :mod:`agent.pi.ai` sub-package, which is a
Python port of `@mariozechner/pi-ai <https://github.com/badlogic/pi-mono>`_
(Required + selected Maybe features). The :mod:`agent.pi`
namespace is reserved for additional peer subpackages alongside ``ai``.

Importing this module re-exports the ``agent.pi.ai`` public surface and
triggers registration of all built-in providers (Gateway, Anthropic,
OpenAI Responses, Google Gemini).
"""

from __future__ import annotations

from .pi.ai import (
    AssistantMessage,
    AssistantMessageEvent,
    AssistantMessageEventStream,
    Context,
    EventStream,
    Message,
    Model,
    SimpleStreamOptions,
    StopReason,
    StreamOptions,
    Tool,
    ToolResultMessage,
    ToolValidationError,
    Usage,
    UserMessage,
    clear_api_providers,
    complete,
    complete_simple,
    get_api_provider,
    register_api_provider,
    stream,
    stream_simple,
    validate_tool_arguments,
)

__all__ = [
    "AssistantMessage",
    "AssistantMessageEvent",
    "AssistantMessageEventStream",
    "Context",
    "EventStream",
    "Message",
    "Model",
    "SimpleStreamOptions",
    "StopReason",
    "StreamOptions",
    "Tool",
    "ToolResultMessage",
    "ToolValidationError",
    "Usage",
    "UserMessage",
    "clear_api_providers",
    "complete",
    "complete_simple",
    "get_api_provider",
    "register_api_provider",
    "stream",
    "stream_simple",
    "validate_tool_arguments",
]
