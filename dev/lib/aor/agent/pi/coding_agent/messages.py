"""Custom message types and `convert_to_llm` for the coding agent.

Python port of `vendor/pi-mono-upstream/packages/coding-agent/src/core/messages.ts`.

Upstream extends `AgentMessage` via TypeScript declaration merging on
`CustomAgentMessages`. Python doesn't have that mechanism; we simply expose
new dataclasses tagged with a `role` discriminator and convert them to
plain `UserMessage`/`AssistantMessage` objects in `convert_to_llm`.
"""

from __future__ import annotations

import time
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from ..ai.types import (
    AssistantMessage,
    Message,
    TextContent,
    ToolResultMessage,
    UserMessage,
)

# ---------------------------------------------------------------------------
# Constants matching upstream
# ---------------------------------------------------------------------------

COMPACTION_SUMMARY_PREFIX = (
    "The conversation history before this point was compacted into the following "
    "summary:\n\n<summary>\n"
)
COMPACTION_SUMMARY_SUFFIX = "\n</summary>"

BRANCH_SUMMARY_PREFIX = (
    "The following is a summary of a branch that this conversation came back from:"
    "\n\n<summary>\n"
)
BRANCH_SUMMARY_SUFFIX = "</summary>"


# ---------------------------------------------------------------------------
# Custom messages
# ---------------------------------------------------------------------------


class BashExecutionMessage(BaseModel):
    """User-initiated bash output via the `!`/`!!` prefix."""

    role: Literal["bashExecution"] = "bashExecution"
    command: str
    output: str
    exit_code: int | None = Field(default=None, validation_alias="exitCode")
    cancelled: bool = False
    truncated: bool = False
    full_output_path: str | None = Field(default=None, validation_alias="fullOutputPath")
    timestamp: int
    exclude_from_context: bool = Field(default=False, validation_alias="excludeFromContext")

    model_config = ConfigDict(populate_by_name=True)


class CustomMessage(BaseModel):
    """Extension-injected message via `pi.send_message()`.

    `display=False` makes the message LLM-only (not surfaced to UIs).
    """

    role: Literal["custom"] = "custom"
    custom_type: str = Field(validation_alias="customType")
    content: str | list[TextContent]
    display: bool = True
    details: Any = None
    timestamp: int

    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)


class BranchSummaryMessage(BaseModel):
    role: Literal["branchSummary"] = "branchSummary"
    summary: str
    from_id: str = Field(validation_alias="fromId")
    timestamp: int

    model_config = ConfigDict(populate_by_name=True)


class CompactionSummaryMessage(BaseModel):
    role: Literal["compactionSummary"] = "compactionSummary"
    summary: str
    tokens_before: int = Field(validation_alias="tokensBefore")
    timestamp: int

    model_config = ConfigDict(populate_by_name=True)


CodingAgentMessage = (
    UserMessage
    | AssistantMessage
    | ToolResultMessage
    | BashExecutionMessage
    | CustomMessage
    | BranchSummaryMessage
    | CompactionSummaryMessage
)
"""Widened agent-message union for the coding agent.

Compatible with `agent.pi.core.AgentMessage` for the LLM-facing
roles; the four new roles are filtered/transformed by `convert_to_llm`.
"""


# ---------------------------------------------------------------------------
# Conversions
# ---------------------------------------------------------------------------


def bash_execution_to_text(msg: BashExecutionMessage) -> str:
    text = f"Ran `{msg.command}`\n"
    if msg.output:
        text += f"```\n{msg.output}\n```"
    else:
        text += "(no output)"
    if msg.cancelled:
        text += "\n\n(command cancelled)"
    elif msg.exit_code not in (None, 0):
        text += f"\n\nCommand exited with code {msg.exit_code}"
    if msg.truncated and msg.full_output_path:
        text += f"\n\n[Output truncated. Full output: {msg.full_output_path}]"
    return text


def _now_ms() -> int:
    return int(time.time() * 1000)


def create_branch_summary_message(summary: str, from_id: str, timestamp_ms: int | None = None) -> BranchSummaryMessage:
    return BranchSummaryMessage(
        summary=summary, from_id=from_id, timestamp=timestamp_ms or _now_ms()
    )


def create_compaction_summary_message(
    summary: str, tokens_before: int, timestamp_ms: int | None = None
) -> CompactionSummaryMessage:
    return CompactionSummaryMessage(
        summary=summary, tokens_before=tokens_before, timestamp=timestamp_ms or _now_ms()
    )


def create_custom_message(
    custom_type: str,
    content: str | list[TextContent],
    display: bool,
    details: Any,
    timestamp_ms: int | None = None,
) -> CustomMessage:
    return CustomMessage(
        custom_type=custom_type,
        content=content,
        display=display,
        details=details,
        timestamp=timestamp_ms or _now_ms(),
    )


def convert_to_llm(messages: list[CodingAgentMessage]) -> list[Message]:
    """Transform widened messages into the LLM-facing `Message` union.

    - `bashExecution` becomes a user message with rendered shell output;
      `exclude_from_context=True` drops the message entirely.
    - `custom` becomes a user message (string upgraded to text block).
    - `branchSummary`/`compactionSummary` become user messages prefixed
      with the documented `<summary>...</summary>` envelope.
    - `user`/`assistant`/`toolResult` pass through unchanged.
    """
    out: list[Message] = []
    for m in messages:
        role = getattr(m, "role", None)
        if role == "bashExecution":
            assert isinstance(m, BashExecutionMessage)
            if m.exclude_from_context:
                continue
            out.append(
                UserMessage(
                    role="user",
                    content=[TextContent(type="text", text=bash_execution_to_text(m))],
                    timestamp=m.timestamp,
                )
            )
        elif role == "custom":
            assert isinstance(m, CustomMessage)
            content = (
                [TextContent(type="text", text=m.content)]
                if isinstance(m.content, str)
                else m.content
            )
            out.append(UserMessage(role="user", content=content, timestamp=m.timestamp))
        elif role == "branchSummary":
            assert isinstance(m, BranchSummaryMessage)
            out.append(
                UserMessage(
                    role="user",
                    content=[
                        TextContent(
                            type="text",
                            text=BRANCH_SUMMARY_PREFIX + m.summary + BRANCH_SUMMARY_SUFFIX,
                        )
                    ],
                    timestamp=m.timestamp,
                )
            )
        elif role == "compactionSummary":
            assert isinstance(m, CompactionSummaryMessage)
            out.append(
                UserMessage(
                    role="user",
                    content=[
                        TextContent(
                            type="text",
                            text=COMPACTION_SUMMARY_PREFIX
                            + m.summary
                            + COMPACTION_SUMMARY_SUFFIX,
                        )
                    ],
                    timestamp=m.timestamp,
                )
            )
        elif role in ("user", "assistant", "toolResult"):
            out.append(m)  # type: ignore[arg-type]
    return out


__all__ = [
    "BRANCH_SUMMARY_PREFIX",
    "BRANCH_SUMMARY_SUFFIX",
    "BashExecutionMessage",
    "BranchSummaryMessage",
    "COMPACTION_SUMMARY_PREFIX",
    "COMPACTION_SUMMARY_SUFFIX",
    "CodingAgentMessage",
    "CompactionSummaryMessage",
    "CustomMessage",
    "bash_execution_to_text",
    "convert_to_llm",
    "create_branch_summary_message",
    "create_compaction_summary_message",
    "create_custom_message",
]
