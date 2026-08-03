# Agent Logging MCP Server

Provides structured event-stream logging for agent reasoning and decision tracking. Uses append-only JSONL format for robustness in non-DAG workflows.

## Features

- **Fully generic** - No domain-specific logic, works for ANY event schema
- **Append-only JSONL format** - Robust, never requires read-modify-write
- **Self-describing events** - Each event contains full context (attempt, step, check, etc.)
- **Workflow-agnostic** - Works with any control flow (loops, backtracking, DAG, non-DAG)
- **Queryable** - Filter events by type, fields, or arbitrary criteria
- **Aggregatable** - Aggregate on any field with count_unique, count_by_value, list_unique
- **Summary statistics** - Get generic metrics (event counts, time range, sequence range)

## Tools

### `create_log`

Initialize a new log file with optional metadata.

```python
create_log(
    log_path="/path/to/logs/2026-08-03-query.jsonl",
    metadata={"query": "What stocks to buy?", "session_id": "abc123"}
)
```

### `append_event`

Append an event to the log. Automatically adds timestamp and sequence number.

```python
append_event(
    log_path="/path/to/logs/2026-08-03-query.jsonl",
    event_type="attempt_start",
    event_data={"attempt": 1, "model_hypothesis": "Power bottleneck extends moat"}
)
```

### `read_log`

Read all events or a slice from the log.

```python
read_log(
    log_path="/path/to/logs/2026-08-03-query.jsonl",
    limit=10,
    offset=0
)
```

### `query_events`

Query events with filters.

```python
query_events(
    log_path="/path/to/logs/2026-08-03-query.jsonl",
    event_type="check_fail",
    filters={"attempt": 1}
)
```

### `get_summary`

Get generic summary statistics from the log.

```python
get_summary(
    log_path="/path/to/logs/2026-08-03-query.jsonl"
)

# Returns:
# {
#   "total_events": 21,
#   "event_counts": {"attempt_start": 2, "check_fail": 1, ...},
#   "start_time": "2026-08-03T06:30:00Z",
#   "end_time": "2026-08-03T06:45:00Z",
#   "sequence_range": {"min": 1, "max": 21}
# }
```

### `aggregate_field`

Aggregate events by any field (fully generic).

```python
# Count unique attempts
aggregate_field(
    log_path="/path/to/logs/2026-08-03-query.jsonl",
    field_name="attempt",
    aggregation="count_unique"
)
# Returns: {"result": 2}

# Count by check type
aggregate_field(
    log_path="/path/to/logs/2026-08-03-query.jsonl",
    field_name="check",
    aggregation="count_by_value"
)
# Returns: {"result": {"mechanistic_depth": 4, "evidence_weighting": 1}}

# List unique user IDs (works for ANY field!)
aggregate_field(
    log_path="/path/to/logs/2026-08-03-query.jsonl",
    field_name="user_id",
    aggregation="list_unique"
)
```

## Event Schema

Each event is a JSON object with standard fields:

- `event`: Event type (string)
- `timestamp`: ISO 8601 timestamp (string)
- `seq`: Sequence number (integer, monotonically increasing)
- Additional fields specific to event type

### Example Events

```jsonl
{"event": "query_start", "timestamp": "2026-08-03T06:30:00Z", "seq": 1, "query": "What stocks to buy?"}
{"event": "attempt_start", "timestamp": "2026-08-03T06:30:15Z", "seq": 2, "attempt": 1, "model_hypothesis": "Power bottleneck"}
{"event": "check_fail", "timestamp": "2026-08-03T06:31:00Z", "seq": 5, "check": "mechanistic_depth", "attempt": 1, "achieved_level": 2, "required_level": 3}
{"event": "attempt_end", "timestamp": "2026-08-03T06:31:10Z", "seq": 6, "attempt": 1, "result": "rejected", "reason": "shallow"}
{"event": "query_end", "timestamp": "2026-08-03T06:45:00Z", "seq": 20, "selected_attempt": 2, "confidence": "high"}
```

## Installation

```bash
cd mcps/python/log-agent
uv venv
source .venv/bin/activate  # or `.venv/Scripts/activate` on Windows
uv pip install -e .
```

## Usage

### As MCP Server

Add to your MCP client configuration:

```json
{
  "mcpServers": {
    "log-agent": {
      "command": "python",
      "args": ["/path/to/mcps/python/log-agent/server.py"]
    }
  }
}
```

### Direct Python Usage

```python
from server import create_log, append_event, read_log, get_summary

# Create log
create_log(
    log_path="/tmp/test.jsonl",
    metadata={"query": "Test query"}
)

# Append events
append_event(
    log_path="/tmp/test.jsonl",
    event_type="attempt_start",
    event_data={"attempt": 1}
)

# Read log
result = read_log(log_path="/tmp/test.jsonl")
print(result["events"])

# Get summary
summary = get_summary(log_path="/tmp/test.jsonl")
print(summary)
```

## Use Cases

### Any Agent Workflow

The tools are **fully generic** and work for ANY event schema:

**Example 1: Think reasoning framework**
```python
# Events: attempt_start, check_fail, depth_level, etc.
aggregate_field(log_path="...", field_name="attempt", aggregation="count_unique")
```

**Example 2: Web scraping agent**
```python
# Events: page_visited, data_extracted, error_occurred, etc.
aggregate_field(log_path="...", field_name="page_url", aggregation="list_unique")
aggregate_field(log_path="...", field_name="error_type", aggregation="count_by_value")
```

**Example 3: Customer support bot**
```python
# Events: message_received, intent_classified, response_generated, etc.
aggregate_field(log_path="...", field_name="user_id", aggregation="count_unique")
aggregate_field(log_path="...", field_name="intent", aggregation="count_by_value")
```

**Example 4: CI/CD pipeline**
```python
# Events: build_started, test_run, deployment_triggered, etc.
aggregate_field(log_path="...", field_name="build_id", aggregation="list_unique")
query_events(log_path="...", event_type="test_failed")
```

### Agent Reasoning Framework

Track decision lineage in reasoning frameworks:

- Model attempts and why they failed
- Verification check results
- Alternative generation strategies
- Final confidence assessment

```python
# Generic tools, domain-specific usage
aggregate_field(log_path="...", field_name="attempt", aggregation="count_unique")
query_events(log_path="...", event_type="check_fail")
aggregate_field(log_path="...", field_name="check", aggregation="count_by_value")
```

### Debugging

Reconstruct agent decision paths:

- Why did attempt 1 fail?
- Which checks are failing most often?
- How many iterations before success?

### Meta-Learning

Analyze patterns across multiple queries:

- Average attempts per query
- Most common failure modes
- Mechanistic depth distributions
- Evidence strength calibration

## Design Principles

1. **Append-only** - Never read-modify-write, only append
2. **Self-describing** - Each event has full context
3. **Order-preserving** - Sequence numbers prevent ambiguity
4. **Workflow-agnostic** - Works with any control flow
5. **Queryable** - Easy to filter and analyze

## License

MIT
