---
name: check-constraints
description: Validate repository state against the active project profile and constraint manifest. Use before finalizing edits, before commits, or when diagnosing forbidden patterns, protected-branch state, build-policy drift, or instruction compliance.
---

# check-constraints — lightweight constraint compliance check

> Canonical repository skill. Codex discovers it natively from `.agents/skills/`;
> Claude Code reaches it through the matching `.claude/skills/` delegate.

Lightweight constraint compliance check without running full pre-commit.

## Execution

```bash
.agents/bin/agent-check-constraints
```

## Behaviour (guaranteed)

- Checks dependency management compliance (Poetry, virtual environments).
- Checks git workflow compliance (protected branches).
- Checks Python version requirements.
- Checks lock file synchronisation.

Exit code:
- `0` — no critical violations
- `1` — violations found
