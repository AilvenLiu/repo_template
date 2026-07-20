# Vendor-Neutral Agent Runtime

This directory is the canonical, vendor-neutral home for repository skills,
constraints, deterministic commands, hook implementations, project metadata,
and agent-facing documentation. Platform-native directories contain only the
registration or discovery adapters their respective tools require.

## Directory Structure

```text
.agents/
  skills/            # Canonical skills; discovered natively by Codex
  constraints/       # Shared and profile-specific mandatory policy
  scripts/           # Shared runtime core and deterministic checks
  bin/               # Stable repository command wrappers
  hooks/             # Canonical hook implementations and tests
  docs/              # Cross-platform architecture documentation
  capabilities.yml   # Capability manifest for session audits
  project.yml        # Active project profile
  README.md          # This file
```

## Capability Audits

The `capabilities.yml` file is the canonical manifest of required capabilities.
Manifest v2 separates:
- `common_requirements` (shared checks)
- `platform_requirements.<platform>` (platform-specific checks)

At session start, agents should:

1. Read `capabilities.yml` to understand required capabilities
2. Check which capabilities are available on the current machine
3. Report missing capabilities to the user
4. Hard-fail if required capabilities are missing (Claude Code enforces this)

For Claude Context7 integration checks, the runtime prefers live MCP health
results (`claude mcp list`) and falls back to plugin metadata
(`claude plugins list --json`) when health probing is transiently unavailable.

Both Claude and Codex use the shared audit runtime:
- Claude Code: `/init` -> `.agents/scripts/session_init.py --platform claude`
- Codex / Cursor / Cline / generic agents.md consumers:
  `.agents/bin/agent-init --platform codex`

## How It Works

1. **This directory is the sole source of truth for all constraint content.**
   Constraints are vendor-neutral and live exclusively under `.agents/constraints/`;
   there is no platform-specific constraint directory — both Claude Code and Codex
   receive the same profile-aware manifest from this location and read the same
   canonical bodies as needed.
2. **Shared runtime** (`.agents/scripts`) implements deterministic checks and gates.
3. **Native platform entrypoints**:
   - `CLAUDE.md` is loaded automatically by Claude Code.
   - `AGENTS.md` is loaded automatically by Codex / Cursor / Cline /
     other agents.md-aware tools (per the [agents.md spec](https://agents.md)).
4. **Native discovery and adapters**:
   - Codex discovers canonical skills directly from `.agents/skills/`.
   - Claude Code discovers thin delegates from `.claude/skills/`.
   - `.codex/hooks.json` and `.claude/settings.json` register thin platform
     hook adapters; canonical hook logic remains under `.agents/hooks/` and
     `.agents/scripts/`.
   - `.agents/bin/agent-*` exposes deterministic workflows to every platform.

## Constraint Loading Contract

Project type is determined from `.agents/project.yml`. Prefer `project_profile`
when present and fall back to legacy `project_type` only when needed.

| Profile | Constraint families selected for the init manifest |
|---------|------------------------------------------|
| Python | `.agents/constraints/common/`, `.agents/constraints/python/` |
| C++/CUDA | `.agents/constraints/common/`, `.agents/constraints/cpp/` |
| Hybrid Python/C++/CUDA | `.agents/constraints/common/`, `.agents/constraints/python/`, `.agents/constraints/cpp/`, `.agents/constraints/hybrid/` |

The canonical rule bodies remain in `.agents/constraints/`. Initialisation prints a
bounded manifest; agents read the listed files and constraints relevant to the
intended work before editing. Short mandatory summaries in `AGENTS.md`,
`CLAUDE.md`, and generated-template entrypoints must point back here instead of
becoming separate policy sources.

## Native Build Ownership Enforcement

For C++/CUDA and hybrid projects, CMake owns the native build graph and CPM owns
lightweight C++ dependency acquisition. Python packaging may expose native
artifacts, but must not become the owner of compiler flags, CUDA architecture
policy, native dependency discovery, native tests, benchmarks, or install/export
targets.

Run the fast policy sweep with:

```bash
.agents/bin/agent-check-constraints
```

It combines structural constraint checks, instruction-safety scanning, and
forbidden-pattern scanning, including representative checks for Python-first
native build orchestration in C++/CUDA and hybrid projects.

## Adding a New AI Agent Platform

To support a new agent platform:

1. If the platform reads `AGENTS.md` natively (most agents.md-aware tools), no
   new entrypoint is needed — `AGENTS.md` already covers it.
2. Otherwise, add a single platform-specific entrypoint at the project root
   that points back to `AGENTS.md` and lists `.agents/bin/agent-*` wrappers.
3. Map the platform's invocation style (slash command, native skill loader,
   plain shell, etc.) onto the wrappers in `.agents/bin/`.

### Platform-Specific Skill Mappings

Different platforms have different ways to invoke procedures:

| Procedure | Claude Code | Codex / Cursor / Cline / generic |
|-----------|-------------|----------------------------------|
| Session init | `/init` | `.agents/bin/agent-init --platform codex` |
| Pre-commit | `/pre-commit validate` | `.agents/bin/agent-precommit` |
| Add dependency | `/dependency add <pkg>` | `.agents/bin/agent-dependency add <pkg>` |
| Roadmap workflow | `/roadmap <cmd>` | `.agents/bin/agent-roadmap <cmd>` |
| Constraint check | `/check-constraints` | `.agents/bin/agent-check-constraints` |
| Build orchestration | `/build` | `.agents/bin/agent-build <subcommand>` |
| Commit with policy | _(not exposed)_ | `.agents/bin/agent-commit -m "..." <files...>` |
| Host deployment guidance | `/deploy-service` | `.agents/skills/deploy-service/SKILL.md` |
| GitHub Actions CI/CD | `/service-cicd` | `.agents/skills/service-cicd/SKILL.md` |

The constraint files describe **what** must be done; the wrappers implement
**how** to do it.

## Constraint Categories

### Common (all languages)
- **git-workflow.md** - Branch policy, commit conventions, protected branches
- **session-discipline.md** - Session continuity, decision hygiene
- **closure-discipline.md** - Review, validation, and evidence required before closure
- **roadmap-awareness.md** - Multi-session task management
- **ascii-only.md** - ASCII-only identifiers in source code
- **mcp-integration.md** - External documentation lookup requirements

### Python
- **dependencies.md** - Poetry, virtual environments, version pinning
- **error-handling.md** - Exception handling, context managers
- **security.md** - Input validation, secrets, SQL injection prevention
- **documentation.md** - Docstrings, README, API docs
- **testing.md** - pytest, coverage, test organisation
- **formatting.md** - ruff (sole formatter, linter, and import sorter), PEP 8
- **type-checking.md** - mypy, type hints
- **forbidden-practices.md** - Banned patterns and anti-patterns

### C++/CUDA
- **dependencies.md** - CPM-first dependency policy, CMake integration
- **error-handling.md** - Exception safety, RAII
- **memory-safety.md** - Smart pointers, ownership, RAII
- **documentation.md** - Doxygen-style comments
- **testing.md** - Google Test, Catch2, coverage
- **formatting.md** - clang-format, naming conventions
- **static-analysis.md** - clang-tidy, cppcheck
- **forbidden-practices.md** - Banned patterns
- **cmake.md** - CMake 3.24+, modern targets
- **cuda.md** - CUDA APIs, error checking, memory management
