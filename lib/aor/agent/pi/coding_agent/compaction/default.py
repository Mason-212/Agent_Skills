"""Default compaction strategy.

Python port of the default `summarizeAndCompact` flow from
`vendor/pi-mono-upstream/packages/coding-agent/src/core/compaction/compaction.ts`.
The port uses a simple deterministic summary (file ops + last assistant
text) instead of a live LLM summarization call, so the compactor is fully
offline-testable. Callers can subclass `DefaultCompactor` and override
`_generate_summary` to plug in a live model.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Awaitable, Callable, Protocol

from ...ai.types import AssistantMessage, TextContent
from ..messages import (
    CodingAgentMessage,
    create_compaction_summary_message,
)
from .utils import (
    compute_file_lists,
    create_file_ops,
    estimate_tokens,
    extract_file_ops_from_message,
    format_file_operations,
)


@dataclass
class CompactionPreparation:
    """Snapshot of the state the compactor will operate on."""

    messages_before: list[CodingAgentMessage]
    tokens_before: int
    kept_messages: list[CodingAgentMessage]
    compacted_messages: list[CodingAgentMessage]


@dataclass
class CompactionResult:
    summary: str
    tokens_before: int
    messages: list[CodingAgentMessage] = field(default_factory=list)
    details: Any = None


class Compactor(Protocol):
    """Strategy interface — swap implementations for custom behaviour."""

    def should_compact(self, messages: list[CodingAgentMessage]) -> bool: ...

    async def compact(
        self, messages: list[CodingAgentMessage]
    ) -> CompactionResult: ...


@dataclass
class DefaultCompactor:
    """Token-budget compactor keeping the last `keep_tail` messages.

    `target_tokens` is the soft upper bound — when the estimated token
    count exceeds it, `should_compact` returns `True` and the caller
    should invoke `compact`.
    """

    target_tokens: int = 100_000
    keep_tail: int = 8
    summarize_fn: Callable[[list[CodingAgentMessage]], Awaitable[str]] | None = None

    def should_compact(self, messages: list[CodingAgentMessage]) -> bool:
        if len(messages) <= self.keep_tail:
            return False
        return estimate_tokens(messages) > self.target_tokens

    async def compact(self, messages: list[CodingAgentMessage]) -> CompactionResult:
        tokens_before = estimate_tokens(messages)
        if len(messages) <= self.keep_tail:
            return CompactionResult(summary="", tokens_before=tokens_before, messages=list(messages))

        keep = messages[-self.keep_tail :]
        compacted = messages[: -self.keep_tail]

        summary = await self._generate_summary(compacted)
        summary_msg = create_compaction_summary_message(summary=summary, tokens_before=tokens_before)
        return CompactionResult(
            summary=summary,
            tokens_before=tokens_before,
            messages=[summary_msg, *keep],
            details=CompactionPreparation(
                messages_before=list(messages),
                tokens_before=tokens_before,
                kept_messages=list(keep),
                compacted_messages=list(compacted),
            ),
        )

    async def _generate_summary(self, compacted: list[CodingAgentMessage]) -> str:
        if self.summarize_fn is not None:
            return await self.summarize_fn(compacted)
        fileops = create_file_ops()
        assistant_texts: list[str] = []
        for m in compacted:
            extract_file_ops_from_message(m, fileops)
            if isinstance(m, AssistantMessage):
                for block in m.content:
                    if isinstance(block, TextContent) and block.text.strip():
                        assistant_texts.append(block.text.strip())
        read_files, modified_files = compute_file_lists(fileops)
        sections: list[str] = []
        file_section = format_file_operations(read_files, modified_files)
        if file_section:
            sections.append(file_section)
        if assistant_texts:
            sections.append(
                "<assistant-turns>\n" + "\n\n".join(assistant_texts[-5:]) + "\n</assistant-turns>"
            )
        sections.append(f"<compacted-turns>{len(compacted)}</compacted-turns>")
        return "\n".join(sections)


__all__ = [
    "CompactionPreparation",
    "CompactionResult",
    "Compactor",
    "DefaultCompactor",
]
