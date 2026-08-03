#!/usr/bin/env python3
"""
Agent Logging MCP Server

Provides structured event-stream logging for agent reasoning and decision tracking.
Uses append-only JSONL format for robustness in non-DAG workflows.
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Optional
from fastmcp import FastMCP

mcp = FastMCP("log-agent")


def _ensure_log_dir(log_path: str) -> None:
    """Ensure the directory for the log file exists."""
    Path(log_path).parent.mkdir(parents=True, exist_ok=True)


def _get_timestamp() -> str:
    """Get current ISO 8601 timestamp."""
    return datetime.utcnow().isoformat() + "Z"


@mcp.tool()
def create_log(
    log_path: str,
    metadata: Optional[dict[str, Any]] = None
) -> dict[str, Any]:
    """
    Initialize a new log file with metadata.
    
    Creates a new JSONL log file and writes an initial metadata event.
    Safe to call on existing file (will not overwrite).
    
    Args:
        log_path: Absolute path to log file (e.g., "/path/to/logs/2026-08-03-query.jsonl")
        metadata: Optional metadata to include (e.g., {"query": "...", "session_id": "..."})
    
    Returns:
        Dictionary with status and log path
    """
    _ensure_log_dir(log_path)
    
    # Check if file already exists
    if os.path.exists(log_path):
        return {
            "status": "exists",
            "message": f"Log file already exists: {log_path}",
            "log_path": log_path
        }
    
    # Write initial metadata event
    metadata = metadata or {}
    event = {
        "event": "log_created",
        "timestamp": _get_timestamp(),
        "seq": 1,
        **metadata
    }
    
    with open(log_path, "w") as f:
        f.write(json.dumps(event) + "\n")
    
    return {
        "status": "created",
        "message": f"Created log file: {log_path}",
        "log_path": log_path,
        "initial_event": event
    }


@mcp.tool()
def append_event(
    log_path: str,
    event_type: str,
    event_data: dict[str, Any]
) -> dict[str, Any]:
    """
    Append an event to the log file.
    
    Atomically appends a single event to the JSONL log. Automatically adds
    timestamp and sequence number.
    
    Args:
        log_path: Absolute path to log file
        event_type: Event type (e.g., "attempt_start", "check_fail", "step_end")
        event_data: Event-specific data (will be merged with event, timestamp, seq)
    
    Returns:
        Dictionary with status and the written event
    """
    _ensure_log_dir(log_path)
    
    # Read current log to get next sequence number
    seq = 1
    if os.path.exists(log_path):
        with open(log_path, "r") as f:
            lines = f.readlines()
            if lines:
                last_event = json.loads(lines[-1])
                seq = last_event.get("seq", 0) + 1
    
    # Create event
    event = {
        "event": event_type,
        "timestamp": _get_timestamp(),
        "seq": seq,
        **event_data
    }
    
    # Append to log
    with open(log_path, "a") as f:
        f.write(json.dumps(event) + "\n")
    
    return {
        "status": "appended",
        "event": event,
        "log_path": log_path
    }


@mcp.tool()
def read_log(
    log_path: str,
    limit: Optional[int] = None,
    offset: Optional[int] = None
) -> dict[str, Any]:
    """
    Read events from the log file.
    
    Reads all events or a slice of events from the JSONL log.
    
    Args:
        log_path: Absolute path to log file
        limit: Optional maximum number of events to return
        offset: Optional offset to start reading from (0-indexed)
    
    Returns:
        Dictionary with events and metadata
    """
    if not os.path.exists(log_path):
        return {
            "status": "error",
            "message": f"Log file not found: {log_path}",
            "events": []
        }
    
    with open(log_path, "r") as f:
        events = [json.loads(line) for line in f if line.strip()]
    
    total_events = len(events)
    
    # Apply offset and limit
    if offset is not None:
        events = events[offset:]
    if limit is not None:
        events = events[:limit]
    
    return {
        "status": "success",
        "total_events": total_events,
        "returned_events": len(events),
        "events": events,
        "log_path": log_path
    }


@mcp.tool()
def query_events(
    log_path: str,
    event_type: Optional[str] = None,
    filters: Optional[dict[str, Any]] = None,
    limit: Optional[int] = None
) -> dict[str, Any]:
    """
    Query events from the log with filters.
    
    Filter events by type and/or arbitrary field values.
    
    Args:
        log_path: Absolute path to log file
        event_type: Optional event type to filter by (e.g., "check_fail")
        filters: Optional dictionary of field filters (e.g., {"attempt": 1, "step": 2})
        limit: Optional maximum number of events to return
    
    Returns:
        Dictionary with matching events
    """
    if not os.path.exists(log_path):
        return {
            "status": "error",
            "message": f"Log file not found: {log_path}",
            "events": []
        }
    
    with open(log_path, "r") as f:
        events = [json.loads(line) for line in f if line.strip()]
    
    # Filter by event type
    if event_type:
        events = [e for e in events if e.get("event") == event_type]
    
    # Filter by additional fields
    if filters:
        for key, value in filters.items():
            events = [e for e in events if e.get(key) == value]
    
    # Apply limit
    if limit is not None:
        events = events[:limit]
    
    return {
        "status": "success",
        "matched_events": len(events),
        "events": events,
        "log_path": log_path
    }


@mcp.tool()
def get_summary(log_path: str) -> dict[str, Any]:
    """
    Get summary statistics from the log.
    
    Returns generic statistics that work for any event schema:
    - Total events
    - Event counts by type
    - Start and end times
    - Sequence range
    
    Args:
        log_path: Absolute path to log file
    
    Returns:
        Dictionary with generic summary statistics
    """
    if not os.path.exists(log_path):
        return {
            "status": "error",
            "message": f"Log file not found: {log_path}"
        }
    
    with open(log_path, "r") as f:
        events = [json.loads(line) for line in f if line.strip()]
    
    if not events:
        return {
            "status": "success",
            "message": "Log is empty",
            "total_events": 0
        }
    
    # Count events by type (generic)
    event_counts = {}
    for event in events:
        event_type = event.get("event", "unknown")
        event_counts[event_type] = event_counts.get(event_type, 0) + 1
    
    # Get start and end times (generic)
    start_time = events[0].get("timestamp") if events else None
    end_time = events[-1].get("timestamp") if events else None
    
    # Get sequence range (generic)
    seq_numbers = [e.get("seq") for e in events if "seq" in e]
    seq_range = {
        "min": min(seq_numbers) if seq_numbers else None,
        "max": max(seq_numbers) if seq_numbers else None
    }
    
    return {
        "status": "success",
        "log_path": log_path,
        "total_events": len(events),
        "event_counts": event_counts,
        "start_time": start_time,
        "end_time": end_time,
        "sequence_range": seq_range
    }


@mcp.tool()
def aggregate_field(
    log_path: str,
    field_name: str,
    aggregation: str = "count_unique"
) -> dict[str, Any]:
    """
    Aggregate events by a specific field.
    
    Generic aggregation that works for any field in any event schema.
    
    Args:
        log_path: Absolute path to log file
        field_name: Field to aggregate on (e.g., "attempt", "check", "user_id")
        aggregation: Type of aggregation:
            - "count_unique": Count unique values
            - "count_by_value": Count occurrences of each value
            - "list_unique": List unique values
    
    Returns:
        Dictionary with aggregation results
    """
    if not os.path.exists(log_path):
        return {
            "status": "error",
            "message": f"Log file not found: {log_path}"
        }
    
    with open(log_path, "r") as f:
        events = [json.loads(line) for line in f if line.strip()]
    
    # Extract field values
    values = [e.get(field_name) for e in events if field_name in e]
    
    if aggregation == "count_unique":
        result = len(set(values))
    elif aggregation == "count_by_value":
        result = {}
        for value in values:
            result[str(value)] = result.get(str(value), 0) + 1
    elif aggregation == "list_unique":
        result = list(set(values))
    else:
        return {
            "status": "error",
            "message": f"Unknown aggregation type: {aggregation}"
        }
    
    return {
        "status": "success",
        "field_name": field_name,
        "aggregation": aggregation,
        "result": result,
        "total_events_with_field": len(values),
        "log_path": log_path
    }


def main():
    """Run the MCP server."""
    mcp.run()


if __name__ == "__main__":
    main()
