# check-constraints — lightweight constraint compliance check

> Vendor-neutral procedure description. Claude Code dispatches
> `/check-constraints` to this body via the stub at
> `.claude/skills/check-constraints/SKILL.md`. Codex / Cursor / Cline consult
> this file directly via the AGENTS.md procedures table.

Lightweight constraint compliance check without running full pre-commit.

## Execution

```bash
.ai/bin/agent-check-constraints
```

## Behaviour (guaranteed)

- Checks dependency management compliance (Poetry, virtual environments).
- Checks git workflow compliance (protected branches).
- Checks Python version requirements.
- Checks lock file synchronisation.

Exit code:
- `0` — no critical violations
- `1` — violations found
