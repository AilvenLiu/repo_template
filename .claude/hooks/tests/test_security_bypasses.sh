#!/bin/bash
# Pre-Init Security Policy Regression Tests
# Tests that the fail-closed pre-init enforcement works correctly

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
HOOK_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
REPO_ROOT="$(cd "$HOOK_DIR/../.." && pwd)"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

PASSED=0
FAILED=0

# Test helper: run hook and expect it to block (exit 1)
test_blocked() {
    local test_name="$1"
    local json_input="$2"

    echo -n "Testing: $test_name ... "

    if echo "$json_input" | "$HOOK_DIR/pre_tool_use.sh" 2>/dev/null; then
        echo -e "${RED}FAILED${NC} (should have been blocked)"
        FAILED=$((FAILED + 1))
        return 1
    else
        echo -e "${GREEN}PASSED${NC} (correctly blocked)"
        PASSED=$((PASSED + 1))
        return 0
    fi
}

# Test helper: run hook and expect it to allow (exit 0)
test_allowed() {
    local test_name="$1"
    local json_input="$2"

    echo -n "Testing: $test_name ... "

    if echo "$json_input" | "$HOOK_DIR/pre_tool_use.sh" 2>/dev/null; then
        echo -e "${GREEN}PASSED${NC} (correctly allowed)"
        PASSED=$((PASSED + 1))
        return 0
    else
        echo -e "${RED}FAILED${NC} (should have been allowed)"
        FAILED=$((FAILED + 1))
        return 1
    fi
}

echo "========================================================================"
echo "Pre-Init Security Policy Regression Tests"
echo "========================================================================"
echo ""

# Remove session state to simulate pre-init environment
SESSION_STATE="$REPO_ROOT/.claude/session_state.json"
if [ -f "$SESSION_STATE" ]; then
    mv "$SESSION_STATE" "$SESSION_STATE.backup"
    echo "Backed up existing session state"
fi

echo "Testing pre-init enforcement (session_state.json does not exist)"
echo "------------------------------------------------------------------------"
echo ""

# ============================================================================
# Policy Test 1: ALL Write/Edit/MultiEdit operations blocked before init
# ============================================================================
echo "=== Policy 1: Write/Edit/MultiEdit Tools Blocked ==="
echo ""

test_blocked "Write to session_state.json" '{
  "tool_name": "Write",
  "tool_input": {
    "file_path": ".claude/session_state.json",
    "content": "{\"initialized\": true}"
  }
}'

test_blocked "Write to arbitrary file" '{
  "tool_name": "Write",
  "tool_input": {
    "file_path": "src/test.py",
    "content": "print(\"hello\")"
  }
}'

test_blocked "Edit session_state.json" '{
  "tool_name": "Edit",
  "tool_input": {
    "file_path": ".claude/session_state.json",
    "old_string": "old",
    "new_string": "new"
  }
}'

test_blocked "Edit arbitrary file" '{
  "tool_name": "Edit",
  "tool_input": {
    "file_path": "README.md",
    "old_string": "old",
    "new_string": "new"
  }
}'

echo ""

# ============================================================================
# Policy Test 2: ONLY init script allowed via Bash before init
# ============================================================================
echo "=== Policy 2: Only Init Script Allowed via Bash ==="
echo ""

test_allowed "Init script with python3" '{
  "tool_name": "Bash",
  "tool_input": {
    "command": "python3 .claude/skills/init/scripts/init.py"
  }
}'

test_allowed "Init script with python" '{
  "tool_name": "Bash",
  "tool_input": {
    "command": "python .claude/skills/init/scripts/init.py"
  }
}'

test_allowed "Init script with --verbose flag" '{
  "tool_name": "Bash",
  "tool_input": {
    "command": "python3 .claude/skills/init/scripts/init.py --verbose"
  }
}'

echo ""

# ============================================================================
# Policy Test 3: ALL other Bash commands blocked before init
# ============================================================================
echo "=== Policy 3: All Other Bash Commands Blocked ==="
echo ""

# Previously-allowed read-only commands are now blocked
test_blocked "ls command" '{
  "tool_name": "Bash",
  "tool_input": {
    "command": "ls -la"
  }
}'

test_blocked "cat command" '{
  "tool_name": "Bash",
  "tool_input": {
    "command": "cat README.md"
  }
}'

test_blocked "git status" '{
  "tool_name": "Bash",
  "tool_input": {
    "command": "git status"
  }
}'

test_blocked "echo command" '{
  "tool_name": "Bash",
  "tool_input": {
    "command": "echo hello"
  }
}'

echo ""

# ============================================================================
# Policy Test 4: Shell bypass attempts all blocked
# ============================================================================
echo "=== Policy 4: Shell Bypass Attempts Blocked ==="
echo ""

test_blocked "Echo redirect to session_state.json" '{
  "tool_name": "Bash",
  "tool_input": {
    "command": "echo test > .claude/session_state.json"
  }
}'

test_blocked "Echo redirect with absolute path" '{
  "tool_name": "Bash",
  "tool_input": {
    "command": "echo test > /full/path/.claude/session_state.json"
  }
}'

test_blocked "Echo redirect with tilde" '{
  "tool_name": "Bash",
  "tool_input": {
    "command": "echo test > ~/.claude/session_state.json"
  }
}'

test_blocked "Echo append redirect" '{
  "tool_name": "Bash",
  "tool_input": {
    "command": "echo test >> .claude/session_state.json"
  }
}'

test_blocked "Command chaining with &&" '{
  "tool_name": "Bash",
  "tool_input": {
    "command": "ls && echo test > src/file.py"
  }
}'

test_blocked "Command chaining with ;" '{
  "tool_name": "Bash",
  "tool_input": {
    "command": "cat README.md; rm -rf src/"
  }
}'

test_blocked "Command chaining with ||" '{
  "tool_name": "Bash",
  "tool_input": {
    "command": "false || echo malicious > .claude/session_state.json"
  }
}'

test_blocked "Command chaining with pipe" '{
  "tool_name": "Bash",
  "tool_input": {
    "command": "echo test | tee .claude/session_state.json"
  }
}'

test_blocked "Subshell bypass" '{
  "tool_name": "Bash",
  "tool_input": {
    "command": "(echo test > .claude/session_state.json)"
  }
}'

test_blocked "Command substitution bypass" '{
  "tool_name": "Bash",
  "tool_input": {
    "command": "echo $(echo test > .claude/session_state.json)"
  }
}'

echo ""

# ============================================================================
# Policy Test 5: Init-prefix bypass attempts all blocked
#
# These test the specific vulnerability reported:
#   "python3 .claude/skills/init/scripts/init.py && echo hacked"
# passes the OLD prefix-match check but must be blocked by the new code.
# ============================================================================
echo "=== Policy 5: Init-Prefix Bypass Attempts Blocked ==="
echo ""
echo "These test that chaining/injection after the init path is rejected."
echo ""

test_blocked "init && command chaining (&&)" '{
  "tool_name": "Bash",
  "tool_input": {
    "command": "python3 .claude/skills/init/scripts/init.py && echo hacked > .claude/session_state.json"
  }
}'

test_blocked "init ; command chaining (;)" '{
  "tool_name": "Bash",
  "tool_input": {
    "command": "python3 .claude/skills/init/scripts/init.py; echo hacked > .claude/session_state.json"
  }
}'

test_blocked "init | pipe injection" '{
  "tool_name": "Bash",
  "tool_input": {
    "command": "python3 .claude/skills/init/scripts/init.py | tee .claude/session_state.json"
  }
}'

test_blocked "init with dollar-paren command substitution" '{
  "tool_name": "Bash",
  "tool_input": {
    "command": "python3 .claude/skills/init/scripts/init.py $(echo hacked)"
  }
}'

test_blocked "init with backtick command substitution" '{
  "tool_name": "Bash",
  "tool_input": {
    "command": "python3 .claude/skills/init/scripts/init.py `echo hacked`"
  }
}'

test_blocked "init with newline-separated suffix" '{
  "tool_name": "Bash",
  "tool_input": {
    "command": "python3 .claude/skills/init/scripts/init.py\necho hacked > .claude/session_state.json"
  }
}'

test_blocked "init with unknown flag (not in allowlist)" '{
  "tool_name": "Bash",
  "tool_input": {
    "command": "python3 .claude/skills/init/scripts/init.py --unknown-flag"
  }
}'

test_blocked "init with extra positional argument" '{
  "tool_name": "Bash",
  "tool_input": {
    "command": "python3 .claude/skills/init/scripts/init.py extra_arg"
  }
}'

test_blocked "init with redirect output" '{
  "tool_name": "Bash",
  "tool_input": {
    "command": "python3 .claude/skills/init/scripts/init.py > .claude/session_state.json"
  }
}'

test_blocked "init with input redirect" '{
  "tool_name": "Bash",
  "tool_input": {
    "command": "python3 .claude/skills/init/scripts/init.py < /etc/passwd"
  }
}'

test_blocked "init with env var expansion" '{
  "tool_name": "Bash",
  "tool_input": {
    "command": "python3 .claude/skills/init/scripts/init.py $HOME"
  }
}'

test_blocked "init with || chaining" '{
  "tool_name": "Bash",
  "tool_input": {
    "command": "python3 .claude/skills/init/scripts/init.py || echo hacked > .claude/session_state.json"
  }
}'

echo ""

# ============================================================================
# Restore session state and test post-init
# ============================================================================
echo "========================================================================"
echo "Testing post-init enforcement (session_state.json exists)"
echo "------------------------------------------------------------------------"
echo ""

# Create a minimal session state
cat > "$SESSION_STATE" <<'EOF'
{
  "initialized": true,
  "timestamp": "2026-03-16T00:00:00",
  "project_type": "python",
  "branch": "master",
  "loaded_constraints": []
}
EOF

echo "Created minimal session_state.json"
echo ""

# ============================================================================
# Post-init: python -m pip should still be blocked
# ============================================================================
echo "=== Post-Init: python -m pip Blocking ==="
echo ""

test_blocked "python -m pip install" '{
  "tool_name": "Bash",
  "tool_input": {
    "command": "python -m pip install requests"
  }
}'

test_blocked "python3 -m pip install" '{
  "tool_name": "Bash",
  "tool_input": {
    "command": "python3 -m pip install numpy"
  }
}'

test_blocked "python3.11 -m pip install" '{
  "tool_name": "Bash",
  "tool_input": {
    "command": "python3.11 -m pip install pandas"
  }
}'

# Verify regular pip is still blocked
test_blocked "pip install (baseline)" '{
  "tool_name": "Bash",
  "tool_input": {
    "command": "pip install requests"
  }
}'

test_blocked "pip3 install (baseline)" '{
  "tool_name": "Bash",
  "tool_input": {
    "command": "pip3 install requests"
  }
}'

echo ""

# ============================================================================
# Cleanup and summary
# ============================================================================
echo "========================================================================"
echo "Cleanup"
echo "------------------------------------------------------------------------"

# Remove test session state
rm -f "$SESSION_STATE"

# Restore original if it existed
if [ -f "$SESSION_STATE.backup" ]; then
    mv "$SESSION_STATE.backup" "$SESSION_STATE"
    echo "Restored original session state"
else
    echo "Removed test session state"
fi

echo ""
echo "========================================================================"
echo "Test Summary"
echo "========================================================================"
echo ""
echo -e "${GREEN}PASSED: $PASSED${NC}"
echo -e "${RED}FAILED: $FAILED${NC}"
echo ""

if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}All tests passed!${NC}"
    exit 0
else
    echo -e "${RED}Some tests failed. Review the output above.${NC}"
    exit 1
fi
