# Python Environment Setup: Quick Reference

This document provides a quick reference for the python-env-setup skill and common pyenv+Poetry issues.

## The Critical Issue: VIRTUAL_ENV Interference

**Problem:** Poetry checks the `VIRTUAL_ENV` environment variable before checking PATH. If this variable points to a system Python, Poetry will always use it regardless of pyenv configuration.

**Quick Check:**
```bash
env | grep VIRTUAL_ENV
```

**Quick Fix:**
```bash
unset VIRTUAL_ENV
echo "unset VIRTUAL_ENV" >> ~/.zshrc
source ~/.zshrc
```

## Using the python-env-setup Skill

### Diagnose Issues
```bash
python3 .ai/scripts/python-env-setup/diagnose.py
```

### Fix Issues
```bash
python3 .ai/scripts/python-env-setup/fix.py
```

### Verify Configuration
```bash
python3 .ai/scripts/python-env-setup/verify.py
```

## Common Scenarios

### Scenario 1: poetry install fails with version error

**Symptom:**
```
Current Python version (X.X.X) is not allowed by the project (^Y.Y)
```

**Solution:**
1. Run diagnostics: `python3 .ai/scripts/python-env-setup/diagnose.py`
2. Check for VIRTUAL_ENV: `env | grep VIRTUAL_ENV`
3. If set, unset it: `unset VIRTUAL_ENV`
4. Add to ~/.zshrc: `echo "unset VIRTUAL_ENV" >> ~/.zshrc`
5. Recreate Poetry venv: `poetry env remove --all && poetry env use 3.12`
6. Install: `poetry install`

### Scenario 2: Poetry detects wrong Python

**Symptom:**
```bash
$ poetry env info
Python:         3.9.6  # Wrong!
```

**Solution:**
1. Check VIRTUAL_ENV: `env | grep VIRTUAL_ENV`
2. Unset if present: `unset VIRTUAL_ENV`
3. Remove Poetry venv: `poetry env remove --all`
4. Create with correct Python: `poetry env use 3.12`

### Scenario 3: pyenv installed but not working

**Symptom:**
```bash
$ pyenv --version
bash: pyenv: command not found
```

**Solution:**
Add to ~/.zshrc:
```bash
export PYENV_ROOT="$HOME/.pyenv"
[[ -d $PYENV_ROOT/bin ]] && export PATH="$PYENV_ROOT/bin:$PATH"
eval "$(pyenv init -)"
eval "$(pyenv virtualenv-init -)"
unset VIRTUAL_ENV
```

Then: `source ~/.zshrc`

## Complete Setup from Scratch

```bash
# 1. Install pyenv
curl https://pyenv.run | bash

# 2. Configure shell
cat >> ~/.zshrc << 'EOF'

# Python Environment Configuration (pyenv + Poetry)
export PYENV_ROOT="$HOME/.pyenv"
[[ -d $PYENV_ROOT/bin ]] && export PATH="$PYENV_ROOT/bin:$PATH"
eval "$(pyenv init -)"
eval "$(pyenv virtualenv-init -)"
unset VIRTUAL_ENV
EOF

# 3. Reload shell
source ~/.zshrc

# 4. Install Python
pyenv install 3.12.13
pyenv local 3.12.13

# 5. Install Poetry
curl -sSL https://install.python-poetry.org | python3 -

# 6. Configure Poetry
poetry config virtualenvs.in-project true --local

# 7. Create environment
poetry env use 3.12.13

# 8. Install dependencies
poetry install

# 9. Verify
python3 .ai/scripts/python-env-setup/verify.py
```

## Verification Checklist

After setup, verify:

```bash
# VIRTUAL_ENV should be unset
env | grep VIRTUAL_ENV  # Should return nothing

# Python version should match
python --version  # Should show pyenv Python

# Poetry should detect correct Python
poetry env info  # Should show correct Python version

# pyenv shims should be in PATH
echo $PATH | grep pyenv  # Should show .pyenv/shims
```

## Integration with Other Skills

### With /dependency skill

The dependency skill will work correctly only if the environment is properly configured. If you encounter issues:

1. Run python-env-setup diagnostics first
2. Fix any critical issues
3. Then use the dependency skill

### With /init skill

The init skill loads project constraints. If you see Python environment issues after /init:

1. Run python-env-setup diagnostics
2. Fix issues before proceeding with development

## Reference: Poetry's Python Detection Order

Poetry checks for Python in this order:

1. **VIRTUAL_ENV variable** (highest priority - this is the problem!)
2. `poetry env use` configuration
3. Python matching pyproject.toml constraint in PATH
4. System Python

This is why unsetting VIRTUAL_ENV is critical.

## Reference: pyenv How It Works

pyenv uses "shims" - lightweight executables that intercept Python commands:

```bash
$ which python
/Users/username/.pyenv/shims/python  # pyenv shim

$ python --version
Python 3.12.13  # pyenv redirects to correct version
```

The shims must be first in PATH to work correctly.

## For More Details

See the full documentation:
- Skill documentation: `.claude/skills/python-env-setup/SKILL.md`
- Comprehensive guide: Reference the original PYENV_POETRY_SETUP.md document

## Quick Command Reference

```bash
# Diagnostics
python3 .ai/scripts/python-env-setup/diagnose.py

# Fix
python3 .ai/scripts/python-env-setup/fix.py

# Verify
python3 .ai/scripts/python-env-setup/verify.py

# Check VIRTUAL_ENV
env | grep VIRTUAL_ENV

# Unset VIRTUAL_ENV
unset VIRTUAL_ENV

# Poetry commands
poetry env info              # Show current environment
poetry env list              # List all environments
poetry env remove --all      # Remove all environments
poetry env use 3.12          # Create environment with Python 3.12
poetry install               # Install dependencies

# pyenv commands
pyenv versions               # List installed Python versions
pyenv version                # Show current Python version
pyenv install 3.12.13        # Install Python 3.12.13
pyenv local 3.12.13          # Set local Python version
```
