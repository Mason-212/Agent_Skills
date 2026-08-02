#!/usr/bin/env python3
"""
Analyze natural language goal and suggest verifications.

MVP Phase 1: Hardcoded suggestion logic.
Phase 2: Will use YAML manifest discovery.

Usage:
    python analyze_goal.py "Refactor billing module" --files billing.py
"""

import argparse
import json
import sys
from typing import List, Dict, Any


def classify_goal_type(goal: str) -> str:
    """Classify goal into type for pattern matching."""
    goal_lower = goal.lower()

    if any(kw in goal_lower for kw in ["refactor", "clean up", "improve"]):
        return "refactor"
    elif any(kw in goal_lower for kw in ["add", "implement", "create", "new"]):
        return "add_feature"
    elif any(kw in goal_lower for kw in ["fix", "bug", "error", "broken"]):
        return "fix_bug"
    else:
        return "modify"


def calculate_confidence(goal: str, files: List[str], verification: Dict[str, Any]) -> float:
    """Calculate confidence score 0.0-1.0 for a verification."""
    score = 0.0
    goal_lower = goal.lower()

    # Keyword matching
    for keyword in verification.get("keywords", []):
        if keyword in goal_lower:
            score += 0.3

    # File pattern matching (simplified)
    if verification.get("file_patterns"):
        for file in files:
            if file.endswith(".py"):
                score += 0.2
                break

    # Base confidence boost
    score += verification.get("confidence_boost", 0.0)

    return min(score, 1.0)


def suggest_verifications(goal: str, target_files: List[str]) -> List[Dict[str, Any]]:
    """
    Analyze goal and return suggested verifications.

    MVP: Hardcoded verification library.
    Phase 2: Will scan YAML manifests.
    """

    # Hardcoded verification library for MVP
    verifications = [
        {
            "name": "existing_tests",
            "label": "Existing tests still pass",
            "type": "behavioral",
            "plain_language": "Runs existing test suite to prevent regressions",
            "why_it_matters": "Ensures changes don't break current functionality",
            "keywords": ["refactor", "change", "modify", "fix"],
            "file_patterns": ["*.py"],
            "confidence_boost": 0.6,
            "manifest_path": "resources/verifiers/behavioral/existing_tests.yaml"
        },
        {
            "name": "check_type_hints",
            "label": "All functions have type hints",
            "type": "structural",
            "plain_language": "Uses AST to check all functions have return type hints",
            "why_it_matters": "Catches type errors before runtime",
            "keywords": ["type hint", "typing", "refactor"],
            "file_patterns": ["*.py"],
            "confidence_boost": 0.3,
            "manifest_path": "resources/verifiers/structural/check_type_hints.yaml"
        },
        {
            "name": "check_docstrings",
            "label": "All functions have docstrings",
            "type": "structural",
            "plain_language": "Checks that all functions have docstrings",
            "why_it_matters": "Improves code documentation",
            "keywords": ["docstring", "documentation", "document"],
            "file_patterns": ["*.py"],
            "confidence_boost": 0.2,
            "manifest_path": "resources/verifiers/structural/check_docstrings.yaml"
        },
        {
            "name": "api_response",
            "label": "API returns expected HTTP status",
            "type": "behavioral",
            "plain_language": "Tests API endpoint returns correct status code",
            "why_it_matters": "Verifies API behavior matches requirements",
            "keywords": ["api", "endpoint", "http", "rest"],
            "file_patterns": ["**/api/*.py", "**/routes/*.py"],
            "confidence_boost": 0.4,
            "manifest_path": "resources/verifiers/behavioral/api_response.yaml"
        }
    ]

    suggestions = []

    for verification in verifications:
        confidence = calculate_confidence(goal, target_files, verification)

        if confidence > 0.3:  # Relevance threshold
            suggestions.append({
                "name": verification["name"],
                "label": verification["label"],
                "type": verification["type"],
                "confidence": confidence,
                "plain_language": verification["plain_language"],
                "why_it_matters": verification["why_it_matters"],
                "manifest_path": verification["manifest_path"]
            })

    # Sort by confidence
    suggestions.sort(key=lambda x: x["confidence"], reverse=True)

    return suggestions


def main():
    parser = argparse.ArgumentParser(description="Analyze goal and suggest verifications")
    parser.add_argument("goal", help="Natural language goal")
    parser.add_argument("--files", nargs="*", default=[], help="Target files")
    parser.add_argument("--output", help="Output JSON file (default: stdout)")

    args = parser.parse_args()

    goal_type = classify_goal_type(args.goal)
    suggestions = suggest_verifications(args.goal, args.files)

    result = {
        "goal": args.goal,
        "goal_type": goal_type,
        "target_files": args.files,
        "verifications": suggestions
    }

    output = json.dumps(result, indent=2)

    if args.output:
        with open(args.output, 'w') as f:
            f.write(output)
    else:
        print(output)

    return 0


if __name__ == "__main__":
    sys.exit(main())
