# C++/CUDA Constraints Overview

> **This directory contains topic-specific constraint files for C++/CUDA development.**
> Each file focuses on a specific aspect of C++/CUDA development standards.

## Constraint Files

### 1. [testing.md](testing.md)
**Testing Requirements and Standards**
- Testing frameworks (Google Test, Catch2)
- Test organisation and structure
- Test naming conventions
- CUDA testing requirements
- Test coverage requirements (70% minimum, 80%+ target)
- Pre-commit test requirements

**Key Topics:**
- Unit testing, integration testing, CUDA testing
- Test patterns (Arrange-Act-Assert)
- CMake test integration
- CI/CD testing requirements

### 2. [formatting.md](formatting.md)
**Code Style and Formatting Standards**
- clang-format configuration and usage
- Naming conventions (variables, functions, classes)
- Code layout and indentation
- Header file organisation
- CUDA-specific formatting

**Key Topics:**
- British English spelling requirements
- ASCII-only character requirements
- Pointer/reference alignment
- Namespace formatting
- Pre-commit formatting checks

### 3. [cmake.md](cmake.md)
**CMake Build System Requirements**
- CMake version requirements (3.20+ minimum)
- Project configuration standards
- Modern CMake target-based approach
- CUDA support and configuration
- Dependency management (Conan primary, vcpkg alternative)

**Key Topics:**
- CMakeLists.txt structure
- Cross-compilation with toolchain files
- Installation and packaging
- Build configuration best practices
- Dependency documentation requirements

### 4. [cuda.md](cuda.md)
**CUDA-Specific Development Guidelines**
- CUDA toolkit requirements (11.0+ minimum)
- CUDA memory management and RAII wrappers
- CUDA error handling (mandatory checking)
- Kernel development best practices
- CUDA performance optimisation

**Key Topics:**
- Memory coalescing and shared memory usage
- Kernel launch configuration
- CUDA streams for concurrency
- Debugging with cuda-memcheck
- Profiling with nvprof/Nsight

### 5. [memory-safety.md](memory-safety.md)
**Memory Safety and Resource Management**
- RAII principle (mandatory for all resources)
- Smart pointers (unique_ptr, shared_ptr, weak_ptr)
- Ownership semantics and documentation
- Move semantics implementation
- CUDA memory safety with RAII wrappers

**Key Topics:**
- Exception safety
- Memory leak detection (Valgrind, cuda-memcheck)
- Common memory safety pitfalls
- Const correctness
- Pre-commit memory safety checks

### 6. [static-analysis.md](static-analysis.md)
**Static Analysis Requirements**
- clang-tidy configuration and usage
- cppcheck for additional analysis
- CUDA static analysis with cuda-memcheck
- Common issues detected by static analysis
- CI/CD integration

**Key Topics:**
- .clang-tidy configuration
- Check categories (bugprone, cppcoreguidelines, modernize, performance, readability)
- Suppressing false positives
- Pre-commit static analysis requirements
- Tool versions and compatibility

### 7. [documentation.md](documentation.md)
**Documentation Standards**
- Doxygen-style documentation requirements
- Function and class documentation
- CUDA kernel documentation
- Implementation comments
- README.md documentation

**Key Topics:**
- Doxygen tags reference
- API documentation generation
- British English and ASCII-only requirements
- Documentation best practices
- Pre-commit documentation requirements

### 8. [forbidden-practices.md](forbidden-practices.md)
**Absolutely Forbidden Practices**
- Protected branch commit prohibition
- Raw pointer ownership prohibition
- Manual new/delete prohibition
- C-style cast prohibition
- using namespace in headers prohibition
- CUDA error ignoring prohibition
- Compiler warning prohibition

**Key Topics:**
- Memory management forbidden practices
- Type safety forbidden practices
- CUDA-specific forbidden practices
- Concurrency forbidden practices
- Enforcement and exceptions

## Quick Reference

### Pre-Commit Checklist
Before every commit, ensure:
- [ ] All tests pass ([testing.md](testing.md))
- [ ] Code is formatted with clang-format ([formatting.md](formatting.md))
- [ ] CMake builds successfully ([cmake.md](cmake.md))
- [ ] CUDA error checking is present ([cuda.md](cuda.md))
- [ ] No memory leaks (Valgrind/cuda-memcheck) ([memory-safety.md](memory-safety.md))
- [ ] Static analysis passes (clang-tidy/cppcheck) ([static-analysis.md](static-analysis.md))
- [ ] Public APIs are documented ([documentation.md](documentation.md))

### Common Requirements Across All Files
- **British English spelling**: colour, behaviour, optimise, initialise
- **ASCII-only characters**: No emoji, special symbols, or non-English characters
- **RAII principle**: All resources managed automatically
- **Error checking**: All CUDA API calls must be checked
- **Documentation**: All public APIs must be documented

## File Organisation

```
.claude/constraints/cpp/
|-- README.md              # This file
|-- testing.md             # Testing requirements
|-- formatting.md          # Code style and formatting
|-- cmake.md               # CMake build system
|-- cuda.md                # CUDA-specific guidelines
|-- memory-safety.md       # Memory safety and RAII
|-- static-analysis.md     # Static analysis tools
|-- documentation.md       # Documentation standards
`-- forbidden-practices.md # Absolutely forbidden practices
```

## Usage

### For Developers
1. Read all constraint files before starting development
2. Refer to specific files when working on related topics
3. Use pre-commit checklist before committing
4. Keep constraints in mind during code review

### For AI Agents (Claude Code)
1. Load relevant constraint files based on task
2. Follow all requirements strictly
3. Reference specific sections when explaining decisions
4. Ensure all pre-commit requirements are met

## Relationship to Other Documents

These constraint files are extracted from:
- `/Users/ailven.liu/proj/Personal/repo_template/CLAUDE.md` - Agent operating constraints
- `/Users/ailven.liu/proj/Personal/repo_template/CONTRIBUTING.md` - Contribution guidelines

**Authority hierarchy:**
1. `agent_roadmaps/<active>/INVARIANTS.md` (if active roadmap exists)
2. `agent_roadmaps/README.md`
3. `CLAUDE.md`
4. `CONTRIBUTING.md`
5. These constraint files (topic-specific details)
6. Repository source code and comments

## Maintenance

### Updating Constraints
When updating these files:
1. Ensure consistency across all constraint files
2. Update this README.md if adding/removing files
3. Keep in sync with CLAUDE.md and CONTRIBUTING.md
4. Document changes in commit messages

### Adding New Constraints
To add a new constraint file:
1. Create the file in this directory
2. Follow the same format and style
3. Update this README.md with the new file
4. Update the pre-commit checklist if needed

## Support

For questions or clarifications:
1. Check the specific constraint file
2. Refer to CLAUDE.md or CONTRIBUTING.md
3. Review source code examples in the repository
4. Ask the team for guidance

---

**Remember**: These constraints exist to maintain code quality, safety, and maintainability. Following them ensures a healthy, sustainable codebase.
