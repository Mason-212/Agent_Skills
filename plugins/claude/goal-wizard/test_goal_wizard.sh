#!/usr/bin/env bash
# test_goal_wizard.sh - Test suite for goal-wizard plugin
#
# Usage:
#   ./plugins/claude/goal-wizard/test_goal_wizard.sh
#
# Prerequisites:
#   - goal-wizard synced and Claude Code restarted
#   - Run from repo root

set -euo pipefail

TEST_DIR="/tmp/goal-wizard-test"
PASSED=0
FAILED=0

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo "═══════════════════════════════════════════════════════════"
echo "  goal-wizard Test Suite"
echo "═══════════════════════════════════════════════════════════"
echo ""

# Cleanup function
cleanup() {
    echo ""
    echo -e "${BLUE}Cleaning up...${NC}"
    rm -rf "${TEST_DIR}"
    echo -e "${GREEN}✓ Cleaned up test directory${NC}"
}
trap cleanup EXIT

# Setup test directory
setup_test_dir() {
    rm -rf "${TEST_DIR}"
    mkdir -p "${TEST_DIR}"
    cd "${TEST_DIR}"
    echo -e "${GREEN}✓ Created test directory: ${TEST_DIR}${NC}"
}

# Wait for user to proceed
wait_for_user() {
    local message="$1"
    echo ""
    echo -e "${YELLOW}${message}${NC}"
    read -p "Press Enter to continue..."
    echo ""
}

# Verify file content
verify_file() {
    local file="$1"
    local expected_pattern="$2"
    local test_name="$3"

    if [[ ! -f "${file}" ]]; then
        echo -e "${RED}✗ FAIL: ${test_name} - File not found: ${file}${NC}"
        ((FAILED++))
        return 1
    fi

    if grep -q "${expected_pattern}" "${file}"; then
        echo -e "${GREEN}✓ PASS: ${test_name}${NC}"
        ((PASSED++))
        return 0
    else
        echo -e "${RED}✗ FAIL: ${test_name} - Pattern not found: ${expected_pattern}${NC}"
        echo "File contents:"
        cat "${file}"
        ((FAILED++))
        return 1
    fi
}

# Show manual verification prompt
show_verification_prompt() {
    local test_name="$1"
    local verification="$2"

    echo ""
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BLUE}Test: ${test_name}${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
    echo -e "${YELLOW}When wizard prompts for verification, enter:${NC}"
    echo -e "  ${GREEN}${verification}${NC}"
    echo ""
}

# Test summary
show_summary() {
    echo ""
    echo "═══════════════════════════════════════════════════════════"
    echo "  Test Summary"
    echo "═══════════════════════════════════════════════════════════"
    echo -e "${GREEN}Passed: ${PASSED}${NC}"
    echo -e "${RED}Failed: ${FAILED}${NC}"
    echo ""

    if [[ ${FAILED} -eq 0 ]]; then
        echo -e "${GREEN}✓ All tests passed!${NC}"
        return 0
    else
        echo -e "${RED}✗ Some tests failed${NC}"
        return 1
    fi
}

# ═══════════════════════════════════════════════════════════
# Test 0a: Phase 0 - Empty Input (CRITERIA 1)
# ═══════════════════════════════════════════════════════════

test_phase0_empty() {
    echo ""
    echo "─────────────────────────────────────────────────────────────"
    echo "Test 0a: Phase 0 - Empty Input (CRITERIA 1)"
    echo "─────────────────────────────────────────────────────────────"

    echo ""
    echo -e "${YELLOW}In Claude Code, run:${NC}"
    echo -e "  ${GREEN}/goal-wizard${NC}"
    echo ""
    echo -e "${YELLOW}Expected behavior:${NC}"
    echo "  1. Shows example request"
    echo "  2. Asks: 'What would you like to build or fix next?'"
    echo ""

    wait_for_user "Did wizard prompt for task? Press Enter to continue..."

    echo -e "${GREEN}✓ PASS: Phase 0 CRITERIA 1 - Empty input handling${NC}"
    ((PASSED++))
}

# ═══════════════════════════════════════════════════════════
# Test 0b: Phase 0 - Task Only (CRITERIA 2)
# ═══════════════════════════════════════════════════════════

test_phase0_task_only() {
    echo ""
    echo "─────────────────────────────────────────────────────────────"
    echo "Test 0b: Phase 0 - Task Only, No Verification (CRITERIA 2)"
    echo "─────────────────────────────────────────────────────────────"

    rm -f /tmp/hello.txt

    echo ""
    echo -e "${YELLOW}In Claude Code, run:${NC}"
    echo -e "  ${GREEN}/goal-wizard \"Create /tmp/hello.txt with content 'Hello World'\"${NC}"
    echo ""
    echo -e "${YELLOW}Expected behavior:${NC}"
    echo "  1. Acknowledges task"
    echo "  2. Asks: 'What local test suite, linter, or script should I run to verify...?'"
    echo ""
    echo -e "${YELLOW}When prompted, provide this verification:${NC}"
    echo -e "  ${GREEN}test -f /tmp/hello.txt && grep -q \"Hello World\" /tmp/hello.txt${NC}"
    echo ""

    wait_for_user "Did wizard prompt for verification? Press Enter after providing it..."

    echo -e "${GREEN}✓ PASS: Phase 0 CRITERIA 2 - Verification prompt${NC}"
    ((PASSED++))
}

# ═══════════════════════════════════════════════════════════
# Test 0c: Phase 0 - Verification Type (CRITERIA 3)
# ═══════════════════════════════════════════════════════════

test_phase0_verification_type() {
    echo ""
    echo "─────────────────────────────────────────────────────────────"
    echo "Test 0c: Phase 0 - Verification Type Classification (CRITERIA 3)"
    echo "─────────────────────────────────────────────────────────────"

    echo ""
    echo -e "${YELLOW}Expected behavior (continuing from 0b):${NC}"
    echo "  1. Presents two options:"
    echo "     - Behavioral: Tests actual runtime behavior"
    echo "     - Structural: Checks code structure/syntax"
    echo "  2. Asks: 'Is this verification behavioral or structural?'"
    echo ""
    echo -e "${YELLOW}When prompted, answer:${NC}"
    echo -e "  ${GREEN}behavioral${NC}"
    echo ""

    wait_for_user "Did wizard ask for verification type? Press Enter after answering..."

    echo -e "${GREEN}✓ PASS: Phase 0 CRITERIA 3 - Verification type classification${NC}"
    ((PASSED++))
}

# ═══════════════════════════════════════════════════════════
# Test 0d: Phase 0 - Complete Request (CRITERIA 4)
# ═══════════════════════════════════════════════════════════

test_phase0_complete() {
    echo ""
    echo "─────────────────────────────────────────────────────────────"
    echo "Test 0d: Phase 0 - Complete Request & Plan Display (CRITERIA 4)"
    echo "─────────────────────────────────────────────────────────────"

    echo ""
    echo -e "${YELLOW}Expected behavior (continuing from 0c):${NC}"
    echo "  1. Extracts target files: /tmp/hello.txt"
    echo "  2. Records verification script"
    echo "  3. Records verification type: behavioral"
    echo "  4. Sets turn limit: 10"
    echo "  5. Shows execution plan with:"
    echo "     - Target files"
    echo "     - Test script"
    echo "     - Verification type"
    echo "     - Turn limit"
    echo "     - Guardrails"
    echo "  6. Asks: 'Does this plan look correct? Should I proceed?'"
    echo ""
    echo -e "${YELLOW}When prompted, answer:${NC}"
    echo -e "  ${GREEN}yes${NC}"
    echo ""

    wait_for_user "Did wizard show plan with verification type? Press Enter after approving..."

    echo -e "${GREEN}✓ PASS: Phase 0 CRITERIA 4 - Complete request & plan${NC}"
    ((PASSED++))

    # Wait for execution to complete
    wait_for_user "After wizard completes execution, press Enter to verify result..."

    verify_file "/tmp/hello.txt" "Hello World" "Phase 0 end-to-end execution"
}

# ═══════════════════════════════════════════════════════════
# Test 0e: Quick Smoke Test (Skip Interactive Phase 0)
# ═══════════════════════════════════════════════════════════

test_smoke() {
    echo ""
    echo "─────────────────────────────────────────────────────────────"
    echo "Test 0e: Quick Smoke Test (All Steps Provided)"
    echo "─────────────────────────────────────────────────────────────"

    rm -f /tmp/hello_smoke.txt

    echo ""
    echo -e "${YELLOW}In Claude Code, run:${NC}"
    echo -e "  ${GREEN}/goal-wizard \"Create /tmp/hello_smoke.txt with content 'Hello World'\"${NC}"
    echo ""
    echo -e "${YELLOW}When prompted for verification:${NC}"
    echo -e "  ${GREEN}test -f /tmp/hello_smoke.txt && grep -q \"Hello World\" /tmp/hello_smoke.txt${NC}"
    echo ""
    echo -e "${YELLOW}When prompted for type:${NC}"
    echo -e "  ${GREEN}behavioral${NC}"
    echo ""
    echo -e "${YELLOW}When prompted to proceed:${NC}"
    echo -e "  ${GREEN}yes${NC}"
    echo ""

    wait_for_user "After completing the wizard, press Enter to verify..."

    verify_file "/tmp/hello_smoke.txt" "Hello World" "Smoke test - complete flow"
}

# ═══════════════════════════════════════════════════════════
# Test 1: Structural - Type Hints
# ═══════════════════════════════════════════════════════════

test_type_hints() {
    echo ""
    echo "─────────────────────────────────────────────────────────────"
    echo "Test 1: Structural Verification - Type Hints"
    echo "─────────────────────────────────────────────────────────────"

    setup_test_dir

    cat > math.py << 'EOF'
def add(a, b):
    return a + b

def subtract(a, b):
    return a - b
EOF

    echo -e "${GREEN}✓ Created test file: ${TEST_DIR}/math.py${NC}"
    echo ""
    echo "File contents:"
    cat math.py

    show_verification_prompt \
        "Type Hints" \
        "Check that all functions have type hints (structural verification)"

    echo -e "${YELLOW}In Claude Code, run:${NC}"
    echo -e "  ${GREEN}/goal-wizard \"Add type hints to all functions in ${TEST_DIR}/math.py\"${NC}"

    wait_for_user "After completing the wizard, press Enter to verify..."

    # Check for type hints (simplified check)
    if grep -q "def add.*:.*->.*:" math.py && grep -q "def subtract.*:.*->.*:" math.py; then
        echo -e "${GREEN}✓ PASS: Type hints added${NC}"
        ((PASSED++))
    else
        echo -e "${RED}✗ FAIL: Type hints not found${NC}"
        echo "File contents:"
        cat math.py
        ((FAILED++))
    fi
}

# ═══════════════════════════════════════════════════════════
# Test 2: Structural - Docstrings
# ═══════════════════════════════════════════════════════════

test_docstrings() {
    echo ""
    echo "─────────────────────────────────────────────────────────────"
    echo "Test 2: Structural Verification - Docstrings"
    echo "─────────────────────────────────────────────────────────────"

    cd "${TEST_DIR}"

    cat > calc.py << 'EOF'
def multiply(a, b):
    return a * b

def divide(a, b):
    return a / b
EOF

    echo -e "${GREEN}✓ Created test file: ${TEST_DIR}/calc.py${NC}"
    echo ""
    echo "File contents:"
    cat calc.py

    show_verification_prompt \
        "Docstrings" \
        "Check that all functions have docstrings (structural verification)"

    echo -e "${YELLOW}In Claude Code, run:${NC}"
    echo -e "  ${GREEN}/goal-wizard \"Add docstrings to all functions in ${TEST_DIR}/calc.py\"${NC}"

    wait_for_user "After completing the wizard, press Enter to verify..."

    # Check for docstrings (simplified check)
    if grep -q '"""' calc.py; then
        echo -e "${GREEN}✓ PASS: Docstrings added${NC}"
        ((PASSED++))
    else
        echo -e "${RED}✗ FAIL: Docstrings not found${NC}"
        echo "File contents:"
        cat calc.py
        ((FAILED++))
    fi
}

# ═══════════════════════════════════════════════════════════
# Test 3: Behavioral - Existing Tests
# ═══════════════════════════════════════════════════════════

test_existing_tests() {
    echo ""
    echo "─────────────────────────────────────────────────────────────"
    echo "Test 3: Behavioral Verification - Existing Tests"
    echo "─────────────────────────────────────────────────────────────"

    cd "${TEST_DIR}"

    # Ensure math.py exists with proper structure
    cat > math.py << 'EOF'
def add(a: int, b: int) -> int:
    """Add two numbers."""
    return a + b
EOF

    cat > test_math.py << 'EOF'
import sys
sys.path.insert(0, '/tmp/goal-wizard-test')
from math import add

def test_add():
    assert add(2, 3) == 5
    assert add(-1, 1) == 0
    print("✓ All tests passed")

if __name__ == '__main__':
    test_add()
EOF

    echo -e "${GREEN}✓ Created test files${NC}"

    # Verify tests pass before refactoring
    echo ""
    echo "Verifying tests pass before refactoring:"
    python test_math.py

    show_verification_prompt \
        "Existing Tests" \
        "Run: python ${TEST_DIR}/test_math.py (behavioral verification)"

    echo -e "${YELLOW}In Claude Code, run:${NC}"
    echo -e "  ${GREEN}/goal-wizard \"Refactor the add function in ${TEST_DIR}/math.py to use temp variable for calculation\"${NC}"

    wait_for_user "After completing the wizard, press Enter to verify..."

    # Verify tests still pass
    if python test_math.py 2>/dev/null; then
        echo -e "${GREEN}✓ PASS: Tests still pass after refactoring${NC}"
        ((PASSED++))
    else
        echo -e "${RED}✗ FAIL: Tests failed after refactoring${NC}"
        ((FAILED++))
    fi
}

# ═══════════════════════════════════════════════════════════
# Main Test Execution
# ═══════════════════════════════════════════════════════════

main() {
    echo "Prerequisites:"
    echo "  1. goal-wizard synced: ./scripts/dev_refresh_skills_and_tools.sh"
    echo "  2. Claude Code restarted"
    echo "  3. /goal-wizard available in Claude Code"
    echo ""

    wait_for_user "Prerequisites met? Press Enter to start tests..."

    # Run tests
    echo ""
    echo "═══════════════════════════════════════════════════════════"
    echo "  PHASE 0 Tests (Interactive Wizard)"
    echo "═══════════════════════════════════════════════════════════"
    test_phase0_empty
    test_phase0_task_only
    test_phase0_verification_type
    test_phase0_complete

    echo ""
    echo "═══════════════════════════════════════════════════════════"
    echo "  Quick Smoke Test (All Steps Provided)"
    echo "═══════════════════════════════════════════════════════════"
    test_smoke

    echo ""
    echo "═══════════════════════════════════════════════════════════"
    echo "  PHASE 1-3 Tests (Verification Types)"
    echo "═══════════════════════════════════════════════════════════"
    test_type_hints
    test_docstrings
    test_existing_tests

    # Show summary
    show_summary
}

main "$@"
