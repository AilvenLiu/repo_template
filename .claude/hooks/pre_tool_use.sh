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
SESSION_STATE="$REPO_ROOT/.claude/session_state.json"

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

            # ALLOWLIST: Only permit the exact init script invocation
            # We must validate the ENTIRE command to prevent injection attacks.
            # Allowed forms:
            #   python3 .claude/skills/init/scripts/init.py
            #   python3 .claude/skills/init/scripts/init.py --verbose
            #   python .claude/skills/init/scripts/init.py
            #   python .claude/skills/init/scripts/init.py --verbose
            #
            # First, reject any command containing shell metacharacters that could
            # be used for command chaining, injection, or redirection.
            if echo "$COMMAND" | grep -qE '[;&|<>$`\\]'; then
                echo "BLOCKED: Shell metacharacters detected in command." >&2
                echo "  Only the plain init script invocation is allowed before initialization." >&2
                exit 1
            fi

            # Now validate against exact allowed patterns (entire command must match)
            if echo "$COMMAND" | grep -qE '^\s*python3?\s+\.claude/skills/init/scripts/init\.py\s*$'; then
                # Init script with no arguments - allow
                exit 0
            elif echo "$COMMAND" | grep -qE '^\s*python3?\s+\.claude/skills/init/scripts/init\.py\s+--verbose\s*$'; then
                # Init script with --verbose flag - allow
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
