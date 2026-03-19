#!/bin/bash
# Write Gate: delegates init/audit policy to .ai/tools/policy_gate.py and keeps file guards.

set -euo pipefail

INPUT="$1"
HOOK_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
REPO_ROOT="$(cd "$HOOK_DIR/.." && pwd)"

# Shared mutate gate (session initialized + audit passed)
python3 "$REPO_ROOT/.ai/tools/policy_gate.py" --op mutate --context '{}' >/dev/null

FILE_PATH="$(echo "$INPUT" | python3 -c '
import json,sys
try:
    d=json.load(sys.stdin)
    print(d.get("tool_input",{}).get("file_path",""))
except Exception:
    print("")
' 2>/dev/null)"

if [ -z "$FILE_PATH" ]; then
    exit 0
fi

if echo "$FILE_PATH" | grep -qE '\.claude/settings\.json$'; then
    echo "WARNING: Modifying .claude/settings.json changes hook enforcement." >&2
    exit 0
fi

if echo "$FILE_PATH" | grep -qE 'agent_roadmaps/.+/INVARIANTS\.md$'; then
    echo "BLOCKED: Modifying roadmap INVARIANTS.md requires explicit user instruction." >&2
    exit 1
fi

if echo "$FILE_PATH" | grep -qE '^\.git/|/\.git/'; then
    echo "BLOCKED: Direct write to .git/ directory." >&2
    exit 1
fi

exit 0
