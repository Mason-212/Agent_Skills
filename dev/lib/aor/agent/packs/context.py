"""Session-scoped execution context for domain pack tools.

Two objects, two lifetimes:

- :class:`SessionContext` — built **once per session** when the adapter is
  created (or when a REST call begins).  It validates ``session_id``, creates
  the workspace directory, and is a natural home for any session-scoped state
  a pack wants to amortise across turns (warm model handle, conversation cache,
  prior-approval flag).

- :class:`PackExecutionContext` — built **once per tool call**.  It wraps a
  ``SessionContext`` and injects the per-turn fields (``tool_call_id``,
  ``signal``, ``on_update``) supplied by the Pi Agent loop.

Tools receive a ``PackExecutionContext`` and access ``session_id`` and
``workspace_dir`` as delegation properties — the API is unchanged for existing
pack tool functions.

## Deployment scope and pre-conditions

This module is designed for **single-process deployments**. The following
assumptions must hold; violating them causes silent data loss or incorrect
multi-turn behavior:

1. **Session ID stability**: ``session_id`` must be the same value for all
   tool calls within a single conversation. If the agent framework generates
   a new session ID per message rather than per conversation, each turn gets
   a different workspace and state persistence silently fails.

2. **No concurrent writes within a session**: workspace files are not
   protected by any lock. Two simultaneous tool calls in the same session
   writing to the same file will race — last writer wins. Tools within a
   session must be called sequentially.

3. **Filesystem durability**: the default workspace root is ``/tmp/edc_sessions``,
   which is cleared on reboot on macOS and on many Linux configurations.
   Workspace state does not survive process restarts. Do not rely on workspace
   files for durable storage.

4. **Single-node only**: if the pack is deployed behind a load balancer,
   turn 1 and turn 2 may land on different nodes with different ``/tmp``
   filesystems. Workspace files will not be shared. Override
   ``EDC_SESSION_WORKSPACE_ROOT`` to a shared mount (e.g. NFS, EFS) for
   multi-node deployments.

5. **Caller-owned cleanup**: ``cleanup()`` and ``cleanup_session_workspace()``
   are not called automatically. In production, configure a session-end hook
   or a TTL reaper to reclaim disk space; otherwise ``/tmp/edc_sessions``
   grows without bound at scale.
"""

from __future__ import annotations

import logging
import os
import shutil
import tempfile
import unicodedata
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Optional

_logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from agent.pi.core.types import AbortSignal, AgentToolUpdateCallback


# Use tempfile.gettempdir() as the base rather than a hardcoded "/tmp" path.
# Publicly writable directories (/tmp) are safe only when the subdirectory is
# created with owner-only permissions (0o700) so other users on the same host
# cannot read or enumerate session files. See _SESSION_DIR_MODE below.
DEFAULT_SESSION_WORKSPACE_ROOT = Path(
    os.environ.get("EDC_SESSION_WORKSPACE_ROOT", str(Path(tempfile.gettempdir()) / "edc_sessions"))
)

# Owner-only permissions for all session workspace directories.
# Prevents other local users from reading or writing session files in a
# shared /tmp on multi-user hosts.
_SESSION_DIR_MODE = 0o700

_UNSAFE_PATH_CHARS = frozenset("/\\\x00")

# Allowlist: printable ASCII minus the filesystem-unsafe characters.
# This intentionally excludes all non-ASCII Unicode to prevent normalization
# attacks (e.g. U+FF0F FULLWIDTH SOLIDUS → '/', U+2215 DIVISION SLASH → '/').
# Valid characters: letters, digits, hyphen, underscore, and at-sign
# (for tenant/org prefixes).
_SESSION_ID_SAFE_CHARS = frozenset(
    "abcdefghijklmnopqrstuvwxyz"
    "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    "0123456789"
    "-_@"
)


def _validate_session_id(session_id: str) -> None:
    """Raise ValueError if session_id is unsafe to use as a path component.

    Applies Unicode NFC normalization first so that visually similar characters
    (e.g. U+FF0F FULLWIDTH SOLIDUS, which normalizes to U+002F '/') are caught
    before the character allowlist is checked.

    Rejects:
    - empty strings
    - the reserved path components ``"."`` and ``".."``
    - strings containing ``/``, ``\\``, or null bytes (post-normalization)
    - any non-ASCII or non-allowlisted character, blocking Unicode lookalike
      attacks (fullwidth solidus, division slash, URL-encoded sequences, etc.)

    Allowed characters: ``A-Z``, ``a-z``, ``0-9``, ``-``, ``_``, ``@``.
    """
    # Normalize to NFC so composed forms (e.g. fullwidth solidus U+FF0F) are
    # reduced before the character checks run.
    normalized = unicodedata.normalize("NFC", session_id)

    if not normalized:
        raise ValueError("session_id must not be empty")
    if normalized in (".", ".."):
        raise ValueError(f"session_id must not be {session_id!r}")
    if any(c in normalized for c in _UNSAFE_PATH_CHARS):
        raise ValueError(
            f"session_id contains unsafe path characters: {session_id!r}. "
            "Remove '/', '\\\\', and null bytes."
        )
    invalid = frozenset(normalized) - _SESSION_ID_SAFE_CHARS
    if invalid:
        sorted_invalid = sorted(
            f"U+{ord(c):04X} ({unicodedata.name(c, 'UNKNOWN')})" for c in invalid
        )
        raise ValueError(
            f"session_id contains disallowed characters: {session_id!r}. "
            f"Only ASCII letters, digits, hyphens, underscores, and '@' are permitted. "
            f"Rejected: {', '.join(sorted_invalid)}"
        )


@dataclass
class SessionContext:
    """Session-scoped state built **once** when the adapter (or REST call) starts.

    Owns validation, workspace creation, and cleanup.  A natural home for any
    state a pack wants to amortise across turns — warm model handle,
    conversation cache, prior-approval flag — stored as ordinary attributes.

    Attributes:
        session_id: Validated session identifier.
        workspace_dir: Isolated directory for this session's files.
                      Created eagerly on construction.
                      Format: ``{workspace_root}/{session_id}/``.
    """

    session_id: str
    workspace_dir: Path = field(init=False)
    _workspace_root: Path = field(default=DEFAULT_SESSION_WORKSPACE_ROOT, repr=False)

    def __post_init__(self) -> None:
        _validate_session_id(self.session_id)
        self.workspace_dir = self._workspace_root / self.session_id
        try:
            # mode=0o700: owner-only access so other local users on a shared
            # host (e.g. a multi-user /tmp) cannot read or write session files.
            self.workspace_dir.mkdir(mode=_SESSION_DIR_MODE, parents=True, exist_ok=True)
        except OSError as exc:
            _logger.error(
                "pack context: failed to create workspace directory "
                "[session_id=%s workspace_dir=%s]: %s",
                self.session_id,
                self.workspace_dir,
                exc,
            )
            raise OSError(
                f"Cannot create workspace for session '{self.session_id}' "
                f"at '{self.workspace_dir}': {exc}"
            ) from exc

    def for_call(
        self,
        tool_call_id: str,
        signal: Optional["AbortSignal"] = None,
        on_update: Optional["AgentToolUpdateCallback"] = None,
    ) -> "PackExecutionContext":
        """Stamp per-turn fields onto this session, returning a PackExecutionContext."""
        return PackExecutionContext(
            _session=self,
            tool_call_id=tool_call_id,
            signal=signal,
            on_update=on_update,
        )

    def cleanup(self) -> None:
        """Delete the session workspace directory and all its contents.

        Call this when the session ends to reclaim disk space. Safe to call
        multiple times — no-op if the workspace has already been removed.

        **Production note**: cleanup is caller-responsibility. If a session
        ends abnormally (crash, timeout, unhandled exception), cleanup will
        not be called automatically. At scale, uncleaned workspaces cause
        unbounded disk growth in ``EDC_SESSION_WORKSPACE_ROOT``. Consider
        a TTL reaper (e.g., a cron that deletes directories older than N hours)
        or a session-end hook in the agent framework to ensure cleanup runs.
        """
        if not self.workspace_dir.exists():
            _logger.debug("cleanup() called but workspace already absent: %s", self.workspace_dir)
            return
        try:
            shutil.rmtree(self.workspace_dir)
            _logger.debug("Cleaned up session workspace: %s", self.workspace_dir)
        except OSError as exc:
            _logger.error(
                "pack context: failed to remove workspace directory "
                "[session_id=%s workspace_dir=%s]: %s",
                self.session_id,
                self.workspace_dir,
                exc,
            )
            raise RuntimeError(
                f"Cleanup failed for session '{self.session_id}' "
                f"at '{self.workspace_dir}': {exc}"
            ) from exc


@dataclass
class PackExecutionContext:
    """Per-tool-call context passed to every pack tool invocation.

    Wraps a :class:`SessionContext` (built once per session) and injects the
    per-turn fields supplied by the Pi Agent loop.  ``session_id`` and
    ``workspace_dir`` are delegation properties — pack tool functions that
    access them need no changes.

    Attributes:
        session: The session-scoped context (shared across all turns).
        tool_call_id: Unique ID for this specific tool invocation.
                     Matches the LLM tool-call ID so results can be correlated.
        signal: Cancellation signal. Set when the user or framework requests
               abort. None for REST API callers (no cancellation support).
        on_update: Streaming callback for partial progress updates. Tools call
                  this to stream intermediate results to the UI. None for REST
                  API callers (no streaming support).
    """

    _session: SessionContext
    tool_call_id: str
    signal: Optional["AbortSignal"] = None
    on_update: Optional["AgentToolUpdateCallback"] = None

    # --- delegation properties (backward-compatible API) ---

    @property
    def session_id(self) -> str:
        """Session identifier (delegated from SessionContext)."""
        return self._session.session_id

    @property
    def workspace_dir(self) -> Path:
        """Isolated workspace directory (delegated from SessionContext)."""
        return self._session.workspace_dir

    @property
    def is_cancelled(self) -> bool:
        """Whether the caller has requested cancellation.

        Always ``False`` for REST API contexts (signal is None).
        """
        return self.signal is not None and self.signal.aborted

    def cleanup(self) -> None:
        """Delegate cleanup to the underlying SessionContext."""
        self._session.cleanup()

    # --- convenience factories (kept for REST callers and tests) ---

    @classmethod
    def for_session(
        cls,
        session_id: str,
        tool_call_id: str,
        signal: Optional["AbortSignal"] = None,
        on_update: Optional["AgentToolUpdateCallback"] = None,
        workspace_root: Path = DEFAULT_SESSION_WORKSPACE_ROOT,
    ) -> "PackExecutionContext":
        """Create a context for a conversational (AgentSession) tool call.

        Builds a :class:`SessionContext` and stamps per-turn fields.  Prefer
        :func:`create_tool_adapter` for multi-turn use — it builds the
        ``SessionContext`` once at adapter-creation time and re-uses it across
        all turns, avoiding repeated validation and ``mkdir`` calls.

        Args:
            session_id: From ``session_manager.header.id``. **Must be stable
                       for the lifetime of the conversation** — if the framework
                       rotates this value per message rather than per session,
                       each turn will receive a different workspace and
                       multi-turn state persistence will silently fail.
            tool_call_id: From the LLM tool-call invocation.
            signal: Abort signal from the agent loop (optional).
            on_update: Streaming callback from the agent loop (optional).
            workspace_root: Root for all session workspaces.
                           Default: ``/tmp/edc_sessions``.
        """
        session = SessionContext(session_id=session_id, _workspace_root=workspace_root)
        return cls(_session=session, tool_call_id=tool_call_id, signal=signal, on_update=on_update)

    @classmethod
    def for_rest(
        cls,
        tenant_id: str,
        tool_call_id: str,
        workspace_root: Path = DEFAULT_SESSION_WORKSPACE_ROOT,
    ) -> "PackExecutionContext":
        """Create a context for a direct REST API invocation.

        Uses ``tenant_id`` as the session identifier. No cancellation or
        streaming support (signal and on_update are None). The ``tenant_id``
        is validated before the workspace path is composed.

        Args:
            tenant_id: Tenant identifier from the REST request.
            tool_call_id: Caller-supplied correlation ID (e.g., request UUID).
            workspace_root: Root for all session workspaces.
                           Default: ``/tmp/edc_sessions``.

        Returns:
            PackExecutionContext with workspace created.
        """
        session = SessionContext(session_id=tenant_id, _workspace_root=workspace_root)
        return cls(_session=session, tool_call_id=tool_call_id, signal=None, on_update=None)


def cleanup_session_workspace(
    session_id: str,
    workspace_root: Path = DEFAULT_SESSION_WORKSPACE_ROOT,
) -> None:
    """Delete a session's workspace directory by session ID.

    Convenience function for callers that don't hold a ``PackExecutionContext``
    or ``SessionContext`` at cleanup time (e.g., a session-end hook or a TTL
    reaper).

    **Production note**: this function should be wired into a session-end hook
    in the agent framework, or called by a TTL reaper process. Workspaces are
    not cleaned up automatically; uncleaned sessions cause unbounded disk growth
    in ``EDC_SESSION_WORKSPACE_ROOT`` at scale.

    Args:
        session_id: Session identifier whose workspace should be removed.
        workspace_root: Root directory for session workspaces.
                       Default: ``/tmp/edc_sessions``.

    Example::

        # In a session-end handler:
        cleanup_session_workspace(session_manager.header.id)
    """
    _validate_session_id(session_id)
    workspace_dir = workspace_root / session_id
    if not workspace_dir.exists():
        _logger.debug("cleanup_session_workspace() called but workspace absent: %s", workspace_dir)
        return
    try:
        shutil.rmtree(workspace_dir)
        _logger.debug("Cleaned up session workspace: %s", workspace_dir)
    except OSError as exc:
        _logger.error(
            "pack context: failed to remove workspace directory "
            "[session_id=%s workspace_dir=%s]: %s",
            session_id,
            workspace_dir,
            exc,
        )
        raise RuntimeError(
            f"Cleanup failed for session '{session_id}' "
            f"at '{workspace_dir}': {exc}"
        ) from exc
