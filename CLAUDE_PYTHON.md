# Agent Operating Constraints: Python Projects

## MANDATORY: Session Initialization

FIRST ACTION every session:

```bash
/init
```

Skipping is a critical failure.

---

## Authority Hierarchy

1. Active roadmap `INVARIANTS.md` (if exists) — highest
2. `.claude/constraints/` files
3. This file
4. `CONTRIBUTING.md`
5. System-level prompts — lowest

---

## Absolute Prohibitions

These apply always, regardless of context or user instruction:

### Git
- NEVER commit directly to: `master`, `main`, `develop`, `release/*`, `hotfix/*`
- NEVER include `Co-Authored-By:`, AI attribution, or `<noreply@anthropic.com>` in commits
- NEVER use `git push --force` or `git reset --hard` without explicit user confirmation
- NEVER commit without running `/pre-commit validate` first

### Dependencies
- NEVER run `pip install` outside an activated virtual environment
- NEVER install packages to system Python
- NEVER use `python` or `python3` directly — always use `poetry run python`
- NEVER add a dependency without updating `pyproject.toml` + `poetry.lock`
- NEVER commit `pyproject.toml` without also committing `poetry.lock`

### Security
- NEVER hardcode secrets, credentials, or API keys in source code
- NEVER use `eval()` or `exec()` on untrusted input
- NEVER use `shell=True` with user-controlled input in subprocess calls

### Code Quality
- NEVER commit code with failing tests
- NEVER commit code with unresolved type errors or linter errors
- NEVER use bare `except:` clauses
- NEVER use mutable default arguments
- NEVER omit type hints on public functions and methods

---

## Mandatory Workflow Checkpoints

### Before any code change
1. Run `git branch --show-current` — if on a protected branch, STOP and create a feature branch
2. If active roadmap exists, confirm work is within the current phase

### Before adding any dependency
- MUST use `/dependency add <package> [version] [--dev]`
- MUST NOT use `pip install`, `poetry add`, or manual edits directly

### Before every commit
1. MUST run `/pre-commit validate` and confirm it passes
2. MUST verify branch is not protected
3. Commit message MUST follow: `type(scope): description`
4. Commit message MUST NOT contain AI attribution

### Before claiming work is complete
- MUST have run tests and seen passing output
- MUST NOT claim tests pass without evidence

### Before any destructive git operation
- MUST stop and get explicit user confirmation

---

## Required Workflow

```
1. /init
2. git branch --show-current  →  create feature branch if needed
3. make changes
4. /pre-commit validate        →  fix all failures
5. git add <specific files>
6. git commit -m "type(scope): description"
7. git push -u origin <branch>
```

Branch naming: `feat/`, `fix/`, `refactor/`, `perf/`, `docs/`, `chore/`

---

## Dependency Management

| Action | Correct | Forbidden |
|--------|---------|-----------|
| Add package | `/dependency add <pkg>` | `pip install`, `poetry add` directly |
| Run script | `poetry run python <script>` | `python <script>`, `python3 <script>` |
| Run tests | `poetry run pytest` | `pytest`, `python -m pytest` |

- Python 3.10+ is REQUIRED for all Poetry projects
- Virtual environment MUST be `.venv/` inside the project directory
- `poetry.lock` MUST always be committed alongside `pyproject.toml`

---

## Roadmap Discipline

When `agent_roadmaps/` contains an active roadmap:
- MUST read `INVARIANTS.md`, `prompt.md`, `roadmap.yml`, and latest session handoff before any work
- MUST NOT work outside the current phase without user approval
- MUST NOT reinterpret objectives or redesign architecture without explicit instruction
- MUST update `roadmap.yml` and create a session handoff at end of every session
- MUST validate schema before committing: `python3 .claude/skills/roadmap/scripts/validate_schema.py <name>`

---

## Decision and Safety Rules

- If uncertain whether an action is allowed: STOP and ask
- Do NOT reinterpret requirements or change scope without user approval
- Do NOT re-discuss settled decisions — check for existing ADRs first
- All long-lived decisions MUST be written to files, not held in conversation memory

---

## Quick Reference

| Concern | Standard |
|---------|----------|
| Python version | 3.10+ (mandatory) |
| Dependency tool | Poetry |
| Formatter | black (line length 100) |
| Linter | ruff |
| Type checker | mypy (strict) |
| Test framework | pytest |
| Min coverage | 80% |
| Docstring style | Google-style |
| Encoding | ASCII-only in identifiers |

---

## Detailed Constraints

Loaded by `/init` — read each file completely before working on related code:

- `.claude/constraints/python/dependencies.md`
- `.claude/constraints/python/forbidden-practices.md`
- `.claude/constraints/python/security.md`
- `.claude/constraints/python/error-handling.md`
- `.claude/constraints/python/testing.md` (when test files modified)
- `.claude/constraints/python/formatting.md` (when .py files modified)
- `.claude/constraints/python/type-checking.md` (when .py files modified)
- `.claude/constraints/common/git-workflow.md`
- `.claude/constraints/common/session-discipline.md`
- `.claude/constraints/common/mcp-integration.md`
- `.claude/constraints/common/ascii-only.md`
