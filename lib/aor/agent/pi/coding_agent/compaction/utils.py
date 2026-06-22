"""Helpers shared between compaction and branch summarization.

Python port of `vendor/pi-mono-upstream/packages/coding-agent/src/core/compaction/utils.ts`.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from ...ai.types import AssistantMessage


@dataclass
class FileOperations:
    read: set[str] = field(default_factory=set)
    written: set[str] = field(default_factory=set)
    edited: set[str] = field(default_factory=set)


def create_file_ops() -> FileOperations:
    return FileOperations()


def extract_file_ops_from_message(message: Any, fileops: FileOperations) -> None:
    if not isinstance(message, AssistantMessage):
        return
    for block in message.content:
        if getattr(block, "type", None) != "toolCall":
            continue
        args = getattr(block, "arguments", None) or {}
        path = args.get("path") if isinstance(args, dict) else None
        if not isinstance(path, str):
            continue
        name = getattr(block, "name", "")
        if name == "read":
            fileops.read.add(path)
        elif name == "write":
            fileops.written.add(path)
        elif name == "edit":
            fileops.edited.add(path)


def compute_file_lists(fileops: FileOperations) -> tuple[list[str], list[str]]:
    modified = fileops.edited | fileops.written
    read_only = sorted(fileops.read - modified)
    return read_only, sorted(modified)


def format_file_operations(read_files: list[str], modified_files: list[str]) -> str:
    sections: list[str] = []
    if read_files:
        sections.append("<read-files>\n" + "\n".join(read_files) + "\n</read-files>")
    if modified_files:
        sections.append("<modified-files>\n" + "\n".join(modified_files) + "\n</modified-files>")
    return "\n".join(sections)


def estimate_tokens(messages: list[Any]) -> int:
    """Cheap token estimator: ~4 chars per token. Good enough for budgeting."""
    total = 0
    for m in messages:
        content = getattr(m, "content", None)
        if isinstance(content, str):
            total += max(1, len(content) // 4)
        elif isinstance(content, list):
            for block in content:
                t = getattr(block, "text", None) or getattr(block, "thinking", None) or ""
                total += max(1, len(t) // 4)
                if getattr(block, "type", None) == "toolCall":
                    args = getattr(block, "arguments", None) or {}
                    try:
                        total += max(1, len(str(args)) // 4)
                    except Exception:  # noqa: BLE001
                        pass
    return total


__all__ = [
    "FileOperations",
    "compute_file_lists",
    "create_file_ops",
    "estimate_tokens",
    "extract_file_ops_from_message",
    "format_file_operations",
]
