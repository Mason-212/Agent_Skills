"""Domain pack base interfaces and supporting types.

This module defines the core contract that all domain packs must implement.
A domain pack is a self-contained plugin that provides one ML capability
(forecasting, scoring, classification, etc.) through a standardized interface.
"""

from __future__ import annotations

import logging
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import TYPE_CHECKING, Any, List, Optional, Protocol

from agent.packs.skill_provider import SkillProvider  # noqa: F401 — re-exported

if TYPE_CHECKING:
    from agent.packs.orchestrator import WorkflowDirectOutcome
    from agent.pi.core.types import AgentTool  # type: ignore[import]

    # Forward references for optional extension points not yet implemented.
    # These will be replaced with real imports as each subsystem is built.
    class ContextExtractor(Protocol): ...      # agent.context
    class CompactionStrategy(Protocol): ...    # agent.memory
    class Verifier(Protocol): ...              # agent.verification
    class PackEvaluator(Protocol): ...         # agent.evaluation
    class ApprovalPolicy(Protocol): ...        # agent.approval


class PackWorkflow(Protocol):
    """Shared workflow wrapper contract used by BoundDomainPack.

    All wrappers expose ``run()`` and ``supports_resume``. Callers must
    check ``supports_resume`` before calling ``resume()``; wrappers that
    do not support it will raise ``NotImplementedError``.

    Return type of ``run()`` depends on the concrete implementation:
    - ``PackWorkflowWrapper`` returns whatever the callable returns.
    - ``PackWorkflowOrchestrator`` returns a ``WorkflowOutcome``
      (``Completed | Paused | Failed``).

    ``_execute_workflow`` and ``_resume_workflow`` in ``BoundDomainPack``
    unwrap ``WorkflowOutcome`` transparently so ``run_direct()`` and
    ``resume_direct()`` always call ``build_result()`` with raw output.
    """

    @property
    def supports_resume(self) -> bool:
        """Whether this wrapper supports interrupt/resume via checkpoints."""
        ...

    async def run(self, request: Any) -> Any:
        """Execute a workflow request."""
        ...

    async def resume(self, checkpoint: Any, response: Any) -> Any:
        """Resume a previously paused workflow request.

        Raises:
            NotImplementedError: If ``supports_resume`` is ``False``.
        """
        ...


@dataclass
class PackDescriptor:
    """Pack metadata and identification.

    Attributes:
        id: Unique identifier (e.g., "moirai_forecast")
        name: Human-readable name
        version: Semantic version string
        description: Brief description of capability
    """
    id: str
    name: str
    version: str
    description: str = ""


@dataclass
class ExecutionContext:
    """Execution metadata passed to pack methods.

    Attributes:
        request_id: Unique identifier for this execution
        tenant_id: Tenant identifier for isolation
        timestamp: When execution started
        metadata: Additional context (e.g., user info, trace IDs)
    """
    request_id: str
    tenant_id: str
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class PackResult:
    """Standardized result envelope from pack execution.

    Attributes:
        pack_id: Identifier of pack that produced this result
        request_id: Execution request identifier
        output: Pack-specific output data
        metadata: Additional result metadata (timing, model version, etc.)
        errors: List of error messages if execution partially failed
    """
    pack_id: str
    request_id: str
    output: Any
    metadata: dict[str, Any] = field(default_factory=dict)
    errors: list[str] = field(default_factory=list)


@dataclass
class HealthStatus:
    """Health check result.

    Attributes:
        healthy: Whether pack is ready to handle requests
        message: Human-readable status message
        details: Additional diagnostic information
    """
    healthy: bool
    message: str = ""
    details: dict[str, Any] = field(default_factory=dict)


class BoundDomainPack(ABC):
    """Domain pack interface for ML capability integration.

    A domain pack is a self-contained plugin that provides one ML capability
    through a standardized interface. Packs integrate with the EDC agent
    framework via two independent entry points:

    - **Workflow entry point** (``run_direct`` / ``resume_direct``): stateless.
      No ``session_id``, no workspace. Each call is independent. Use for REST
      endpoints, batch jobs, and scheduled tasks.

    - **Tool entry point** (``get_tools`` → ``AgentTool.execute``): stateful
      per conversation. Each ``session_id`` gets an isolated workspace directory
      for large artifacts (DataFrames, tensors) that cannot round-trip through
      the LLM context window. Use for multi-turn ``AgentSession`` conversations.

    Multi-session safety rules (all three must hold):

    1. **Pack-instance state must be read-only.** Resources on ``self``
       (models, configs) are shared across all concurrent sessions. Load them
       once in ``_open_impl()`` and never mutate them afterward.

    2. **Never hold a long-lived AgentSession on the pack instance.**
       ``AgentSession`` carries mutable message history. Storing one on ``self``
       and reusing it across ``run_direct()`` calls causes cross-session leakage
       — Alice's data appears in Bob's LLM context with no error raised.
       Any ``AgentSession`` used inside a workflow node must be constructed fresh
       per call and shut down before the node returns.

    3. **Workspace writes must be session-scoped.** Always write artifacts to
       ``ctx.workspace_dir``, never to a shared path on the pack instance. Two
       concurrent sessions writing to the same file will race silently.

    Lifecycle:
        1. Pack instantiated with workspace directory
        2. ``open()`` called once to load shared resources
        3. Pack serves multiple concurrent sessions
        4. ``close()`` called once to release resources
    """

    def __init__(self, workspace_dir: Path):
        """Initialize pack with workspace directory.

        Args:
            workspace_dir: Per-pack directory for model cache, temp files.
                          Default: /var/edc/packs/{pack_id}/
        """
        self._workspace_dir = workspace_dir
        self._logger: Optional[logging.Logger] = None
        self._opened: bool = False
        # Keyed by session_id. get_tools() populates this; _build_tools() is
        # called at most once per session_id so SessionContext / mkdir never
        # run more than once regardless of how often the host calls get_tools().
        self._tools_cache: dict[str, "List[AgentTool]"] = {}

    @property
    def workspace_dir(self) -> Path:
        """Pack workspace directory for persistent storage."""
        return self._workspace_dir

    @property
    def is_open(self) -> bool:
        """Whether open() has been called and close() has not yet been called."""
        return self._opened

    @property
    def logger(self) -> logging.Logger:
        """Pack-scoped logger following edc-python conventions.

        Logger name format: edc.pack.{pack_id}
        This allows per-pack log level configuration.
        """
        if self._logger is None:
            self._logger = logging.getLogger(f"edc.pack.{self.descriptor.id}")
        return self._logger

    # ---- Required Methods ----

    @property
    @abstractmethod
    def descriptor(self) -> PackDescriptor:
        """Pack metadata (id, name, version).

        Returns:
            PackDescriptor with pack identification
        """
        ...

    async def open(self) -> None:
        """Initialize resources (load models, connect to services).

        Called once when pack is loaded. Models/resources loaded here
        are shared across all sessions.

        On failure: callers must invoke close() in a finally block for cleanup.

        This method is idempotent. The base class owns `is_open` lifecycle
        state; subclasses implement the resource allocation in `_open_impl()`.
        """
        if self._opened:
            return
        await self._open_impl()
        self._opened = True

    def get_workflow_wrapper(self) -> "Optional[PackWorkflow]":
        """Get workflow wrapper for this pack, or ``None`` for tools-only packs.

        Defines the execution flow: validation → inference → post-processing.
        The workflow is **stateless** — it has no ``session_id`` and no
        workspace. Each ``run_direct()`` / ``resume_direct()`` call is
        independent.

        Override to expose a workflow-driven execution path (single async
        callable or multi-node graph). Tools-only packs (``ToolPack``,
        model-driven packs) can leave this unimplemented; ``run_direct`` /
        ``resume_direct`` will then raise ``NotImplementedError``.

        If a workflow node needs LLM-assisted reasoning via ``AgentSession``,
        construct it **fresh inside the node callable** and shut it down before
        the callable returns. Never store an ``AgentSession`` on ``self`` and
        reuse it here — doing so causes cross-call leakage where one caller's
        message history bleeds into the next caller's context (see class
        docstring rule 2).

        Returns:
            Workflow wrapper implementing the ``PackWorkflow`` protocol,
            or ``None`` if the pack has no workflow path.

        Example (multi-node graph workflow):
            def get_workflow_wrapper(self) -> PackWorkflowOrchestrator:
                from orchestrator import WorkflowBuilder, WorkflowNode, CallableExecutor
                from agent.packs.orchestrator import PackWorkflowOrchestrator

                workflow = (
                    WorkflowBuilder("forecast")
                    .add_node(WorkflowNode(name="validate", executor=CallableExecutor(self._validate_input), allowed_next_nodes=("infer",)))
                    .add_node(WorkflowNode(name="infer", executor=CallableExecutor(self._run_inference), allowed_next_nodes=()))
                    .set_start("validate")
                    .build()
                )
                return PackWorkflowOrchestrator(workflow)

        Example (simple single-function workflow):
            def get_workflow_wrapper(self) -> PackWorkflowWrapper:
                from agent.packs.orchestrator import PackWorkflowWrapper

                return PackWorkflowWrapper(self._run_workflow)
        """
        return None

    @abstractmethod
    def build_result(
        self,
        orchestrator_output: Any,
        context: ExecutionContext
    ) -> PackResult:
        """Format orchestrator output as standard result envelope.

        Args:
            orchestrator_output: Final output from orchestrator.run()
            context: Execution metadata (request_id, timing, tenant_id)

        Returns:
            PackResult with standardized format

        Example:
            def build_result(self, output, context):
                return PackResult(
                    pack_id=self.descriptor.id,
                    request_id=context.request_id,
                    output=output,
                    metadata={"model_version": "1.0"}
                )
        """
        ...

    async def close(self) -> None:
        """Clean up resources (unload models, close connections).

        Must handle partial initialization (open() may have failed halfway).
        Always call via a finally block to ensure cleanup even after open() failure.

        This method is idempotent. It flips ``_opened`` to ``False`` before
        calling ``_close_impl()``, which prevents *new* ``run_direct()`` /
        ``resume_direct()`` calls from entering once shutdown begins.

        **Concurrency caveat**: the ``_opened`` flag is not a lock. A
        ``run_direct()`` call that has already passed the guard and is
        executing inside ``_execute_workflow`` will continue concurrently
        with ``_close_impl()``. Pack implementations that hold shared
        mutable state (models, DB connections) must coordinate their own
        shutdown safety if concurrent in-flight calls are possible.
        """
        if not self._opened:
            return
        self._opened = False
        await self._close_impl()

    @abstractmethod
    async def _open_impl(self) -> None:
        """Allocate pack resources; called by `open()` on first transition.

        Intentionally ``async`` so implementations can do real I/O (model
        download, service connection). A sync body is fine — just omit any
        ``await`` expressions; the coroutine overhead is negligible.
        """
        ...

    @abstractmethod
    async def _close_impl(self) -> None:
        """Release resources allocated by `_open_impl()`; called by `close()` once.

        Intentionally ``async`` for the same reason as ``_open_impl`` — future
        implementations may need to flush buffers or close network connections.
        A sync body (e.g. ``self._model = None``) is fine.
        """
        ...

    # ---- Convenience Methods (concrete defaults) ----

    async def run_direct(self, request: Any) -> "WorkflowDirectOutcome":
        """Direct invocation entry point — stateless, no session concept.

        Each call is fully independent: no ``session_id``, no workspace, no
        shared conversation state. This is the correct entry point for REST
        endpoints, batch jobs, and scheduled tasks.

        If the workflow internally spins up an ``AgentSession`` for LLM-assisted
        reasoning, that session **must** be constructed fresh inside the workflow
        callable and shut down before it returns. Storing an ``AgentSession`` on
        the pack instance and reusing it here causes cross-call leakage (see
        class docstring rule 2).

        Args:
            request: Pack-specific request payload passed to the workflow.

        Returns:
            ``WorkflowCompleted`` — workflow finished; access result via
            ``outcome.result`` (a ``PackResult``).

            ``WorkflowPaused`` — workflow hit an interrupt and is waiting for
            human input. This is **expected control flow**, not an error. Pass
            ``outcome.checkpoint`` to ``resume_direct()`` to continue::

                outcome = await pack.run_direct(request)
                while isinstance(outcome, WorkflowPaused):
                    response = await ask_user(outcome.interrupts)
                    outcome = await pack.resume_direct(
                        outcome.checkpoint, response, request
                    )
                result = outcome.result

        Raises:
            RuntimeError: If called before ``open()`` or after ``close()``.
            NotImplementedError: If the pack does not expose a workflow
                (i.e. ``get_workflow_wrapper()`` returns ``None``).
                Use ``get_tools(session_id)`` for tools-only packs.
            WorkflowFailedError: If the workflow reaches a terminal failure.
                Carries ``payload`` and ``reason`` attributes for diagnostics.
        """
        if not self._opened:
            raise RuntimeError(
                f"Pack '{self.descriptor.id}' is not open. "
                "Call await pack.open() before run_direct()."
            )
        if self.get_workflow_wrapper() is None:
            raise NotImplementedError(
                f"Pack '{self.descriptor.id}' does not expose a workflow. "
                "Use get_tools(session_id) for tools-only packs."
            )
        context = self._build_execution_context(request)
        return await self._execute_workflow(request, context)

    async def _execute_workflow(
        self, request: Any, context: ExecutionContext
    ) -> "WorkflowDirectOutcome":
        """Execute the workflow wrapper and return a pack-layer outcome.

        ``Completed`` → ``WorkflowCompleted`` (wraps the built ``PackResult``).
        ``Paused``    → ``WorkflowPaused`` (return value, not exception — expected
                        control flow that APM/retry decorators must not intercept).
        ``Failed``    → raises ``WorkflowFailedError`` (genuine error).

        Plain callable wrappers (``PackWorkflowWrapper``) return raw output
        directly; it is wrapped in ``WorkflowCompleted``.

        Subclasses may override to thread ``context`` into workflow nodes.
        """
        from agent.packs.orchestrator import (
            Completed,
            Failed,
            Paused,
            WorkflowCompleted,
            WorkflowFailedError,
            WorkflowPaused,
        )

        wrapper = self.get_workflow_wrapper()
        if wrapper is None:
            raise NotImplementedError(
                f"Pack '{self.descriptor.id}' does not expose a workflow."
            )
        result = await wrapper.run(request)
        if isinstance(result, Paused):
            return WorkflowPaused(
                pack_id=self.descriptor.id,
                checkpoint=result.checkpoint,
                interrupts=result.interrupts,
            )
        if isinstance(result, Failed):
            raise WorkflowFailedError(
                pack_id=self.descriptor.id,
                payload=result.payload,
                reason=result.reason,
            )
        raw = result.output if isinstance(result, Completed) else result
        return WorkflowCompleted(result=self.build_result(raw, context))

    def _build_execution_context(self, request: Any) -> ExecutionContext:
        """Construct execution context for direct invocation.

        Default behavior pulls `request_id` and `tenant_id` from a mapping-like
        request body or an object-level `metadata` mapping when available, and
        generates stable fallback values when absent.
        """
        metadata: dict[str, Any] = {}
        request_id: str | None = None
        tenant_id: str | None = None

        if isinstance(request, dict):
            request_id = _as_non_empty_str(request.get("request_id"))
            tenant_id = _as_non_empty_str(request.get("tenant_id"))
            request_meta = request.get("metadata")
            if isinstance(request_meta, dict):
                metadata = dict(request_meta)
        else:
            request_meta = getattr(request, "metadata", None)
            if isinstance(request_meta, dict):
                metadata = dict(request_meta)
            request_id = _as_non_empty_str(getattr(request, "request_id", None))
            tenant_id = _as_non_empty_str(getattr(request, "tenant_id", None))

        if request_id is None:
            request_id = _as_non_empty_str(metadata.get("request_id"))
        if tenant_id is None:
            tenant_id = _as_non_empty_str(metadata.get("tenant_id"))

        if request_id is None:
            request_id = f"req-{uuid.uuid4()}"
        if tenant_id is None:
            tenant_id = "unknown-tenant"

        return ExecutionContext(
            request_id=request_id,
            tenant_id=tenant_id,
            metadata=metadata,
        )

    async def resume_direct(
        self, checkpoint: Any, response: Any, request: Any
    ) -> "WorkflowDirectOutcome":
        """Direct resume entry point for interrupted workflows.

        Use this after ``run_direct()`` (or a previous ``resume_direct()``)
        returns a ``WorkflowPaused`` outcome.

        If the resumed workflow pauses **again** (multi-pause workflows),
        returns another ``WorkflowPaused``. Use a flat loop::

            outcome = await pack.run_direct(request)
            while isinstance(outcome, WorkflowPaused):
                response = await ask_user(outcome.interrupts)
                outcome = await pack.resume_direct(
                    outcome.checkpoint, response, request
                )
            result = outcome.result   # WorkflowCompleted

        Args:
            checkpoint: ``WorkflowPaused.checkpoint`` from a previous call.
            response: Caller-provided response used to continue the workflow.
            request: Original or reconstructed request used to rebuild context.
                    Pass the same request as the original ``run_direct()`` call
                    to preserve ``request_id``, ``tenant_id``, and ``metadata``.

        Returns:
            ``WorkflowCompleted`` — workflow finished.
            ``WorkflowPaused`` — workflow paused again; keep looping.

        Raises:
            RuntimeError: If called before ``open()`` or after ``close()``.
            WorkflowFailedError: If the resumed workflow reaches a terminal failure.
            NotImplementedError: If the workflow wrapper does not support resume.
        """
        if not self._opened:
            raise RuntimeError(
                f"Pack '{self.descriptor.id}' is not open. "
                "Call await pack.open() before resume_direct()."
            )
        wrapper = self.get_workflow_wrapper()
        if wrapper is None:
            raise NotImplementedError(
                f"Pack '{self.descriptor.id}' does not expose a workflow. "
                "Use get_tools(session_id) for tools-only packs."
            )
        if not wrapper.supports_resume:
            raise NotImplementedError(
                f"Pack '{self.descriptor.id}': the active workflow wrapper "
                f"({type(wrapper).__name__}) does not support interrupt/resume. "
                "Use PackWorkflowOrchestrator with a WorkflowSpec to enable resume."
            )
        context = self._build_execution_context(request)
        return await self._resume_workflow(checkpoint, response, context)

    async def _resume_workflow(
        self, checkpoint: Any, response: Any, context: ExecutionContext
    ) -> "WorkflowDirectOutcome":
        """Resume the workflow wrapper and return a pack-layer outcome.

        Mirrors ``_execute_workflow``: ``Paused`` → ``WorkflowPaused`` return
        value, ``Failed`` → ``WorkflowFailedError`` exception.

        Subclasses may override to thread context into resumed nodes.
        """
        from agent.packs.orchestrator import (
            Completed,
            Failed,
            Paused,
            WorkflowCompleted,
            WorkflowFailedError,
            WorkflowPaused,
        )

        wrapper = self.get_workflow_wrapper()
        if wrapper is None:
            raise NotImplementedError(
                f"Pack '{self.descriptor.id}' does not expose a workflow."
            )
        result = await wrapper.resume(checkpoint, response)
        if isinstance(result, Paused):
            return WorkflowPaused(
                pack_id=self.descriptor.id,
                checkpoint=result.checkpoint,
                interrupts=result.interrupts,
            )
        if isinstance(result, Failed):
            raise WorkflowFailedError(
                pack_id=self.descriptor.id,
                payload=result.payload,
                reason=result.reason,
            )
        raw = result.output if isinstance(result, Completed) else result
        return WorkflowCompleted(result=self.build_result(raw, context))

    # ---- Optional Methods (defaults provided) ----

    def get_tools(self, session_id: Optional[str] = None) -> "List[AgentTool]":
        """Return the cached tool list for ``session_id``.

        This method is **not** intended to be overridden. It owns the
        session → tool-list cache so that :func:`_build_tools` (and
        therefore :func:`~agent.packs.adapter.create_tool_adapter`)
        is called at most once per ``session_id``, regardless of how many
        times the host calls ``get_tools()``.

        Override :func:`_build_tools` to provide pack-specific tools.

        **Host wiring contract**: the host must derive ``session_id`` once from
        a durable source (e.g. ``SessionManager.create().header.id`` or a
        conversation ID from its own database) and pass the **same value** to
        both ``pack.get_tools(session_id=...)`` and the ``SessionManager`` that
        keys the Pi Agent JSONL. This ensures the two parallel stores — the pack
        workspace and the LLM conversation history — share the same identifier
        and can be correlated for debugging.

        Args:
            session_id: Host-supplied stable session identifier for this
                       conversation. ``None`` for non-conversational callers
                       (e.g. REST) — returns an empty list without calling
                       ``_build_tools``.

        Returns:
            Cached list of AgentTool instances for the session.
        """
        if session_id is None:
            return []
        if session_id not in self._tools_cache:
            self._tools_cache[session_id] = self._build_tools(session_id)
        return list(self._tools_cache[session_id])

    def _build_tools(self, session_id: str) -> "List[AgentTool]":
        """Build the tool list for a new session. Called **once per session_id**.

        Override this method to provide pack-specific tools. The base class
        ``get_tools()`` caches the result and guarantees this is called exactly
        once per ``session_id`` — so it is safe to call
        :func:`~agent.packs.adapter.create_tool_adapter` here without
        any additional caching. The resulting ``SessionContext`` and workspace
        directory are created exactly once per conversation.

        ``session_id`` is always a non-empty, validated string — ``get_tools()``
        filters out ``None`` before reaching here. It is the **same identifier**
        the host uses to key the Pi Agent ``SessionManager`` JSONL, forming the
        shared key between the two parallel stores (workspace and LLM history).

        **Workspace writes**: inside tool functions, always write artifacts to
        ``ctx.workspace_dir``. Never write to a path derived from ``self`` —
        two concurrent sessions would race silently (see class docstring rule 3).

        Args:
            session_id: Host-supplied stable identifier for this conversation.

        Returns:
            List of AgentTool instances. Default: empty list.

        Example::

            from agent.packs.adapter import create_tool_adapter

            def _build_tools(self, session_id: str) -> list[AgentTool]:
                async def forecast_tool(ctx: PackExecutionContext, args: dict):
                    # self._model is shared read-only — safe
                    result = await self._model.forecast(args["data"])
                    # write to session-isolated workspace — never to self.*
                    import json
                    (ctx.workspace_dir / "forecast.json").write_text(json.dumps(result))
                    return AgentToolResult(output=result["summary"])

                return [
                    AgentTool(
                        name="forecast_revenue",
                        label="Forecast Revenue",
                        description="Generate revenue forecast",
                        parameters={"data": "dict"},
                        execute=create_tool_adapter(forecast_tool, session_id),
                    )
                ]
        """
        return []

    def evict_session(self, session_id: str) -> None:
        """Remove the cached tool list for ``session_id``.

        Call this when a conversation ends so the cache does not hold stale
        ``AgentTool`` closures (and their ``SessionContext`` references)
        indefinitely. Pair with
        :func:`~agent.packs.context.cleanup_session_workspace` to also
        delete the workspace directory::

            pack.evict_session(session_id)
            cleanup_session_workspace(session_id)

        The next ``get_tools(session_id)`` call after eviction will invoke
        ``_build_tools`` again, creating a fresh ``SessionContext`` and workspace.

        Safe to call with an unknown ``session_id`` — no-op if not cached.

        Args:
            session_id: Session identifier to evict.
        """
        self._tools_cache.pop(session_id, None)

    def get_skill_provider(self) -> "Optional[SkillProvider]":
        """Get pack-specific skill provider for agent sessions.

        Override to expose pack-authored markdown SKILL.md files to the Pi
        Agent's <available_skills> block.  Use PackSkillProvider for the
        standard layout where skills/ lives beside the pack's __init__.py.

        Returns:
            SkillProvider instance or None. Default: None (no skills).

        Example::

            from agent.packs.skill_provider import PackSkillProvider

            def get_skill_provider(self):
                return PackSkillProvider(Path(__file__).parent / "skills")
        """
        return None

    def get_context_extractor(self) -> "Optional[ContextExtractor]":
        """Get context extractor for this pack.

        Extracts domain-specific context from requests to guide agent behavior.

        Returns:
            ContextExtractor instance or None. Default: None.
        """
        return None

    def get_compaction_strategy(self) -> "Optional[CompactionStrategy]":
        """Get context compaction strategy for long conversations.

        Controls how conversation history is summarized when it exceeds
        the model's context window.

        Returns:
            CompactionStrategy instance or None. Default: framework default.
        """
        return None

    def get_verifiers(self) -> "list[Verifier]":
        """Get result verification rules.

        Verifiers validate workflow output before it is returned to the caller.
        Run after build_result(); a failing verifier should raise.

        Returns:
            List of Verifier instances. Default: empty list (no verification).
        """
        return []

    def get_evaluator(self) -> "Optional[PackEvaluator]":
        """Get quality metrics evaluator.

        Evaluators compute offline quality metrics (precision, recall, etc.)
        for pack outputs. Used in evaluation pipelines, not in serving hot path.

        Returns:
            PackEvaluator instance or None. Default: None.
        """
        return None

    def get_approval_policy(self) -> "Optional[ApprovalPolicy]":
        """Get human-in-loop approval policy.

        Controls when the workflow should pause and request human approval
        before proceeding (e.g. before irreversible actions).

        Returns:
            ApprovalPolicy instance or None. Default: None (no approval required).
        """
        return None

    async def check_health(self) -> HealthStatus:
        """Check if pack is ready after open().

        Returns:
            HealthStatus indicating readiness. Default: always healthy.

        Example:
            async def check_health(self) -> HealthStatus:
                if not hasattr(self, '_model'):
                    return HealthStatus(
                        healthy=False,
                        message="Model not loaded"
                    )
                return HealthStatus(healthy=True)
        """
        return HealthStatus(healthy=True, message="Pack ready")


def _as_non_empty_str(value: Any) -> str | None:
    if isinstance(value, str) and value:
        return value
    return None
