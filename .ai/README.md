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
  README.md          # This file
```

## How It Works

1. **This directory is the source of truth** for all constraint content.
2. **Vendor-specific wrappers** (e.g. `.claude/`, `.cursor/`) import from here.
3. **Agent instruction file** (`AGENT.md`) provides the vendor-neutral
   operating instructions that reference these constraints.
4. **Vendor-specific files** (`CLAUDE.md`, etc.) are thin wrappers that
   include the agent instruction file plus any platform-specific configuration.

## Adding a New AI Agent Platform

To support a new agent platform:

1. Create the platform's config directory (e.g. `.newagent/`)
2. Create a thin wrapper instruction file (e.g. `NEWAGENT.md`) that:
   - References `AGENT.md` for constraints
   - Adds any platform-specific skill mappings
3. Map platform-specific skills to the generic procedures described in
   the constraint files (session init, pre-commit validation, dependency
   management, etc.)

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
