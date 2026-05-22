---
name: goal-sandbox
description: Execute safe, git-isolated autonomous tasks with interactive setup wizard for spec, verification, and guardrails
---

# Goal Sandbox

Execute a safe, git-isolated autonomous task with an interactive setup wizard that ensures proper specification, verification strategy, and safety guardrails before invoking Claude's `/goal` command.

## When to Use

Use this skill when:
- The user wants to delegate an autonomous coding task with safety boundaries
- The task needs clear verification criteria before execution
- You need to protect staged changes and ensure branch safety
- The user mentions "goal", "autonomous", "sandbox", or "isolated task"

## PHASE 0: INTERACTIVE WIZARD (Input Validation)

Evaluate the user's input. Do NOT proceed to execution until all three components are defined.

### CRITERIA 1: Empty or Help Request
If input is completely empty or just says "help", print this example and ask what they want to build:

```
Example of a complete request:
"Refactor the payment gateway inside services/billing.py to support multi-currency. 
Verify by running pytest tests/test_billing.py."
```

Then ask: **"What would you like to build or fix next?"**

### CRITERIA 2: Task Present, Missing Verification
If the user has described a task but no verification method:
1. Acknowledge the task
2. Ask: **"What local test suite, linter, or script should I run to verify that my changes are correct and working?"**
3. Wait for their response before proceeding

### CRITERIA 3: Complete Request
If both task and verification are present:
1. Extract target files (if specified)
2. Extract verification script
3. Set default guardrail: **10 max turns** (unless user specified different)
4. Proceed to Phase 1

---

## PHASE 1: ENVIRONMENTAL GUARDRAILS

Before making any changes, establish safety boundaries:

1. **Baseline Capture**: Run `git status` to capture current repository state

2. **Staged Changes Isolation**: 
   - Run `git diff --cached --name-only`
   - You are FORBIDDEN from editing, modifying, or deleting any files in the staged index
   - Treat staged files as read-only context only

3. **Protected Branch Check**:
   - Check current branch name
   - If on `main`, `master`, or `develop`: STOP immediately
   - Alert user: "Cannot run goal-sandbox on protected branch. Please checkout a feature branch."

4. **Untracked Junk Control**:
   - Create or use `.gitignore`'d directory (e.g., `tmp/`, `.goal-sandbox/`)
   - Write any temporary logging, dumps, or scratchpad files there only

---

## PHASE 2: PLAN & SCOPE (Specification)

Before executing, present a clear plan:

1. Print a bulleted summary to the user:
   - **Target files** you intend to modify
   - **Test script** you will run for verification
   - **Turn limit** you're operating under
   - **Guardrails** in effect (staged files protected, temp dir, etc.)

2. Ask: **"Does this plan look correct? Should I proceed?"**

3. Once approved, formulate execution path and invoke `/goal` with the task

---

## PHASE 3: VERIFICATION LOOP

You cannot self-certify completion. Use deterministic machine output:

1. **Baseline Test**: Run verification command BEFORE making changes to confirm baseline behavior

2. **Post-Change Test**: Run verification command AFTER changes

3. **Success Criteria**: Task is complete ONLY when verification script returns exit code `0`

4. **Iteration**: If verification fails, analyze output, adjust approach, and retry (within turn limit)

---

## PHASE 4: CIRCUIT BREAKER

Prevent infinite loops and runaway execution:

1. **Turn Cap Enforcement**:
   - Track number of modification attempts
   - If turn cap reached (default: 10) without passing verification: STOP

2. **Safe Rollback**:
   - Run `git checkout -- .` to revert unstaged changes
   - Preserve staged files (do not run `git reset`)
   - Report summary: "Reached turn limit without passing verification. Changes reverted. Here's what went wrong: [analysis]"

3. **Debug Report**:
   - Final verification output
   - What was attempted
   - Suspected blockers or issues discovered

---

## Execution Flow Summary

```
User Input → Phase 0 (Validate) → Phase 1 (Guardrails) → Phase 2 (Plan) 
→ Invoke /goal → Phase 3 (Verify Loop) → Success or Phase 4 (Circuit Breaker)
```

## Important Notes

- This skill is a WRAPPER around `/goal` - it adds safety and structure, not replacement
- Always respect the user's staged changes - never modify them
- Turn limits are per-execution, not cumulative across sessions
- Verification scripts must be deterministic (same input = same output)
- Git state should be cleaner after execution than before (use temp dirs for junk)
