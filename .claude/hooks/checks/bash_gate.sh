#!/bin/bash
# Bash Gate adapter: delegates command policy checks to .ai/tools/policy_gate.py

set -euo pipefail

INPUT="$1"
HOOK_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
REPO_ROOT="$(cd "$HOOK_DIR/.." && pwd)"

COMMAND="$(echo "$INPUT" | python3 -c '
import json,sys
try:
    d=json.load(sys.stdin)
    print(d.get("tool_input",{}).get("command",""))
except Exception:
    print("")
' 2>/dev/null)"

if [ -z "$COMMAND" ]; then
    echo "BLOCKED: bash_gate failed to parse command from hook input." >&2
    exit 1
fi

CONTEXT_JSON="$(python3 -c '
import json,sys
cmd=sys.argv[1]
print(json.dumps({"command": cmd}))
' "$COMMAND")"

python3 "$REPO_ROOT/.ai/tools/policy_gate.py" --op bash --context "$CONTEXT_JSON"
