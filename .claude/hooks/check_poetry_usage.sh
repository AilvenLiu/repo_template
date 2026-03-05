#!/bin/bash
# Poetry Enforcement Hook
# This hook checks if commands are using system Python instead of Poetry
# and provides warnings to guide the agent toward correct usage.
# It also enforces Python 3.10+ requirement for Poetry projects.

COMMAND="$1"

# Check if this is a Python project
if [ ! -f "pyproject.toml" ] && [ ! -f "requirements.txt" ]; then
    # Not a Python project, allow command
    exit 0
fi

# Check if this is a Poetry project
IS_POETRY_PROJECT=false
if [ -f "pyproject.toml" ]; then
    if grep -q "\[tool.poetry\]" pyproject.toml || grep -q "poetry-core" pyproject.toml; then
        IS_POETRY_PROJECT=true
    fi
fi

# For Poetry projects, check Python version requirement
if [ "$IS_POETRY_PROJECT" = true ]; then
    # Check if Python 3.10+ is available
    PYTHON_VERSION=""
    if command -v python3.10 &> /dev/null; then
        PYTHON_VERSION="3.10+"
    elif command -v python3.11 &> /dev/null; then
        PYTHON_VERSION="3.11+"
    elif command -v python3.12 &> /dev/null; then
        PYTHON_VERSION="3.12+"
    elif command -v python3 &> /dev/null; then
        # Check if python3 is 3.10+
        PY_VERSION=$(python3 --version 2>&1 | grep -oP '(?<=Python )\d+\.\d+')
        PY_MAJOR=$(echo $PY_VERSION | cut -d. -f1)
        PY_MINOR=$(echo $PY_VERSION | cut -d. -f2)
        if [ "$PY_MAJOR" -eq 3 ] && [ "$PY_MINOR" -ge 10 ]; then
            PYTHON_VERSION="$PY_VERSION"
        fi
    fi

    if [ -z "$PYTHON_VERSION" ]; then
        echo "ERROR: Python 3.10+ is required for Poetry projects" >&2
        echo "" >&2
        echo "  This project uses Poetry, which requires Python 3.10 or higher." >&2
        echo "" >&2
        echo "  Install Python 3.10+ using one of these methods:" >&2
        echo "" >&2
        echo "  Option 1: Using pyenv (Recommended)" >&2
        echo "    curl https://pyenv.run | bash" >&2
        echo "    pyenv install 3.10" >&2
        echo "    pyenv global 3.10" >&2
        echo "" >&2
        echo "  Option 2: Using system package manager" >&2
        echo "    # macOS: brew install python@3.10" >&2
        echo "    # Ubuntu: sudo apt install python3.10 python3.10-venv" >&2
        echo "    # Fedora: sudo dnf install python3.10" >&2
        echo "" >&2
        echo "  See .claude/constraints/python/dependencies.md for details" >&2
        echo "" >&2
        exit 1
    fi
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
