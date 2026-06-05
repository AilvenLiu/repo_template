---
name: pre-commit
description: "Code quality validation before commits. Runs formatters, linters, type checkers, and tests."
---

# /pre-commit

Pre-commit validation. Run before every `git commit`. Must pass with zero errors.

## Execution

```bash
bin/agent-precommit
```

## Behaviour (guaranteed)

1. Detects project type via `.ai/project.yml` / heuristics.
2. Runs language-appropriate tools in sequence (see tables below).
3. Prints a consolidated pass/fail summary with detailed errors.
4. Exits `0` on clean, `1` on any failure.

## Python tools (run in order)

| Tool | What it checks |
|------|----------------|
| `ruff format --check .` | Formatting |
| `ruff check .` | Lint + import order (`I` rule) |
| `mypy src/` | Static type checking (strict mode) |
| `pytest` | Full test suite |

All invoked via `poetry run <tool>` — never via bare `python`/`python3`.

## C++ tools (run in order)

| Tool | What it checks |
|------|----------------|
| `clang-format --dry-run -Werror` | Formatting |
| `clang-tidy` | Static analysis |
| `cppcheck --error-exitcode=1` | Additional static analysis |
| `cmake --build build` | Compilation (requires existing `build/`) |
| `ctest --output-on-failure` | Tests |

## Hybrid projects

Runs both Python and C++ tool chains. Python first, then C++.

## Behaviour (best-effort)

- Warns and skips missing tools rather than failing the whole run.
- C++ build check skipped when no `build/` directory exists.

## Mandatory rule

NEVER commit without a passing `/pre-commit` run. Fix all failures — do not
suppress individual checks.
