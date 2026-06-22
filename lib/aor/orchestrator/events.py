"""Helpers for creating structured workflow events."""

from __future__ import annotations

from typing import Any

from .types import RuntimeEvent


def step_started(node_name: str, attempt: int) -> RuntimeEvent:
    return RuntimeEvent(
        type="step_started",
        node_name=node_name,
        attempt=attempt,
        message=f"Starting node {node_name!r} attempt {attempt}",
    )


def step_finished(node_name: str, attempt: int, status: str) -> RuntimeEvent:
    return RuntimeEvent(
        type="step_finished",
        node_name=node_name,
        attempt=attempt,
        message=f"Finished node {node_name!r} attempt {attempt} with status {status}",
        payload={"status": status},
    )


def decision_made(node_name: str, action: str, next_node: str | None) -> RuntimeEvent:
    return RuntimeEvent(
        type="decision_made",
        node_name=node_name,
        message=f"Policy chose {action!r} after node {node_name!r}",
        payload={"action": action, "next_node": next_node},
    )


def interrupt_requested(node_name: str, value: Any) -> RuntimeEvent:
    return RuntimeEvent(
        type="interrupt_requested",
        node_name=node_name,
        message="Workflow interrupted and is waiting to resume",
        payload={"value": value},
    )


def interrupt_resumed(node_name: str, response: Any) -> RuntimeEvent:
    return RuntimeEvent(
        type="interrupt_resumed",
        node_name=node_name,
        message=f"Received interrupt response for node {node_name!r}",
        payload={"response": response},
    )


def workflow_completed(final_output: Any) -> RuntimeEvent:
    return RuntimeEvent(
        type="workflow_completed",
        message="Workflow completed successfully",
        payload={"final_output": final_output},
    )


def workflow_failed(reason: str | None) -> RuntimeEvent:
    return RuntimeEvent(
        type="workflow_failed",
        message=reason or "Workflow failed",
        payload={"reason": reason},
    )


def pi_tool_called(node_name: str, tool_name: str, is_error: bool) -> RuntimeEvent:
    return RuntimeEvent(
        type="pi_tool_called",
        node_name=node_name,
        message=f"Pi agent called tool {tool_name!r}",
        payload={"tool_name": tool_name, "is_error": is_error},
    )


def pi_agent_completed(node_name: str, turn_count: int, tool_call_count: int) -> RuntimeEvent:
    return RuntimeEvent(
        type="pi_agent_completed",
        node_name=node_name,
        message=f"Pi agent finished: {turn_count} turns, {tool_call_count} tool calls",
        payload={"turn_count": turn_count, "tool_call_count": tool_call_count},
    )
