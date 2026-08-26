# Agent Operating Constraints: Python Projects

## MANDATORY: Session Initialization

FIRST ACTION every session — run the platform's session initialization procedure.
Skipping is a critical failure.

### Platform-specific session-init invocation

| Platform | Invocation |
|----------|------------|
| Claude Code | `/init` (slash command; equivalent to `.agents/bin/agent-init --platform claude`) |
| Codex CLI | `.agents/bin/agent-init --platform codex` |
| Cursor / Cline / generic agents.md consumers | `.agents/bin/agent-init --platform codex` |

All three paths execute the same Python entry point and produce the same
profile-aware constraint manifest; only the capability-audit subset and the
`session_state.json` mirror differ per platform.

### Capability Audit

Session initialization includes a deterministic capability audit that verifies
required plugins, skills, and integrations are available. The audit:

1. Reads `.agents/capabilities.yml` — the canonical manifest of required capabilities
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
`.agents/constraints/common/karpathy-guidelines.md`.

Before closing any session, task, commit, or roadmap phase, follow
`.agents/constraints/common/closure-discipline.md`: re-check the request and
constraints, review changes critically, run the strongest relevant validation,
fix in-scope issues found during review, and report residual risk honestly.

### Project Configuration

This template supports both the new `project_profile` schema and the legacy
`project_type` field in `.agents/project.yml`. The legacy field continues to work
exactly as before; the new schema is optional and provides finer-grained control
for hybrid projects.

For details, see `.agents/adr/0001-project-profile.md`.

---

## Platform and Repository-Local Policy

Repository policy does not supersede higher-priority platform safety,
developer, organisational, or tool-enforced requirements. If they conflict,
follow the higher-priority requirement, minimise the deviation, and report it.

Within repository-controlled guidance, use the scoped order in
`.agents/constraints/common/instruction-hierarchy.md`. In particular, current
`roadmap.yml` state takes precedence over roadmap prose and session records;
temporary notes cannot change durable project policy.

---

## Absolute Prohibitions

These apply always, regardless of context or user instruction:

### Git
- NEVER commit directly to `master`, `main`, `develop`, `release/*`, or `hotfix/*`, except through the bounded `.agents/bin/agent-release bump <x.y.z>` operation on clean, current `develop`
- A PR/MR targeting `master` MUST originate in the same repository from `release/v<MAJOR>.<MINOR>.<PATCH>` or `hotfix/v<MAJOR>.<MINOR>.<PATCH>` only; `develop` is not a valid source. The version comes from the authoritative manifest at the recorded source commit and the merged commit is tagged `release-v<MAJOR>.<MINOR>.<PATCH>`
- A master-bound PR/MR MUST pass `master-merge-gate`; its source tree MUST NOT contain `.ai/`, `.agents/`, `.claude/`, `.codex/`, `agent_roadmaps/`, `AGENTS.md`, `CLAUDE.md`, `CODEX.md`, or `docs/` outside `docs/changelog/`
- For ordinary releases, `develop` MUST NOT merge from or rebase onto `master`; a release tree may differ from its recorded `develop` SHA only by forbidden-path deletions
- A master-origin hotfix MUST record its reduced validation and MUST return to `develop` through a reviewed merge or cherry-pick PR, never through rebase
- NEVER include `Co-Authored-By:`, AI attribution, or AI-related email addresses in commits
- NEVER use `git push --force` or `git reset --hard` without explicit user confirmation
- NEVER commit without running pre-commit validation first, except the release wrapper's structurally verified version-only commit

### Dependencies
- NEVER run `pip install` / `pip3 install` / `python -m pip install` for any reason
- NEVER use `python` / `python3` / `pip` / `pip3` directly — use `poetry run python` or `poetry add`
- NEVER install packages to system Python
- NEVER install Poetry via `curl -sSL https://install.python-poetry.org` or `brew install poetry`
- Poetry MUST be installed via pipx: `PIPX_HOME="$HOME/.local/share/pipx" PIPX_BIN_DIR="$HOME/.local/bin" pipx install poetry`
- `poetry.toml` MUST exist in the project root with `in-project = true`
- Custom package sources, when declared, MUST use HTTPS, omit credentials, and set a reviewed priority
- Agent infrastructure commands (`.agents/bin/agent-*`, `.agents/scripts/*`) are exempt when using controlled wrappers
- NEVER add a dependency without updating `pyproject.toml` + `poetry.lock`
- NEVER commit `pyproject.toml` without also committing `poetry.lock`, except
  a version-only `agent-release bump` that changes no dependency input

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
1. Run `git branch --show-current` — if on a protected branch, STOP and create a feature branch unless the operation is
   exactly the bounded release-version wrapper on clean, current `develop`
2. If active roadmap exists, confirm work is within the current phase

### Before adding any dependency
- MUST use the platform's dependency management procedure
- MUST NOT use `pip install`, `poetry add`, or manual edits directly

### Before every commit
1. MUST run pre-commit validation and confirm it passes
2. MUST verify branch is not protected, unless the commit is created inside the exact bounded release-version wrapper
3. Commit message MUST follow: `type(scope): description`
4. Commit message MUST NOT contain AI attribution

### Before claiming work is complete
- MUST have run tests and seen passing output
- MUST NOT claim tests pass without evidence
- MUST perform a focused review pass and fix in-scope issues before closure

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

Every workflow procedure is exposed as an executable `.agents/bin/agent-*` wrapper.
Agents without a native skill loader (Codex, Cursor, Cline, etc.) invoke them
directly. Claude Code users can also invoke the corresponding `/<name>` slash
command, which dispatches to the same script.

| Procedure | Wrapper | Slash command (Claude) |
|-----------|---------|------------------------|
| Session init | `.agents/bin/agent-init --platform <claude\|codex>` | `/init` |
| Release preparation | `.agents/bin/agent-release <bump\|prepare\|verify-metadata>` | _(command only)_ |
| Build orchestration | `.agents/bin/agent-build <setup\|compile\|test\|full\|doctor\|clean>` | `/build` |
| Pre-commit validation | `.agents/bin/agent-precommit` | `/pre-commit` |
| Add dependency | `.agents/bin/agent-dependency add <pkg> [version] [--dev]` | `/dependency` |
| Python env recovery | `.agents/bin/agent-python-env-setup <diagnose\|fix\|verify>` | `/python-env-setup` |
| Constraint check | `.agents/bin/agent-check-constraints` | `/check-constraints` |
| Roadmap workflow | `.agents/bin/agent-roadmap <check\|create\|status\|update\|handoff\|complete\|validate>` | `/roadmap` |
| Commit with policy guard | `.agents/bin/agent-commit -m "type(scope): description" <files...>` | _(command only)_ |
| Documentation lookup | _(none)_ | `/context7` (or platform Context7 MCP) |
| Code navigation | `.agents/skills/navigate/SKILL.md` | `/navigate` |
| Host deployment guidance | `.agents/skills/deploy-service/SKILL.md` | `/deploy-service` |
| GitHub Actions CI/CD | `.agents/skills/service-cicd/SKILL.md` | `/service-cicd` |
| Branch governance | `.agents/skills/branch-governance/SKILL.md` | `/branch-governance` |

For host deployment or GitHub Actions CI/CD work, agents MUST read both
`.agents/constraints/common/service-deployment.md` and
`.agents/constraints/common/github-actions-cicd.md` before applying the skills.
Skill bodies supplement these constraints; they do not replace them.

Absent a durable, reviewed project-specific release policy, automatic deployment
and automatic release run only after `master` is updated and promote the exact
resulting `master` SHA. A `release/*` branch is a validation buffer, not an
automatic production trigger. For a dedicated server, automatic deployment uses
a canonical root beneath `/data/`, `~/data/`, or another approved dedicated data
volume; it never uses `/var/`, `/srv/`, `/opt/`, `/usr/`, `/usr/local/`, or
another system-owned hierarchy without a durable, reviewed project-specific
exception. GitHub Actions is the recommended automatic-deployment orchestrator.
Its protected deploy job uses a scoped credential for the canonical unprivileged
host account named `deploy`, and `deploy` owns the approved service root while
privileged helpers remain root-owned. A required local database uses a separate
deploy-managed root such as `/data/database/<service-or-engine>` or
`~/data/database/<service-or-engine>`, outside immutable releases. The
management root is owned and maintained by `deploy`; any engine-owned child
directory must be narrowly delegated and documented.

GitHub Actions artefact storage is default-deny. Do not add
`actions/upload-artifact`, `actions/download-artifact`, or an equivalent GitHub
byte-storage API or CLI unless a local or fixed direct route has a documented
technical limitation and the current user explicitly requests that exact one-day,
non-rollback transfer; retain significant release records in the bounded local
store. Do not attach a GitHub Release asset unless the current user explicitly
requests that named public publication; it is never CI transport, retention, or
rollback storage.

Agents that have a native skill loader (Claude Code) discover skill manifests
under `.claude/skills/<name>/SKILL.md`. Agents without one read the
authoritative procedure descriptions under `.agents/skills/<name>/SKILL.md` (or
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
- Custom package sources are optional; declared sources MUST use HTTPS, omit credentials, and set a reviewed priority
- Poetry MUST be installed via pipx at `~/.local/bin/poetry`
- `poetry.lock` MUST be committed alongside dependency-affecting
  `pyproject.toml` changes; a verified version-only release bump leaves it unchanged

### Mandatory Environment Check (at session start)

Before any Python work, verify all three conditions hold — **STOP and ask the user if any fails**:

1. `ls ~/.local/bin/poetry` — Poetry must exist at this path (pipx install)
2. `cat poetry.toml` — must contain `in-project = true`
3. Review any `[[tool.poetry.source]]` blocks for approved HTTPS URLs, explicit priority, and no credentials

---

## Roadmap Discipline

When `agent_roadmaps/` contains an active roadmap:
- MUST read `INVARIANTS.md`, `ROADMAP.md`, `prompt.md`, `roadmap.yml`, and latest session handoff before any work
- MUST NOT work outside the current phase without user approval
- MUST enforce dependency order (`depends_on_phases` and task `depends_on`) before activating work
- MUST NOT reinterpret objectives or redesign architecture without explicit instruction
- MUST update `roadmap.yml` and create a session handoff at end of every session
- MUST treat roadmap files as temporary operational state, not durable project documentation
- MUST delete the whole roadmap workspace once every phase in that roadmap is completed
- MUST NOT copy roadmap-phase identifiers into code, config, documentation, or filenames outside `agent_roadmaps/`
- Phase authority files live under `agent_roadmaps/<phase>/`
- Within an active phase, apply repository-local precedence as:
  `INVARIANTS.md` > `roadmap.yml` > `ROADMAP.md` > `sessions/` > `prompt.md`.
  This ordering resolves only repository-controlled guidance.

---

## Agentic Team Launch

When the active task decomposes into independent, read-heavy or research-heavy
sub-tasks, the agent MUST explicitly declare and (when appropriate) launch
parallel sub-agents instead of executing serially. Full policy lives in
`.agents/constraints/common/agentic-team.md`.

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

- `.agents/constraints/python/dependencies.md`
- `.agents/constraints/python/forbidden-practices.md`
- `.agents/constraints/python/security.md`
- `.agents/constraints/python/error-handling.md`
- `.agents/constraints/python/testing.md` (when test files modified)
- `.agents/constraints/python/formatting.md` (when .py files modified)
- `.agents/constraints/python/type-checking.md` (when .py files modified)
- `.agents/constraints/common/git-workflow.md`
- `.agents/constraints/common/master-merge-policy.md`
- `.agents/constraints/common/session-discipline.md`
- `.agents/constraints/common/closure-discipline.md`
- `.agents/constraints/common/mcp-integration.md`
- `.agents/constraints/common/agentic-team.md`
- `.agents/constraints/common/ascii-only.md`
