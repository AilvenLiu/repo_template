#!/bin/bash
# Write Gate: delegates init/audit policy to .ai/scripts/policy_gate.py and keeps file guards.

set -euo pipefail

INPUT="$1"
HOOK_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
REPO_ROOT="$(cd "$HOOK_DIR/../.." && pwd)"

FILE_PATH="$(echo "$INPUT" | python3 -c '
import json,sys
try:
    d=json.load(sys.stdin)
    print(d.get("tool_input",{}).get("file_path",""))
except Exception:
    print("")
' 2>/dev/null)"

if [ -z "$FILE_PATH" ]; then
    python3 "$REPO_ROOT/.ai/scripts/policy_gate.py" --op mutate --context '{}' >/dev/null
    exit 0
fi

CONTEXT_JSON="$(python3 -c '
import json,sys
print(json.dumps({"file_path": sys.argv[1]}))
' "$FILE_PATH")"

# Shared mutate gate (session initialized + audit passed + high-risk file policy)
python3 "$REPO_ROOT/.ai/scripts/policy_gate.py" --op mutate --context "$CONTEXT_JSON" >/dev/null

if echo "$FILE_PATH" | grep -qE '\.claude/settings\.json$'; then
    echo "WARNING: Modifying .claude/settings.json changes hook enforcement." >&2
    exit 0
fi

if echo "$FILE_PATH" | grep -qE '(^|/)pyproject\.toml$|(^|/)CMakeLists\.txt$|(^|/)cmake/Dependencies\.cmake$|(^|/)cmake/Options\.cmake$'; then
    echo "WARNING: This file can affect dependency/build ownership. Run .ai/bin/agent-check-constraints before final response." >&2
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
