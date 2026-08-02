"""Context compaction: pluggable strategy interface + default implementation.

Python port of `vendor/pi-mono-upstream/packages/coding-agent/src/core/compaction/*`.

The SDK calls the current `Compactor` before each LLM turn when
`estimated_tokens > target_tokens`. The default strategy keeps the most
recent `keep_tail` messages and replaces earlier messages with a single
`CompactionSummaryMessage` containing a bulleted summary of file ops and
assistant text.

Extensions can install a custom compactor via `pi.on("session_compact",
...)` (observation only) or by swapping the `Compactor` passed to
`create_agent_session` (full control).
"""

from .default import (
    CompactionPreparation,
    CompactionResult,
    Compactor,
    DefaultCompactor,
)
from .utils import (
    FileOperations,
    compute_file_lists,
    create_file_ops,
    estimate_tokens,
    extract_file_ops_from_message,
    format_file_operations,
)

__all__ = [
    "CompactionPreparation",
    "CompactionResult",
    "Compactor",
    "DefaultCompactor",
    "FileOperations",
    "compute_file_lists",
    "create_file_ops",
    "estimate_tokens",
    "extract_file_ops_from_message",
    "format_file_operations",
]
