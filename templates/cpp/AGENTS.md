# Agent Operating Constraints: C++/CUDA Projects

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
- NEVER commit directly to: `master`, `main`, `develop`, `release/*`, `hotfix/*`
- A PR/MR targeting `master` MUST originate in the same repository from `develop`, `release/*`, or `hotfix/*` only
- A master-bound PR/MR MUST pass `master-merge-gate`; its diff MUST NOT change `.ai/`, `.agents/`, `.claude/`, `.codex/`, `agent_roadmaps/`, `AGENTS.md`, `CLAUDE.md`, `CODEX.md`, or `docs/` outside `docs/changelog/`
- NEVER include `Co-Authored-By:`, AI attribution, or AI-related email addresses in commits
- NEVER use `git push --force` or `git reset --hard` without explicit user confirmation
- NEVER commit without running pre-commit validation first
- NEVER commit first-party code with compiler warnings (use per-target `-Werror`)

### Dependencies
- NEVER install C++ libraries via system package managers: `apt install`, `yum install`, `brew install`, `pacman -S` (NVIDIA/AMD GPU libraries excepted)
- NEVER add a C++ dependency outside `cmake/Dependencies.cmake` unless an ADR approves a system SDK or exceptional manager
- NEVER use floating dependency branches such as `main`, `master`, or `develop`
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
2. If active roadmap exists, confirm work is within the current phase

### Before adding any dependency
- MUST use the platform's dependency management procedure
- MUST NOT use system package managers or ad-hoc external package-manager installs directly

### Before every commit
1. MUST run pre-commit validation and confirm it passes (clang-format, clang-tidy, cppcheck, build)
2. MUST verify branch is not protected
3. Commit message MUST follow: `type(scope): description`
4. Commit message MUST NOT contain AI attribution

### Before claiming work is complete
- MUST have run tests and seen passing output
- MUST have zero compiler warnings in first-party code with `-Wall -Wextra -Wpedantic`
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
| Build orchestration | `.agents/bin/agent-build <setup\|compile\|test\|full\|doctor\|clean>` | `/build` |
| Pre-commit validation | `.agents/bin/agent-precommit` | `/pre-commit` |
| Add dependency | `.agents/bin/agent-dependency add <pkg> [version]` | `/dependency` |
| Constraint check | `.agents/bin/agent-check-constraints` | `/check-constraints` |
| Roadmap workflow | `.agents/bin/agent-roadmap <check\|create\|status\|update\|handoff\|complete\|validate>` | `/roadmap` |
| Commit with policy guard | `.agents/bin/agent-commit -m "type(scope): description" <files...>` | _(command only)_ |
| Documentation lookup | _(none)_ | `/context7` (or platform Context7 MCP) |
| Code navigation | `.agents/skills/navigate/SKILL.md` | `/navigate` |
| Host deployment guidance | `.agents/skills/deploy-service/SKILL.md` | `/deploy-service` |
| GitHub Actions CI/CD | `.agents/skills/service-cicd/SKILL.md` | `/service-cicd` |
| Branch governance | `.agents/skills/branch-governance/SKILL.md` | `/branch-governance` |
| GPU CI guidance | `.agents/skills/gpu-ci/SKILL.md` | `/gpu-ci` |

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

Agents that have a native skill loader (Claude Code) discover skill manifests
under `.claude/skills/<name>/SKILL.md`. Agents without one read the
authoritative procedure descriptions under `.agents/skills/<name>/SKILL.md` (or
follow the wrapper directly).

---

## Dependency Management

| Action | Correct | Forbidden |
|--------|---------|-----------|
| Add library | CPM entry in `cmake/Dependencies.cmake` | `apt install`, `brew install`, manual package-manager install |
| Install deps | Direct CMake configure/build with CPM cache | System package managers for C++ libraries |

- CMake 3.24+ is REQUIRED for all C++/CUDA projects
- CMake owns the native build graph
- CPM owns lightweight C++ dependency acquisition
- System/binary SDKs such as CUDA Toolkit, TensorRT, cuDNN, NCCL, and OpenMPI are discovered with `find_package`, cache variables, environment paths, or toolchain files
- Conan, vcpkg, Bazel, and git submodules require an ADR and are not defaults
- All dependencies MUST be pinned by immutable version, commit, or archive hash

Required native validation:

```bash
cmake -S . -B build -G Ninja -DCMAKE_BUILD_TYPE=RelWithDebInfo
cmake --build build -j
ctest --test-dir build --output-on-failure
```

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
- STOP and ask before: architectural changes, CUDA kernel launch configs, memory management strategy, threading model changes

---

## C++ First Principle

This is a C++/CUDA project. C++ is the only implementation language. There is no
Python layer unless the project explicitly includes one (in which case, see the
Hybrid project constraints and the `hybrid/cpp-first.md` policy).

Every feature, algorithm, and data structure MUST be implemented in C++. There are
no Python helpers, no Python glue scripts, and no prototyping in Python.

## Quick Reference

| Concern | Standard |
|---------|----------|
| C++ version | C++17 minimum, C++20 recommended |
| CUDA version | 11.0 minimum, 12.0+ recommended |
| CMake version | 3.24+ (mandatory) |
| Dependency mechanisms | CPM first for C++ source deps; `find_package` for system/binary SDKs |
| Formatter | clang-format |
| Static analysis | clang-tidy + cppcheck |
| Test framework | Google Test (primary), Catch2 (alternative) |
| Min coverage | 70% |
| Memory model | RAII mandatory for all resources |
| Encoding | ASCII-only in identifiers |

---

## Detailed Constraints

Read each file completely before working on related code:

- `.agents/constraints/cpp/dependencies.md`
- `.agents/constraints/cpp/forbidden-practices.md`
- `.agents/constraints/cpp/error-handling.md`
- `.agents/constraints/cpp/static-analysis.md`
- `.agents/constraints/cpp/testing.md` (when test files modified)
- `.agents/constraints/cpp/formatting.md` (when .cpp/.hpp files modified)
- `.agents/constraints/cpp/memory-safety.md` (when .cpp/.hpp files modified)
- `.agents/constraints/cpp/cuda.md` (when .cu/.cuh files modified)
- `.agents/constraints/cpp/cmake.md` (when CMakeLists.txt modified)
- `.agents/constraints/common/git-workflow.md`
- `.agents/constraints/common/master-merge-policy.md`
- `.agents/constraints/common/session-discipline.md`
- `.agents/constraints/common/closure-discipline.md`
- `.agents/constraints/common/mcp-integration.md`
- `.agents/constraints/common/agentic-team.md`
- `.agents/constraints/common/ascii-only.md`
