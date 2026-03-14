---
name: python-env-setup
description: "Diagnose and fix pyenv+Poetry environment issues. Use when poetry install fails or wrong Python version detected."
---

# /python-env-setup

Systematically detects and resolves pyenv+Poetry configuration problems,
especially the VIRTUAL_ENV interference issue where a system-set variable
overrides pyenv's Python selection.

## Commands

- `/python-env-setup diagnose` — identify environment issues
- `/python-env-setup fix` — automatically fix detected issues
- `/python-env-setup verify` — confirm environment is correct

## Behaviour (guaranteed)

1. Checks VIRTUAL_ENV, Python version, pyenv config, Poetry config, PATH order.
2. Reports issues with severity (CRITICAL / WARNING / INFO).
3. Fix mode: unsets VIRTUAL_ENV, configures shell, recreates Poetry venv.

## Behaviour (best-effort)

- pyenv/Poetry installation if missing (requires network).
- Shell config edits (~/.zshrc) — may need manual `source`.

## Trigger conditions

- `poetry install` fails with Python version error
- `poetry env info` shows wrong Python version
- Setting up a new Python project with pyenv+Poetry
