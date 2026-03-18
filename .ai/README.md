# Vendor-Neutral AI Agent Constraints

This directory contains the canonical, vendor-neutral constraint definitions
for AI agent behaviour in this repository. These constraints define coding
standards, workflow rules, and quality requirements that apply regardless of
which AI agent platform is used.

## Directory Structure

```
.ai/
  constraints/
    common/          # Cross-language constraints (git, sessions, roadmaps)
    python/          # Python-specific constraints
    cpp/             # C++/CUDA-specific constraints
  capabilities.yml   # Capability manifest for session audits
  README.md          # This file
```

## Capability Audits

The `capabilities.yml` file is the canonical manifest of required plugins,
skills, and integrations for this project. At session start, agents should:

1. Read `capabilities.yml` to understand required capabilities
2. Check which capabilities are available on the current machine
3. Report missing capabilities to the user
4. Hard-fail if required capabilities are missing (Claude Code enforces this)

For Claude Code, the `/init` skill runs this audit automatically and locks
down the session if required capabilities are missing. Non-Claude agents
should implement similar checks or report missing capabilities and continue
with partial functionality where constraints allow.

## How It Works

1. **This directory is the source of truth** for all constraint content.
2. **Vendor-specific wrappers** (e.g. `.claude/`, `.cursor/`) import from here.
3. **Agent instruction file** (`AGENTS.md`) provides the vendor-neutral
   operating instructions that reference these constraints.
4. **Vendor-specific files** (`CLAUDE.md`, etc.) are self-sufficient
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

For Google's Codex agent:

1. **Codex discovers `AGENTS.md` automatically** as a standard instruction file
2. **AGENTS.md is self-sufficient** — contains all mandatory constraints inline
3. **Codex reads `.ai/constraints/` files** when referenced by AGENTS.md
4. **No Codex-specific wrapper needed** — the vendor-neutral architecture works directly

Key differences from Claude Code:
- **Claude Code**: Uses `CLAUDE.md` as entrypoint → references `AGENTS.md` → loads `.ai/constraints/` via `/init` skill
- **Codex**: Uses `AGENTS.md` as entrypoint → reads `.ai/constraints/` files directly when needed
- **Other agents**: Can use either pattern depending on their file discovery mechanism

### Platform-Specific Skill Mappings

Different platforms have different ways to invoke procedures:

| Procedure | Claude Code | Codex | Generic |
|-----------|-------------|-------|---------|
| Session init | `/init` | Read AGENTS.md + constraints | Platform-specific |
| Pre-commit | `/pre-commit validate` | Run validation script | `python3 .claude/skills/pre-commit/scripts/validate.py` |
| Add dependency | `/dependency add <pkg>` | Run dependency script | `python3 .claude/skills/dependency/scripts/add.py` |

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
- **formatting.md** - black, ruff, PEP 8
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
