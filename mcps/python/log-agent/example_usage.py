#!/usr/bin/env python3
"""
Example: Using log-agent MCP in an agent workflow

This demonstrates how an agent would use the log-agent MCP to track
decision lineage during a reasoning task.
"""

import sys
import os
from datetime import datetime

sys.path.insert(0, os.path.dirname(__file__))
from server import create_log, append_event, read_log, get_summary


def simulate_agent_reasoning():
    """Simulate an agent using log-agent to track reasoning."""
    
    # Setup log path
    timestamp = datetime.now().strftime("%Y-%m-%d-%H%M%S")
    log_path = f"/tmp/think-{timestamp}-stock-analysis.jsonl"
    
    print("=" * 70)
    print("AGENT REASONING SESSION WITH LOGGING")
    print("=" * 70)
    print(f"Log: {log_path}\n")
    
    # Initialize log
    create_log(
        log_path=log_path,
        metadata={
            "query": "What stock opportunities exist in August 2026?",
            "session_id": "demo-session",
            "framework": "think-6step"
        }
    )
    print("✓ Log initialized\n")
    
    # --- Attempt 1: Simple model ---
    print("🤔 Attempting Model 1: Power bottleneck hypothesis\n")
    
    append_event(
        log_path=log_path,
        event_type="attempt_start",
        event_data={
            "attempt": 1,
            "model_hypothesis": "NVDA benefits from power bottleneck",
            "generation_method": "abductive_reasoning"
        }
    )
    
    # Step 2: Validate - Mechanistic depth check
    print("   Running mechanistic depth check...")
    append_event(
        log_path=log_path,
        event_type="check_start",
        event_data={"attempt": 1, "check": "mechanistic_depth"}
    )
    
    # Simulate depth probing
    append_event(
        log_path=log_path,
        event_type="depth_level",
        event_data={
            "attempt": 1,
            "level": 1,
            "question": "Why does power bottleneck create value?",
            "answer": "GPUs need power"
        }
    )
    
    append_event(
        log_path=log_path,
        event_type="depth_level",
        event_data={
            "attempt": 1,
            "level": 2,
            "question": "Why do GPUs need more power?",
            "answer": "Higher compute density"
        }
    )
    
    append_event(
        log_path=log_path,
        event_type="depth_stop",
        event_data={
            "attempt": 1,
            "level": 2,
            "reason": "circular_reasoning"
        }
    )
    
    # Check fails
    append_event(
        log_path=log_path,
        event_type="check_fail",
        event_data={
            "attempt": 1,
            "check": "mechanistic_depth",
            "achieved_level": 2,
            "required_level": 3,
            "diagnosis": "Shallow - no explanation for WHY bottleneck creates moat"
        }
    )
    print("   ❌ Mechanistic depth check FAILED (Level 2, need 3+)\n")
    
    # Reject attempt
    append_event(
        log_path=log_path,
        event_type="attempt_end",
        event_data={
            "attempt": 1,
            "result": "rejected",
            "reason": "mechanistic_depth_fail",
            "learned": "Need deeper causal chain explaining mechanism"
        }
    )
    print("   ❌ Attempt 1 REJECTED\n")
    
    # Generate alternative
    print("🔄 Generating alternative model...\n")
    append_event(
        log_path=log_path,
        event_type="alternative_generation",
        event_data={
            "method": "extend_mechanism",
            "constraint": "Previous model stopped at Level 2, need 3+ levels",
            "new_hypothesis": "Power → 800V co-engineering → Switching costs → Moat"
        }
    )
    
    # --- Attempt 2: Deeper model ---
    print("🤔 Attempting Model 2: 800V co-engineering hypothesis\n")
    
    append_event(
        log_path=log_path,
        event_type="attempt_start",
        event_data={
            "attempt": 2,
            "model_hypothesis": "800V co-engineering creates technical moat",
            "generation_method": "extend_mechanism"
        }
    )
    
    # Step 2: Validate - Mechanistic depth check
    print("   Running mechanistic depth check...")
    append_event(
        log_path=log_path,
        event_type="check_start",
        event_data={"attempt": 2, "check": "mechanistic_depth"}
    )
    
    # Deeper probing
    for level, question, answer in [
        (1, "Why power bottleneck?", "Data centers can't deploy without upgrades"),
        (2, "Why upgrades needed?", "800V DC architecture required"),
        (3, "Why 800V creates moat?", "Co-engineering with Vertiv"),
        (4, "Why co-engineering valuable?", "Customer switching costs"),
        (5, "Why switching costs extend moat?", "18-24 month re-validation cycle")
    ]:
        append_event(
            log_path=log_path,
            event_type="depth_level",
            event_data={
                "attempt": 2,
                "level": level,
                "question": question,
                "answer": answer
            }
        )
    
    append_event(
        log_path=log_path,
        event_type="check_pass",
        event_data={
            "attempt": 2,
            "check": "mechanistic_depth",
            "achieved_level": 5,
            "assessment": "Deep causal understanding"
        }
    )
    print("   ✅ Mechanistic depth check PASSED (Level 5)\n")
    
    # Evidence weighting
    print("   Running evidence weighting...")
    append_event(
        log_path=log_path,
        event_type="evidence_assessed",
        event_data={
            "attempt": 2,
            "source": "Vertiv Q2 2026 earnings",
            "claim": "Power infrastructure demand growing",
            "direction": "supports",
            "strength": "strong",
            "independence": True,
            "rationale": "Independent supplier confirms bottleneck"
        }
    )
    
    append_event(
        log_path=log_path,
        event_type="check_pass",
        event_data={
            "attempt": 2,
            "check": "evidence_weighting",
            "strong_count": 1,
            "assessment": "Sufficient - at least one Strong independent source"
        }
    )
    print("   ✅ Evidence weighting PASSED (1 Strong source)\n")
    
    # Accept attempt
    append_event(
        log_path=log_path,
        event_type="attempt_end",
        event_data={
            "attempt": 2,
            "result": "accepted",
            "reason": "passed_all_checks"
        }
    )
    print("   ✅ Attempt 2 ACCEPTED\n")
    
    # Query end
    append_event(
        log_path=log_path,
        event_type="query_end",
        event_data={
            "selected_attempt": 2,
            "total_attempts": 2,
            "confidence": "high"
        }
    )
    
    # Show summary
    print("=" * 70)
    print("SESSION SUMMARY (GENERIC)")
    print("=" * 70)
    summary = get_summary(log_path=log_path)
    print(f"Total events logged: {summary['total_events']}")
    print(f"Event types:")
    for event_type, count in summary["event_counts"].items():
        print(f"  - {event_type}: {count}")
    print(f"Sequence range: {summary['sequence_range']}")
    
    # Get think-specific stats using generic aggregate_field
    from server import aggregate_field
    
    print("\n" + "=" * 70)
    print("THINK-SPECIFIC ANALYSIS (using generic aggregate_field)")
    print("=" * 70)
    
    # Count attempts
    attempts_result = aggregate_field(log_path=log_path, field_name="attempt", aggregation="count_unique")
    print(f"Total attempts: {attempts_result['result']}")
    
    # Count failed checks by type
    failed_checks_result = aggregate_field(log_path=log_path, field_name="check", aggregation="count_by_value")
    print(f"Check results: {failed_checks_result['result']}")
    
    # Get final confidence (query last event)
    final_event = read_log(log_path=log_path, limit=1, offset=summary['total_events']-1)
    if final_event['events']:
        final = final_event['events'][0]
        if final.get('event') == 'query_end':
            print(f"Final confidence: {final.get('confidence')}")
            print(f"Selected attempt: {final.get('selected_attempt')}")
    
    print(f"\nLog file: {log_path}")
    print("=" * 70)
    
    # Show how to query specific events
    print("\n" + "=" * 70)
    print("EXAMPLE QUERIES")
    print("=" * 70)
    
    from server import query_events
    
    # Query all failures
    print("\n1. Query all check failures:")
    result = query_events(log_path=log_path, event_type="check_fail")
    for event in result["events"]:
        print(f"   - {event['check']}: {event['diagnosis']}")
    
    # Query attempt 1 events
    print("\n2. Query all events from attempt 1:")
    result = query_events(log_path=log_path, filters={"attempt": 1})
    for event in result["events"]:
        print(f"   - seq {event['seq']}: {event['event']}")
    
    # Query depth levels for attempt 2
    print("\n3. Query mechanistic depth levels for attempt 2:")
    result = query_events(
        log_path=log_path,
        event_type="depth_level",
        filters={"attempt": 2}
    )
    for event in result["events"]:
        print(f"   - Level {event['level']}: {event['question']} → {event['answer']}")
    
    print("\n" + "=" * 70)
    print(f"Log saved to: {log_path}")
    print("You can analyze it later for meta-learning!")
    print("=" * 70)


if __name__ == "__main__":
    simulate_agent_reasoning()
