---
name: pre-commit
description: Run the repository-owned profile-aware quality gate before commit or handoff. Use after edits to format, lint, type-check, test, scan forbidden patterns, and validate the active Python, C++/CUDA, or hybrid project.
---

# pre-commit — code-quality validation before commits

> Canonical repository skill. Codex discovers it natively from `.agents/skills/`;
> Claude Code reaches it through the matching `.claude/skills/` delegate.

Orchestrates code-quality tools appropriate to the detected project type.

## Execution

```bash
.agents/bin/agent-precommit
```

## Behaviour (guaranteed)

1. Detects project type via shared `project_type.py`.
2. Runs language-appropriate tools in sequence.
3. Prints consolidated pass/fail summary with detailed errors.

## Failure behavior

- Missing required tools fail the gate and must be provisioned through the declared workflow.
- C++ build validation requires direct configuration/build first; a missing `build/` is a failure.

## Python tools

ruff (format + lint + import order), mypy, pytest

## C++ tools

clang-format, clang-tidy, cppcheck, cmake build

## Detailed reference

Read [references/guide.md](references/guide.md) for the expanded gate summary.
