"""`agent.pi.coding_agent` — Python port of `@mariozechner/pi-coding-agent`.

Core entry points:

- `create_agent_session(...)` / `run_once(...)` / `stream(...)` — SDK.
- `AgentSession` / `AgentSessionOptions` — direct construction.
- `create_all_tools` / `create_coding_tools` / `select_tools` — tool
  factories (see `agent.pi.coding_agent.tools`).
- `build_system_prompt` / `load_skills` / `load_context_files` — prompt
  assembly helpers.
- `SessionManager` — JSONL persistence with branching.
- `load_extensions` / `ExtensionRunner` — dynamic extension host.
- `DefaultCompactor` — context-budget compactor.
"""

from .agent_session import AgentSession, AgentSessionOptions
from .compaction import Compactor, DefaultCompactor
from .defaults import (
    ALL_TOOL_NAMES,
    DEFAULT_THINKING_LEVEL,
    DEFAULT_TOOL_NAMES,
    READ_ONLY_TOOL_NAMES,
    ThinkingLevel,
)
from .extensions import (
    Extension,
    ExtensionAPI,
    ExtensionContext,
    ExtensionRunner,
    load_extensions,
)
from .messages import (
    CodingAgentMessage,
    CustomMessage,
    convert_to_llm,
    create_custom_message,
)
from .resource_loader import ContextFile, load_context_files
from .sdk import create_agent_session, run_once, stream
from .session_manager import SessionManager
from .skills import Skill, load_skills
from .system_prompt import (
    BuildSystemPromptOptions,
    build_system_prompt,
)
from .tools import (
    create_all_tools,
    create_bash_tool,
    create_coding_tools,
    create_edit_tool,
    create_find_tool,
    create_grep_tool,
    create_ls_tool,
    create_read_only_tools,
    create_read_tool,
    create_write_tool,
    select_tools,
)

__all__ = [
    "ALL_TOOL_NAMES",
    "AgentSession",
    "AgentSessionOptions",
    "BuildSystemPromptOptions",
    "CodingAgentMessage",
    "Compactor",
    "ContextFile",
    "CustomMessage",
    "DEFAULT_THINKING_LEVEL",
    "DEFAULT_TOOL_NAMES",
    "DefaultCompactor",
    "Extension",
    "ExtensionAPI",
    "ExtensionContext",
    "ExtensionRunner",
    "READ_ONLY_TOOL_NAMES",
    "SessionManager",
    "Skill",
    "ThinkingLevel",
    "build_system_prompt",
    "convert_to_llm",
    "create_agent_session",
    "create_all_tools",
    "create_bash_tool",
    "create_coding_tools",
    "create_custom_message",
    "create_edit_tool",
    "create_find_tool",
    "create_grep_tool",
    "create_ls_tool",
    "create_read_only_tools",
    "create_read_tool",
    "create_write_tool",
    "load_context_files",
    "load_extensions",
    "load_skills",
    "run_once",
    "select_tools",
    "stream",
]
