---
name: python-env-setup
description: "Diagnose and fix pyenv+Poetry environment issues. Checks pipx install, in-project venv, TUNA source, Python version. STOP and ask user if any mandatory check fails."
---

# /python-env-setup

Systematic diagnosis and repair of pyenv+Poetry configuration, enforcing the
mandatory three-check policy:

1. **Poetry via pipx** — must be at `~/.local/bin/poetry`
2. **In-project venv** — `poetry.toml` must have `in-project = true`
3. **TUNA as primary source** — `pyproject.toml` must have TUNA with `priority = "primary"`

If any of checks 1–3 fail, the agent **MUST STOP and ask the user** before proceeding.

## Execution

```bash
.ai/bin/agent-python-env-setup <diagnose|fix|verify>
```

## Subcommands

| Subcommand | What it does |
|------------|--------------|
| `diagnose` | Runs all checks. Reports CRITICAL / WARNING / OK per check. |
| `fix` | Best-effort repair: creates `poetry.toml`, relocates external venvs. |
| `verify` | Confirms all checks pass; exits 0 if environment is correct. |

## Checks performed

| # | Check | Severity if fails |
|---|-------|------------------|
| 1 | `~/.local/bin/poetry` exists (pipx install) | CRITICAL |
| 2 | `poetry.toml` present with `in-project = true` | CRITICAL |
| 3 | TUNA configured as `priority = "primary"` in `pyproject.toml` | CRITICAL |
| 4 | `VIRTUAL_ENV` env var not set | CRITICAL |
| 5 | Poetry venv Python matches `pyproject.toml` requirement | WARNING |
| 6 | pyenv installed and shims on PATH | WARNING |
| 7 | `~/.local/bin` on PATH before system directories | WARNING |

## Trigger conditions — run this skill when

- Any Python or Hybrid project session starts (MANDATORY check)
- `poetry install` fails with a Python version or venv error
- `poetry env info` shows the wrong Python version or wrong path
- Setting up a new Python project for the first time
- After upgrading Python or installing a new pyenv version

## On critical failure

```
STOP — report which check failed, show the exact fix command, wait for user.
```

## Correct environment state

```bash
ls ~/.local/bin/poetry              # Must exist
cat poetry.toml                     # Must have: in-project = true
poetry env info --path              # Must print <project>/.venv
poetry run python --version         # Must be Python 3.10+
```
