#!/bin/bash
# PreToolUse Hook Dispatcher
# Receives JSON on stdin: {"tool_name": "...", "tool_input": {...}}
# Exit 0 = allow, Exit 1 = block (message on stderr shown to agent)

HOOK_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$HOOK_DIR/../.." && pwd)"

# Read JSON input from stdin
INPUT="$(cat)"

TOOL_NAME="$(echo "$INPUT" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('tool_name',''))" 2>/dev/null)"

# Fail closed: if we couldn't parse the tool name, block the call
if [ -z "$TOOL_NAME" ]; then
    echo "BLOCKED: Hook failed to parse tool input JSON." >&2
    echo "  This is a safety measure — please report this if it persists." >&2
    exit 1
fi

# ── 0. Pre-init gate (FAIL-CLOSED) ───────────────────────────────────────────
# Before session initialization, use a strict allowlist approach:
# - Block ALL Write/Edit/MultiEdit operations (no exceptions)
# - Allow Bash ONLY for the exact init script invocation
# - After init, delegate to post-init policy gates
SESSION_STATE="$REPO_ROOT/.agents/session_state.json"

if [ ! -f "$SESSION_STATE" ]; then
    case "$TOOL_NAME" in
        Write|Edit|MultiEdit)
            # Block ALL writes before init - no exceptions
            # Only the init script (via Bash tool) can create session_state.json
            echo "BLOCKED: Session not initialized." >&2
            echo "" >&2
            echo "  Run /init before making any changes." >&2
            echo "  Read-only exploration (Read, Glob, Grep) is allowed before init." >&2
            exit 1
            ;;
        Bash)
            COMMAND="$(echo "$INPUT" | python3 -c "
import sys, json
d = json.load(sys.stdin)
print(d.get('tool_input', {}).get('command', ''))
" 2>/dev/null)"

            # Fail closed: if command parsing failed, block
            if [ -z "$COMMAND" ]; then
                echo "BLOCKED: Failed to parse Bash command." >&2
                echo "  This is a safety measure — please report this if it persists." >&2
                exit 1
            fi

            # ALLOWLIST: Only permit the canonical session-init wrapper.
            # Allowed forms:
            #   .agents/bin/agent-init
            #   .agents/bin/agent-init --platform claude
            #   .agents/bin/agent-init --platform codex
            #   .agents/bin/agent-init --verbose
            #
            # First, reject any command containing shell metacharacters that could
            # be used for command chaining, injection, or redirection.
            if echo "$COMMAND" | grep -qE '[;&|<>$`\\]'; then
                echo "BLOCKED: Shell metacharacters detected in command." >&2
                echo "  Only the plain init wrapper is allowed before initialization." >&2
                exit 1
            fi

            # Validate against exact allowed pattern (entire command must match)
            if echo "$COMMAND" | grep -qE '^\s*\.agents/bin/agent-init(\s+--platform\s+(claude|codex))?(\s+--verbose)?\s*$'; then
                exit 0
            fi

            # Everything else is blocked before init
            echo "BLOCKED: Session not initialized." >&2
            echo "" >&2
            echo "  Run /init before executing any commands." >&2
            echo "  Only the init script is allowed before initialization." >&2
            echo "" >&2
            echo "  After running /init, you can use:" >&2
            echo "    - Read, Glob, Grep for exploration" >&2
            echo "    - Bash for git commands and other operations" >&2
            echo "    - Write, Edit for making changes" >&2
            exit 1
            ;;
    esac
fi

# ── 1. Post-init capability audit gate ───────────────────────────────────────
# After init, check if capability audit failed
# If audit failed, block all mutation operations (Write/Edit/Bash)
# Allow read-only operations (Read/Glob/Grep) to continue
if [ -f "$SESSION_STATE" ]; then
    AUDIT_PASSED="$(python3 -c "
import sys, json
try:
    with open('$SESSION_STATE') as f:
        state = json.load(f)
    audit = state.get('capability_audit')
    if audit is None:
        # No audit recorded - assume pass for backwards compatibility
        print('true')
    else:
        print('true' if audit.get('passed', True) else 'false')
except:
    # If we can't read state, fail closed
    print('false')
" 2>/dev/null)"

    if [ "$AUDIT_PASSED" = "false" ]; then
        case "$TOOL_NAME" in
            Write|Edit|MultiEdit|Bash)
                echo "BLOCKED: Capability audit failed." >&2
                echo "" >&2
                echo "  The session capability audit failed during /init." >&2
                echo "  Mutation operations are blocked until the audit passes." >&2
                echo "" >&2
                echo "  REQUIRED ACTION:" >&2
                echo "    1. Review the audit failures from /init output" >&2
                echo "    2. Install missing plugins, skills, or integrations" >&2
                echo "    3. Re-run /init to pass the audit" >&2
                echo "" >&2
                echo "  Read-only operations (Read, Glob, Grep) remain available." >&2
                exit 1
                ;;
        esac
    fi
fi

# ── Dispatch to specific gates ────────────────────────────────────────────────
case "$TOOL_NAME" in
    Bash)
        exec "$HOOK_DIR/checks/bash_gate.sh" "$INPUT"
        ;;
    Write|Edit|MultiEdit)
        exec "$HOOK_DIR/checks/write_gate.sh" "$INPUT"
        ;;
    *)
        exit 0
        ;;
esac
