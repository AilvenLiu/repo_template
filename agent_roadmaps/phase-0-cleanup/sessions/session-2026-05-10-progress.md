# Session Handoff: 2026-05-10 Phase-0 Progress

## Session Summary

**Date**: 2026-05-10
**Phase**: phase-0-cleanup
**Branch**: roadmap/phase-0-cleanup
**Session type**: Multi-task execution

## Work Completed

### Task-0-1: Modernise CUDA tooling references (COMPLETED)
**Commit**: 2b8882e

**Changes**:
- Replaced all `nvprof` command examples with `ncu` (Nsight Compute) or `nsys` (Nsight Systems)
- Replaced all `cuda-memcheck` command examples with `compute-sanitizer`
- Added deprecation notes: "nvprof is deprecated in CUDA 11.0+; use ncu"
- Added deprecation notes: "cuda-memcheck is deprecated in CUDA 11.6+; use compute-sanitizer"

**Files modified**:
- `.ai/constraints/cpp/cuda.md`
- `.ai/constraints/cpp/memory-safety.md`
- `.ai/constraints/cpp/testing.md`
- `.ai/constraints/cpp/static-analysis.md`

**Acceptance criteria verified**:
- ✓ No `nvprof` outside deprecation notes
- ✓ No `cuda-memcheck` outside deprecation notes
- ✓ All command examples use modern tools

### Task-0-2: Add modern SM architectures (COMPLETED)
**Commit**: 4578902

**Changes**:
- Added SM_89 (Ada Lovelace / RTX 40xx) to architecture lists
- Added SM_90 (Hopper / H100) to architecture lists
- Added SM_100 (Blackwell / B100, GB200) to architecture lists
- Changed default recommendation to `CMAKE_CUDA_ARCHITECTURES=native` for auto-detection
- Updated all architecture examples to include modern GPUs

**Files modified**:
- `.ai/constraints/cpp/cmake.md`
- `.ai/constraints/cpp/cuda.md`

**Acceptance criteria verified**:
- ✓ SM_89, SM_90, SM_100 each appear with architecture name comments
- ✓ Default example uses `native` or lists including 89, 90, 100
- ✓ No example pins to SM_70-87 without explanatory comment

### Task-0-3: Scope -Werror to first-party targets (COMPLETED)
**Commit**: 2c8dd04

**Changes**:
- Rewrote -Werror guidance to apply only to first-party code
- Documented `target_compile_options(PRIVATE -Werror)` pattern
- Documented `target_include_directories(SYSTEM PRIVATE ...)` pattern for third-party headers
- Added examples for CUTLASS, Thrust, Eigen as SYSTEM includes
- Updated forbidden-practices.md to reflect scoped approach
- Updated templates/cpp/AGENTS.md with scoped language

**Files modified**:
- `.ai/constraints/cpp/cmake.md`
- `.ai/constraints/cpp/forbidden-practices.md`
- `templates/cpp/AGENTS.md`

**Rationale**: Prevents builds from breaking when third-party libraries (CUTLASS, Thrust, 
Eigen) emit warnings, while maintaining strict warning discipline for project code.

**Acceptance criteria verified**:
- ✓ -Werror requirement explicitly says "first-party targets"
- ✓ CMake snippets show `target_compile_options(PRIVATE -Werror)` and SYSTEM includes
- ✓ forbidden-practices.md table reflects scoped rule

### Task-0-4: Fix broken CUDA streams example (COMPLETED)
**Commit**: 7d9ede7

**Changes**:
- Replaced variable-length array `cudaStream_t streams[num_streams]` with `std::vector<cudaStream_t>`
- Moved device memory allocation outside async operations loop
- Moved device memory deallocation to cleanup phase after synchronisation
- Wrapped all CUDA API calls in `CUDA_CHECK` macro
- Added `CUDA_CHECK(cudaGetLastError())` after kernel launch

**Files modified**:
- `.ai/constraints/cpp/cuda.md` (section 7.4)

**Issues fixed**:
1. VLA not portable in C++
2. Allocating inside async loop defeats concurrency purpose
3. Freeing inside async loop before synchronisation is incorrect
4. Missing error checking on all CUDA calls

**Acceptance criteria verified**:
- ✓ No variable-length array
- ✓ cudaMalloc/cudaFree once per stream, outside async loop
- ✓ All CUDA API calls wrapped in CUDA_CHECK

### Task-0-5: Broaden dependency mechanism rules (COMPLETED)
**Commit**: d785fa1

**Changes**:
- Removed "Conan is the mandatory first choice" language
- Added support for multiple documented mechanisms:
  - Conan (recommended for most projects)
  - vcpkg (alternative package manager)
  - CPM (CMake Package Manager)
  - FetchContent (CMake built-in)
  - Git submodules (for vendored dependencies)
  - NVIDIA/AMD system libraries (CUDA Toolkit, cuDNN, NCCL, TensorRT, ROCm)
- Added selection criteria for each mechanism
- Added CMake integration examples for each mechanism
- Rewrote system package manager prohibition to explicitly allow NVIDIA/AMD GPU libraries
- Updated templates to reflect broader mechanism support

**Files modified**:
- `.ai/constraints/cpp/dependencies.md` (major rewrite)
- `templates/cpp/AGENTS.md`
- `templates/cpp/CLAUDE.md`

**Key principle preserved**: Every dependency MUST be declared in a documented, 
reproducible mechanism. System package managers forbidden for general C++ libraries 
but allowed for NVIDIA/AMD GPU ecosystem.

**Acceptance criteria verified**:
- ✓ Each mechanism (Conan, vcpkg, CPM, FetchContent, submodules, NVIDIA) has selection criteria
- ✓ System package manager prohibition allows CUDA Toolkit, cuDNN, NCCL, TensorRT, ROCm
- ✓ "Conan is the mandatory first choice" phrase removed

## Current State

**Active task**: task-0-6 (Reconcile drift and prune unenforceable rules)

**Roadmap status**:
- Phase: active, started 2026-05-09
- Tasks completed: 5/6 (83%)
- Tasks active: 0/6 (task-0-6 ready to start)
- Tasks pending: 1/6

**Branch state**:
- Branch: `roadmap/phase-0-cleanup`
- Commits: 5 (2b8882e, 4578902, 2c8dd04, 7d9ede7, d785fa1)
- All commits follow "chore(constraints): ..." format
- No AI attribution in any commit (per root CLAUDE.md policy)

## Next Steps for Task-0-6

Task-0-6 is the final and most complex task. It requires:

1. **Fix ARCHITECTURE.md drift**:
   - `.claude/skills/ARCHITECTURE.md` references `verify_skills.py`
   - Script does not exist at referenced path
   - Options: remove reference OR create thin wrapper delegating to `.ai/scripts/roadmap/validate_schema.py`

2. **Audit C++/CUDA constraints for enforcement**:
   - Search all MUST/FORBIDDEN clauses in:
     - `.ai/constraints/cpp/cuda.md`
     - `.ai/constraints/cpp/dependencies.md`
     - `.ai/constraints/cpp/cmake.md`
     - `.ai/constraints/cpp/testing.md`
   - For each clause, identify enforcement path:
     - Hook (pre-commit, commit-msg, etc.)
     - Wrapper script (`bin/agent-*`)
     - CI gate
     - Advisory only (no enforcement)

3. **Demote or remove unenforceable rules**:
   - If no enforcement path exists, either:
     - Demote MUST → SHOULD
     - Demote FORBIDDEN → DISCOURAGED
     - Remove entirely if not useful as guidance
   - Document each change with rationale

4. **Session handoff documentation**:
   - List every demoted/removed rule
   - Provide rationale for each decision
   - Note which rules remain as "advisory only"

**Estimated effort**: Medium (2-3 hours)

**Dependencies**: All prior tasks completed

## Decisions Made

1. **Branch strategy**: Cut phase branch from chore branch rather than waiting for 
   merge to master (approved by user for momentum)

2. **Deprecation notes**: Kept one-line notes for deprecated tools (nvprof, cuda-memcheck) 
   to help users migrating from older CUDA versions

3. **-Werror scoping**: Applied to first-party targets only via `target_compile_options(PRIVATE)` 
   rather than global flags, preventing third-party library warnings from breaking builds

4. **Dependency mechanisms**: Broadened from "Conan or vcpkg only" to multiple documented 
   mechanisms with selection criteria, recognizing that AI infra projects (TVM, MLC-LLM, 
   FlashInfer) use diverse dependency strategies

## Blockers

None.

## Notes

- All changes are surgical, touching only content specified in task descriptions
- British English spelling and ASCII-only enforcement preserved throughout
- No AI attribution in commit messages per root CLAUDE.md policy
- Each task verified against acceptance criteria before marking complete
- Context7 installed and capability audit passes (22/22 capabilities)

## Statistics

- **Session duration**: ~4 hours
- **Tasks completed**: 5
- **Files modified**: 11 unique files
- **Commits**: 5
- **Lines changed**: ~400 insertions, ~200 deletions (estimated)
