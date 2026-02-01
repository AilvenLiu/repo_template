#!/bin/bash
# Poetry Enforcement Hook
# This hook checks if commands are using system Python instead of Poetry
# and provides warnings to guide the agent toward correct usage.

COMMAND="$1"

# Check if this is a Python project
if [ ! -f "pyproject.toml" ] && [ ! -f "requirements.txt" ]; then
    # Not a Python project, allow command
    exit 0
fi

# Check for forbidden patterns
if echo "$COMMAND" | grep -qE "^(python|python3|pip|pip3)\s"; then
    # Check if it's already wrapped in poetry run
    if ! echo "$COMMAND" | grep -q "poetry run"; then
        echo "WARNING: Direct Python/pip usage detected!" >&2
        echo "  Command: $COMMAND" >&2
        echo "" >&2
        echo "  You should use Poetry instead:" >&2

        if echo "$COMMAND" | grep -qE "^pip\s+install"; then
            PKG=$(echo "$COMMAND" | sed 's/^pip[0-9]* install //')
            echo "  Correct: poetry add $PKG" >&2
        elif echo "$COMMAND" | grep -qE "^python[0-9]*\s"; then
            SCRIPT=$(echo "$COMMAND" | sed 's/^python[0-9]* //')
            echo "  Correct: poetry run python $SCRIPT" >&2
        fi

        echo "" >&2
        echo "  See .claude/constraints/python/dependencies.md for details" >&2
        echo "" >&2

        # Return non-zero to block the command
        exit 1
    fi
fi

# Allow command
exit 0
