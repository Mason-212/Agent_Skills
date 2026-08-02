# goal-wizard Test Procedure

Complete test procedure covering all verification types and features.

---

## Setup (One-Time)

```bash
# 1. Sync plugin and skill
./scripts/dev_refresh_skills_and_tools.sh

# 2. Restart Claude Code to load goal-wizard

# 3. Verify loaded
# In Claude Code, check that /goal-wizard is available
```

---

## Test 1: Structural Verification (Type Hints)

**Tests**: AST-based structural checks

### Setup
```bash
mkdir -p /tmp/goal-wizard-test
cd /tmp/goal-wizard-test
cat > math.py << 'EOF'
def add(a, b):
    return a + b

def subtract(a, b):
    return a - b
EOF
```

### Execute
```
/goal-wizard "Add type hints to all functions in /tmp/goal-wizard-test/math.py"
```

### Expected Wizard Behavior
1. **Analyzes goal**: Detects keywords "type hints"
2. **Suggests verification**: "Check that all functions have type hints" (structural)
3. **Shows confidence**: High confidence for type hint verification
4. **Presents plan**:
   - Target: math.py
   - Verification: AST-based type hint checker
   - Turn limit: 10

### When Prompted
```
Q: "What test verifies success?"
A: (Accept suggested verification or specify custom)
```

### Verification Run
- Wizard calls `check_type_hints` verification
- Checks AST for type annotations
- Pass: `def add(a: int, b: int) -> int:`
- Fail: `def add(a, b):` (no types)

### Verify Manually
```bash
cat /tmp/goal-wizard-test/math.py
```

**Expected result**:
```python
def add(a: int, b: int) -> int:
    return a + b

def subtract(a: int, b: int) -> int:
    return a - b
```

**Success criteria**:
- ✅ Wizard suggested structural verification
- ✅ Type hints added
- ✅ Verification passed

---

## Test 2: Structural Verification (Docstrings)

**Tests**: AST-based docstring checks

### Setup
```bash
cat > /tmp/goal-wizard-test/calc.py << 'EOF'
def multiply(a, b):
    return a * b

def divide(a, b):
    return a / b
EOF
```

### Execute
```
/goal-wizard "Add docstrings to all functions in /tmp/goal-wizard-test/calc.py"
```

### Expected Wizard Behavior
1. **Analyzes goal**: Detects keywords "docstrings"
2. **Suggests verification**: "Check that all functions have docstrings" (structural)
3. **Shows confidence**: High

### Verification Run
- Wizard calls `check_docstrings` verification
- Checks AST for docstring presence
- Pass: Function has `"""..."""` after def
- Fail: No docstring

### Verify Manually
```bash
cat /tmp/goal-wizard-test/calc.py
```

**Expected result**:
```python
def multiply(a, b):
    """Multiply two numbers."""
    return a * b

def divide(a, b):
    """Divide two numbers."""
    return a / b
```

**Success criteria**:
- ✅ Wizard suggested docstring verification
- ✅ Docstrings added
- ✅ Verification passed

---

## Test 3: Behavioral Verification (Existing Tests)

**Tests**: Runtime test execution

### Setup
```bash
cat > /tmp/goal-wizard-test/test_math.py << 'EOF'
def test_add():
    from math import add
    assert add(2, 3) == 5
    assert add(-1, 1) == 0
EOF
```

### Execute
```
/goal-wizard "Refactor the add function in /tmp/goal-wizard-test/math.py to use a different variable name"
```

### Expected Wizard Behavior
1. **Analyzes goal**: Detects keywords "refactor"
2. **Suggests verification**: "Run existing tests to ensure no regressions" (behavioral)
3. **Shows confidence**: High

### When Prompted
```
Q: "What test verifies success?"
A: "pytest /tmp/goal-wizard-test/test_math.py"
```

### Verification Run
- Wizard calls `existing_tests` verification
- Runs: `pytest /tmp/goal-wizard-test/test_math.py`
- Pass: All tests pass (exit code 0)
- Fail: Any test fails

### Verify Manually
```bash
pytest /tmp/goal-wizard-test/test_math.py -v
```

**Expected**: All tests pass

**Success criteria**:
- ✅ Wizard suggested behavioral verification
- ✅ Refactoring complete
- ✅ Tests still pass

---

## Test 4: Behavioral Verification (API Response)

**Tests**: HTTP endpoint testing

### Setup
```bash
cat > /tmp/goal-wizard-test/server.py << 'EOF'
from flask import Flask
app = Flask(__name__)

@app.route('/health')
def health():
    return {'status': 'ok'}

if __name__ == '__main__':
    app.run(port=5000)
EOF
```

### Execute
```
/goal-wizard "Add a /ping endpoint to /tmp/goal-wizard-test/server.py that returns 'pong'"
```

### Expected Wizard Behavior
1. **Analyzes goal**: Detects keywords "endpoint"
2. **Suggests verification**: "Check that API returns expected status" (behavioral)
3. **Shows confidence**: Medium-high

### When Prompted
```
Q: "What test verifies success?"
A: "curl http://localhost:5000/ping returns 'pong' with 200 status"
```

### Verification Run
- Wizard calls `api_response` verification
- Runs: `curl -s -o /dev/null -w "%{http_code}" http://localhost:5000/ping`
- Pass: Returns 200
- Fail: Returns 404 or error

### Verify Manually
```bash
# Start server in background
python /tmp/goal-wizard-test/server.py &
sleep 2

# Test
curl http://localhost:5000/ping

# Cleanup
killall python
```

**Expected**: Returns "pong"

**Success criteria**:
- ✅ Wizard suggested API verification
- ✅ Endpoint added
- ✅ Returns expected response

---

## Test 5: Property Verification (Hypothesis)

**Tests**: Property-based testing (placeholder in MVP)

### Setup
```bash
cat > /tmp/goal-wizard-test/sort.py << 'EOF'
def bubble_sort(arr):
    n = len(arr)
    for i in range(n):
        for j in range(0, n-i-1):
            if arr[j] > arr[j+1]:
                arr[j], arr[j+1] = arr[j+1], arr[j]
    return arr
EOF
```

### Execute
```
/goal-wizard "Add a quicksort implementation that has the property: output is always sorted"
```

### Expected Wizard Behavior
1. **Analyzes goal**: Detects keywords "property", "always"
2. **Suggests verification**: "Property holds for all inputs" (property)
3. **Shows confidence**: Medium (hypothesis integration pending in MVP)

### When Prompted
```
Q: "What test verifies success?"
A: "Verify that for any input list, output is sorted in ascending order"
```

### Verification Run (MVP Placeholder)
- Wizard acknowledges property-based verification
- Falls back to manual test cases
- Suggests hypothesis integration for Phase 2

**Success criteria**:
- ✅ Wizard recognizes property-based verification need
- ✅ Suggests appropriate verification strategy
- ⚠️ Full hypothesis integration pending Phase 2

---

## Test 6: Safety Guardrails

**Tests**: Protected branches and staged files

### Test 6a: Protected Branch
```bash
cd /tmp/goal-wizard-test
git init
git checkout -b main
```

### Execute
```
/goal-wizard "Add a comment to math.py"
```

### Expected
- ❌ Wizard **blocks execution** or **warns**
- Message: "Cannot run on protected branch: main"
- Suggests: "Checkout feature branch first"

---

### Test 6b: Staged Files
```bash
cd /tmp/goal-wizard-test
echo "staged content" > staged.txt
git add staged.txt
```

### Execute
```
/goal-wizard "Modify staged.txt"
```

### Expected
- ❌ Wizard **blocks** or **warns**
- Message: "Cannot modify staged files"
- Protects: staged.txt remains unchanged

---

### Test 6c: Turn Limit
```bash
cat > /tmp/goal-wizard-test/impossible.py << 'EOF'
# Intentionally vague task
EOF
```

### Execute
```
/goal-wizard "Make impossible.py do something amazing"
```

### Expected
- Wizard sets turn limit (default: 10)
- After 10 failed attempts: **circuit breaker**
- Rolls back changes
- Reports: "Reached turn limit without passing verification"

**Success criteria**:
- ✅ Protected branch blocked
- ✅ Staged files protected
- ✅ Turn limit enforced
- ✅ Rollback executed

---

## Verification Type Summary

| Type | What It Checks | Test Case | Verification Method |
|------|----------------|-----------|---------------------|
| **Structural** | Code structure (AST) | Type hints, docstrings | AST parsing |
| **Behavioral** | Runtime behavior | Tests pass, API works | Execute tests/commands |
| **Property** | Invariants hold | Always sorted, never negative | Property-based testing |

---

## Test Checklist

After running all tests:

### Phase 0 (Interactive Wizard)
```
✅ Test 0a: CRITERIA 1 - Empty input handling
✅ Test 0b: CRITERIA 2 - Task only, prompts for verification
✅ Test 0c: CRITERIA 3 - Verification type classification
✅ Test 0d: CRITERIA 4 - Complete request & plan display
✅ Test 0e: End-to-end Phase 0 flow
```

### Phase 1-3 (Verification Types)
```
✅ Test 1: Structural (type hints) - AST verification
✅ Test 2: Structural (docstrings) - AST verification
✅ Test 3: Behavioral (existing tests) - pytest execution
✅ Test 4: Behavioral (API) - HTTP check
✅ Test 5: Property (placeholder) - Recognition only
```

### Phase 1 & 4 (Safety Guardrails)
```
✅ Test 6a: Guardrail (protected branch) - Blocked
✅ Test 6b: Guardrail (staged files) - Protected
✅ Test 6c: Guardrail (turn limit) - Circuit breaker
```

**All phases and verification types tested** ✅

---

## Test 0: Phase 0 Wizard Flow (All Interactive Steps)

**Tests**: Complete interactive wizard from empty input to execution

### Test 0a: Empty Input (CRITERIA 1)
```
/goal-wizard
```

**Expected Wizard Behavior**:
1. Shows example request
2. Asks: "What would you like to build or fix next?"

**Success criteria**: ✅ Wizard prompts for task

---

### Test 0b: Task Only, No Verification (CRITERIA 2)
```
/goal-wizard "Create /tmp/hello.txt with content 'Hello World'"
```

**Expected Wizard Behavior**:
1. Acknowledges task
2. Asks: "What local test suite, linter, or script should I run to verify that my changes are correct and working?"

**User provides**: 
```
test -f /tmp/hello.txt && grep -q "Hello World" /tmp/hello.txt
```

**Success criteria**: ✅ Wizard prompts for verification method

---

### Test 0c: Verification Type Classification (CRITERIA 3)
After providing verification method above:

**Expected Wizard Behavior**:
1. Presents two options:
   - **Behavioral:** Tests actual runtime behavior
   - **Structural:** Checks code structure/syntax
2. Asks: "Is this verification behavioral (runtime tests) or structural (syntax/build checks)?"

**User provides**:
```
behavioral
```

**Success criteria**: ✅ Wizard classifies verification type

---

### Test 0d: Complete Request (CRITERIA 4)
Once all three components provided:

**Expected Wizard Behavior**:
1. Extracts target files: `/tmp/hello.txt`
2. Records verification script
3. Records verification type: `behavioral`
4. Sets turn limit: 10 (default)
5. Proceeds to Phase 1 (Guardrails)

**Success criteria**: ✅ Wizard transitions to Phase 1

---

### Test 0e: End-to-End Phase 0 Flow
Complete interactive flow from empty to execution:

```bash
# Start
/goal-wizard

# Response to "What would you like to build?"
Create /tmp/hello.txt with content 'Hello World'

# Response to "What verification?"
test -f /tmp/hello.txt && grep -q "Hello World" /tmp/hello.txt

# Response to "Behavioral or structural?"
behavioral

# Wizard shows plan, asks "Proceed?"
yes
```

**Expected execution plan display**:
```
**Target files:** /tmp/hello.txt
**Test script:** test -f /tmp/hello.txt && grep -q "Hello World" /tmp/hello.txt
**Verification type:** behavioral
**Turn limit:** 10
**Guardrails:** staged files protected, temp dir, branch isolation
```

**Success criteria**:
- ✅ All Phase 0 steps completed
- ✅ Plan shows verification type
- ✅ Execution proceeds to Phase 1

---

## Quick Smoke Test (Minimal)

If you just want to verify it works (skips Phase 0 interactive steps):

```bash
# 1. Sync
./scripts/dev_refresh_skills_and_tools.sh

# 2. Restart Claude Code

# 3. Quick test with complete request (skips CRITERIA 1-2)
/goal-wizard "Create /tmp/hello.txt with 'Hello World'"

When prompted for verification:
"test -f /tmp/hello.txt && grep -q 'Hello World' /tmp/hello.txt"

When prompted for type:
"behavioral"

# 4. Verify
cat /tmp/hello.txt
```

**Expected**: File created with correct content ✅

---

## Cleanup

```bash
rm -rf /tmp/goal-wizard-test
rm -f /tmp/hello.txt
```
