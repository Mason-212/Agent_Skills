"""agent.pi.core: Python port of @mariozechner/pi-agent-core.

Mirrors the TS package structure (`vendor/pi-mono-upstream/packages/agent/src/`)
one-to-one:

- `types`: contracts (`AgentMessage`, `AgentContext`, `AgentEvent` union,
  `AgentLoopConfig`, `AgentTool`, `AbortController`/`AbortSignal`, ...).
- `agent_loop`: stateless engine (`agent_loop`, `agent_loop_continue`,
  internal `run_loop` / `stream_assistant_response` / `execute_tool_calls`).
- `agent`: session façade (`Agent` class) with steering/follow-up queues and
  subscribe/emit fanout.

The upstream TS package also ships an optional `proxy` transport for
browser-based clients that route LLM calls through a backend. That module
was intentionally not ported: this codebase runs server-side, so the auth
and CORS concerns it solves don't apply. Add it back as `transports/proxy.py`
if/when a thin client needs to plug into `Agent` over HTTP.

Dependency: the LLM layer (`agent.pi.ai`) — providers, `stream_simple`,
`EventStream`, `validate_tool_arguments`. Importing this subpackage does not
register providers; either import `agent.pi.ai` (which does) or
register providers manually before constructing an `Agent`.

Design trade-off captured here (was decided during port):

- **AgentMessage** is aliased to the LLM `Message` union. Upstream TS declares
  an extension seam via declaration merging on `CustomAgentMessages`. In
  Python we can widen the alias later without breaking callers, and the
  default `convert_to_llm` already filters by role so custom roles are
  dropped from LLM calls naturally.
"""

from __future__ import annotations

from agent.pi.core.agent import Agent, QueueMode
from agent.pi.core.agent_loop import (
    AgentEventStream,
    agent_loop,
    agent_loop_continue,
)
from agent.pi.core.types import (
    AbortController,
    AbortSignal,
    AgentContext,
    AgentEnd,
    AgentEvent,
    AgentLoopConfig,
    AgentMessage,
    AgentStart,
    AgentState,
    AgentTool,
    AgentToolResult,
    AgentToolUpdateCallback,
    ConvertToLlmFn,
    GetApiKeyFn,
    GetMessagesFn,
    MessageEnd,
    MessageStart,
    MessageUpdate,
    StreamFn,
    ThinkingLevel,
    ToolExecuteFn,
    ToolExecutionEnd,
    ToolExecutionStart,
    ToolExecutionUpdate,
    TransformContextFn,
    TurnEnd,
    TurnStart,
)

__all__ = [
    "AbortController",
    "AbortSignal",
    "Agent",
    "AgentContext",
    "AgentEnd",
    "AgentEvent",
    "AgentEventStream",
    "AgentLoopConfig",
    "AgentMessage",
    "AgentStart",
    "AgentState",
    "AgentTool",
    "AgentToolResult",
    "AgentToolUpdateCallback",
    "ConvertToLlmFn",
    "GetApiKeyFn",
    "GetMessagesFn",
    "MessageEnd",
    "MessageStart",
    "MessageUpdate",
    "QueueMode",
    "StreamFn",
    "ThinkingLevel",
    "ToolExecuteFn",
    "ToolExecutionEnd",
    "ToolExecutionStart",
    "ToolExecutionUpdate",
    "TransformContextFn",
    "TurnEnd",
    "TurnStart",
    "agent_loop",
    "agent_loop_continue",
]
