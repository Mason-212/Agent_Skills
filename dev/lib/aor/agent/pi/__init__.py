"""agent.pi: namespace for the pi-mono Python port.

This package is an umbrella for sibling subpackages that together cover the
pi-mono surface. Importing `agent.pi` on its own has no side effects and
exposes no symbols; pick an explicit subpackage:

- `agent.pi.ai` -- streaming LLM providers, tool calls, event streams,
  model catalog, and cost accounting (port of pi-ai). Importing it registers
  built-in providers as a side effect.
- `agent.pi.core` -- stateless agent runtime (``Agent`` session facade,
  ``agent_loop`` engine, ``AgentTool`` / ``AgentEvent`` / ``AbortController``
  contracts). Sits on top of ``pi.ai`` and is the one component that turns
  a user prompt into a finished, tool-using conversation. Port of
  pi-agent-core.
- `agent.pi.edc_harness` -- runtime-layer contracts above ``pi.ai``: canonical
  ``ToolExecutionResult`` record plus a deterministic text projection
  (``to_model_message``) consumed by the LLM on its next turn. See
  ``edc_harness/TODO.md`` for open design questions.
- `agent.pi.coding_agent` -- coding-agent SDK on top of ``pi.core``:
  ``AgentSession`` wrapper, built-in filesystem / shell tools
  (``read`` / ``bash`` / ``edit`` / ``write`` / ``grep`` / ``find`` / ``ls``),
  skills and system-prompt assembly, session persistence with branching,
  extension host, and a default context-budget compactor. Port of
  pi-coding-agent.

No re-exports live here; each subpackage owns its own public API.
"""

from __future__ import annotations

__all__: list[str] = []
