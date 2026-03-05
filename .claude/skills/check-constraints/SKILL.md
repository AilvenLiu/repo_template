---
name: check-constraints
description: Validate constraint compliance at any time during development
---

# Check Constraints Skill

This skill validates constraint compliance without running full pre-commit checks.

## Usage

```bash
python3 .claude/skills/check-constraints/scripts/check.py
```

## What It Checks

- Dependency management compliance (Poetry, virtual environments)
- Git workflow compliance (protected branches)
- Python version requirements
- Lock file synchronization

## When to Use

- During development to catch violations early
- After making changes to verify compliance
- Before running full pre-commit validation
- When uncertain about constraint adherence

## Exit Codes

- 0: No critical violations
- 1: Critical violations found
