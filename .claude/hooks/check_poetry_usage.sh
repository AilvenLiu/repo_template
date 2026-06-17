#!/bin/bash
# Poetry Enforcement Hook
#
# Blocks direct use of system Python/pip commands and enforces:
#   1. Poetry as the only dependency/environment tool
#   2. Poetry installed via pipx at ~/.local/bin
#   3. Python 3.10+ available
#
# This hook is non-negotiable. There are no "trivial project" exceptions.

COMMAND="$1"

# Not a Python project — allow all commands
if [ ! -f "pyproject.toml" ] && [ ! -f "requirements.txt" ]; then
    exit 0
fi

# -----------------------------------------------------------------------
# Block: direct pip / pip3 / python / python3 usage
# These are forbidden in all Python projects without exception.
# -----------------------------------------------------------------------

if echo "$COMMAND" | grep -qE "^[[:space:]]*(pip3?|python3?)[[:space:]]"; then
    # Allow commands that are already wrapped in 'poetry run'
    if echo "$COMMAND" | grep -q "poetry run"; then
        exit 0
    fi

    # Allow agent infrastructure scripts (controlled runtime)
    if echo "$COMMAND" | grep -qE "bin/agent-|\.ai/scripts/"; then
        exit 0
    fi

    echo "ERROR: Direct Python/pip command is forbidden." >&2
    echo "  Command: $COMMAND" >&2
    echo "" >&2
    echo "  REQUIRED: Use Poetry for all Python operations." >&2
    echo "" >&2

    if echo "$COMMAND" | grep -qE "^[[:space:]]*(pip3?)[[:space:]]+install"; then
        PKG=$(echo "$COMMAND" | sed -E 's/^[[:space:]]*(pip3?)[[:space:]]+install[[:space:]]+//')
        echo "  Instead of: $COMMAND" >&2
        echo "  Use:        poetry add $PKG" >&2
    elif echo "$COMMAND" | grep -qE "^[[:space:]]*(python3?)[[:space:]]"; then
        SCRIPT=$(echo "$COMMAND" | sed -E 's/^[[:space:]]*(python3?)[[:space:]]+//')
        echo "  Instead of: $COMMAND" >&2
        echo "  Use:        poetry run python $SCRIPT" >&2
    fi

    echo "" >&2
    echo "  See .ai/constraints/python/dependencies.md for full policy." >&2
    exit 1
fi

# -----------------------------------------------------------------------
# For Poetry projects: verify Poetry is installed via pipx and Python 3.10+
# -----------------------------------------------------------------------

IS_POETRY_PROJECT=false
if [ -f "pyproject.toml" ]; then
    if grep -q "\[tool.poetry\]" pyproject.toml 2>/dev/null || \
       grep -q "poetry-core" pyproject.toml 2>/dev/null; then
        IS_POETRY_PROJECT=true
    fi
fi

if [ "$IS_POETRY_PROJECT" = true ]; then

    # Check Python 3.10+
    PYTHON_OK=false
    for pybin in python3.10 python3.11 python3.12 python3.13; do
        if command -v "$pybin" &>/dev/null; then
            PYTHON_OK=true
            break
        fi
    done
    if [ "$PYTHON_OK" = false ] && command -v python3 &>/dev/null; then
        PY_MINOR=$(python3 -c "import sys; print(sys.version_info.minor)" 2>/dev/null)
        [ "${PY_MINOR:-0}" -ge 10 ] && PYTHON_OK=true
    fi

    if [ "$PYTHON_OK" = false ]; then
        echo "ERROR: Python 3.10+ is required for Poetry projects." >&2
        echo "  Install via pyenv:" >&2
        echo "    curl https://pyenv.run | bash" >&2
        echo "    pyenv install 3.10.12 && pyenv local 3.10.12" >&2
        exit 1
    fi

    # Check Poetry is installed via pipx at ~/.local/bin
    EXPECTED_POETRY="$HOME/.local/bin/poetry"
    if [ ! -f "$EXPECTED_POETRY" ]; then
        echo "ERROR: Poetry not found at ~/.local/bin/poetry." >&2
        echo "" >&2
        echo "  Poetry MUST be installed via pipx into \$HOME/.local:" >&2
        echo "" >&2
        echo '  PIPX_HOME="$HOME/.local/share/pipx" \\' >&2
        echo '  PIPX_BIN_DIR="$HOME/.local/bin" \\' >&2
        echo '  pipx install poetry' >&2
        echo "" >&2
        echo "  Do NOT use: curl -sSL https://install.python-poetry.org | python3 -" >&2
        echo "  Do NOT use: pip install poetry" >&2
        echo "  Do NOT use: brew install poetry" >&2
        exit 1
    fi

fi

# Allow command
exit 0
