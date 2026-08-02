"""JSONL session persistence with branching (id/parentId chain).

Python port of a scoped subset of
`vendor/pi-mono-upstream/packages/coding-agent/src/core/session-manager.ts`.

What is preserved
-----------------
- Append-only JSONL file under `{agent_dir}/sessions/`. Filenames are
  ISO-8601 timestamped and include the session id.
- Header entry (`type: session`) at the top containing version, cwd,
  parent_session, and the creation timestamp.
- Entry types: `message`, `branch_summary`, `compaction`, `custom`,
  `custom_message`, `label`, `session_info`.
- `id` / `parent_id` link entries into a DAG; `leaf_id` tracks the current
  tip for appending the next entry.
- Branching: `branch_from(entry_id)` creates a new session whose header
  points at the old file's entry, and whose first replayed entries are
  copied so the new file is fully self-contained up to the branch point.

Two architectural commitments drive every simplification below
--------------------------------------------------------------
1. **Single writer per file.** Exactly one Python process writes to a
   given JSONL at a time. The SDK and print mode are both single-process
   callers; there is no concurrent-writer scenario to defend against.
2. **One file is one linear chain.** Each file is a strict append-only
   list of entries where every ``parent_id`` points at the previous
   entry's ``id``. Branching is expressed as "fork the file" — a new
   file whose header records the original via ``parent_session`` — not
   as multiple children of the same entry inside one file.

What is simplified vs upstream (and which commitment drives it)
---------------------------------------------------------------
- *(driven by #1 — single writer)* No file-level locking and no
  crash-safe atomic renames. ``_append_line`` opens the file in append
  mode, writes, ``flush`` + ``fsync``, and closes. Concurrent appenders
  would interleave lines; we don't have any.
- *(driven by #2 — linear chain)* No tree navigation. ``iter_messages``
  is a single forward pass over ``self._entries``; there is no graph
  walk because the file IS the path from root to leaf.
- *(driven by #2 — linear chain)* ``branch_from`` writes a brand-new
  file containing a deep-copied prefix of the source, instead of
  splicing a sibling chain into the same file. This keeps every file
  trivially flat at the cost of duplicating the prefix on disk.
- *(driven by #1 — single writer)* ``find()`` and ``branch_from`` use
  O(n) linear scans rather than maintaining a ``dict[str, Entry]``
  index, because there is no second writer that could invalidate it
  between calls.
- *(scope, not commitment)* No reader API for labels / session names —
  ``set_label`` / ``set_session_name`` only write. Files round-trip
  without losing data, but no consumer in this port reads those fields
  back yet, so we kept the surface honest.
- *(scope, not commitment)* JSONL keys are ``snake_case``. Upstream
  TypeScript writes ``camelCase`` (``parentId`` etc.); files written by
  one are not readable by the other today. The wire-protocol messages
  inside each entry use Pydantic aliases and would parse either way; it
  is the entry envelope that diverges.
"""

from __future__ import annotations

import json
import os
import uuid
from copy import deepcopy
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Iterator

from pydantic import BaseModel

from ..ai.types import (
    AssistantMessage,
    ToolResultMessage,
    UserMessage,
)
from .config import get_agent_dir
from .defaults import CURRENT_SESSION_VERSION
from .messages import CodingAgentMessage

# ---------------------------------------------------------------------------
# Serialization helpers
# ---------------------------------------------------------------------------


def _now_iso() -> str:
    import datetime as dt

    return dt.datetime.now(dt.timezone.utc).isoformat()


def _message_to_jsonable(m: Any) -> dict[str, Any]:
    if isinstance(m, BaseModel):
        return m.model_dump(mode="json", by_alias=True)
    if isinstance(m, dict):
        return m
    raise TypeError(f"Cannot serialize message of type {type(m).__name__}")


def _message_from_jsonable(data: dict[str, Any]) -> CodingAgentMessage:
    from .messages import (
        BashExecutionMessage,
        BranchSummaryMessage,
        CompactionSummaryMessage,
        CustomMessage,
    )

    role = data.get("role")
    if role == "user":
        return UserMessage.model_validate(data)
    if role == "assistant":
        return AssistantMessage.model_validate(data)
    if role == "toolResult":
        return ToolResultMessage.model_validate(data)
    if role == "bashExecution":
        return BashExecutionMessage.model_validate(data)
    if role == "custom":
        return CustomMessage.model_validate(data)
    if role == "branchSummary":
        return BranchSummaryMessage.model_validate(data)
    if role == "compactionSummary":
        return CompactionSummaryMessage.model_validate(data)
    raise ValueError(f"Unknown message role: {role}")


# ---------------------------------------------------------------------------
# Entry + header dataclasses
# ---------------------------------------------------------------------------


@dataclass
class SessionHeader:
    id: str
    cwd: str
    timestamp: str
    version: int = CURRENT_SESSION_VERSION
    parent_session: str | None = None
    type: str = "session"


@dataclass
class MessageEntry:
    id: str
    parent_id: str | None
    timestamp: str
    message: dict[str, Any]
    type: str = "message"


@dataclass
class BranchSummaryEntry:
    id: str
    parent_id: str | None
    timestamp: str
    from_id: str
    summary: str
    details: Any = None
    from_hook: bool = False
    type: str = "branch_summary"


@dataclass
class CompactionEntry:
    id: str
    parent_id: str | None
    timestamp: str
    summary: str
    first_kept_entry_id: str
    tokens_before: int
    details: Any = None
    from_hook: bool = False
    type: str = "compaction"


@dataclass
class CustomEntry:
    id: str
    parent_id: str | None
    timestamp: str
    custom_type: str
    data: Any = None
    type: str = "custom"


@dataclass
class LabelEntry:
    id: str
    parent_id: str | None
    timestamp: str
    target_id: str
    label: str | None
    type: str = "label"


@dataclass
class SessionInfoEntry:
    id: str
    parent_id: str | None
    timestamp: str
    name: str | None
    type: str = "session_info"


SessionEntry = (
    MessageEntry
    | BranchSummaryEntry
    | CompactionEntry
    | CustomEntry
    | LabelEntry
    | SessionInfoEntry
)


# ---------------------------------------------------------------------------
# Session manager
# ---------------------------------------------------------------------------


class SessionManager:
    """Append-only JSONL session store with a single-branch linear view.

    Not thread-safe — create one per agent instance.
    """

    def __init__(self, *, file_path: str | Path, header: SessionHeader) -> None:
        self._path = str(file_path)
        self._header = header
        self._entries: list[SessionEntry] = []
        self._leaf_id: str | None = None

    # ---- Class-level constructors ---------------------------------------------------

    @classmethod
    def create(
        cls,
        *,
        cwd: str | None = None,
        sessions_dir: str | None = None,
        parent_session: str | None = None,
        session_id: str | None = None,
    ) -> "SessionManager":
        resolved_cwd = cwd or os.getcwd()
        sess_dir = Path(sessions_dir or (get_agent_dir() / "sessions"))
        sess_dir.mkdir(parents=True, exist_ok=True)
        sid = session_id or uuid.uuid4().hex
        ts = _now_iso()
        safe_ts = ts.replace(":", "-")
        path = sess_dir / f"{safe_ts}_{sid}.jsonl"
        header = SessionHeader(
            id=sid, cwd=resolved_cwd, timestamp=ts, parent_session=parent_session
        )
        mgr = cls(file_path=path, header=header)
        mgr._write_header()
        return mgr

    @classmethod
    def open(cls, file_path: str | Path) -> "SessionManager":
        """Reopen an existing session file (read-only until next append)."""
        path = Path(file_path)
        if not path.is_file():
            raise FileNotFoundError(file_path)
        header: SessionHeader | None = None
        entries: list[SessionEntry] = []
        with path.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                obj = json.loads(line)
                if obj.get("type") == "session":
                    header = SessionHeader(
                        id=obj["id"],
                        cwd=obj["cwd"],
                        timestamp=obj["timestamp"],
                        version=obj.get("version", 1),
                        parent_session=obj.get("parent_session"),
                    )
                else:
                    entries.append(_entry_from_json(obj))
        if header is None:
            raise ValueError(f"Session file missing header: {file_path}")
        mgr = cls(file_path=path, header=header)
        mgr._entries = entries
        mgr._leaf_id = entries[-1].id if entries else None
        return mgr

    # ---- Public properties ---------------------------------------------------

    @property
    def path(self) -> str:
        return self._path

    @property
    def id(self) -> str:
        return self._header.id

    @property
    def leaf_id(self) -> str | None:
        return self._leaf_id

    @property
    def header(self) -> SessionHeader:
        return self._header

    @property
    def entries(self) -> list[SessionEntry]:
        return list(self._entries)

    # ---- Writing ------------------------------------------------------------

    def _write_header(self) -> None:
        payload = asdict(self._header)
        self._append_line(payload)

    def _append_line(self, payload: dict[str, Any]) -> None:
        line = json.dumps(payload, ensure_ascii=False)
        with open(self._path, "a", encoding="utf-8") as f:
            f.write(line + "\n")
            f.flush()
            try:
                os.fsync(f.fileno())
            except OSError:
                pass

    def append_message(self, message: CodingAgentMessage) -> MessageEntry:
        entry = MessageEntry(
            id=uuid.uuid4().hex,
            parent_id=self._leaf_id,
            timestamp=_now_iso(),
            message=_message_to_jsonable(message),
        )
        self._entries.append(entry)
        self._append_line(asdict(entry))
        self._leaf_id = entry.id
        return entry

    def append_branch_summary(
        self, *, from_id: str, summary: str, details: Any = None, from_hook: bool = False
    ) -> BranchSummaryEntry:
        entry = BranchSummaryEntry(
            id=uuid.uuid4().hex,
            parent_id=self._leaf_id,
            timestamp=_now_iso(),
            from_id=from_id,
            summary=summary,
            details=details,
            from_hook=from_hook,
        )
        self._entries.append(entry)
        self._append_line(asdict(entry))
        self._leaf_id = entry.id
        return entry

    def append_compaction(
        self,
        *,
        summary: str,
        first_kept_entry_id: str,
        tokens_before: int,
        details: Any = None,
        from_hook: bool = False,
    ) -> CompactionEntry:
        entry = CompactionEntry(
            id=uuid.uuid4().hex,
            parent_id=self._leaf_id,
            timestamp=_now_iso(),
            summary=summary,
            first_kept_entry_id=first_kept_entry_id,
            tokens_before=tokens_before,
            details=details,
            from_hook=from_hook,
        )
        self._entries.append(entry)
        self._append_line(asdict(entry))
        self._leaf_id = entry.id
        return entry

    def append_custom(self, custom_type: str, data: Any = None) -> CustomEntry:
        entry = CustomEntry(
            id=uuid.uuid4().hex,
            parent_id=self._leaf_id,
            timestamp=_now_iso(),
            custom_type=custom_type,
            data=data,
        )
        self._entries.append(entry)
        self._append_line(asdict(entry))
        self._leaf_id = entry.id
        return entry

    def set_label(self, target_id: str, label: str | None) -> LabelEntry:
        entry = LabelEntry(
            id=uuid.uuid4().hex,
            parent_id=self._leaf_id,
            timestamp=_now_iso(),
            target_id=target_id,
            label=label,
        )
        self._entries.append(entry)
        self._append_line(asdict(entry))
        self._leaf_id = entry.id
        return entry

    def set_session_name(self, name: str | None) -> SessionInfoEntry:
        entry = SessionInfoEntry(
            id=uuid.uuid4().hex,
            parent_id=self._leaf_id,
            timestamp=_now_iso(),
            name=name,
        )
        self._entries.append(entry)
        self._append_line(asdict(entry))
        self._leaf_id = entry.id
        return entry

    # ---- Reading / iteration ------------------------------------------------

    def iter_messages(self) -> Iterator[CodingAgentMessage]:
        """Yield messages from the linear chain in order."""
        for e in self._entries:
            if isinstance(e, MessageEntry):
                yield _message_from_jsonable(e.message)

    def messages(self) -> list[CodingAgentMessage]:
        return list(self.iter_messages())

    def find(self, entry_id: str) -> SessionEntry | None:
        for e in self._entries:
            if e.id == entry_id:
                return e
        return None

    # ---- Branching ----------------------------------------------------------

    def branch_from(
        self,
        entry_id: str,
        *,
        sessions_dir: str | None = None,
    ) -> "SessionManager":
        """Fork a new session at `entry_id`.

        The new file copies all entries from the root up to and including
        `entry_id`, with `parent_session` set to the current file. Future
        appends land in the new session.
        """
        idx = None
        for i, e in enumerate(self._entries):
            if e.id == entry_id:
                idx = i
                break
        if idx is None:
            raise KeyError(f"entry {entry_id} not found in session {self._header.id}")

        new_mgr = SessionManager.create(
            cwd=self._header.cwd,
            sessions_dir=sessions_dir,
            parent_session=self._path,
        )
        new_mgr._entries = []
        for src in self._entries[: idx + 1]:
            # Deep-copy so post-fork mutations on either side cannot bleed
            # into the other session's in-memory entry list.
            copy = deepcopy(src)
            new_mgr._entries.append(copy)
            new_mgr._append_line(asdict(copy))
        new_mgr._leaf_id = entry_id
        return new_mgr


def _entry_from_json(obj: dict[str, Any]) -> SessionEntry:
    kind = obj.get("type")
    if kind == "message":
        return MessageEntry(**obj)
    if kind == "branch_summary":
        return BranchSummaryEntry(**obj)
    if kind == "compaction":
        return CompactionEntry(**obj)
    if kind == "custom":
        return CustomEntry(**obj)
    if kind == "label":
        return LabelEntry(**obj)
    if kind == "session_info":
        return SessionInfoEntry(**obj)
    raise ValueError(f"Unknown entry type: {kind}")


__all__ = [
    "BranchSummaryEntry",
    "CompactionEntry",
    "CustomEntry",
    "LabelEntry",
    "MessageEntry",
    "SessionEntry",
    "SessionHeader",
    "SessionInfoEntry",
    "SessionManager",
]
