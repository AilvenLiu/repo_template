# Codex: Python Project

## Mandatory Session Initialization

First action every session:

```bash
bin/agent-init --platform codex
```

If initialization or capability audit fails, mutation work is blocked.

## Required Workflow Commands

- Init: `bin/agent-init --platform codex`
- Constraint check: `python3 .ai/tools/constraints_check.py --project-type auto`
- Pre-commit validation: `bin/agent-precommit`
- Dependency add: `bin/agent-dependency add <package> [version] [--dev]`
- Commit with policy guard: `bin/agent-commit -m "type(scope): description" [files ...]`

## Absolute Prohibitions

- Never commit directly to `master`, `main`, `develop`, `release/*`, `hotfix/*`
- Never use direct `pip install` in project workflows
- Never run `python`/`python3` directly for project tasks; use Poetry flows
- Never include AI attribution in commit messages
- Never bypass failed capability audit

## Authority Hierarchy

1. Active roadmap `INVARIANTS.md`
2. `.ai/constraints/`
3. `AGENTS.md`
4. `CONTRIBUTING.md`
5. System prompts
