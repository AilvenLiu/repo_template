---
name: python-env-setup
description: "Diagnose and fix pyenv+Poetry environment issues. Use when poetry install fails or wrong Python version detected."
---

# /python-env-setup

Systematic diagnosis and repair of pyenv+Poetry configuration issues, especially
the `VIRTUAL_ENV` interference problem where a system-set variable overrides
pyenv's Python selection.

## Execution

```bash
bin/agent-python-env-setup <diagnose|fix|verify>
```

## Subcommands

| Subcommand | What it does |
|------------|--------------|
| `diagnose` | Checks `VIRTUAL_ENV`, Python version, pyenv config, Poetry config, PATH order. Reports issues with severity. |
| `fix` | Unsets `VIRTUAL_ENV`, configures shell init, removes external Poetry venvs, recreates `.venv/` inside the project. |
| `verify` | Confirms Python 3.10+, Poetry env inside `.venv/`, and `poetry install` succeeds cleanly. |

## Trigger conditions — run this skill when

- `poetry install` fails with a Python version mismatch error
- `poetry env info` shows the wrong Python version (not 3.10+)
- `python --version` shows a different version than `poetry run python --version`
- Setting up a new Python project with pyenv+Poetry on a machine for the first time
- After upgrading Python or installing a new pyenv version

## Behaviour (guaranteed)

1. Checks `VIRTUAL_ENV`, Python version, pyenv config, Poetry config, PATH order.
2. Reports issues with severity: CRITICAL / WARNING / INFO.
3. **Fix mode**: unsets `VIRTUAL_ENV`, patches shell config (`~/.zshrc` /
   `~/.bashrc`), removes external Poetry venvs, configures `virtualenvs.in-project true`,
   recreates venv as `.venv/` inside the project.

## Behaviour (best-effort)

- pyenv / Poetry installation if missing (requires network).
- Shell config edits — may require `source ~/.zshrc` manually after fix.

## Correct environment state

```bash
poetry env info --path   # Must print <project>/.venv
poetry run python --version  # Must be Python 3.10+
```
