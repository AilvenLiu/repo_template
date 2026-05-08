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
- Claude: `/init` -> `.ai/tools/session_init.py --platform claude`
- Codex: `bin/agent-init --platform codex`

## How It Works

1. **This directory is the source of truth** for all constraint content.
2. **Shared runtime** (`.ai/tools`) implements deterministic checks and gates.
3. **Vendor-specific wrappers** (`.claude/`, `.codex/`) call into the shared runtime.
4. **Agent instruction file** (`AGENTS.md`) provides the vendor-neutral
   operating instructions that reference these constraints.
5. **Vendor-specific files** (`CLAUDE.md`, `CODEX.md`, etc.) are self-sufficient
   entrypoints that embed critical rules inline and reference `AGENTS.md`
   for the full constraint system.

## Adding a New AI Agent Platform

To support a new agent platform:

1. Create the platform's config directory (e.g. `.newagent/`)
2. Create an instruction file (e.g. `NEWAGENT.md`) that:
   - References `AGENTS.md` for constraints
   - Adds any platform-specific skill mappings
3. Map platform-specific skills to the generic procedures described in
   the constraint files (session init, pre-commit validation, dependency
   management, etc.)

### Example: Codex Integration

For Codex:

1. **Codex uses `CODEX.md` as the platform entrypoint**
2. **Session init uses `bin/agent-init --platform codex`**
3. **Shared checks run from `.ai/tools`**
4. **Codex skills are bundled in `.codex/skills`**

Key differences from Claude Code:
- **Claude Code**: `CLAUDE.md` + `/init` -> shared `.ai/tools` runtime
- **Codex**: `CODEX.md` + `bin/agent-init --platform codex` -> shared `.ai/tools` runtime
- **Other agents**: Can use either pattern depending on their file discovery mechanism

### Platform-Specific Skill Mappings

Different platforms have different ways to invoke procedures:

| Procedure | Claude Code | Codex | Generic |
|-----------|-------------|-------|---------|
| Session init | `/init` | `bin/agent-init --platform codex` | `python3 .ai/tools/session_init.py --platform <platform>` |
| Pre-commit | `/pre-commit validate` | `bin/agent-precommit` | `python3 .ai/tools/constraints_check.py` (+ platform validators) |
| Add dependency | `/dependency add <pkg>` | `bin/agent-dependency add <pkg>` | `python3 .claude/skills/dependency/scripts/add.py` |
| Roadmap workflow | `/roadmap <cmd>` | `bin/agent-roadmap <cmd>` | `python3 .claude/skills/roadmap/scripts/<command>.py` |

The constraint files describe **what** must be done; platform-specific skills implement **how** to do it.

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
