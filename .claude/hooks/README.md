# Claude Code Hooks

This directory contains hooks that enforce project constraints at runtime.

## Available Hooks

### check_poetry_usage.sh

**Purpose**: Prevents direct usage of system Python/pip commands and enforces Poetry usage.

**What it does**:
- Intercepts bash commands before execution
- Detects direct `python`, `python3`, `pip`, or `pip3` usage
- Blocks the command and suggests the correct Poetry alternative
- Allows commands that are already wrapped in `poetry run`

**Example**:
```bash
# This will be blocked:
python script.py
# Suggested: poetry run python script.py

# This will be blocked:
pip install requests
# Suggested: poetry add requests

# This will be allowed:
poetry run python script.py
poetry add requests
```

## Enabling Hooks

To enable hooks in your project, add them to `.claude/settings.json`:

```json
{
  "hooks": {
    "before_bash": ".claude/hooks/check_poetry_usage.sh"
  }
}
```

**Note**: Hooks are currently an experimental feature and may not be available in all Claude Code versions.

## Creating Custom Hooks

Hooks are bash scripts that:
1. Receive the command as the first argument (`$1`)
2. Return exit code 0 to allow the command
3. Return non-zero exit code to block the command
4. Can write warnings/errors to stderr

Example:
```bash
#!/bin/bash
COMMAND="$1"

if echo "$COMMAND" | grep -q "dangerous_pattern"; then
    echo "ERROR: Dangerous command detected!" >&2
    exit 1
fi

exit 0
```

## Limitations

- Hooks only work for bash commands, not for other tools
- Hooks add latency to command execution
- Hooks can be bypassed if Claude Code doesn't respect them
- Not all Claude Code versions support hooks

## Alternative: Policy-Based Enforcement

If hooks are not available or not working, rely on:
1. Strong constraint language in `.claude/constraints/`
2. Mandatory `/init` at session start to load constraints
3. Pre-commit validation with `/pre-commit`
4. Code review to catch violations
