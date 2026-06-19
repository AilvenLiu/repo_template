---
name: check-constraints
description: "Validate constraint compliance at any time during development."
---

# /check-constraints

Lightweight constraint compliance check. Use at any point during development —
does not require running the full test suite.

## Execution

```bash
.ai/bin/agent-check-constraints
```

Exit `0` = no critical violations. Exit `1` = violations found.

## Behaviour (guaranteed)

1. **Dependency management compliance** — verifies Poetry is used for Python,
   no bare `pip install` traces, `.venv/` is inside the project.
2. **Git workflow compliance** — checks current branch is not a protected branch
   (`master`, `main`, `develop`, `release/*`, `hotfix/*`).
3. **Python version requirement** — confirms Python 3.10+ is active for Poetry projects.
4. **Lock file synchronisation** — confirms `poetry.lock` exists and is not stale
   relative to `pyproject.toml`.
5. **Forbidden pattern scan** — runs `.ai/scripts/forbidden_patterns.py` to detect
   `pip install`, bare `except:`, `eval()`/`exec()`, mutable defaults, hardcoded secrets.

## When to use

- Before starting a work session (quick sanity check)
- After making dependency changes
- When the pre-commit hook reports a constraint violation

## Difference from `/pre-commit`

`/check-constraints` checks policy compliance (branch, deps, forbidden patterns).
`/pre-commit` additionally runs formatters, linters, type checker, and tests.
Run `/check-constraints` for a fast policy check; run `/pre-commit` before committing.
