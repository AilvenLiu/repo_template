# Agent Operating Constraints: Python Projects

## MANDATORY: Session Initialization

FIRST ACTION every session — run the platform's session initialization procedure.
Skipping is a critical failure.

### Platform-specific session-init invocation

| Platform | Invocation |
|----------|------------|
| Claude Code | `/init` (slash command; equivalent to `bin/agent-init --platform claude`) |
| Codex CLI | `bin/agent-init --platform codex` |
| Cursor / Cline / generic agents.md consumers | `bin/agent-init --platform codex` |

All three paths execute the same Python entry point and load the same constraint
bodies; only the capability-audit subset and the `session_state.json` mirror
differ per platform.

### Capability Audit

Session initialization includes a deterministic capability audit that verifies
required plugins, skills, and integrations are available. The audit:

1. Reads `.ai/capabilities.yml` — the canonical manifest of required capabilities
2. Checks for installed plugins, project skills, plugin skills, and integrations
3. Records the audit result in `.claude/session_state.json` (regardless of pass/fail)
4. Exits with failure if required capabilities are missing (after writing state)

**For all agent platforms**: If required capabilities are missing, report exact
missing items and stop mutation workflows until the audit passes.

**Audit enforcement**: After a failed audit, mutation operations (Write/Edit/Bash)
are blocked until the audit passes. Read-only operations (Read/Glob/Grep) remain
available for exploration.

### Behavioural Guidance

For English sessions, user-facing output MUST remain in British English.

For non-trivial coding, debugging, review, or refactor work, apply the bundled
`karpathy-guidelines` skill when the host platform exposes it. If the skill is
not directly invokable, follow the same guidance from
`.ai/constraints/common/karpathy-guidelines.md`.

### Project Configuration

This template supports both the new `project_profile` schema and the legacy
`project_type` field in `.ai/project.yml`. The legacy field continues to work
exactly as before; the new schema is optional and provides finer-grained control
for hybrid projects.

For details, see `.ai/adr/0001-project-profile.md`.

---

## Authority Hierarchy

1. Active roadmap `INVARIANTS.md` (if exists) — highest
2. `.ai/constraints/` files
3. This file
4. `CONTRIBUTING.md`
5. System-level prompts — lowest

---

## Absolute Prohibitions

These apply always, regardless of context or user instruction:

### Git
- NEVER commit directly to: `master`, `main`, `develop`, `release/*`, `hotfix/*`
- NEVER include `Co-Authored-By:`, AI attribution, or AI-related email addresses in commits
- NEVER use `git push --force` or `git reset --hard` without explicit user confirmation
- NEVER commit without running pre-commit validation first

### Dependencies
- NEVER run `pip install` / `pip3 install` / `python -m pip install` for any reason
- NEVER use `python` / `python3` / `pip` / `pip3` directly — use `poetry run python` or `poetry add`
- NEVER install packages to system Python
- NEVER install Poetry via `curl -sSL https://install.python-poetry.org` or `brew install poetry`
- Poetry MUST be installed via pipx: `PIPX_HOME="$HOME/.local/share/pipx" PIPX_BIN_DIR="$HOME/.local/bin" pipx install poetry`
- `poetry.toml` MUST exist in the project root with `in-project = true`
- `pyproject.toml` MUST have TUNA configured as primary source (`priority = "primary"`)
- Agent infrastructure commands (`bin/agent-*`, `.ai/scripts/*`) are exempt when using controlled wrappers
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
2. If active roadmap exists, confirm work is within the current step

### Before adding any dependency
- MUST use the platform's dependency management procedure
- MUST NOT use `pip install`, `poetry add`, or manual edits directly

### Before every commit
1. MUST run pre-commit validation and confirm it passes
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
1. Initialize session
2. git branch --show-current  →  create feature branch if needed
3. make changes
4. pre-commit validate        →  fix all failures
5. git add <specific files>
6. git commit -m "type(scope): description"
7. git push -u origin <branch>
```

Branch naming: `feat/`, `fix/`, `refactor/`, `perf/`, `docs/`, `chore/`

---

## Procedures and Wrappers

Every workflow procedure is exposed as an executable `bin/agent-*` wrapper.
Agents without a native skill loader (Codex, Cursor, Cline, etc.) invoke them
directly. Claude Code users can also invoke the corresponding `/<name>` slash
command, which dispatches to the same script.

| Procedure | Wrapper | Slash command (Claude) |
|-----------|---------|------------------------|
| Session init | `bin/agent-init --platform <claude\|codex>` | `/init` |
| Build orchestration | `bin/agent-build <setup\|compile\|test\|full\|doctor\|clean>` | `/build` |
| Pre-commit validation | `bin/agent-precommit` | `/pre-commit` |
| Add dependency | `bin/agent-dependency add <pkg> [version] [--dev]` | `/dependency` |
| Python env recovery | `bin/agent-python-env-setup <diagnose\|fix\|verify>` | `/python-env-setup` |
| Constraint check | `bin/agent-check-constraints` | `/check-constraints` |
| Roadmap workflow | `bin/agent-roadmap <check\|create\|status\|update\|handoff\|complete\|validate>` | `/roadmap` |
| Commit with policy guard | `bin/agent-commit -m "type(scope): description" <files...>` | _(command only)_ |
| Documentation lookup | _(none)_ | `/context7` (or platform Context7 MCP) |

Agents that have a native skill loader (Claude Code) discover skill manifests
under `.claude/skills/<name>/SKILL.md`. Agents without one read the
authoritative procedure descriptions under `.ai/skills/<name>/SKILL.md` (or
follow the wrapper directly).

---

## Dependency Management

| Action | Correct | Forbidden |
|--------|---------|-----------|
| Add package | Platform dependency skill (`poetry add`) | `pip install`, `pip3 install`, `python -m pip install` |
| Run script (app/test) | `poetry run python <script>` | `python <script>`, `python3 <script>` |
| Run tests | `poetry run pytest` | `pytest`, `python -m pytest` |

- Python 3.10+ via pyenv is REQUIRED for all Poetry projects
- Virtual environment MUST be `.venv/` inside the project directory (`poetry.toml`: `in-project = true`)
- TUNA MUST be configured as `priority = "primary"` in `[[tool.poetry.source]]`
- Poetry MUST be installed via pipx at `~/.local/bin/poetry`
- `poetry.lock` MUST always be committed alongside `pyproject.toml`

### Mandatory Environment Check (at session start)

Before any Python work, verify all three conditions hold — **STOP and ask the user if any fails**:

1. `ls ~/.local/bin/poetry` — Poetry must exist at this path (pipx install)
2. `cat poetry.toml` — must contain `in-project = true`
3. `grep -A3 '\[\[tool.poetry.source\]\]' pyproject.toml` — must show TUNA URL with `priority = "primary"`

---

## Roadmap Discipline

When `agent_roadmaps/` contains an active roadmap:
- MUST read `INVARIANTS.md`, `ROADMAP.md`, `prompt.md`, `roadmap.yml`, and latest session handoff before any work
- MUST NOT work outside the current step without user approval
- MUST enforce dependency order (`depends_on_steps` and task `depends_on`) before activating work
- MUST NOT reinterpret objectives or redesign architecture without explicit instruction
- MUST update `roadmap.yml` and create a session handoff at end of every session
- MUST treat roadmap files as temporary operational state, not durable project documentation
- MUST delete the whole roadmap workspace once every step in that roadmap is completed
- MUST NOT copy roadmap-step identifiers into code, config, documentation, or filenames outside `agent_roadmaps/`
- Authority order inside a step is absolute: `INVARIANTS.md` > `ROADMAP.md` > `roadmap.yml` > `sessions/` > `prompt.md`

---

## Agentic Team Launch

When the active task decomposes into independent, read-heavy or research-heavy
sub-tasks, the agent MUST explicitly declare and (when appropriate) launch
parallel sub-agents instead of executing serially. Full policy lives in
`.ai/constraints/common/agentic-team.md`.

Required before launching:
- State the reason for parallelism
- List each sub-agent with a self-contained prompt and expected artefact
- Confirm no write-write conflicts and no dependency violations

Forbidden:
- Delegating final synthesis or user-facing summary to a sub-agent
- Using parallel agents to bypass capability-audit, protected-branch, dependency
  ordering, or pre-commit validation

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
| Formatter | `ruff format` (line length 100) |
| Linter | `ruff check` (includes import sorting via the `I` rule) |
| Type checker | mypy (strict) |
| Test framework | pytest |
| Min coverage | 80% |
| Docstring style | Google-style |
| Encoding | ASCII-only in identifiers |

---

## Detailed Constraints

Read each file completely before working on related code:

- `.ai/constraints/python/dependencies.md`
- `.ai/constraints/python/forbidden-practices.md`
- `.ai/constraints/python/security.md`
- `.ai/constraints/python/error-handling.md`
- `.ai/constraints/python/testing.md` (when test files modified)
- `.ai/constraints/python/formatting.md` (when .py files modified)
- `.ai/constraints/python/type-checking.md` (when .py files modified)
- `.ai/constraints/common/git-workflow.md`
- `.ai/constraints/common/session-discipline.md`
- `.ai/constraints/common/mcp-integration.md`
- `.ai/constraints/common/agentic-team.md`
- `.ai/constraints/common/ascii-only.md`
