#!/bin/bash
# PreToolUse Hook Dispatcher
# Receives JSON on stdin: {"tool_name": "...", "tool_input": {...}}
# Exit 0 = allow, Exit 1 = block (message on stderr shown to agent)

HOOK_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Read JSON input from stdin
INPUT="$(cat)"

TOOL_NAME="$(echo "$INPUT" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('tool_name',''))" 2>/dev/null)"

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
