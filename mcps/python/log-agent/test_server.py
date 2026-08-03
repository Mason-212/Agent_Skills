#!/usr/bin/env python3
"""
Test script for log-agent MCP
"""

import json
import os
import sys
import tempfile

# Add parent directory to path to import server
sys.path.insert(0, os.path.dirname(__file__))

from server import create_log, append_event, read_log, query_events, get_summary


def test_log_agent():
    """Test all log-agent MCP tools."""
    
    # Create temporary log file path (don't create the file yet)
    temp_dir = tempfile.gettempdir()
    log_path = os.path.join(temp_dir, f"test_log_agent_{os.getpid()}.jsonl")
    
    # Clean up any existing file from previous test
    if os.path.exists(log_path):
        os.remove(log_path)
    
    print(f"Testing with log file: {log_path}\n")
    
    try:
        # Test 1: Create log
        print("=" * 60)
        print("TEST 1: create_log")
        print("=" * 60)
        result = create_log(
            log_path=log_path,
            metadata={"query": "Test stock analysis", "session_id": "test123"}
        )
        print(json.dumps(result, indent=2))
        assert result["status"] == "created", f"Failed to create log, got status: {result['status']}"
        print("✓ Log created successfully\n")
        
        # Test 2: Append events
        print("=" * 60)
        print("TEST 2: append_event (multiple events)")
        print("=" * 60)
        
        # Attempt 1 start
        result = append_event(
            log_path=log_path,
            event_type="attempt_start",
            event_data={"attempt": 1, "model_hypothesis": "Power bottleneck extends moat"}
        )
        print("Event 1 (attempt_start):")
        print(json.dumps(result["event"], indent=2))
        assert result["status"] == "appended", "Failed to append event"
        
        # Check fail
        result = append_event(
            log_path=log_path,
            event_type="check_fail",
            event_data={
                "attempt": 1,
                "check": "mechanistic_depth",
                "achieved_level": 2,
                "required_level": 3,
                "diagnosis": "Shallow - no explanation for mechanism"
            }
        )
        print("\nEvent 2 (check_fail):")
        print(json.dumps(result["event"], indent=2))
        
        # Attempt 1 end
        result = append_event(
            log_path=log_path,
            event_type="attempt_end",
            event_data={
                "attempt": 1,
                "result": "rejected",
                "reason": "mechanistic_depth_fail"
            }
        )
        print("\nEvent 3 (attempt_end):")
        print(json.dumps(result["event"], indent=2))
        
        # Attempt 2 start
        result = append_event(
            log_path=log_path,
            event_type="attempt_start",
            event_data={"attempt": 2, "model_hypothesis": "800V co-engineering creates moat"}
        )
        print("\nEvent 4 (attempt_start):")
        print(json.dumps(result["event"], indent=2))
        
        # Check pass
        result = append_event(
            log_path=log_path,
            event_type="check_pass",
            event_data={
                "attempt": 2,
                "check": "mechanistic_depth",
                "achieved_level": 5,
                "assessment": "Deep causal understanding"
            }
        )
        print("\nEvent 5 (check_pass):")
        print(json.dumps(result["event"], indent=2))
        
        # Attempt 2 end (accepted)
        result = append_event(
            log_path=log_path,
            event_type="attempt_end",
            event_data={"attempt": 2, "result": "accepted", "reason": "passed_all_checks"}
        )
        print("\nEvent 6 (attempt_end):")
        print(json.dumps(result["event"], indent=2))
        
        # Query end
        result = append_event(
            log_path=log_path,
            event_type="query_end",
            event_data={
                "selected_attempt": 2,
                "total_attempts": 2,
                "confidence": "high"
            }
        )
        print("\nEvent 7 (query_end):")
        print(json.dumps(result["event"], indent=2))
        print("✓ All events appended successfully\n")
        
        # Test 3: Read log
        print("=" * 60)
        print("TEST 3: read_log")
        print("=" * 60)
        result = read_log(log_path=log_path)
        print(f"Total events: {result['total_events']}")
        print(f"Returned events: {result['returned_events']}")
        print("\nFirst 3 events:")
        for i, event in enumerate(result["events"][:3], 1):
            print(f"{i}. {event['event']} (seq={event['seq']})")
        assert result["total_events"] == 8, f"Expected 8 events, got {result['total_events']}"
        print("✓ Log read successfully\n")
        
        # Test 4: Query events (filter by type)
        print("=" * 60)
        print("TEST 4: query_events (filter by event_type)")
        print("=" * 60)
        result = query_events(
            log_path=log_path,
            event_type="check_fail"
        )
        print(f"Matched events: {result['matched_events']}")
        for event in result["events"]:
            print(f"  - {event['event']}: check={event['check']}, attempt={event['attempt']}")
        assert result["matched_events"] == 1, "Expected 1 check_fail event"
        print("✓ Query by event_type successful\n")
        
        # Test 5: Query events (filter by field)
        print("=" * 60)
        print("TEST 5: query_events (filter by attempt)")
        print("=" * 60)
        result = query_events(
            log_path=log_path,
            filters={"attempt": 1}
        )
        print(f"Matched events (attempt=1): {result['matched_events']}")
        for event in result["events"]:
            print(f"  - {event['event']} (seq={event['seq']})")
        assert result["matched_events"] == 3, f"Expected 3 events for attempt 1, got {result['matched_events']}"
        print("✓ Query by field filter successful\n")
        
        # Test 6: Get summary
        print("=" * 60)
        print("TEST 6: get_summary (generic)")
        print("=" * 60)
        result = get_summary(log_path=log_path)
        print(f"Status: {result['status']}")
        print(f"Total events: {result['total_events']}")
        print(f"\nEvent counts:")
        for event_type, count in result["event_counts"].items():
            print(f"  - {event_type}: {count}")
        print(f"\nSequence range: {result['sequence_range']}")
        print(f"Start time: {result['start_time']}")
        print(f"End time: {result['end_time']}")
        assert result["total_events"] == 8, "Expected 8 events"
        print("✓ Generic summary generated successfully\n")
        
        # Test 7: Aggregate field (think-specific analysis using generic tool)
        print("=" * 60)
        print("TEST 7: aggregate_field (think-specific usage)")
        print("=" * 60)
        
        from server import aggregate_field
        
        # Count unique attempts
        result = aggregate_field(
            log_path=log_path,
            field_name="attempt",
            aggregation="count_unique"
        )
        print(f"Unique attempts: {result['result']}")
        assert result["result"] == 2, "Expected 2 attempts"
        
        # Count by check type
        result = aggregate_field(
            log_path=log_path,
            field_name="check",
            aggregation="count_by_value"
        )
        print(f"Checks by type: {result['result']}")
        
        print("✓ Field aggregation successful\n")
        
        # Test 8: Read raw JSONL
        print("=" * 60)
        print("TEST 8: Verify raw JSONL format")
        print("=" * 60)
        with open(log_path, 'r') as f:
            lines = f.readlines()
        print(f"Total lines in file: {len(lines)}")
        print("\nFirst event (raw JSON):")
        print(lines[0].strip())
        print("\nLast event (raw JSON):")
        print(lines[-1].strip())
        
        # Verify each line is valid JSON
        for i, line in enumerate(lines, 1):
            try:
                event = json.loads(line)
                assert "event" in event, f"Line {i} missing 'event' field"
                assert "seq" in event, f"Line {i} missing 'seq' field"
                assert "timestamp" in event, f"Line {i} missing 'timestamp' field"
            except json.JSONDecodeError as e:
                print(f"✗ Line {i} is not valid JSON: {e}")
                raise
        print("✓ All lines are valid JSONL format\n")
        
        print("=" * 60)
        print("ALL TESTS PASSED ✓")
        print("=" * 60)
        
    finally:
        # Cleanup
        if os.path.exists(log_path):
            os.remove(log_path)
            print(f"\nCleaned up test file: {log_path}")


if __name__ == "__main__":
    test_log_agent()
