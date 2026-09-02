---
name: python-env-setup
description: Diagnose, repair, or verify the repository's pyenv and Poetry environment. Use when Python selection, in-project virtual environments, Poetry installation, package sources, or environment isolation is missing or inconsistent.
---

# python-env-setup — diagnose and fix pyenv+Poetry environment issues

> Canonical repository skill. Codex discovers it natively from `.agents/skills/`;
> Claude Code reaches it through the matching `.claude/skills/` delegate.

Systematically detects and resolves pyenv+Poetry configuration problems,
enforcing the mandatory Poetry environment policy:
1. Poetry available from an approved isolated installation (normally pipx or a pinned tool image)
2. `poetry.toml` exists with `in-project = true`
3. Custom package sources, when present, use HTTPS, contain no credentials, and declare reviewed priority
4. The calling shell has no unwanted `VIRTUAL_ENV` that interferes with pyenv selection
5. Python 3.10+ available via pyenv

## Execution

```bash
.agents/bin/agent-python-env-setup <diagnose|fix|verify>
```

## Subcommands

- `diagnose` — identify environment issues (runs all checks, reports CRITICAL/WARNING/OK)
- `fix` — automatically fix detected issues where possible
- `verify` — confirm environment is correct (exit 0 if all checks pass)

## Behaviour (guaranteed)

1. **Check 1**: Poetry is available on PATH from the approved isolated tool installation
2. **Check 2**: `poetry.toml` exists and contains `in-project = true`
3. **Check 3**: declared package sources use HTTPS, contain no embedded credentials, and set an approved priority
4. **Check 4**: caller `VIRTUAL_ENV`, captured before Poetry starts, does not shadow pyenv
5. **Check 5**: Python version in Poetry venv satisfies the complete supported
   `pyproject.toml` constraint; bounded, caret, and tilde ranges fail closed
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

## Detailed reference

Read [references/pyenv-poetry-recovery.md](references/pyenv-poetry-recovery.md)
when a login-shell environment, zsh initialisation, incomplete pyenv build, or
Poetry-environment rebuild needs expanded troubleshooting.
