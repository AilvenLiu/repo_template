# Vendor-Neutral AI Agent Constraints

This directory contains the canonical, vendor-neutral constraint definitions
for AI agent behaviour in this repository. These constraints define coding
standards, workflow rules, and quality requirements that apply regardless of
which AI agent platform is used.

## Directory Structure

```
.ai/
  tools/             # Shared runtime core (init/audit/policy/constraints)
  constraints/
    common/          # Cross-language constraints (git, sessions, roadmaps)
    python/          # Python-specific constraints
    cpp/             # C++/CUDA-specific constraints
  capabilities.yml   # Capability manifest for session audits
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
- Claude Code: `/init` -> `.ai/tools/session_init.py --platform claude`
- Codex / Cursor / Cline / generic agents.md consumers:
  `bin/agent-init --platform codex`

## How It Works

1. **This directory is the source of truth** for all constraint content.
2. **Shared runtime** (`.ai/tools`) implements deterministic checks and gates.
3. **Native platform entrypoints**:
   - `CLAUDE.md` is loaded automatically by Claude Code.
   - `AGENTS.md` is loaded automatically by Codex / Cursor / Cline /
     other agents.md-aware tools (per the [agents.md spec](https://agents.md)).
4. **Vendor-specific wrappers** (`.claude/skills/`, `bin/agent-*`) call into
   the shared runtime. `.codex/skills/` holds Codex-side procedure manifests
   that are read on demand from `AGENTS.md`.

## Adding a New AI Agent Platform

To support a new agent platform:

1. If the platform reads `AGENTS.md` natively (most agents.md-aware tools), no
   new entrypoint is needed — `AGENTS.md` already covers it.
2. Otherwise, add a single platform-specific entrypoint at the project root
   that points back to `AGENTS.md` and lists `bin/agent-*` wrappers.
3. Map the platform's invocation style (slash command, native skill loader,
   plain shell, etc.) onto the wrappers in `bin/`.

### Platform-Specific Skill Mappings

Different platforms have different ways to invoke procedures:

| Procedure | Claude Code | Codex / Cursor / Cline / generic |
|-----------|-------------|----------------------------------|
| Session init | `/init` | `bin/agent-init --platform codex` |
| Pre-commit | `/pre-commit validate` | `bin/agent-precommit` |
| Add dependency | `/dependency add <pkg>` | `bin/agent-dependency add <pkg>` |
| Roadmap workflow | `/roadmap <cmd>` | `bin/agent-roadmap <cmd>` |
| Constraint check | `/check-constraints` | `bin/agent-check-constraints` |
| Build orchestration | `/build` | `bin/agent-build <subcommand>` |
| Commit with policy | _(not exposed)_ | `bin/agent-commit -m "..." <files...>` |

The constraint files describe **what** must be done; the wrappers implement
**how** to do it.

## Constraint Categories

### Common (all languages)
- **git-workflow.md** - Branch policy, commit conventions, protected branches
- **session-discipline.md** - Session continuity, decision hygiene
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
- **dependencies.md** - Conan/vcpkg, CMake integration
- **error-handling.md** - Exception safety, RAII
- **memory-safety.md** - Smart pointers, ownership, RAII
- **documentation.md** - Doxygen-style comments
- **testing.md** - Google Test, Catch2, coverage
- **formatting.md** - clang-format, naming conventions
- **static-analysis.md** - clang-tidy, cppcheck
- **forbidden-practices.md** - Banned patterns
- **cmake.md** - CMake 3.20+, modern targets
- **cuda.md** - CUDA APIs, error checking, memory management
