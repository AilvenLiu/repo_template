# Development & Collaboration Guidelines for C++/CUDA Projects

> **This document defines mandatory contribution standards for C++/CUDA repositories.**
> All contributors (human or AI) must follow these rules.

## 1. General Principles

- Prefer **clarity over cleverness**
- Prefer **explicit decisions over implicit assumptions**
- Prefer **small, reviewable changes over large, opaque ones**
- Never trade correctness or safety for speed
- Follow modern C++ best practices (C++17+)
- Prioritize memory safety and RAII principles

If unsure, ask before acting.

## 2. Branching Model

### 2.1 Main Branches

The repository follows a **trunk-based development model** with the following conventions:

- **master** (or **main**)
    - Always stable
    - Always releasable
    - Protected branch (no direct commits)
    - All tests must pass
    - No compiler warnings

Optional long-lived branches (if applicable):
- `release/*` — release stabilization
- `hotfix/*` — urgent fixes on released versions

### 2.2 Feature / Work Branches

All work MUST be done on a dedicated branch.

Naming convention:
```
<type>/<short-description>
```

Allowed types:
- `feat/` — new features
- `fix/` — bug fixes
- `refactor/` — structural changes without behavior change
- `perf/` — performance improvements
- `chore/` — tooling, infra, non-code changes
- `docs/` — documentation only

Examples:
```
feat/add-cuda-kernel-optimization
refactor/decouple-memory-manager
fix/memory-leak-in-buffer
perf/optimize-matrix-multiplication
```

Branches MUST be:
- Short-lived (ideally < 1 week)
- Scoped to a single logical change
- Deleted after merge

## 3. Commit Message Convention

### 3.1 Format

All commits MUST follow this format:
```
<type>(optional-scope): <short summary>

[optional body]
```

Types:
- `feat` — new feature
- `fix` — bug fix
- `refactor` — code restructuring without behavior change
- `perf` — performance improvement
- `docs` — documentation changes
- `test` — adding or updating tests
- `chore` — build system, dependencies, tooling
- `style` — formatting, missing semicolons (no code change)

Examples:
```
feat(cuda): add optimized matrix multiplication kernel
fix(memory): resolve memory leak in Buffer destructor
refactor(core): split validation logic into separate class
perf(kernel): reduce shared memory bank conflicts
docs(api): add Doxygen comments for public interface
test(cuda): add unit tests for device memory allocation
chore(cmake): update CUDA architecture targets
```

### 3.2 Rules

- **Summary line**:
    - Less than 72 characters
    - Imperative mood ("add", not "added" or "adds")
    - No period at the end
    - Lowercase after type prefix
    - **ASCII-only characters** (no emoji, special symbols, or non-English characters)
    - **British English spelling** (e.g., "optimise" not "optimize", "colour" not "color")
- **Body** (if present):
    - Explains **why**, not just what
    - Wrap at 72 characters
    - Separate from summary with blank line
    - **ASCII-only characters**
    - **British English spelling**
- **One logical change per commit**
- **Atomic commits**: Each commit should compile and pass tests

### 3.3 Commit Message Examples

Good:
```
feat(cuda): implement tiled matrix multiplication

Add a CUDA kernel that uses shared memory tiling to improve
memory access patterns. This reduces global memory transactions
by ~60% for large matrices (>1024x1024).

Benchmark results show 3x speedup over naive implementation.
```

```
fix(memory): prevent double-free in CudaBuffer

The destructor was calling cudaFree on already-freed memory
when move constructor was used. Added nullptr check and
proper move semantics.

Fixes issue #123
```

Bad:
```
update stuff
fix bug
wip
changes
```

## 4. Pull Request (PR) Guidelines

### 4.1 When to Open a PR

Open a PR when:
- A logical unit of work is complete
- All tests are passing
- Code compiles without warnings
- Static analysis passes (clang-tidy, cppcheck)
- The change is ready for review

Draft PRs are encouraged for early feedback on architecture or approach.

### 4.2 PR Title

PR titles MUST follow the same convention as commit messages:
```
<type>(optional-scope): <short description>
```

Examples:
```
feat(cuda): add optimized convolution kernels
refactor(memory): implement RAII wrappers for CUDA resources
fix(build): resolve CMake CUDA architecture detection
```

### 4.3 PR Description (Required Sections)

Each PR MUST include:

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
- Memory transfer optimizations
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
- Related ADRs or roadmaps
```

### 4.4 PR Size and Scope Control

- A PR SHOULD address one concern
- **Avoid mixing**:
    - Refactors + new features
    - Behavior changes + formatting
    - Multiple unrelated bug fixes
- **Size guidelines**:
    - Small: < 200 lines changed (preferred)
    - Medium: 200-500 lines changed
    - Large: > 500 lines (requires justification)
- Large changes should be split into multiple PRs when possible
- Use stacked PRs for dependent changes

### 4.5 Code Review Checklist

Before requesting review, ensure:
- [ ] Code compiles without warnings (`-Wall -Wextra -Wpedantic`)
- [ ] All tests pass
- [ ] clang-tidy passes with project configuration
- [ ] cppcheck shows no issues
- [ ] Code is formatted (clang-format)
- [ ] CUDA error checking is present for all API calls
- [ ] Memory leaks checked (valgrind, cuda-memcheck)
- [ ] Documentation updated (Doxygen comments)
- [ ] CMakeLists.txt updated if needed
- [ ] Dependencies documented in README.md

## 5. C++/CUDA Specific Commit Standards

### 5.1 Code Compilation

**MANDATORY**: Every commit MUST:
- Compile successfully with the project's supported compilers
- Produce no warnings with strict warning flags enabled
- Pass all existing tests

```bash
# Verify before committing
mkdir -p build && cd build
cmake .. -DCMAKE_BUILD_TYPE=Debug \
         -DCMAKE_CXX_FLAGS="-Wall -Wextra -Wpedantic -Werror"
cmake --build .
ctest --output-on-failure
```

### 5.2 Static Analysis

**MANDATORY**: Run static analysis before committing:

```bash
# clang-tidy
clang-tidy src/**/*.cpp src/**/*.cu -p build/

# cppcheck
cppcheck --enable=all --suppress=missingIncludeSystem src/

# CUDA-specific checks
cuda-memcheck ./build/tests/test_cuda_kernels
```

### 5.3 Code Formatting

**MANDATORY**: Format code before committing:

```bash
# clang-format (use project .clang-format config)
clang-format -i src/**/*.cpp src/**/*.hpp src/**/*.cu

# Or format all changed files
git diff --name-only --cached | grep -E '\.(cpp|hpp|cu|cuh)$' | xargs clang-format -i
```

Example `.clang-format`:
```yaml
BasedOnStyle: Google
IndentWidth: 4
ColumnLimit: 100
PointerAlignment: Left
DerivePointerAlignment: false
AlignConsecutiveAssignments: true
AlignConsecutiveDeclarations: true
AllowShortFunctionsOnASingleLine: Empty
AllowShortIfStatementsOnASingleLine: Never
```

### 5.4 Memory Safety

**MANDATORY** checks before committing:

```bash
# Valgrind for C++ memory issues
valgrind --leak-check=full --show-leak-kinds=all ./build/tests/test_suite

# CUDA memory checker
cuda-memcheck --leak-check full ./build/tests/test_cuda_suite

# Address sanitizer (compile with -fsanitize=address)
cmake .. -DCMAKE_CXX_FLAGS="-fsanitize=address -g"
./build/tests/test_suite
```

### 5.5 CUDA-Specific Requirements

When committing CUDA code:
- **Error Checking**: Every CUDA API call MUST be checked
- **Kernel Launches**: Check with `cudaGetLastError()` and `cudaDeviceSynchronize()`
- **Documentation**: Document thread/block dimensions and shared memory usage
- **Testing**: Test with various input sizes and edge cases
- **Profiling**: Profile with `nvprof` or Nsight for performance-critical changes

Example commit checklist for CUDA:
```bash
# Compile with verbose ptxas output
nvcc -Xptxas=-v kernel.cu

# Check for register usage and occupancy
# Profile kernel
nvprof ./build/cuda_app

# Memory check
cuda-memcheck ./build/cuda_app
```

## 6. Testing and Quality Assurance

### 6.1 Test Requirements

**MANDATORY**:
- All new features MUST include unit tests
- Bug fixes MUST include regression tests
- CUDA kernels MUST have correctness tests
- Performance-critical code SHOULD have benchmarks

### 6.2 Test Organization

```
tests/
├── unit/
│   ├── test_module1.cpp
│   ├── test_module2.cpp
│   └── CMakeLists.txt
├── integration/
│   ├── test_workflow.cpp
│   └── CMakeLists.txt
├── cuda/
│   ├── test_kernels.cu
│   ├── test_memory.cu
│   └── CMakeLists.txt
└── benchmarks/
    ├── benchmark_matrix_mul.cpp
    └── CMakeLists.txt
```

### 6.3 Test Framework Setup

Using Google Test:
```cpp
// test_module.cpp
#include <gtest/gtest.h>
#include "module.hpp"

class ModuleTest : public ::testing::Test {
protected:
    void SetUp() override {
        // Setup code
    }

    void TearDown() override {
        // Cleanup code
    }
};

TEST_F(ModuleTest, FunctionName_Condition_ExpectedBehavior) {
    // Arrange
    int input = 42;

    // Act
    int result = function_under_test(input);

    // Assert
    EXPECT_EQ(result, 84);
}

TEST_F(ModuleTest, FunctionName_InvalidInput_ThrowsException) {
    EXPECT_THROW(function_under_test(-1), std::invalid_argument);
}
```

### 6.4 CUDA Testing

```cpp
// test_cuda_kernel.cu
#include <gtest/gtest.h>
#include <cuda_runtime.h>
#include "kernels.cuh"

class CudaKernelTest : public ::testing::Test {
protected:
    void SetUp() override {
        cudaMalloc(&d_input, size * sizeof(float));
        cudaMalloc(&d_output, size * sizeof(float));
    }

    void TearDown() override {
        cudaFree(d_input);
        cudaFree(d_output);
    }

    float* d_input;
    float* d_output;
    size_t size = 1024;
};

TEST_F(CudaKernelTest, VectorAdd_ValidInput_CorrectOutput) {
    // Arrange
    std::vector<float> h_input(size, 1.0f);
    std::vector<float> h_output(size);

    cudaMemcpy(d_input, h_input.data(), size * sizeof(float),
               cudaMemcpyHostToDevice);

    // Act
    vectorAddKernel<<<(size + 255) / 256, 256>>>(d_input, d_output, size);
    cudaDeviceSynchronize();

    // Assert
    ASSERT_EQ(cudaGetLastError(), cudaSuccess);
    cudaMemcpy(h_output.data(), d_output, size * sizeof(float),
               cudaMemcpyDeviceToHost);

    for (size_t i = 0; i < size; ++i) {
        EXPECT_FLOAT_EQ(h_output[i], 2.0f);
    }
}
```

### 6.5 Coverage Requirements

- **Minimum**: 70% line coverage
- **Target**: 80%+ line coverage
- **Critical paths**: 90%+ coverage

```bash
# Generate coverage report
cmake .. -DCMAKE_BUILD_TYPE=Debug -DCMAKE_CXX_FLAGS="--coverage"
cmake --build .
ctest
lcov --capture --directory . --output-file coverage.info
lcov --remove coverage.info '/usr/*' '*/tests/*' --output-file coverage.info
genhtml coverage.info --output-directory coverage_report
```

## 7. Documentation Standards

### 7.1 Code Documentation

**MANDATORY**: All public APIs MUST have Doxygen documentation:

```cpp
/**
 * @brief Computes the matrix product C = A * B using CUDA
 *
 * This function performs matrix multiplication on the GPU using
 * a tiled algorithm with shared memory optimization.
 *
 * @param d_A Device pointer to matrix A (M x K)
 * @param d_B Device pointer to matrix B (K x N)
 * @param d_C Device pointer to output matrix C (M x N)
 * @param M Number of rows in A
 * @param K Number of columns in A / rows in B
 * @param N Number of columns in B
 *
 * @pre d_A, d_B, d_C must point to valid device memory
 * @pre M, K, N must be positive
 * @post d_C contains the matrix product A * B
 *
 * @throws std::runtime_error if CUDA operations fail
 *
 * @note This function synchronizes the device
 * @note Time complexity: O(M * N * K)
 * @note Space complexity: O(1) additional device memory
 *
 * @see matrixMulKernel for kernel implementation details
 *
 * @par Example:
 * @code
 * float *d_A, *d_B, *d_C;
 * cudaMalloc(&d_A, M * K * sizeof(float));
 * cudaMalloc(&d_B, K * N * sizeof(float));
 * cudaMalloc(&d_C, M * N * sizeof(float));
 *
 * matrixMultiply(d_A, d_B, d_C, M, K, N);
 * @endcode
 */
void matrixMultiply(const float* d_A, const float* d_B, float* d_C,
                    int M, int K, int N);
```

### 7.2 CUDA Kernel Documentation

```cpp
/**
 * @brief Matrix multiplication kernel using shared memory tiling
 *
 * @param A Input matrix A in row-major order
 * @param B Input matrix B in row-major order
 * @param C Output matrix C in row-major order
 * @param M Number of rows in A
 * @param K Number of columns in A / rows in B
 * @param N Number of columns in B
 *
 * @note Launch configuration:
 *       - Block size: (TILE_SIZE, TILE_SIZE) = (16, 16)
 *       - Grid size: ((N + TILE_SIZE - 1) / TILE_SIZE,
 *                     (M + TILE_SIZE - 1) / TILE_SIZE)
 *
 * @note Shared memory usage: 2 * TILE_SIZE * TILE_SIZE * sizeof(float)
 *
 * @note Memory access pattern:
 *       - Coalesced reads from global memory
 *       - Shared memory used to reduce global memory accesses
 *       - Each thread computes one element of C
 *
 * @note Performance characteristics:
 *       - Occupancy: ~75% on Volta (sm_70)
 *       - Register usage: 32 registers per thread
 *       - Achieves ~80% of peak FLOPS for large matrices
 */
__global__ void matrixMulKernel(const float* A, const float* B, float* C,
                                 int M, int K, int N);
```

### 7.3 README.md Requirements

Every project MUST have a comprehensive README.md:

```markdown
# Project Name

Brief description of the project.

## Requirements

### Build Requirements
- CMake 3.18 or later
- C++17 compatible compiler:
  - GCC 9.0+
  - Clang 10.0+
  - MSVC 2019+
- CUDA Toolkit 11.0+ (for CUDA features)

### Runtime Requirements
- CUDA-capable GPU with compute capability 7.0+ (Volta or later)
- CUDA Runtime 11.0+

## Dependencies

- **Eigen3** (3.4.0+): Linear algebra operations
- **Google Test** (1.12.0+): Unit testing framework
- **spdlog** (1.10.0+): Logging library

## Building

```bash
# Clone repository
git clone https://github.com/user/project.git
cd project

# Create build directory
mkdir build && cd build

# Configure
cmake .. -DCMAKE_BUILD_TYPE=Release \
         -DCMAKE_CUDA_ARCHITECTURES="70;75;80;86"

# Build
cmake --build . -j$(nproc)

# Run tests
ctest --output-on-failure
```

## Usage

```cpp
#include "project/api.hpp"

int main() {
    // Example usage
    auto result = compute(input);
    return 0;
}
```

## Performance

Benchmark results on NVIDIA RTX 3090:
- Matrix multiplication (4096x4096): 2.3 ms
- Convolution (1024x1024, 3x3 kernel): 0.8 ms

## License

MIT License - see LICENSE file for details.
```

## 8. Build System Standards

### 8.1 CMakeLists.txt Structure

```cmake
cmake_minimum_required(VERSION 3.18)
project(ProjectName VERSION 1.0.0 LANGUAGES CXX CUDA)

# C++ standard
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

# CUDA standard
set(CMAKE_CUDA_STANDARD 17)
set(CMAKE_CUDA_STANDARD_REQUIRED ON)
set(CMAKE_CUDA_ARCHITECTURES 70 75 80 86)

# Compiler warnings
if(MSVC)
    add_compile_options(/W4 /WX)
else()
    add_compile_options(-Wall -Wextra -Wpedantic -Werror)
endif()

# Build type
if(NOT CMAKE_BUILD_TYPE)
    set(CMAKE_BUILD_TYPE Release)
endif()

# Dependencies
find_package(CUDAToolkit REQUIRED)
find_package(Eigen3 REQUIRED)

# Library target
add_library(mylib
    src/module1.cpp
    src/module2.cpp
    cuda/kernel1.cu
    cuda/kernel2.cu
)

target_include_directories(mylib PUBLIC
    $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/include>
    $<INSTALL_INTERFACE:include>
)

target_link_libraries(mylib PUBLIC
    CUDA::cudart
    Eigen3::Eigen
)

# Executable target
add_executable(myapp src/main.cpp)
target_link_libraries(myapp PRIVATE mylib)

# Tests
enable_testing()
add_subdirectory(tests)

# Installation
install(TARGETS mylib myapp
    LIBRARY DESTINATION lib
    ARCHIVE DESTINATION lib
    RUNTIME DESTINATION bin
)
install(DIRECTORY include/ DESTINATION include)
```

### 8.2 Dependency Management

When adding a dependency:
1. Update CMakeLists.txt with `find_package()` or `FetchContent`
2. Document in README.md with version requirements
3. Update CI/CD configuration
4. Commit all changes together

## 9. Code Review Process

### 9.1 For Authors

**Before requesting review**:
1. Self-review your changes
2. Run all checks (compile, test, static analysis)
3. Write comprehensive PR description
4. Ensure commits are clean and logical
5. Rebase on latest master if needed

**During review**:
- Respond to feedback constructively
- Make requested changes in new commits (don't force-push during review)
- Mark conversations as resolved when addressed
- Request re-review when ready

**After approval**:
- Squash fixup commits if needed
- Ensure CI passes
- Merge using appropriate strategy (squash for small PRs, merge for large)

### 9.2 For Reviewers

Review for:
- **Correctness**: Does the code do what it claims?
- **Safety**: Memory leaks, race conditions, CUDA errors?
- **Performance**: Unnecessary copies, inefficient algorithms?
- **Maintainability**: Clear code, good naming, documentation?
- **Testing**: Adequate test coverage?
- **Style**: Follows project conventions?

**Review checklist**:
- [ ] Code compiles without warnings
- [ ] Tests pass and provide good coverage
- [ ] CUDA error checking is present
- [ ] Memory management is correct (RAII, no leaks)
- [ ] Documentation is clear and complete
- [ ] Performance is acceptable (profile if needed)
- [ ] No breaking changes without justification
- [ ] CMake changes are correct

**Providing feedback**:
- Be specific and constructive
- Explain the "why" behind suggestions
- Distinguish between blocking issues and suggestions
- Approve when confident the change is safe

## 10. Versioning and Releases

### 10.1 Semantic Versioning

Follow Semantic Versioning (semver.org):
```
v<MAJOR>.<MINOR>.<PATCH>
```

- **MAJOR**: Incompatible API changes
- **MINOR**: Backward-compatible functionality additions
- **PATCH**: Backward-compatible bug fixes

Examples:
```
v1.0.0 - Initial release
v1.1.0 - Add new feature
v1.1.1 - Fix bug
v2.0.0 - Breaking API change
```

### 10.2 Release Process

1. Update version in CMakeLists.txt
2. Update CHANGELOG.md
3. Create release branch: `release/v1.2.0`
4. Run full test suite
5. Create tag: `git tag -a v1.2.0 -m "Release v1.2.0"`
6. Push tag: `git push origin v1.2.0`
7. Create GitHub release with notes

## 11. Continuous Integration

### 11.1 CI Requirements

All PRs MUST pass CI checks:
- Compilation on all supported platforms
- All tests pass
- Static analysis (clang-tidy, cppcheck)
- Code formatting check (clang-format)
- Coverage threshold met (if configured)

### 11.2 Example GitHub Actions Workflow

```yaml
name: CI

on: [push, pull_request]

jobs:
  build:
    runs-on: ubuntu-latest
    container: nvidia/cuda:12.0.0-devel-ubuntu22.04

    steps:
    - uses: actions/checkout@v3

    - name: Install dependencies
      run: |
        apt-get update
        apt-get install -y cmake g++ clang-tidy cppcheck

    - name: Configure
      run: |
        cmake -B build -DCMAKE_BUILD_TYPE=Release \
              -DCMAKE_CXX_FLAGS="-Wall -Wextra -Werror"

    - name: Build
      run: cmake --build build -j$(nproc)

    - name: Test
      run: cd build && ctest --output-on-failure

    - name: Static Analysis
      run: |
        clang-tidy src/**/*.cpp -p build/
        cppcheck --enable=all src/
```

## 12. Forbidden Practices

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

## 13. Working With Roadmaps and AI Agents

If this repository uses `agents_roadmaps/`:
- Do NOT bypass an active roadmap
- Large or multi-session changes MUST follow the roadmap process
- PRs related to a roadmap SHOULD reference:
    - Roadmap name
    - Phase / task identifier
    - Link to roadmap documentation

AI agents MUST follow CLAUDE.md and roadmap constraints at all times.

## 14. Final Rule

> **If a contribution does not clearly improve the codebase,**
> **it should not be merged.**

When in doubt, ask for clarification before proceeding.

---

**Remember**: These guidelines exist to maintain code quality, safety, and maintainability. Following them ensures a healthy, sustainable codebase.
