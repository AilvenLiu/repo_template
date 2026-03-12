#!/bin/bash
# Bash Gate: intercepts Bash tool calls and blocks policy violations
# Receives raw JSON string as $1

INPUT="$1"

# Extract the command from tool_input.command
COMMAND="$(echo "$INPUT" | python3 -c "
import sys, json
d = json.load(sys.stdin)
print(d.get('tool_input', {}).get('command', ''))
" 2>/dev/null)"

if [ -z "$COMMAND" ]; then
    exit 0
fi

# ── 1. Protected branch commit gate ─────────────────────────────────────────
# Block: git commit when on a protected branch
if echo "$COMMAND" | grep -qE '^\s*git\s+commit'; then
    BRANCH="$(git branch --show-current 2>/dev/null)"
    if echo "$BRANCH" | grep -qE '^(master|main|develop)$|^(release|hotfix)/'; then
        echo "BLOCKED: git commit on protected branch '$BRANCH'." >&2
        echo "" >&2
        echo "  You MUST create a feature branch first:" >&2
        echo "    git checkout -b feat/<description>" >&2
        echo "" >&2
        echo "  See .claude/constraints/common/git-workflow.md" >&2
        exit 1
    fi
fi

# ── 2. Force push / hard reset gate ─────────────────────────────────────────
if echo "$COMMAND" | grep -qE 'git\s+push\s+.*--force|git\s+push\s+.*-f\b'; then
    echo "BLOCKED: git push --force requires explicit user confirmation." >&2
    echo "" >&2
    echo "  Force-pushing can overwrite upstream history and is irreversible." >&2
    echo "  Ask the user to confirm before proceeding." >&2
    exit 1
fi

if echo "$COMMAND" | grep -qE 'git\s+reset\s+--hard'; then
    echo "BLOCKED: git reset --hard requires explicit user confirmation." >&2
    echo "" >&2
    echo "  This discards all uncommitted changes and is irreversible." >&2
    echo "  Ask the user to confirm before proceeding." >&2
    exit 1
fi

# ── 3. Direct pip install gate ───────────────────────────────────────────────
# Block pip install / pip3 install not wrapped in poetry run
if echo "$COMMAND" | grep -qE '^\s*(pip|pip3)\s+install'; then
    # Allow: poetry run pip install (rare but valid for some tooling)
    if echo "$COMMAND" | grep -q 'poetry run'; then
        exit 0
    fi
    PKG="$(echo "$COMMAND" | sed -E 's/^\s*pip[0-9]* install //')"
    echo "BLOCKED: Direct pip install detected." >&2
    echo "" >&2
    echo "  Use the /dependency skill instead:" >&2
    echo "    /dependency add $PKG" >&2
    echo "" >&2
    echo "  This ensures Poetry manages the virtual environment and lock file." >&2
    echo "  See .claude/constraints/python/dependencies.md" >&2
    exit 1
fi

# ── 4. Direct python/python3 execution gate ──────────────────────────────────
# Block: python script.py or python3 script.py not wrapped in poetry run
# Allow: python3 .claude/skills/... (internal tooling)
# Allow: poetry run python ...
# Allow: python3 -m pytest (common CI pattern, warn only)
if echo "$COMMAND" | grep -qE '^\s*(python|python3)\s+'; then
    # Allow internal skill scripts
    if echo "$COMMAND" | grep -qE '\.claude/skills/|\.claude/hooks/'; then
        exit 0
    fi
    # Allow poetry run wrapping
    if echo "$COMMAND" | grep -q 'poetry run'; then
        exit 0
    fi
    # Allow pyenv / python version checks
    if echo "$COMMAND" | grep -qE 'python[0-9.]* --version|python[0-9.]* -V'; then
        exit 0
    fi
    echo "BLOCKED: Direct python/python3 usage detected." >&2
    echo "" >&2
    SCRIPT="$(echo "$COMMAND" | sed -E 's/^\s*python[0-9.]* //')"
    echo "  Use Poetry instead:" >&2
    echo "    poetry run python $SCRIPT" >&2
    echo "" >&2
    echo "  See .claude/constraints/python/dependencies.md" >&2
    exit 1
fi

# ── 5. System package manager gate (C++ library installs) ────────────────────
# Block: apt install / yum install / brew install for C++ libraries
# (brew install python/cmake/conan are legitimate toolchain installs — allow those)
if echo "$COMMAND" | grep -qE '^\s*(sudo\s+)?(apt|apt-get)\s+install'; then
    # Check if it looks like a C++ library (lib* prefix or known patterns)
    if echo "$COMMAND" | grep -qE 'lib[a-z]+-dev|libboost|libopencv|libeigen|libfmt|libspdlog|libgtest'; then
        echo "BLOCKED: System package manager used for C++ library." >&2
        echo "" >&2
        echo "  Use the /dependency skill instead:" >&2
        echo "    /dependency add <package>" >&2
        echo "" >&2
        echo "  This ensures Conan manages reproducible builds." >&2
        echo "  See .claude/constraints/cpp/dependencies.md" >&2
        exit 1
    fi
fi

if echo "$COMMAND" | grep -qE '^\s*brew\s+install'; then
    # Allow toolchain installs (cmake, conan, python, llvm, clang-format)
    if echo "$COMMAND" | grep -qE 'brew install (cmake|conan|python|llvm|clang-format|cppcheck|ninja|pkg-config|git)'; then
        exit 0
    fi
    # Block everything else via brew (likely a C++ library)
    PKG="$(echo "$COMMAND" | sed -E 's/^\s*brew install //')"
    echo "BLOCKED: brew install for non-toolchain package '$PKG'." >&2
    echo "" >&2
    echo "  For C++ libraries, use the /dependency skill:" >&2
    echo "    /dependency add $PKG" >&2
    echo "" >&2
    echo "  If this is a legitimate toolchain install, proceed manually." >&2
    echo "  See .claude/constraints/cpp/dependencies.md" >&2
    exit 1
fi

# ── 6. Destructive file operations gate ──────────────────────────────────────
if echo "$COMMAND" | grep -qE 'rm\s+-rf\s+'; then
    # Block rm -rf on anything that looks like source code or config
    if echo "$COMMAND" | grep -qE 'rm\s+-rf\s+\./?(src|lib|include|tests?|\.claude|agent_roadmaps)'; then
        echo "BLOCKED: rm -rf on a protected directory." >&2
        echo "" >&2
        echo "  This would destroy source code or project configuration." >&2
        echo "  Ask the user to confirm before proceeding." >&2
        exit 1
    fi
fi

# Allow all other commands
exit 0
