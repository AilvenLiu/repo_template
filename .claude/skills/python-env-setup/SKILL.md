---
name: python-env-setup
description: Diagnose and fix pyenv+Poetry environment configuration issues. Detects VIRTUAL_ENV interference, Python version mismatches, and Poetry configuration problems. Use when poetry install fails, wrong Python version detected, or environment setup needed.
version: 1.0.0
---

# Python Environment Setup and Troubleshooting Skill

This skill provides comprehensive diagnostics and fixes for pyenv+Poetry environment configuration issues. It systematically detects and resolves common problems that prevent Poetry from using the correct Python version.

## Critical Problem This Skill Solves

**The VIRTUAL_ENV Interference Issue:**

Poetry checks the `VIRTUAL_ENV` environment variable before checking PATH or pyenv shims. If this variable is set to a system Python (e.g., from macOS CommandLineTools), Poetry will always detect the wrong Python version, regardless of pyenv configuration.

**Symptoms:**
- `poetry install` fails with "Current Python version (X.X.X) is not allowed by the project"
- `poetry env use` commands fail repeatedly
- `poetry env info` shows wrong Python version
- pyenv is installed and configured, but Poetry ignores it

**Root Cause:**
System-set `VIRTUAL_ENV` environment variable overrides pyenv's Python selection.

## Available Commands

### `/python-env-setup diagnose`

Run comprehensive environment diagnostics to identify configuration issues.

**Usage:**
```bash
python3 .claude/skills/python-env-setup/scripts/diagnose.py
```

**What it checks:**
1. VIRTUAL_ENV environment variable (critical)
2. Python version (system vs required)
3. pyenv installation and configuration
4. Poetry installation and Python version
5. Poetry environment status
6. PATH order (pyenv shims priority)
7. Shell configuration (~/.zshrc)

**Output:**
- Clear identification of issues
- Severity levels (CRITICAL, WARNING, INFO)
- Actionable fix recommendations

### `/python-env-setup fix`

Automatically fix detected environment issues.

**Usage:**
```bash
python3 .claude/skills/python-env-setup/scripts/fix.py [--auto-approve]
```

**What it fixes:**
1. Unsets VIRTUAL_ENV variable
2. Adds `unset VIRTUAL_ENV` to ~/.zshrc
3. Installs pyenv (if missing)
4. Configures pyenv in shell
5. Installs required Python version
6. Reinstalls Poetry with correct Python
7. Removes external Poetry venvs
8. Creates Poetry environment with correct Python

**Options:**
- `--auto-approve`: Skip confirmation prompts (use with caution)

### `/python-env-setup verify`

Verify that the environment is correctly configured.

**Usage:**
```bash
python3 .claude/skills/python-env-setup/scripts/verify.py
```

**Verification checks:**
- Python version matches requirements
- Poetry detects correct Python
- VIRTUAL_ENV is unset
- pyenv shims are in PATH
- Poetry venv is in project directory

## When to Use This Skill

**Trigger conditions:**
- `poetry install` fails with Python version error
- `poetry env use` commands fail repeatedly
- `poetry env info` shows wrong Python version
- Setting up new Python project with pyenv+Poetry
- After installing pyenv but Poetry still uses system Python
- Migrating from system Python to pyenv

**Integration with other skills:**
- Run BEFORE `/dependency` skill if environment issues exist
- Can be called automatically by `/dependency` if Poetry commands fail
- Run after `/init` if Python environment problems detected

## Diagnostic Workflow

The skill follows this systematic approach:

```
1. Check VIRTUAL_ENV variable
   - If set: CRITICAL issue (highest priority)
   - If unset: Continue

2. Check Python versions
   - System Python version
   - Required Python version (from pyproject.toml)
   - Poetry's detected Python version

3. Check pyenv
   - Is pyenv installed?
   - Is pyenv in PATH?
   - Is pyenv initialized in shell?
   - Is correct Python version installed?

4. Check Poetry
   - Is Poetry installed?
   - Which Python is Poetry using?
   - Where is Poetry's venv located?
   - Does Poetry detect correct Python?

5. Check PATH order
   - Are pyenv shims first in PATH?
   - Is system Python after pyenv?

6. Generate fix recommendations
   - Prioritized by severity
```

## Example Output

### Diagnostic Output

```
======================================================================
PYTHON ENVIRONMENT DIAGNOSTICS
======================================================================

[CRITICAL] VIRTUAL_ENV is set to system Python
  Current value: /Library/Developer/CommandLineTools/Library/Frameworks/Python3.framework/Versions/3.9
  Impact: Poetry will always detect the system Python instead of pyenv Python
  Fix: unset VIRTUAL_ENV && echo "unset VIRTUAL_ENV" >> ~/.zshrc

[WARNING] Poetry detects wrong Python version
  Poetry Python: 3.9.6
  Required: ^3.10
  pyenv Python: 3.12.13
  Fix: Remove Poetry venv and recreate with correct Python

[OK] pyenv is installed and configured
  Version: pyenv 2.6.25
  Python 3.12.13: installed

[OK] pyenv shims are in PATH
  Location: /Users/username/.pyenv/shims

======================================================================
SUMMARY
======================================================================
Critical issues: 1
Warnings: 1
Status: ENVIRONMENT NEEDS FIXES

RECOMMENDED ACTIONS:
1. Unset VIRTUAL_ENV variable (CRITICAL)
2. Add "unset VIRTUAL_ENV" to ~/.zshrc
3. Remove Poetry environment: poetry env remove --all
4. Recreate Poetry environment: poetry env use 3.12.13
5. Verify: poetry env info

Run: python3 .claude/skills/python-env-setup/scripts/fix.py
```

### Fix Output

```
======================================================================
PYTHON ENVIRONMENT FIX
======================================================================

[1/7] Unsetting VIRTUAL_ENV variable...
  [OK] VIRTUAL_ENV unset

[2/7] Adding "unset VIRTUAL_ENV" to ~/.zshrc...
  [OK] Added to ~/.zshrc (line 45)

[3/7] Verifying pyenv installation...
  [OK] pyenv 2.6.25 installed

[4/7] Checking Python 3.12.13...
  [OK] Python 3.12.13 already installed

[5/7] Removing external Poetry venv...
  [OK] Removed venv at /Users/username/Library/Caches/pypoetry/virtualenvs/project-py3.9

[6/7] Creating Poetry environment with Python 3.12.13...
  [OK] Created .venv with Python 3.12.13

[7/7] Verifying configuration...
  [OK] poetry env info shows Python 3.12.13
  [OK] VIRTUAL_ENV is unset
  [OK] Environment ready

======================================================================
ENVIRONMENT FIXED SUCCESSFULLY
======================================================================

Next steps:
1. Open a new terminal (or run: source ~/.zshrc)
2. Run: poetry install
3. Verify: poetry run python --version
```

## Troubleshooting Scenarios

### Scenario 1: VIRTUAL_ENV Interference

**Symptoms:**
```bash
$ poetry env info
Python:         3.9.6  # Wrong version!
```

**Diagnosis:**
```bash
$ python3 .claude/skills/python-env-setup/scripts/diagnose.py
[CRITICAL] VIRTUAL_ENV is set to system Python
```

**Fix:**
```bash
$ python3 .claude/skills/python-env-setup/scripts/fix.py
[OK] VIRTUAL_ENV unset and added to ~/.zshrc
```

### Scenario 2: pyenv Not in PATH

**Symptoms:**
```bash
$ pyenv --version
bash: pyenv: command not found
```

**Diagnosis:**
```bash
$ python3 .claude/skills/python-env-setup/scripts/diagnose.py
[WARNING] pyenv not found in PATH
```

**Fix:**
```bash
$ python3 .claude/skills/python-env-setup/scripts/fix.py
[OK] Added pyenv initialization to ~/.zshrc
```

### Scenario 3: Poetry Using Wrong Python

**Symptoms:**
```bash
$ poetry install
Current Python version (X.X.X) is not allowed by the project (^Y.Y)
```

**Diagnosis:**
```bash
$ python3 .claude/skills/python-env-setup/scripts/diagnose.py
[WARNING] Poetry detects incompatible Python version
```

**Fix:**
```bash
$ python3 .claude/skills/python-env-setup/scripts/fix.py
[OK] Recreated Poetry venv with correct Python version
```

## Integration with Dependency Skill

The `/dependency` skill can automatically invoke this skill when environment issues are detected:

```python
# In dependency/scripts/add.py
from python_env_setup.scripts.diagnose import check_environment

# Before adding dependency
issues = check_environment()
if issues.has_critical():
    print("Environment issues detected. Running python-env-setup...")
    run_fix()
```

This ensures dependencies are added to a correctly configured environment.

## Best Practices

1. **Run diagnostics first**
   - Always run `/python-env-setup diagnose` before attempting fixes
   - Understand what's wrong before applying fixes

2. **Review fixes before applying**
   - Don't use `--auto-approve` unless you understand the changes
   - Check what will be modified in ~/.zshrc

3. **Verify after fixing**
   - Always run `/python-env-setup verify` after fixes
   - Test with `poetry install` to confirm

4. **Document in project README**
   - Add environment setup instructions
   - Reference this skill for troubleshooting

5. **Use with new projects**
   - Run diagnostics when setting up new Python projects
   - Catch environment issues early

## Shell Configuration

The skill adds this configuration to ~/.zshrc:

```bash
# ============================================================================
# Python Environment Configuration (pyenv + Poetry)
# ============================================================================
# pyenv root directory
export PYENV_ROOT="$HOME/.pyenv"

# Add pyenv to PATH if it exists
[[ -d $PYENV_ROOT/bin ]] && export PATH="$PYENV_ROOT/bin:$PATH"

# Initialize pyenv (adds shims to PATH)
eval "$(pyenv init -)"

# Initialize pyenv-virtualenv (enables auto-activation)
eval "$(pyenv virtualenv-init -)"

# CRITICAL: Unset system-set VIRTUAL_ENV to prevent Poetry conflicts
unset VIRTUAL_ENV
# ============================================================================
```

## Technical Details

### Why VIRTUAL_ENV Causes Issues

Poetry's environment detection order:
1. **VIRTUAL_ENV variable** (checked first)
2. poetry env use configuration
3. pyproject.toml Python constraint
4. System Python in PATH

If `VIRTUAL_ENV` points to a system Python installation, Poetry will use it regardless of pyenv configuration. This is the root cause of most environment issues.

### How pyenv Works

pyenv uses "shims" - lightweight executables that intercept Python commands:

```bash
$ which python
/Users/username/.pyenv/shims/python  # pyenv shim

$ python --version
Python 3.12.13  # pyenv redirects to correct version
```

### Poetry's Python Detection

Poetry looks for Python in this order:
1. Explicit `poetry env use <path>` configuration
2. Python matching pyproject.toml constraint in PATH
3. System Python

The skill ensures pyenv's Python is found before system Python.

## Version History

- **1.0.0** (2026-03-05): Initial release
  - Comprehensive environment diagnostics
  - Automatic fix workflow
  - VIRTUAL_ENV detection and resolution
  - pyenv installation and configuration
  - Poetry environment management
  - Integration with dependency skill

