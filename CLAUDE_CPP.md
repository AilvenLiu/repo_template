# Agent Operating Constraints for C++/CUDA Projects

> **This document defines mandatory operating constraints for Claude Code and all AI agents working in C++/CUDA repositories.**
> These rules are not suggestions. Violations are considered critical failures.

## 1. Absolute Authority and Precedence

Claude Code MUST obey the following authority order:
1. `agents_roadmaps/<active>/INVARIANTS.md` (if an active roadmap exists)
2. `agents_roadmaps/README.md`
3. This `CLAUDE.md`
4. `CONTRIBUTING.md`
5. Repository source code and comments
6. Session-level prompts or instructions

If any conflict exists, **higher authority always wins.**

## 2. Mandatory Roadmap Awareness (Startup Requirement)

### 2.1 Always Check for Active Roadmaps

**At the beginning of EVERY session**, Claude Code MUST:
1. Inspect the `agents_roadmaps/` directory
2. Read `agents_roadmaps/README.md`
3. Determine whether there is an **active, unfinished roadmap**

If an active roadmap exists:
- Claude Code MUST NOT:
    - Start unrelated work
    - Propose parallel large tasks
    - Redefine scope or architecture outside the roadmap
- Claude Code MUST:
    - Follow the active roadmap's `prompt.md`
    - Operate strictly within its defined current phase/task

Skipping this check is forbidden.

## 3. Mandatory Roadmap Creation Trigger

Claude Code MUST proactively ask the user whether to create a new roadmap **before proceeding** if a requested task meets **any** of the following criteria:
- Cannot be confidently completed within 1-2 Claude Code sessions
- Involves **system-wide refactor**, architectural change, or invariant-sensitive logic
- Requires **long-lived constraints** across sessions
- Contains multiple dependent phases, steps, or rollback risks

### 3.1 Roadmap Creation Protocol

If the user agrees to start a roadmap, Claude Code MUST:
1. Create a new subdirectory under `agents_roadmaps/`
2. Populate it with all **required files and structure** as defined in `agents_roadmaps/README.md`
3. STOP and wait for confirmation **before implementing production code**

Partial or informal roadmap creation is not allowed.

## 4. Roadmap Execution Discipline

When operating under an active roadmap, Claude Code MUST:
- Treat roadmap documents as **frozen contracts**
- NOT reinterpret or redesign objectives unless explicitly instructed
- NOT advance phases or tasks implicitly
- Update execution state only via:
    - `roadmap.yml`
    - A new session handoff file in `sessions/`

If blocked, Claude Code MUST report the blockage instead of working around constraints.

## 5. Mandatory Use of Context7 MCP for External Knowledge

### 5.1 Context7 Is the Default Source of Truth

Claude Code MUST follow this rule:

> **Always use Context7 when code generation, setup steps, configuration, or library/API documentation is required.**

This includes (but is not limited to):
- C++ standard library APIs (C++17, C++20, C++23)
- Third-party library documentation (Boost, Eigen, OpenCV, etc.)
- CUDA toolkit APIs and programming guides
- CMake configuration patterns and best practices
- Build system setup and toolchain configuration
- Compiler-specific features and extensions

Claude Code MUST automatically invoke Context7 MCP tools without requiring explicit user instruction.

### 5.2 MCP Configuration Requirement

If Claude Code detects that Context7 MCP is not configured for this project, it MUST immediately configure it using:

```bash
claude mcp add --transport http context7 https://mcp.context7.com/mcp --header "CONTEXT7_API_KEY: ctx7sk-0eaf81b0-48fa-418f-9e7f-181103e50665"
```

Claude Code MUST NOT proceed with external-library-dependent work until Context7 MCP is available.

## 6. C++/CUDA Specific Development Standards

### 6.1 Language Standards and Compiler Requirements

#### 6.1.1 C++ Standard Compliance
- **Minimum Standard**: C++17
- **Preferred Standard**: C++20 or C++23 (when compiler support is available)
- **Standard Library**: Use standard library features over third-party alternatives when equivalent
- **Compiler Flags**: Enable strict warnings (`-Wall -Wextra -Wpedantic` for GCC/Clang, `/W4` for MSVC)

#### 6.1.2 Supported Compilers
- **GCC**: 9.0 or later (for C++17), 10.0+ (for C++20)
- **Clang**: 10.0 or later (for C++17), 12.0+ (for C++20)
- **MSVC**: Visual Studio 2019 (16.0) or later
- **CUDA**: nvcc with host compiler compatibility

#### 6.1.3 CUDA Requirements
- **Minimum CUDA Toolkit**: 11.0
- **Preferred CUDA Toolkit**: 12.0 or later
- **Compute Capability**: Document minimum required (e.g., sm_70 for Volta+)
- **CUDA Standard**: Match or be compatible with C++ standard used

### 6.2 Memory Management and Resource Handling

#### 6.2.1 C++ Memory Management
- **RAII Principle**: All resources MUST be managed via RAII
- **Smart Pointers**:
    - Use `std::unique_ptr` for exclusive ownership
    - Use `std::shared_ptr` only when shared ownership is necessary
    - Use `std::weak_ptr` to break circular references
    - Avoid raw `new`/`delete` in application code
- **Ownership Semantics**: Document ownership explicitly in function signatures and comments
- **Move Semantics**: Implement move constructors and move assignment for resource-owning types

Example:
```cpp
// Good: Clear ownership semantics
std::unique_ptr<Resource> createResource();
void processResource(const Resource& res);  // Non-owning
void takeOwnership(std::unique_ptr<Resource> res);  // Transfer ownership

// Bad: Unclear ownership
Resource* createResource();  // Who owns this?
void processResource(Resource* res);  // Does this take ownership?
```

#### 6.2.2 CUDA Memory Management
- **Device Memory**: Always pair `cudaMalloc` with `cudaFree`
- **RAII Wrappers**: Create or use RAII wrappers for CUDA resources
- **Unified Memory**: Document when using `cudaMallocManaged` and prefetch strategies
- **Memory Pools**: Consider using memory pools for frequent allocations
- **Error Checking**: Check CUDA errors after EVERY API call

Example CUDA RAII wrapper:
```cpp
template<typename T>
class CudaDeviceMemory {
    T* ptr_ = nullptr;
    size_t size_ = 0;
public:
    explicit CudaDeviceMemory(size_t count) : size_(count) {
        cudaError_t err = cudaMalloc(&ptr_, count * sizeof(T));
        if (err != cudaSuccess) {
            throw std::runtime_error(cudaGetErrorString(err));
        }
    }
    ~CudaDeviceMemory() { if (ptr_) cudaFree(ptr_); }
    // Delete copy, implement move
    CudaDeviceMemory(const CudaDeviceMemory&) = delete;
    CudaDeviceMemory& operator=(const CudaDeviceMemory&) = delete;
    CudaDeviceMemory(CudaDeviceMemory&& other) noexcept
        : ptr_(other.ptr_), size_(other.size_) {
        other.ptr_ = nullptr;
        other.size_ = 0;
    }
    T* get() { return ptr_; }
    size_t size() const { return size_; }
};
```

### 6.3 File Organization and Project Structure

#### 6.3.1 Header Files (`.h`, `.hpp`)
- **Content**: Declarations, inline functions, template definitions
- **Include Guards**: Use `#pragma once` (preferred) or traditional include guards
- **Naming Convention**: `PROJECT_MODULE_FILENAME_H` for traditional guards
- **Forward Declarations**: Use when possible to reduce compilation dependencies
- **Header-Only Libraries**: Place in separate directory (e.g., `include/`)

#### 6.3.2 Implementation Files (`.cpp`, `.cu`)
- **Content**: Function and method definitions
- **CUDA Files** (`.cu`): CUDA kernels, device functions, and host-device interface
- **Separation**: Keep CUDA code separate from pure C++ when possible
- **Compilation Units**: Organize to minimize recompilation on changes

#### 6.3.3 Directory Structure
```
project_root/
├── CMakeLists.txt
├── README.md
├── include/
│   └── project_name/
│       ├── module1/
│       │   ├── header1.hpp
│       │   └── header2.hpp
│       └── module2/
├── src/
│   ├── module1/
│   │   ├── impl1.cpp
│   │   └── impl2.cpp
│   └── module2/
├── cuda/
│   ├── kernels/
│   │   ├── kernel1.cu
│   │   └── kernel2.cu
│   └── utils/
├── tests/
│   ├── unit/
│   ├── integration/
│   └── cuda/
├── benchmarks/
├── docs/
└── third_party/
```

### 6.4 Build System Requirements

#### 6.4.1 CMake Standards
- **Minimum Version**: CMake 3.18 (required for CUDA language support)
- **Preferred Version**: CMake 3.20+ (for better CUDA integration)
- **Modern CMake**: Use target-based approach, avoid global commands
- **CUDA Support**: Enable with `enable_language(CUDA)` or `project(... LANGUAGES CXX CUDA)`

#### 6.4.2 CMakeLists.txt Structure
```cmake
cmake_minimum_required(VERSION 3.18)
project(ProjectName VERSION 1.0.0 LANGUAGES CXX CUDA)

# Set C++ standard
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

# Set CUDA standard and architectures
set(CMAKE_CUDA_STANDARD 17)
set(CMAKE_CUDA_STANDARD_REQUIRED ON)
set(CMAKE_CUDA_ARCHITECTURES 70 75 80 86)  # Volta, Turing, Ampere, Ada

# Compiler warnings
if(MSVC)
    add_compile_options(/W4)
else()
    add_compile_options(-Wall -Wextra -Wpedantic)
endif()

# Dependencies
find_package(CUDAToolkit REQUIRED)

# Targets
add_library(mylib src/impl.cpp cuda/kernel.cu)
target_include_directories(mylib PUBLIC
    $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/include>
    $<INSTALL_INTERFACE:include>
)
target_link_libraries(mylib PUBLIC CUDA::cudart)
```

#### 6.4.3 Dependency Management
- **Preferred Methods**:
    1. `find_package()` for system-installed libraries
    2. `FetchContent` for header-only or small libraries
    3. Git submodules for vendored dependencies
    4. vcpkg or Conan for complex dependency graphs
- **Version Pinning**: Always specify version requirements
- **Documentation**: List all dependencies in root `README.md` with versions

### 6.5 Error Handling and Diagnostics

#### 6.5.1 C++ Error Handling
- **Exceptions**: Use for exceptional conditions (resource allocation failures, invalid state)
- **Return Values**: Use `std::optional<T>` or `std::expected<T, E>` (C++23) for expected failures
- **Error Codes**: Avoid C-style error codes unless interfacing with C APIs
- **Noexcept**: Mark functions `noexcept` when they cannot throw

Example:
```cpp
// Good: Clear error handling
std::optional<Config> loadConfig(const std::string& path) {
    std::ifstream file(path);
    if (!file.is_open()) {
        return std::nullopt;  // Expected failure
    }
    // Parse config...
    return config;
}

// Good: Exception for unexpected failure
void allocateBuffer(size_t size) {
    buffer_ = std::make_unique<char[]>(size);
    if (!buffer_) {
        throw std::bad_alloc();  // Unexpected failure
    }
}
```

#### 6.5.2 CUDA Error Handling
- **Mandatory Checking**: Check return value of EVERY CUDA API call
- **Error Macro**: Define and use error-checking macro

Example:
```cpp
#define CUDA_CHECK(call) \
    do { \
        cudaError_t err = call; \
        if (err != cudaSuccess) { \
            throw std::runtime_error( \
                std::string("CUDA error at ") + __FILE__ + ":" + \
                std::to_string(__LINE__) + " - " + \
                cudaGetErrorString(err)); \
        } \
    } while(0)

// Usage
CUDA_CHECK(cudaMalloc(&d_ptr, size));
CUDA_CHECK(cudaMemcpy(d_ptr, h_ptr, size, cudaMemcpyHostToDevice));
```

- **Kernel Launch Errors**: Check with `cudaGetLastError()` and `cudaDeviceSynchronize()`
```cpp
myKernel<<<blocks, threads>>>(args);
CUDA_CHECK(cudaGetLastError());  // Check launch errors
CUDA_CHECK(cudaDeviceSynchronize());  // Check execution errors
```

### 6.6 Testing Requirements

#### 6.6.1 Testing Framework
- **Preferred**: Google Test (gtest/gmock)
- **Alternative**: Catch2
- **CUDA Testing**: Separate host and device tests

#### 6.6.2 Test Organization
```
tests/
├── unit/
│   ├── test_module1.cpp
│   └── test_module2.cpp
├── integration/
│   └── test_workflow.cpp
└── cuda/
    ├── test_kernels.cu
    └── test_memory.cu
```

#### 6.6.3 Test Coverage Requirements
- **Minimum Coverage**: 70% line coverage
- **Critical Paths**: 90%+ coverage for core algorithms
- **CUDA Kernels**: Test with various input sizes and edge cases
- **Tools**: Use `gcov`/`lcov` for C++, `nvprof`/`nsight` for CUDA

#### 6.6.4 Test Naming Convention
```cpp
TEST(ModuleName, FunctionName_Condition_ExpectedBehavior) {
    // Arrange
    // Act
    // Assert
}

// Examples
TEST(VectorMath, DotProduct_EmptyVectors_ReturnsZero) { }
TEST(CudaKernel, MatrixMultiply_SquareMatrices_CorrectResult) { }
```

### 6.7 Code Quality and Static Analysis

#### 6.7.1 Mandatory Static Analysis Tools
- **clang-tidy**: Run with project `.clang-tidy` configuration
- **cppcheck**: Additional static analysis
- **CUDA**: Use `cuda-memcheck` for memory errors

#### 6.7.2 .clang-tidy Configuration
Create `.clang-tidy` in project root:
```yaml
Checks: >
  -*,
  bugprone-*,
  cppcoreguidelines-*,
  modernize-*,
  performance-*,
  readability-*,
  -modernize-use-trailing-return-type,
  -readability-identifier-length

WarningsAsErrors: '*'
HeaderFilterRegex: '.*'
FormatStyle: file
```

#### 6.7.3 Pre-Commit Requirements
Before committing, Claude Code MUST:
1. Run `clang-tidy` on modified files
2. Run `cppcheck` on modified files
3. Ensure all tests pass
4. Verify no compiler warnings
5. Check formatting (clang-format)

### 6.8 Documentation Standards

#### 6.8.1 Header Documentation
Use Doxygen-style comments for all public APIs:
```cpp
/**
 * @brief Computes the dot product of two vectors on GPU
 *
 * @param d_a Device pointer to first vector
 * @param d_b Device pointer to second vector
 * @param n Number of elements in each vector
 * @return float The computed dot product
 *
 * @pre d_a and d_b must point to valid device memory of size n
 * @pre n must be positive
 * @post Device memory is not modified
 *
 * @throws std::runtime_error if CUDA operations fail
 *
 * @note This function synchronizes the device
 * @note Time complexity: O(n)
 * @note Space complexity: O(1) device memory
 */
float cudaDotProduct(const float* d_a, const float* d_b, size_t n);
```

#### 6.8.2 CUDA Kernel Documentation
```cpp
/**
 * @brief Matrix multiplication kernel: C = A * B
 *
 * @param A Input matrix A (M x K)
 * @param B Input matrix B (K x N)
 * @param C Output matrix C (M x N)
 * @param M Number of rows in A
 * @param K Number of columns in A / rows in B
 * @param N Number of columns in B
 *
 * @note Launch configuration:
 *       - Block size: (TILE_SIZE, TILE_SIZE)
 *       - Grid size: ((N + TILE_SIZE - 1) / TILE_SIZE, (M + TILE_SIZE - 1) / TILE_SIZE)
 * @note Shared memory usage: 2 * TILE_SIZE * TILE_SIZE * sizeof(float)
 * @note Memory access pattern: Coalesced reads and writes
 */
__global__ void matrixMulKernel(const float* A, const float* B, float* C,
                                 int M, int K, int N);
```

#### 6.8.3 Implementation Comments
- **Complex Algorithms**: Explain the approach and key steps
- **Performance Optimizations**: Document why optimization was made
- **CUDA-Specific**: Explain thread/block organization, memory access patterns
- **Avoid Obvious Comments**: Don't comment what the code clearly shows

### 6.9 Performance Considerations

#### 6.9.1 C++ Performance
- **Avoid Unnecessary Copies**: Use move semantics and pass by reference
- **Inline Small Functions**: Mark with `inline` or define in headers
- **Const Correctness**: Use `const` to enable compiler optimizations
- **Compiler Optimizations**: Test with `-O2` and `-O3`

#### 6.9.2 CUDA Performance
- **Memory Coalescing**: Ensure coalesced global memory access
- **Shared Memory**: Use for frequently accessed data
- **Occupancy**: Aim for high occupancy (use `--ptxas-options=-v`)
- **Divergence**: Minimize warp divergence
- **Streams**: Use CUDA streams for concurrent operations
- **Profiling**: Profile with `nvprof` or Nsight Systems

### 6.10 Dependencies Management

#### 6.10.1 Mandatory Dependency Documentation
When adding ANY dependency, Claude Code MUST:
1. Update root `README.md` with:
    - Library name and version
    - Purpose and usage
    - Installation instructions
    - License information
2. Update CMake configuration to find/fetch the dependency
3. Update CI/CD configuration if needed

#### 6.10.2 Dependency Manifest
For vcpkg, maintain `vcpkg.json`:
```json
{
  "name": "project-name",
  "version": "1.0.0",
  "dependencies": [
    "boost-system",
    "eigen3",
    {
      "name": "opencv4",
      "version>=": "4.5.0"
    }
  ]
}
```

For Conan, maintain `conanfile.txt` or `conanfile.py`.

## 7. Session Continuity and State Discipline

Claude Code MUST:
- Assume **no memory across sessions**
- Externalize all long-lived decisions, constraints, and progress into files
- Never rely on conversational memory for:
    - Architecture decisions
    - Constraints and invariants
    - Roadmap state
    - Build configuration
    - Dependency versions

For roadmap work, every session MUST end with:
- A new handoff record under `agents_roadmaps/<active>/sessions/`

## 8. Decision Hygiene

Claude Code MUST:
- Avoid re-discussing previously settled decisions
- Record irreversible or high-impact decisions explicitly in:
    - Architecture Decision Records (ADRs) if project uses them
    - Roadmap INVARIANTS.md
    - Code comments for local decisions
- Ask before changing:
    - Public API interfaces
    - Architectural boundaries
    - Build system structure
    - Dependency versions (major updates)
    - CUDA compute capability requirements

Silent reinterpretation is forbidden.

## 9. Safety Rule: When in Doubt, Stop

> **If Claude Code is unsure whether an action is allowed,**
> **it MUST stop and ask the user.**

Guessing, inferring intent, or "doing what seems reasonable" is not acceptable.

This applies especially to:
- Memory management decisions
- CUDA kernel launch configurations
- Build system changes
- Dependency updates
- API changes

## 10. Enforcement Statement

Failure to follow this document indicates that:
- The agent is operating outside its mandate
- Output should not be trusted
- The session may need to be restarted

## 11. C++/CUDA Specific Forbidden Practices

Claude Code MUST NEVER:
- Use raw pointers for ownership (use smart pointers)
- Ignore CUDA error codes
- Use `using namespace std;` in headers
- Define macros that could collide with user code (use namespaces)
- Commit code with compiler warnings
- Skip error handling in CUDA code
- Use deprecated CUDA APIs without justification
- Implement manual memory management when RAII is possible
- Use C-style casts (use `static_cast`, `dynamic_cast`, etc.)
- Modify global state without synchronization
- Launch CUDA kernels without error checking
