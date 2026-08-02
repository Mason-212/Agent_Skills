"""agent.pi.ai: Python port of @mariozechner/pi-ai (Required + selected Maybe features).

See specs/plan_rewrite_piai.md for scope and specs/understanding_pi/rewrite-ai.md
for the mapping from pi-ai features to this package.

Public surface is re-exported here. Importing this subpackage triggers
registration of built-in providers (Gateway, Anthropic, OpenAI Responses,
Google Gemini). `agent.pi` itself is a namespace for peer subpackages;
importing `agent.pi` alone does NOT trigger provider registration.
"""

from __future__ import annotations

from . import (
    providers as _providers,  # noqa: F401  (side-effect: registers built-ins)
)
from .event_stream import AssistantMessageEventStream, EventStream
from .registry import (
    clear_api_providers,
    get_api_provider,
    register_api_provider,
)
from .stream import complete, complete_simple, stream, stream_simple
from .types import (
    AssistantMessage,
    AssistantMessageEvent,
    Context,
    Message,
    Model,
    SimpleStreamOptions,
    StopReason,
    StreamOptions,
    Tool,
    ToolResultMessage,
    Usage,
    UserMessage,
)
from .validation import (
    ToolValidationError,
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
