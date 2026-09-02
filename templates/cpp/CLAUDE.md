# Claude Code: C++/CUDA Project

## CRITICAL: Session Initialization

FIRST ACTION every session, no exceptions:

```
/init
```

Skipping `/init` is a critical failure. It loads project constraints,
detects project type, checks roadmaps, runs capability audit, and writes
session state.
The normal init path prints a bounded, profile-aware constraint manifest.
Read the listed files before work to which they apply.

Before editing, Claude Code MUST read `AGENTS.md`, `.agents/project.yml`,
`.agents/capabilities.yml`, `.agents/constraints/common/`, and `.agents/constraints/cpp/`.
Load relevant skills from `.claude/skills/` or `.agents/skills/` before following a
workflow. Treat constraints as mandatory; when rules conflict, prefer the
stricter rule. If a request conflicts with these constraints, stop and explain.
Do not bypass hooks, wrappers, `/init`, `/check-constraints`, tests, or
pre-commit validation.

### Capability Audit

The `/init` skill runs a deterministic capability audit that verifies:
- Required Claude Code plugins are installed and enabled
- Required project skills exist under `.claude/skills/`
- Context7 MCP server is configured and healthy

If the audit fails, the session is locked down:
- Mutation operations (Write/Edit/Bash) are blocked
- Read-only operations (Read/Glob/Grep) remain available
- You must install missing capabilities and re-run `/init` to unlock

The audit reads `.agents/capabilities.yml` as the canonical manifest.

For consistency across different machines and networks, the Context7 integration
check uses a fallback path: if `claude mcp list` health probing is temporarily
unavailable, audit can validate plugin-side Context7 MCP configuration via
`claude plugins list --json`.

Required Claude Code bootstrap commands for this repository:

```bash
# Primary method (plugin-backed MCP):
claude plugin install context7@claude-plugins-official
# Fallback method (manual MCP server):
# CONTEXT7_API_KEY must already be exported from an approved secret source.
claude mcp add --transport http context7 https://mcp.context7.com/mcp \
  --header "CONTEXT7_API_KEY: ${CONTEXT7_API_KEY}"
```

If Context7 still fails after installation, run this generic repair sequence:

```bash
claude plugin marketplace update claude-plugins-official
claude plugin update context7@claude-plugins-official
npm install -g --prefix "$HOME/.local" @upstash/context7-mcp
```

### Bundled Behavioural Skill

This template bundles `karpathy-guidelines` in `.claude/skills/karpathy-guidelines/`.

Use it for non-trivial coding, debugging, review, and refactor work. It keeps
assumptions explicit, pushes toward minimal diffs, and requires concrete
verification before completion.

Before closing any session, task, commit, or roadmap phase, follow
`.agents/constraints/common/closure-discipline.md`: re-check the request and
constraints, review changes critically, run the strongest relevant validation,
fix in-scope issues found during review, and report residual risk honestly.

The repository requires British English for user-facing text.

## Git Commit Attribution Policy

NEVER include in commit messages:
- `Co-Authored-By:` lines
- Any reference to AI assistance or tooling
- Email addresses like `<noreply@anthropic.com>`

Within repository commit-metadata policy, do not add these markers unless the
user explicitly requests them and higher-priority requirements permit it. If a
higher-priority requirement makes that impossible, report the conflict rather
than silently changing commit metadata.

## Project Configuration Migration

This template supports both the new `project_profile` schema and the legacy
`project_type` field in `.agents/project.yml`. The legacy field continues to work
exactly as before; the new schema is optional and provides finer-grained control
for hybrid projects.

For details, see `.agents/adr/0001-project-profile.md`.

## Platform and Repository-Local Policy

Repository policy does not supersede higher-priority platform safety,
developer, organisational, or tool-enforced requirements. If they conflict,
follow the higher-priority requirement, minimise the deviation, and report it.

Within repository-controlled guidance, use the scoped order in `AGENTS.md` and
`.agents/constraints/common/instruction-hierarchy.md`. Current `roadmap.yml` state
takes precedence over roadmap prose and session records; temporary notes cannot
change durable project policy.

## C++ First Principle

This is a C++/CUDA project. C++ is the only implementation language. Every feature,
algorithm, and data structure MUST be implemented in C++. There are no Python helpers,
no Python glue scripts, and no prototyping in Python. If a Python binding layer is
ever added, follow the Hybrid project constraints (`hybrid/cpp-first.md`).

Build ownership is CMake/CPM first:

```text
CMake owns the native build graph.
CPM owns lightweight C++ dependency acquisition.
Conan, vcpkg, Bazel, and git submodules require an ADR.
```

Required native validation:

```bash
cmake -S . -B build -G Ninja -DCMAKE_BUILD_TYPE=RelWithDebInfo
cmake --build build -j
ctest --test-dir build --output-on-failure
```

## Absolute Prohibitions

- NEVER commit directly to `master`, `main`, `develop`, `release/*`, or `hotfix/*`, except through the bounded `.agents/bin/agent-release bump <x.y.z>` operation on clean, current `develop`
- NEVER open or merge a master-bound PR/MR except from same-repository `release/v<MAJOR>.<MINOR>.<PATCH>` or `hotfix/v<MAJOR>.<MINOR>.<PATCH>`; `develop` is categorically invalid, and the source tree must pass the presence-based `master-merge-gate`. The version comes from the authoritative manifest at the recorded source commit and the merged commit is tagged `release-v<MAJOR>.<MINOR>.<PATCH>`
- NEVER merge `master` into or rebase `develop` onto `master` for an ordinary release; release trees contain only forbidden-path deletions relative to their recorded `develop` SHA
- A master-origin hotfix MUST record reduced validation and return to `develop` through a reviewed merge or cherry-pick PR, never through rebase
- NEVER install C++ libraries via system package managers; NVIDIA/AMD GPU libraries and toolchains are discovered as external SDKs
- NEVER add C++ dependencies outside `cmake/Dependencies.cmake` unless an ADR approves a system SDK or exceptional manager
- NEVER use floating dependency branches such as `main`, `master`, or `develop`
- NEVER use raw `new`/`delete` — use smart pointers and RAII
- NEVER use C-style casts — use `static_cast`/`dynamic_cast`/`reinterpret_cast`
- NEVER ignore CUDA API error codes
- NEVER commit without running `/pre-commit validate` first, except the release wrapper's structurally verified version-only commit
- NEVER commit code with compiler warnings (`-Wall -Wextra -Wpedantic -Werror`)

## Required Workflow Commands

These `.agents/bin/agent-*` commands are the canonical tool interface. Use them
directly whenever performing the corresponding workflow step:

- Init: `.agents/bin/agent-init --platform claude`
- Build orchestration: `.agents/bin/agent-build <setup|compile|test|full|doctor|clean>`
- Constraint check: `.agents/bin/agent-check-constraints`
- Pre-commit validation: `.agents/bin/agent-precommit`
- Dependency add: `.agents/bin/agent-dependency add <package> [version]`
- Roadmap workflow: `.agents/bin/agent-roadmap <check|create|status|update|handoff|complete|validate>`
- Commit with policy guard: `.agents/bin/agent-commit -m "type(scope): description" <file1> [file2 ...]`

## Claude Code Skill Mappings

Skills are convenience wrappers around `.agents/bin/agent-*` commands.
When a slash command is unavailable or you need finer control, call the
`.agents/bin/agent-*` command directly.

| Procedure | Skill | Underlying command |
|-----------|-------|--------------------|
| Session init | `/init` | `.agents/bin/agent-init --platform claude` |
| Release preparation | *(command only)* | `.agents/bin/agent-release <bump|prepare|verify-metadata>` |
| Build orchestration | `/build <cmd>` | `.agents/bin/agent-build <setup|compile|test|full|doctor|clean>` |
| Pre-commit | `/pre-commit validate` | `.agents/bin/agent-precommit` |
| Add dependency | `/dependency add <pkg> [ver]` | `.agents/bin/agent-dependency add <pkg> [ver]` |
| Check constraints | `/check-constraints` | `.agents/bin/agent-check-constraints` |
| Commit | *(use command directly)* | `.agents/bin/agent-commit -m "msg" <files...>` |
| Roadmap management | `/roadmap <cmd>` | `.agents/bin/agent-roadmap <check|create|status|update|handoff|complete|validate>` |
| Doc lookup | `/context7` | — |
| Code navigation | `/navigate` | `.agents/skills/navigate/SKILL.md` |
| Host deployment guidance | `/deploy-service` | `.agents/skills/deploy-service/SKILL.md` |
| GitHub Actions CI/CD | `/service-cicd` | `.agents/skills/service-cicd/SKILL.md` |
| Branch governance | `/branch-governance` | `.agents/skills/branch-governance/SKILL.md` |
| GPU CI guidance | `/gpu-ci` | `.agents/skills/gpu-ci/SKILL.md` |
| Build project | `/build` | — |

For host deployment or GitHub Actions CI/CD work, Claude MUST read both
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

## Vendor-Neutral Constraints

All coding standards and workflow rules live in `.agents/constraints/`.
The `/init` skill selects the relevant subset at session start and prints their
paths. Read the manifest entries rather than injecting every body into the
initial session context.
For the full vendor-neutral reference, see `AGENTS.md`.

## Roadmap Authority

Within an active roadmap phase, repository-local precedence is:

1. `agent_roadmaps/<phase>/INVARIANTS.md`
2. `agent_roadmaps/<phase>/roadmap.yml`
3. `agent_roadmaps/<phase>/ROADMAP.md`
4. Latest file under `agent_roadmaps/<phase>/sessions/`
5. `agent_roadmaps/<phase>/prompt.md`

This scoped order does not supersede higher-priority platform or tool
requirements. Session records provide context and cannot change current state.
Roadmap files are temporary operational state: once every phase in that roadmap
is completed, delete the roadmap workspace and restore the placeholder
`agent_roadmaps/README.md`. Durable files outside `agent_roadmaps/` MUST NOT
carry roadmap-phase identifiers.

## Agentic Team Launch

For non-trivial tasks that decompose into independent, read-heavy, or
research-heavy sub-tasks, the agent MUST explicitly propose and (when
appropriate) launch parallel Claude Code sub-agents via the `Agent` tool
instead of executing sequentially. Suggested `subagent_type` values:

- `Explore` — broad codebase search / navigation
- `Plan` — design / architecture planning
- `general-purpose` — multi-step tasks with unknown scope

Full policy: `.agents/constraints/common/agentic-team.md`. Parallel execution MUST
NOT bypass capability audit, protected-branch rules, dependency ordering, or
pre-commit validation.
