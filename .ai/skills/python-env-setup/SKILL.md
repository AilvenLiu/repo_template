# python-env-setup — diagnose and fix pyenv+Poetry environment issues

> Vendor-neutral procedure description. Claude Code dispatches
> `/python-env-setup` to this body via the stub at
> `.claude/skills/python-env-setup/SKILL.md`. Codex / Cursor / Cline read
> this file directly via the AGENTS.md procedures table.

Systematically detects and resolves pyenv+Poetry configuration problems,
especially the `VIRTUAL_ENV` interference issue where a system-set variable
overrides pyenv's Python selection.

## Execution

```bash
bin/agent-python-env-setup <diagnose|fix|verify>
```

## Subcommands

- `diagnose` — identify environment issues
- `fix` — automatically fix detected issues
- `verify` — confirm environment is correct

## Behaviour (guaranteed)

1. Checks `VIRTUAL_ENV`, Python version, pyenv config, Poetry config, PATH order.
2. Reports issues with severity (CRITICAL / WARNING / INFO).
3. Fix mode: unsets `VIRTUAL_ENV`, configures shell, recreates Poetry venv.

## Behaviour (best-effort)

- pyenv/Poetry installation if missing (requires network).
- Shell config edits (`~/.zshrc`) — may need manual `source`.

## Trigger conditions

- `poetry install` fails with Python version error
- `poetry env info` shows wrong Python version
- Setting up a new Python project with pyenv+Poetry
