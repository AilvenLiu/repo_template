---
name: pre-commit
description: "Code quality validation before commits. Runs formatters, linters, type checkers, and tests."
---

# /pre-commit

Pre-commit validation. The canonical, vendor-neutral procedure body lives at
[`.ai/skills/pre-commit/SKILL.md`](../../../.ai/skills/pre-commit/SKILL.md).

## Execution

```bash
bin/agent-precommit
```

## Python tools

ruff (format + lint + import order), mypy, pytest

## C++ tools

clang-format, clang-tidy, cppcheck, cmake build

When this slash command is invoked, also read
[`.ai/skills/pre-commit/SKILL.md`](../../../.ai/skills/pre-commit/SKILL.md) for
the full behavioural spec.
