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
3. Collects application tests from `tests/` and agent-infrastructure tests from
   `.agents/scripts/tests/` explicitly, including when pytest ignores hidden trees.
4. Scopes C++ discovery and cppcheck to first-party sources, excluding generated,
   vendored, environment, roadmap, and agent-infrastructure trees.
5. Prints consolidated pass/fail summary with detailed errors.

## Failure behavior

- Missing required tools fail the gate and must be provisioned through the declared workflow.
- C++ build validation requires a configured `build/native/` or `build/` tree.

## Python tools

Ruff (format + lint + import order), mypy, pytest for both owned test trees

## C++ tools

clang-format, clang-tidy, first-party cppcheck, discovered CMake build

## Detailed reference

Read [references/guide.md](references/guide.md) for the expanded gate summary.
