---
name: python-env-setup
description: "Diagnose and fix pyenv+Poetry environment issues. Use when poetry install fails or wrong Python version detected."
---

# /python-env-setup

Pyenv+Poetry environment diagnosis and repair. The canonical, vendor-neutral
procedure body lives at
[`.ai/skills/python-env-setup/SKILL.md`](../../../.ai/skills/python-env-setup/SKILL.md).

## Execution

```bash
bin/agent-python-env-setup <diagnose|fix|verify>
```

## Subcommands

- `diagnose` — identify environment issues
- `fix` — automatically fix detected issues
- `verify` — confirm environment is correct

When this slash command is invoked, also read
[`.ai/skills/python-env-setup/SKILL.md`](../../../.ai/skills/python-env-setup/SKILL.md)
for the full behavioural spec and trigger conditions.
