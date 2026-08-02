"""Extension system for `agent.pi.coding_agent`.

The Python port keeps a **scoped** extension surface:

- `on(event, handler)` for lifecycle events (see `EVENT_NAMES`).
- `register_tool(tool)` for adding LLM-callable `AgentTool` instances.
- `add_system_prompt_section(text)` to append per-extension instructions.
- `send_message(msg)` / `send_user_message(text)` to inject messages.

Excluded from this port (intentionally):

- TUI widgets, overlays, custom editor components.
- Keyboard shortcuts / keybindings.
- CLI flag registration (use `argparse` at your own layer).
- OAuth providers and `register_provider` (pi-ai registry is in a
  different package and much smaller in scope).

Extensions are plain Python modules. They expose a module-level
``register(pi)`` callable. The loader uses `importlib.util` to import
each file path directly so users can distribute extensions as single
`.py` files without requiring them to be an installed package.
"""

from .loader import (
    LoadExtensionsResult,
    load_extensions,
    reload_extension,
)
from .runner import ExtensionRunner
from .types import (
    EVENT_NAMES,
    AgentEndEvent,
    AgentStartEvent,
    BeforeAgentStartEvent,
    BeforeAgentStartEventResult,
    ContextEvent,
    ContextEventResult,
    Extension,
    ExtensionAPI,
    ExtensionContext,
    ExtensionError,
    ExtensionEvent,
    MessageEndEvent,
    MessageStartEvent,
    MessageUpdateEvent,
    RegisteredTool,
    SessionCompactEvent,
    SessionShutdownEvent,
    SessionStartEvent,
    ToolCallEvent,
    ToolCallEventResult,
    ToolExecutionEndEvent,
    ToolExecutionStartEvent,
    ToolExecutionUpdateEvent,
    ToolResultEvent,
    ToolResultEventResult,
    TurnEndEvent,
    TurnStartEvent,
)
from .wrapper import wrap_tool_with_extensions, wrap_tools_with_extensions

__all__ = [
    "AgentEndEvent",
    "AgentStartEvent",
    "BeforeAgentStartEvent",
    "BeforeAgentStartEventResult",
    "ContextEvent",
    "ContextEventResult",
    "EVENT_NAMES",
    "Extension",
    "ExtensionAPI",
    "ExtensionContext",
    "ExtensionError",
    "ExtensionEvent",
    "ExtensionRunner",
    "LoadExtensionsResult",
    "MessageEndEvent",
    "MessageStartEvent",
    "MessageUpdateEvent",
    "RegisteredTool",
    "SessionCompactEvent",
    "SessionShutdownEvent",
    "SessionStartEvent",
    "ToolCallEvent",
    "ToolCallEventResult",
    "ToolExecutionEndEvent",
    "ToolExecutionStartEvent",
    "ToolExecutionUpdateEvent",
    "ToolResultEvent",
    "ToolResultEventResult",
    "TurnEndEvent",
    "TurnStartEvent",
    "load_extensions",
    "reload_extension",
    "wrap_tool_with_extensions",
    "wrap_tools_with_extensions",
]
