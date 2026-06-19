# pre-commit — code-quality validation before commits

> Vendor-neutral procedure description. Claude Code dispatches `/pre-commit`
> to this body via the stub at `.claude/skills/pre-commit/SKILL.md`. Codex /
> Cursor / Cline consult this file directly via the AGENTS.md procedures table.

Orchestrates code-quality tools appropriate to the detected project type.

## Execution

```bash
.ai/bin/agent-precommit
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
