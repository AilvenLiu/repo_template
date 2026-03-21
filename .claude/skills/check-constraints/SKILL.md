---
name: check-constraints
description: "Validate constraint compliance at any time during development."
---

# /check-constraints

Lightweight constraint compliance check without running full pre-commit.

## Execution

Run:

```bash
bin/agent-check-constraints
```

## Behaviour (guaranteed)

- Checks dependency management compliance (Poetry, virtual environments)
- Checks git workflow compliance (protected branches)
- Checks Python version requirements
- Checks lock file synchronisation

Exit 0 = no critical violations, exit 1 = violations found.
