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

# ── 0. Pre-init gate ─────────────────────────────────────────────────────────
# Block mutating tools (Write/Edit/MultiEdit/Bash-that-mutates) until
# session_state.json exists, UNLESS the command is the init skill itself
# or a read-only exploration.
SESSION_STATE="$REPO_ROOT/.claude/session_state.json"

if [ ! -f "$SESSION_STATE" ]; then
    case "$TOOL_NAME" in
        Write|Edit|MultiEdit)
            # Allow writes to session_state.json itself (init creates it)
            FILE_PATH="$(echo "$INPUT" | python3 -c "
import sys, json
d = json.load(sys.stdin)
print(d.get('tool_input', {}).get('file_path', ''))
" 2>/dev/null)"
            if [ "$FILE_PATH" = "$SESSION_STATE" ]; then
                # init is writing session state — allow
                :
            else
                echo "BLOCKED: Session not initialized." >&2
                echo "" >&2
                echo "  Run /init before making any changes." >&2
                echo "  Read-only exploration is allowed before init." >&2
                exit 1
            fi
            ;;
        Bash)
            COMMAND="$(echo "$INPUT" | python3 -c "
import sys, json
d = json.load(sys.stdin)
print(d.get('tool_input', {}).get('command', ''))
" 2>/dev/null)"
            # Allow: init skill, read-only commands, git read commands
            # Anchor patterns to start-of-command to prevent injection via chaining
            if echo "$COMMAND" | grep -qE '^\s*(python3?\s+)?\.claude/skills/(init|common)/'; then
                :  # init/bootstrap path — allow
            elif echo "$COMMAND" | grep -qE '^\s*(cat|head|tail|less|ls|tree|find|wc|grep|rg|git\s+(status|log|diff|branch|show|remote)|python3?\s+--version|which|echo|pwd|source)\b'; then
                :  # read-only — allow
            else
                echo "BLOCKED: Session not initialized." >&2
                echo "" >&2
                echo "  Run /init before executing mutating commands." >&2
                echo "  Read-only exploration (ls, cat, git status, etc.) is allowed." >&2
                exit 1
            fi
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
