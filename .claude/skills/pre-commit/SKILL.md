---
name: pre-commit
description: "Code quality validation before commits. Runs formatters, linters, type checkers, and tests."
---

# /pre-commit

Orchestrates code quality tools appropriate to the detected project type.

## Execution

Run:

```bash
bin/agent-precommit
```

## Behaviour (guaranteed)

1. Detects project type via shared `project_type.py`.
2. Runs language-appropriate tools in sequence.
3. Prints consolidated pass/fail summary with detailed errors.

## Behaviour (best-effort)

- Tool availability: warns and skips missing tools rather than failing.
- C++ build check requires an existing `build/` directory.

## Python tools

ruff (format + lint + import order), mypy, pytest

## C++ tools

clang-format, clang-tidy, cppcheck, cmake build
