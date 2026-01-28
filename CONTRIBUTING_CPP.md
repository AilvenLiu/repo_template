# Development & Collaboration Guidelines for C++/CUDA Projects

> **This document defines mandatory contribution standards for C++/CUDA repositories.**
> All contributors (human or AI) must follow these rules.

## Quick Start for Contributors

Before making any changes:

1. **Run `/init` at session start** - Loads relevant constraints based on your work
2. **Create a feature branch** - Never commit directly to protected branches
3. **Follow loaded constraints** - Technical requirements are in `.claude/constraints/`
4. **Run `/pre-commit validate`** - Before committing to check formatting, linting, build, tests
5. **Open a pull request** - Follow the PR template below

For detailed technical requirements, see `.claude/constraints/cpp/` and run `/init`.

## 1. General Principles

- Prefer **clarity over cleverness**
- Prefer **explicit decisions over implicit assumptions**
- Prefer **small, reviewable changes over large, opaque ones**
- Never trade correctness or safety for speed
- Follow modern C++ best practices (C++17+)
- Prioritise memory safety and RAII principles

If unsure, ask before acting.

## 2. Constraint System

This repository uses a modular constraint system. Instead of duplicating all technical requirements here, detailed constraints are organised in `.claude/constraints/`:

### C++/CUDA-Specific Constraints
- `cpp/testing.md` - Google Test, Catch2, coverage (70%+)
- `cpp/formatting.md` - clang-format, naming conventions
- `cpp/cmake.md` - CMake 3.20+, modern target-based approach
- `cpp/cuda.md` - CUDA 11.0+, memory management, error checking
- `cpp/memory-safety.md` - RAII (mandatory), smart pointers, ownership
- `cpp/static-analysis.md` - clang-tidy, cppcheck
- `cpp/documentation.md` - Doxygen-style comments

### Common Constraints (All Projects)
- `common/git-workflow.md` - Branch policy, commit conventions, PR guidelines
- `common/roadmap-awareness.md` - Roadmap execution discipline
- `common/session-discipline.md` - Session continuity, decision hygiene

### Loading Constraints Automatically

At the start of every session, run:

```bash
/init
```

This skill will:
- Detect project type (C++/CUDA)
- Check for active roadmaps
- Analyse git status and modified files
- Load only relevant constraints based on your current work
- Warn if you're on a protected branch

See CLAUDE.md for details on the constraint system and authority hierarchy.

## 3. Branching and Commits

### Protected Branches

**ABSOLUTE PROHIBITION**: Never commit directly to:
- `master` or `main`
- `develop`
- `release/*`
- `hotfix/*`

Always work on feature branches: `feat/<description>`, `fix/<description>`, etc.

### Commit Message Format

```
<type>(optional-scope): <short summary>

[optional body]
```

Types: `feat`, `fix`, `refactor`, `perf`, `docs`, `test`, `chore`, `style`

Rules:
- Less than 72 characters
- Imperative mood ("add", not "added")
- ASCII-only characters
- British English spelling

See `.claude/constraints/common/git-workflow.md` for detailed commit conventions.

## 4. Pull Request Guidelines

### PR Title

Follow commit message format:
```
<type>(optional-scope): <short description>
```

### PR Description Template

```markdown
## Summary
Brief description of what this PR does (2-3 sentences).

## Motivation
Why is this change necessary? What problem does it solve?

## Changes
- Bullet list of key changes
- New files added
- Modified interfaces
- Deprecated functionality

## Technical Details
### C++ Changes
- List C++ specific changes
- API modifications
- Memory management changes

### CUDA Changes (if applicable)
- Kernel modifications
- Memory transfer optimisations
- Launch configuration changes
- Performance characteristics

## Performance Impact
- Benchmark results (if applicable)
- Memory usage changes
- Compilation time impact

## Testing
- Unit tests added/modified
- Integration tests
- CUDA-specific tests
- How to verify the changes

## Build & Compatibility
- CMake changes
- Compiler compatibility
- CUDA toolkit version requirements
- Compute capability requirements

## Breaking Changes
- List any breaking changes
- Migration guide (if needed)

## Related
- Related issues: #123, #456
- Related PRs
```

### Before Opening a PR

Run the pre-commit validation:

```bash
/pre-commit validate
```

This checks:
- Code formatting (clang-format)
- Static analysis (clang-tidy, cppcheck)
- Build (CMake)
- Tests (ctest)
- CUDA error checking

Fix any issues before opening the PR.

## 5. Code Review Process

### For Authors

**Before requesting review**:
1. Self-review your changes
2. Run `/pre-commit validate` and fix all issues
3. Write comprehensive PR description
4. Ensure commits are clean and logical
5. Update documentation and CMakeLists.txt

**During review**:
- Respond to feedback constructively
- Make requested changes in new commits
- Mark conversations as resolved when addressed

**After approval**:
- Ensure CI passes
- Merge using appropriate strategy

### For Reviewers

Review for:
- **Correctness**: Does the code do what it claims?
- **Safety**: Memory leaks, race conditions, CUDA errors?
- **Performance**: Unnecessary copies, inefficient algorithms?
- **Maintainability**: Clear code, good naming, documentation?
- **Testing**: Adequate test coverage (70%+)?

**Review checklist**:
- [ ] Code compiles without warnings
- [ ] Tests pass and provide good coverage
- [ ] CUDA error checking is present
- [ ] Memory management is correct (RAII, no leaks)
- [ ] Documentation is clear and complete
- [ ] Performance is acceptable
- [ ] No breaking changes without justification
- [ ] CMake changes are correct

## 6. Technical Standards Quick Reference

For detailed requirements, see `.claude/constraints/cpp/` and run `/init`.

### C++ Version
- **Minimum**: C++17
- **Recommended**: C++20
- **Compiler**: GCC 9+, Clang 10+, MSVC 2019+

### CUDA Version
- **Minimum**: CUDA 11.0
- **Recommended**: CUDA 12.0+
- **Compute Capability**: 7.0+ (Volta and newer)

### Build System
- **CMake**: 3.20+ (minimum), 3.25+ (recommended)
- **Dependency Management**: Conan (primary), vcpkg (alternative)
- **Build Type**: Debug for development, Release for production

### Code Quality Tools
- **Formatter**: clang-format (LLVM style, modified)
- **Static Analysis**: clang-tidy, cppcheck
- **CUDA Analysis**: cuda-memcheck, compute-sanitizer
- **Test Framework**: Google Test (primary), Catch2 (alternative)
- **Coverage**: gcov/lcov (minimum 70%)

### Memory Safety (MANDATORY)
- **RAII**: All resources MUST use RAII
- **Smart Pointers**: Use `std::unique_ptr`, `std::shared_ptr`
- **Raw Pointers**: Only for non-owning references
- **CUDA Memory**: Wrap in RAII classes (never raw cudaMalloc/cudaFree)
- **Error Checking**: Check ALL CUDA API calls

### Testing
- **Minimum coverage**: 70%
- **Target coverage**: 80%+
- **Test file naming**: `test_<module>.cpp`
- **CUDA tests**: Separate test suite for GPU code
- **Memory checks**: Run valgrind (CPU) and cuda-memcheck (GPU)

### Documentation
- **Doxygen**: All public functions, classes, CUDA kernels
- **README.md**: Build instructions, dependencies, usage
- **Inline comments**: For complex algorithms only

## 7. CUDA-Specific Critical Rules

### Error Checking (MANDATORY)
```cpp
// ALWAYS check CUDA API calls
cudaError_t err = cudaMalloc(&ptr, size);
if (err != cudaSuccess) {
    // Handle error
}

// Or use error checking macro
CUDA_CHECK(cudaMalloc(&ptr, size));
```

### Memory Management (MANDATORY)
```cpp
// Good: RAII wrapper
class CudaMemory {
    void* ptr_;
public:
    CudaMemory(size_t size) {
        CUDA_CHECK(cudaMalloc(&ptr_, size));
    }
    ~CudaMemory() {
        cudaFree(ptr_);  // Automatic cleanup
    }
};

// Bad: Raw cudaMalloc/cudaFree
void* ptr;
cudaMalloc(&ptr, size);  // Memory leak risk
// ... use ptr ...
cudaFree(ptr);  // May not be called if exception thrown
```

See `.claude/constraints/cpp/cuda.md` for comprehensive CUDA requirements.

## 8. Versioning and Releases

Follow Semantic Versioning (semver.org):
```
v<MAJOR>.<MINOR>.<PATCH>
```

- **MAJOR**: Incompatible API changes
- **MINOR**: Backward-compatible functionality additions
- **PATCH**: Backward-compatible bug fixes

Update version in:
- `CMakeLists.txt` (project VERSION)
- `CHANGELOG.md`

## 9. Continuous Integration

All PRs MUST pass CI checks:
- Compilation on all supported platforms
- All tests pass
- Static analysis (clang-tidy, cppcheck)
- Code formatting check (clang-format)
- Coverage threshold met (70%+)

## 10. Forbidden Practices

**STRICTLY FORBIDDEN**:
- Committing code that doesn't compile
- Committing code with compiler warnings
- Ignoring CUDA error codes
- Using raw pointers for ownership
- Committing without running tests
- Force-pushing to master/main
- Committing secrets or credentials
- Using `using namespace std;` in headers
- Committing generated files (build artifacts)
- Skipping code review
- Merging your own PRs without approval

**STRICTLY FORBIDDEN: User or Author Attribution**
- **NEVER** include user or author information in commit messages
- **NEVER** include "Generated with", "Co-Authored-By", or any attribution lines
- **NEVER** include tool names, AI assistant names, or generation metadata
- Commit messages and PR descriptions must contain ONLY technical content
- This is a STRICT requirement with NO exceptions

**STRICTLY FORBIDDEN: Non-ASCII Characters**
- **NEVER** use Non-ASCII characters in any files, code, comments, or commit/PR messages
- **NEVER** use emoji, special symbols (checkmark, crossmark, arrows, etc.)
- **NEVER** use non-English characters (Chinese, Japanese, Arabic, Cyrillic, etc.)
- **NEVER** use accented characters (e, a, o, etc.)
- **NEVER** use typographic quotes (" " ' ') - use straight quotes (" ')
- **ONLY** ASCII characters (0x00-0x7F) are allowed
- Configure git hooks and CI/CD to reject Non-ASCII content

**STRICTLY REQUIRED: British English**
- **ALWAYS** use British English spelling in all text
- Examples: colour (not color), optimise (not optimize), initialise (not initialize)
- Applies to: code, comments, commit messages, PR descriptions, documentation
- Configure spell-checkers to use British English (en_GB)
- Document exceptions for third-party API names

## 11. Working With Roadmaps and AI Agents

If this repository uses `agent_roadmaps/`:
- Do NOT bypass an active roadmap
- Large or multi-session changes MUST follow the roadmap process
- PRs related to a roadmap SHOULD reference:
    - Roadmap name
    - Phase / task identifier
    - Link to roadmap documentation

AI agents MUST follow CLAUDE.md and roadmap constraints at all times.

## 12. Skills and Tools

This repository provides skills to streamline development:

- **`/init`** - Session initialisation (MANDATORY at session start)
- **`/roadmap`** - Multi-session workflow management
- **`/pre-commit`** - Code quality validation before commits
- **`/dependency`** - Dependency management

See `.claude/skills/*/README.md` for documentation.

## 13. Final Rule

> **If a contribution does not clearly improve the codebase,**
> **it should not be merged.**

When in doubt, ask for clarification before proceeding.

---

**Remember**: These guidelines exist to maintain code quality, safety, and maintainability. Following them ensures a healthy, sustainable codebase.

For detailed technical requirements, see:
- `.claude/constraints/cpp/` - C++/CUDA-specific constraints
- `.claude/constraints/common/` - Common constraints
- CLAUDE.md - Agent operating constraints and authority hierarchy
