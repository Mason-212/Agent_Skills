"""Workflow checkpoint helpers."""

from __future__ import annotations

from uuid import uuid4

from langchain_core.runnables import RunnableConfig
from pydantic import BaseModel


class WorkflowCheckpointHandle(BaseModel):
    """Public checkpoint handle used by the workflow runtime."""

    thread_id: str
    checkpoint_id: str | None = None

    @classmethod
    def new(cls) -> WorkflowCheckpointHandle:
        return cls(thread_id=str(uuid4()))


def workflow_config(
    handle: WorkflowCheckpointHandle,
    *,
    include_checkpoint_id: bool = True,
) -> RunnableConfig:
    """Convert a checkpoint handle into LangGraph config."""

    configurable: dict[str, str] = {"thread_id": handle.thread_id}
    if include_checkpoint_id and handle.checkpoint_id:
        configurable["checkpoint_id"] = handle.checkpoint_id
    return {"configurable": configurable}
