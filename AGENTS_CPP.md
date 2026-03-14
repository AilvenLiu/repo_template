# Agent Operating Constraints: C++/CUDA Projects

## MANDATORY: Session Initialization

FIRST ACTION every session — run the platform's session initialization procedure.
Skipping is a critical failure.

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
- NEVER commit code with compiler warnings (`-Wall -Wextra -Wpedantic -Werror`)

### Dependencies
- NEVER install C++ libraries via system package managers: `apt install`, `yum install`, `brew install`, `pacman -S`
- NEVER add a dependency without updating `conanfile.txt` (or `vcpkg.json`)
- NEVER commit code that uses a library not declared in the manifest

### Memory Safety
- NEVER use raw pointers for ownership — use `std::unique_ptr` or `std::shared_ptr`
- NEVER use manual `new`/`delete` in application code — use RAII and containers
- NEVER implement manual resource management when RAII is possible

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
- MUST NOT use system package managers or manual `conan install` directly

### Before every commit
1. MUST run pre-commit validation and confirm it passes (clang-format, clang-tidy, cppcheck, build)
2. MUST verify branch is not protected
3. Commit message MUST follow: `type(scope): description`
4. Commit message MUST NOT contain AI attribution

### Before claiming work is complete
- MUST have run tests and seen passing output
- MUST have zero compiler warnings with `-Wall -Wextra -Wpedantic`

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

## Dependency Management

| Action | Correct | Forbidden |
|--------|---------|-----------|
| Add library | Platform dependency skill | `apt install`, `brew install`, `conan install` directly |
| Install deps | `conan install . --build=missing` (via skill) | System package managers |

- CMake 3.20+ is REQUIRED for all C++/CUDA projects
- Conan is the mandatory first choice; vcpkg only if Conan cannot meet the need
- All dependencies MUST be pinned to exact versions in production
- `conanfile.txt` and `CMakeLists.txt` MUST be committed together when deps change

---

## Roadmap Discipline

When `agent_roadmaps/` contains an active roadmap:
- MUST read `INVARIANTS.md`, `prompt.md`, `roadmap.yml`, and latest session handoff before any work
- MUST NOT work outside the current phase without user approval
- MUST NOT reinterpret objectives or redesign architecture without explicit instruction
- MUST update `roadmap.yml` and create a session handoff at end of every session

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
| Dependency tool | Conan (primary), vcpkg (fallback) |
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
- `.ai/constraints/common/ascii-only.md`
