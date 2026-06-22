"""System prompt assembly.

Python port of `vendor/pi-mono-upstream/packages/coding-agent/src/core/system-prompt.ts`.
Builds the default system prompt for the coding agent with:

- Tool catalog (one line per selected tool).
- Adaptive guidelines section — only emits bullets relevant to the enabled
  tools.
- Project context files (e.g., AGENTS.md).
- Skills (XML `<available_skills>` block) — only when the `read` tool is
  available, matching upstream.
- Date/time and cwd appended last.

Upstream keeps references to pi's own documentation (`docs/`, `examples/`);
we preserve the section with empty defaults so downstream callers can
override via `PI_README_PATH` / `PI_DOCS_PATH` / `PI_EXAMPLES_PATH`.
"""

from __future__ import annotations

import datetime as _dt
import os
from dataclasses import dataclass, field
from typing import Iterable

from .config import get_docs_path, get_examples_path, get_readme_path
from .resource_loader import ContextFile
from .skills import Skill, format_skills_for_prompt

TOOL_DESCRIPTIONS: dict[str, str] = {
    "read": "Read file contents",
    "bash": "Execute bash commands (ls, grep, find, etc.)",
    "edit": "Make surgical edits to files (find exact text and replace)",
    "write": "Create or overwrite files",
    "grep": "Search file contents for patterns (respects .gitignore)",
    "find": "Find files by glob pattern (respects .gitignore)",
    "ls": "List directory contents",
}


@dataclass
class BuildSystemPromptOptions:
    custom_prompt: str | None = None
    selected_tools: list[str] | None = None
    tool_snippets: dict[str, str] = field(default_factory=dict)
    prompt_guidelines: list[str] = field(default_factory=list)
    append_system_prompt: str | None = None
    cwd: str | None = None
    context_files: list[ContextFile] = field(default_factory=list)
    skills: list[Skill] = field(default_factory=list)


def _format_now() -> str:
    now = _dt.datetime.now().astimezone()
    return now.strftime("%A, %B %d, %Y %I:%M:%S %p %Z")


def _build_guidelines(tools: list[str], extra: Iterable[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []

    def add(line: str) -> None:
        line = line.strip()
        if not line or line in seen:
            return
        seen.add(line)
        out.append(line)

    has = {name: (name in tools) for name in ("bash", "edit", "write", "grep", "find", "ls", "read")}

    if has["bash"] and not (has["grep"] or has["find"] or has["ls"]):
        add("Use bash for file operations like ls, rg, find")
    elif has["bash"] and (has["grep"] or has["find"] or has["ls"]):
        add("Prefer grep/find/ls tools over bash for file exploration (faster, respects .gitignore)")

    if has["read"] and has["edit"]:
        add("Use read to examine files before editing. You must use this tool instead of cat or sed.")

    if has["edit"]:
        add("Use edit for precise changes (old text must match exactly)")

    if has["write"]:
        add("Use write only for new files or complete rewrites")

    if has["edit"] or has["write"]:
        add(
            "When summarizing your actions, output plain text directly - do NOT use cat or bash to display what you did"
        )

    for g in extra:
        add(g)

    add("Be concise in your responses")
    add("Show file paths clearly when working with files")
    return out


def build_system_prompt(options: BuildSystemPromptOptions | None = None) -> str:
    opts = options or BuildSystemPromptOptions()
    cwd = opts.cwd or os.getcwd()
    dt = _format_now()
    append = f"\n\n{opts.append_system_prompt}" if opts.append_system_prompt else ""

    if opts.custom_prompt:
        prompt = opts.custom_prompt + append
        if opts.context_files:
            prompt += "\n\n# Project Context\n\nProject-specific instructions and guidelines:\n\n"
            for cf in opts.context_files:
                prompt += f"## {cf.path}\n\n{cf.content}\n\n"
        has_read = opts.selected_tools is None or "read" in opts.selected_tools
        if has_read and opts.skills:
            prompt += format_skills_for_prompt(opts.skills)
        prompt += f"\nCurrent date and time: {dt}\nCurrent working directory: {cwd}"
        return prompt

    tools = list(opts.selected_tools or ["read", "bash", "edit", "write"])
    tool_lines = [
        f"- {name}: {opts.tool_snippets.get(name) or TOOL_DESCRIPTIONS.get(name, name)}"
        for name in tools
    ]
    tools_list = "\n".join(tool_lines) if tool_lines else "(none)"

    guidelines = "\n".join(f"- {g}" for g in _build_guidelines(tools, opts.prompt_guidelines))

    readme = get_readme_path()
    docs = get_docs_path()
    examples = get_examples_path()

    prompt = (
        "You are an expert coding assistant operating inside pi, a coding agent edc_harness. "
        "You help users by reading files, executing commands, editing code, and writing new files.\n\n"
        f"Available tools:\n{tools_list}\n\n"
        "In addition to the tools above, you may have access to other custom tools depending on the project.\n\n"
        f"Guidelines:\n{guidelines}\n\n"
        "Pi documentation (read only when the user asks about pi itself, its SDK, extensions, "
        "themes, skills, or TUI):\n"
        f"- Main documentation: {readme}\n"
        f"- Additional docs: {docs}\n"
        f"- Examples: {examples} (extensions, custom tools, SDK)"
    )

    if append:
        prompt += append

    if opts.context_files:
        prompt += "\n\n# Project Context\n\nProject-specific instructions and guidelines:\n\n"
        for cf in opts.context_files:
            prompt += f"## {cf.path}\n\n{cf.content}\n\n"

    if "read" in tools and opts.skills:
        prompt += format_skills_for_prompt(opts.skills)

    prompt += f"\nCurrent date and time: {dt}\nCurrent working directory: {cwd}"
    return prompt


__all__ = [
    "BuildSystemPromptOptions",
    "TOOL_DESCRIPTIONS",
    "build_system_prompt",
]
