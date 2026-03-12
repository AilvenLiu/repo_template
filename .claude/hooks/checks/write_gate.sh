#!/bin/bash
# Write Gate: intercepts Write/Edit/MultiEdit tool calls and blocks policy violations
# Receives raw JSON string as $1

INPUT="$1"

# Extract file path from tool_input
FILE_PATH="$(echo "$INPUT" | python3 -c "
import sys, json
d = json.load(sys.stdin)
inp = d.get('tool_input', {})
# Write uses 'file_path', Edit uses 'file_path', MultiEdit uses 'file_path'
print(inp.get('file_path', ''))
" 2>/dev/null)"

if [ -z "$FILE_PATH" ]; then
    exit 0
fi

# ── 1. Block writes to .claude/settings.json without awareness ───────────────
# settings.json controls hook wiring — changes here affect enforcement itself
if echo "$FILE_PATH" | grep -qE '\.claude/settings\.json$'; then
    echo "WARNING: Modifying .claude/settings.json changes hook enforcement." >&2
    echo "" >&2
    echo "  This file controls which hooks are active and which commands are" >&2
    echo "  auto-approved. Verify the change is intentional." >&2
    echo "" >&2
    # Warn only, do not block — the agent may legitimately need to update this
    exit 0
fi

# ── 2. Block writes to roadmap INVARIANTS.md without explicit instruction ────
if echo "$FILE_PATH" | grep -qE 'agent_roadmaps/.+/INVARIANTS\.md$'; then
    echo "BLOCKED: Modifying roadmap INVARIANTS.md." >&2
    echo "" >&2
    echo "  INVARIANTS.md is the highest-authority document in an active roadmap." >&2
    echo "  It must not be modified without explicit user instruction." >&2
    echo "" >&2
    echo "  If the user has explicitly asked you to update INVARIANTS.md," >&2
    echo "  ask them to confirm before proceeding." >&2
    exit 1
fi

# ── 3. Block writes to .git/ directory ───────────────────────────────────────
if echo "$FILE_PATH" | grep -qE '^\.git/|/\.git/'; then
    echo "BLOCKED: Direct write to .git/ directory." >&2
    echo "" >&2
    echo "  Git internals must not be modified directly." >&2
    echo "  Use git commands instead." >&2
    exit 1
fi

# Allow all other writes
exit 0
