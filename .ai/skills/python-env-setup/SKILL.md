# python-env-setup — diagnose and fix pyenv+Poetry environment issues

> Vendor-neutral procedure description. Claude Code dispatches
> `/python-env-setup` to this body via the stub at
> `.claude/skills/python-env-setup/SKILL.md`. Codex / Cursor / Cline read
> this file directly via the AGENTS.md procedures table.

Systematically detects and resolves pyenv+Poetry configuration problems,
enforcing the mandatory Poetry environment policy:
1. Poetry installed via pipx at `~/.local/bin/poetry`
2. `poetry.toml` exists with `in-project = true`
3. TUNA configured as primary PyPI source in `pyproject.toml`
4. `VIRTUAL_ENV` not interfering with pyenv Python selection
5. Python 3.10+ available via pyenv

## Execution

```bash
.ai/bin/agent-python-env-setup <diagnose|fix|verify>
```

## Subcommands

- `diagnose` — identify environment issues (runs all checks, reports CRITICAL/WARNING/OK)
- `fix` — automatically fix detected issues where possible
- `verify` — confirm environment is correct (exit 0 if all checks pass)

## Behaviour (guaranteed)

1. **Check 1**: Poetry present at `~/.local/bin/poetry` (pipx install location)
2. **Check 2**: `poetry.toml` exists and contains `in-project = true`
3. **Check 3**: `[[tool.poetry.source]]` in `pyproject.toml` has TUNA URL with `priority = "primary"`
4. **Check 4**: `VIRTUAL_ENV` env var not set (would shadow pyenv Python)
5. **Check 5**: Python version in Poetry venv matches `pyproject.toml` requirement
6. **Check 6**: pyenv installed and shims on PATH
7. **Check 7**: `~/.local/bin` on PATH before system directories

Reports issues with severity (CRITICAL / WARNING / INFO). CRITICAL issues require
user action before proceeding — the agent MUST stop and report them.

## Behaviour (best-effort, fix mode only)

- Creates `poetry.toml` with correct content if missing
- Removes external Poetry venvs and recreates in-project
- Guides user through pyenv installation if missing

## Trigger conditions

- **MANDATORY at session start** for any Python or Hybrid project
- `poetry install` fails with Python version or venv error
- `poetry env info` shows wrong Python version or wrong path
- Setting up a new Python project
- Any poetry-related error during development

## On critical failure

If any of checks 1–3 fail, the agent MUST:
1. Report clearly which check failed
2. STOP — do not attempt to continue silently
3. Present the exact remediation command
4. Wait for user confirmation before proceeding
