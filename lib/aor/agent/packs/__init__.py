"""Domain pack system for ML capability integration.

This package provides the core interfaces and utilities for building
domain packs - self-contained plugins that integrate ML capabilities
into the EDC agent framework.
"""

from agent.packs.adapter import create_tool_adapter
from agent.packs.base import (
    BoundDomainPack,
    ExecutionContext,
    HealthStatus,
    PackDescriptor,
    PackResult,
    PackWorkflow,
)
from agent.packs.context import PackExecutionContext, SessionContext, cleanup_session_workspace
from agent.packs.orchestrator import (
    PackWorkflowOrchestrator,
    PackWorkflowWrapper,
    WorkflowCompleted,
    WorkflowDirectOutcome,
    WorkflowFailedError,
    WorkflowPaused,
)
from agent.packs.registry import PackLoadError, PackRegistry
from agent.packs.skill_provider import (
    PackSkillProvider,
    SkillProvider,
    collect_skill_paths_from_pack,
)
from agent.packs.tool_pack import ToolPack, pack_tool
from agent.packs.tool_response import build_tool_response

__all__ = [
    "BoundDomainPack",
    "ExecutionContext",
    "HealthStatus",
    "PackDescriptor",
    "PackExecutionContext",
    "SessionContext",
    "PackWorkflow",
    "PackResult",
    "PackWorkflowOrchestrator",
    "PackWorkflowWrapper",
    "PackLoadError",
    "PackRegistry",
    "SkillProvider",
    "PackSkillProvider",
    "ToolPack",
    "WorkflowCompleted",
    "WorkflowDirectOutcome",
    "WorkflowFailedError",
    "WorkflowPaused",
    "cleanup_session_workspace",
    "collect_skill_paths_from_pack",
    "create_tool_adapter",
    "pack_tool",
    "build_tool_response",
]
