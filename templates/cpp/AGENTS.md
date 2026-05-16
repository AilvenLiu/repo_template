# Agent Operating Constraints: C++/CUDA Projects

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
- NEVER commit first-party code with compiler warnings (use per-target `-Werror`)

### Dependencies
- NEVER install C++ libraries via system package managers: `apt install`, `yum install`, `brew install`, `pacman -S` (NVIDIA/AMD GPU libraries excepted)
- NEVER add a dependency without declaring it in a documented mechanism (conanfile.txt, vcpkg.json, CMakeLists.txt FetchContent, .gitmodules)
- NEVER commit code that uses a library not declared in the manifest

### Memory Safety
- NEVER use raw pointers for ownership — use `std::unique_ptr` or `std::shared_ptr` smart pointers
- NEVER use manual `new`/`delete` in application code — use RAII and containers
- NEVER implement manual resource management when RAII is possible

### Security
- NEVER hardcode secrets, credentials, or API keys in source code
- NEVER pass user-controlled input to `system()`, `popen()`, or shell-like APIs
- NEVER trust input from network or files without validation

### Type Safety
- NEVER use C-style casts — use `static_cast`, `dynamic_cast`, `reinterpret_cast`
- NEVER use `using namespace` in header files

### CUDA
- NEVER ignore CUDA API error codes
- NEVER launch a kernel without checking `cudaGetLastError()` after launch
- NEVER use deprecated CUDA APIs (`cudaThreadSynchronize`, `cudaThreadExit`)

### Code Quality
- NEVER commit code with failing tests
- NEVER suppress clang-tidy or cppcheck warnings without documented justification
- NEVER use generic macro names that could collide — prefix with project name

---

## Mandatory Workflow Checkpoints

### Before any code change
1. Run `git branch --show-current` — if on a protected branch, STOP and create a feature branch
2. If active roadmap exists, confirm work is within the current step

### Before adding any dependency
- MUST use the platform's dependency management procedure
- MUST NOT use system package managers or manual `conan install` directly

### Before every commit
1. MUST run pre-commit validation and confirm it passes (clang-format, clang-tidy, cppcheck, build)
2. MUST verify branch is not protected
3. Commit message MUST follow: `type(scope): description`
4. Commit message MUST NOT contain AI attribution

### Before claiming work is complete
- MUST have run tests and seen passing output
- MUST have zero compiler warnings in first-party code with `-Wall -Wextra -Wpedantic`

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
| Add dependency | `bin/agent-dependency add <pkg> [version]` | `/dependency` |
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
| Add library | Platform dependency skill | `apt install`, `brew install`, manual `conan install` directly |
| Install deps | Via documented mechanism (Conan, vcpkg, FetchContent, CPM, submodule) | System package managers |

- CMake 3.20+ is REQUIRED for all C++/CUDA projects
- Use documented dependency mechanisms: Conan (recommended), vcpkg, FetchContent, CPM, git submodules, or NVIDIA system libraries
- All dependencies MUST be pinned to exact versions in production
- Dependency manifests and CMakeLists.txt MUST be committed together when deps change

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
- MUST NOT copy roadmap-stage identifiers into code, config, documentation, or filenames outside `agent_roadmaps/`
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
- STOP and ask before: architectural changes, CUDA kernel launch configs, memory management strategy, threading model changes

---

## Quick Reference

| Concern | Standard |
|---------|----------|
| C++ version | C++17 minimum, C++20 recommended |
| CUDA version | 11.0 minimum, 12.0+ recommended |
| CMake version | 3.20+ (mandatory) |
| Dependency mechanisms | Conan (recommended), vcpkg, FetchContent, CPM, git submodules, NVIDIA system libraries |
| Formatter | clang-format |
| Static analysis | clang-tidy + cppcheck |
| Test framework | Google Test (primary), Catch2 (alternative) |
| Min coverage | 70% |
| Memory model | RAII mandatory for all resources |
| Encoding | ASCII-only in identifiers |

---

## Detailed Constraints

Read each file completely before working on related code:

- `.ai/constraints/cpp/dependencies.md`
- `.ai/constraints/cpp/forbidden-practices.md`
- `.ai/constraints/cpp/error-handling.md`
- `.ai/constraints/cpp/static-analysis.md`
- `.ai/constraints/cpp/testing.md` (when test files modified)
- `.ai/constraints/cpp/formatting.md` (when .cpp/.hpp files modified)
- `.ai/constraints/cpp/memory-safety.md` (when .cpp/.hpp files modified)
- `.ai/constraints/cpp/cuda.md` (when .cu/.cuh files modified)
- `.ai/constraints/cpp/cmake.md` (when CMakeLists.txt modified)
- `.ai/constraints/common/git-workflow.md`
- `.ai/constraints/common/session-discipline.md`
- `.ai/constraints/common/mcp-integration.md`
- `.ai/constraints/common/agentic-team.md`
- `.ai/constraints/common/ascii-only.md`
