#!/usr/bin/env python3
"""
Enforce guardrails before actions.

Usage:
    python enforce_guardrails.py --action edit --target billing.py --config guardrails.json
"""

import argparse
import json
import subprocess
import sys
from pathlib import Path


def check_protected_branch() -> tuple[bool, str]:
    """Check if current branch is protected."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            capture_output=True,
            text=True,
            check=True
        )
        branch = result.stdout.strip()

        protected = ["main", "master", "develop"]
        if branch in protected:
            return False, f"Cannot run on protected branch: {branch}"

        return True, f"Current branch: {branch}"

    except subprocess.CalledProcessError as e:
        return False, f"Error checking branch: {e}"


def check_staged_files(target: str) -> tuple[bool, str]:
    """Check if target file is staged."""
    try:
        result = subprocess.run(
            ["git", "diff", "--cached", "--name-only"],
            capture_output=True,
            text=True,
            check=True
        )
        staged_files = result.stdout.strip().split("\n")

        if target in staged_files:
            return False, f"File is staged: {target}"

        return True, "File not staged"

    except subprocess.CalledProcessError as e:
        return False, f"Error checking staged files: {e}"


def enforce_guardrails(action: str, target: str, guardrails: list) -> tuple[bool, list]:
    """
    Check if action is allowed by active guardrails.

    Returns:
        (allowed, messages): allowed is True if action is permitted
    """
    messages = []

    for guardrail in guardrails:
        name = guardrail.get("name")

        if name == "protected_branch":
            allowed, msg = check_protected_branch()
            messages.append(f"[{name}] {msg}")
            if not allowed:
                return False, messages

        elif name == "staged_files_isolation" and action == "edit":
            allowed, msg = check_staged_files(target)
            messages.append(f"[{name}] {msg}")
            if not allowed:
                return False, messages

        elif name == "turn_limit":
            # Turn limit is checked by the skill orchestrator, not here
            max_turns = guardrail.get("config", {}).get("max_turns", 10)
            messages.append(f"[{name}] Max turns: {max_turns}")

    return True, messages


def main():
    parser = argparse.ArgumentParser(description="Enforce guardrails")
    parser.add_argument("--action", required=True, help="Action to check (edit, delete, etc.)")
    parser.add_argument("--target", help="Target file/resource")
    parser.add_argument("--config", required=True, help="Guardrails config JSON")

    args = parser.parse_args()

    # Load config
    with open(args.config) as f:
        config = json.load(f)

    guardrails = config.get("guardrails", [])

    # Enforce
    allowed, messages = enforce_guardrails(args.action, args.target, guardrails)

    # Print messages
    for msg in messages:
        print(msg)

    if not allowed:
        print("\n✗ Action blocked by guardrails")
        return 1

    print("\n✓ Action allowed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
