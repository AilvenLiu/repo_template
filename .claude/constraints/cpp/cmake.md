# C++/CUDA CMake Build System Requirements

> **This document defines mandatory CMake build system standards for C++/CUDA projects.**
> All build configurations must follow these requirements.

## 1. CMake Version Requirements

### 1.1 Version Standards
- **Minimum Version**: CMake 3.20 (required for cross-compilation and CUDA support)
- **Preferred Version**: CMake 3.25+ (for improved CUDA cross-compilation)
- **Rationale**: Modern CMake features, better CUDA support, improved toolchain handling

### 1.2 Version Declaration
```cmake
cmake_minimum_required(VERSION 3.20)
# Or for newer features
cmake_minimum_required(VERSION 3.25)
```

## 2. Project Configuration

### 2.1 Project Declaration
```cmake
cmake_minimum_required(VERSION 3.20)
project(ProjectName VERSION 1.0.0 LANGUAGES CXX CUDA)
```

### 2.2 Language Standards
```cmake
# C++ standard
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

# CUDA standard
set(CMAKE_CUDA_STANDARD 17)
set(CMAKE_CUDA_STANDARD_REQUIRED ON)
```

### 2.3 CUDA Architecture Configuration
```cmake
# Single architecture (e.g., Jetson Orin)
set(CMAKE_CUDA_ARCHITECTURES 87)

# Multiple architectures for broader compatibility
set(CMAKE_CUDA_ARCHITECTURES 70 75 80 86 87)
# 70: Volta (V100)
# 75: Turing (RTX 20xx)
# 80: Ampere (A100)
# 86: Ampere (RTX 30xx)
# 87: Ampere (Jetson Orin)
```

## 3. Compiler Configuration

### 3.1 Compiler Warnings
```cmake
# Compiler warnings
if(MSVC)
    add_compile_options(/W4 /WX)
else()
    add_compile_options(-Wall -Wextra -Wpedantic -Werror)
endif()
```

### 3.2 Build Type Configuration
```cmake
# Build type
if(NOT CMAKE_BUILD_TYPE)
    set(CMAKE_BUILD_TYPE Release)
endif()

# Build type specific flags
set(CMAKE_CXX_FLAGS_DEBUG "-g -O0")
set(CMAKE_CXX_FLAGS_RELEASE "-O3 -DNDEBUG")
set(CMAKE_CXX_FLAGS_RELWITHDEBINFO "-O2 -g")
```

## 4. Modern CMake Target-Based Approach

### 4.1 Target Creation
**Use target-based approach, avoid global commands**

```cmake
# Library target
add_library(mylib
    src/module1.cpp
    src/module2.cpp
    cuda/kernel1.cu
    cuda/kernel2.cu
)

# Executable target
add_executable(myapp src/main.cpp)
```

### 4.2 Target Properties
```cmake
# Include directories (target-specific)
target_include_directories(mylib PUBLIC
    $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/include>
    $<INSTALL_INTERFACE:include>
)

# Compile options (target-specific)
target_compile_options(mylib PRIVATE
    $<$<COMPILE_LANGUAGE:CXX>:-Wall -Wextra>
    $<$<COMPILE_LANGUAGE:CUDA>:--expt-relaxed-constexpr>
)

# Link libraries (target-specific)
target_link_libraries(mylib PUBLIC
    CUDA::cudart
    Eigen3::Eigen
)
```

### 4.3 Visibility Keywords
- **PUBLIC**: Propagates to targets that link to this target
- **PRIVATE**: Only applies to this target
- **INTERFACE**: Only propagates to targets that link to this target

```cmake
target_link_libraries(mylib
    PUBLIC CUDA::cudart      # Users of mylib need CUDA
    PRIVATE spdlog::spdlog   # Internal logging, users don't need it
)
```

## 5. CUDA Support

### 5.1 Enabling CUDA
```cmake
# Method 1: In project declaration
project(ProjectName LANGUAGES CXX CUDA)

# Method 2: Enable later
enable_language(CUDA)
```

### 5.2 Finding CUDA Toolkit
```cmake
find_package(CUDAToolkit REQUIRED)

# Link CUDA libraries
target_link_libraries(mylib PUBLIC
    CUDA::cudart        # CUDA runtime
    CUDA::cublas        # cuBLAS
    CUDA::cufft         # cuFFT
)
```

### 5.3 CUDA-Specific Compiler Flags
```cmake
# CUDA compiler flags
target_compile_options(mylib PRIVATE
    $<$<COMPILE_LANGUAGE:CUDA>:
        --expt-relaxed-constexpr
        --expt-extended-lambda
        -use_fast_math
        --ptxas-options=-v
    >
)
```

## 6. Dependency Management

### 6.1 Dependency Management Priority

**CRITICAL: NEVER install libraries system-wide (apt/yum/brew)**

System-wide installation breaks reproducibility, cross-platform compatibility, and version control. Always use a package manager.

**Preferred Methods** (in priority order):

1. **Conan** (STRONGLY RECOMMENDED - use this by default)
   - **This is the mandatory first choice for all C++/CUDA projects**
   - Best for complex dependency graphs
   - Excellent cross-platform support (Linux, Windows, macOS, embedded)
   - Superior version pinning and conflict resolution
   - Active community and extensive package repository
   - Use `conanfile.txt` or `conanfile.py`
   - **Only consider alternatives if Conan genuinely cannot meet your needs**

2. **vcpkg** (alternative - only if Conan is unsuitable)
   - Microsoft-maintained package manager
   - Good Windows support
   - Use `vcpkg.json` manifest mode
   - **Use only if**: Package not available in Conan, or Windows-specific requirements

3. `FetchContent` - Only for header-only or small libraries
   - Downloads source at configure time
   - Good for libraries without complex dependencies
   - Example: nlohmann/json, spdlog

4. Git submodules - Only for vendored dependencies
   - When you need to track specific commits
   - For libraries you may need to modify
   - Requires manual updates

5. `find_package()` - Only AFTER package manager installation
   - Used to locate dependencies installed by Conan/vcpkg
   - NOT a method to find system-installed libraries
   - Always specify version requirements

**Important**: `find_package()` should only be used to locate dependencies that were installed via Conan, vcpkg, or FetchContent. It is NOT a method to use system-installed libraries.

### 6.2 Using find_package()
```cmake
# Find packages (installed via Conan/vcpkg/FetchContent)
find_package(CUDAToolkit REQUIRED)
find_package(Eigen3 REQUIRED)
find_package(OpenCV REQUIRED)

# Link to targets
target_link_libraries(mylib PUBLIC
    CUDA::cudart
    Eigen3::Eigen
    opencv_core
)
```

### 6.3 Using FetchContent
```cmake
include(FetchContent)

# Fetch header-only library
FetchContent_Declare(
    json
    GIT_REPOSITORY https://github.com/nlohmann/json.git
    GIT_TAG v3.11.2
)
FetchContent_MakeAvailable(json)

# Link to target
target_link_libraries(mylib PRIVATE nlohmann_json::nlohmann_json)
```

### 6.4 Conan Integration (Primary)
```cmake
# Include Conan-generated files
include(${CMAKE_BINARY_DIR}/conan_toolchain.cmake)

# Find packages installed by Conan
find_package(Boost REQUIRED)
find_package(Eigen3 REQUIRED)

# Link to targets
target_link_libraries(mylib PUBLIC
    Boost::boost
    Eigen3::Eigen
)
```

Corresponding `conanfile.txt`:
```ini
[requires]
boost/1.82.0
eigen/3.4.0
opencv/4.5.0

[generators]
CMakeDeps
CMakeToolchain

[options]
opencv:shared=True
```

### 6.5 Version Pinning
**Always specify version requirements**:
```cmake
find_package(Eigen3 3.4 REQUIRED)
find_package(OpenCV 4.5 REQUIRED)
```

## 7. Complete CMakeLists.txt Example

### 7.1 Root CMakeLists.txt
```cmake
cmake_minimum_required(VERSION 3.20)
project(ProjectName VERSION 1.0.0 LANGUAGES CXX CUDA)

# C++ standard
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

# CUDA standard and architectures
set(CMAKE_CUDA_STANDARD 17)
set(CMAKE_CUDA_STANDARD_REQUIRED ON)
set(CMAKE_CUDA_ARCHITECTURES 87)  # Jetson Orin (adjust for multi-target: 70 75 80 86 87)

# Compiler warnings
if(MSVC)
    add_compile_options(/W4)
else()
    add_compile_options(-Wall -Wextra -Wpedantic)
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

### 7.2 Tests CMakeLists.txt
```cmake
# tests/CMakeLists.txt
find_package(GTest REQUIRED)

# Unit tests
add_executable(unit_tests
    unit/test_module1.cpp
    unit/test_module2.cpp
)
target_link_libraries(unit_tests PRIVATE
    mylib
    GTest::gtest_main
)
add_test(NAME UnitTests COMMAND unit_tests)

# CUDA tests
add_executable(cuda_tests
    cuda/test_kernels.cu
    cuda/test_memory.cu
)
target_link_libraries(cuda_tests PRIVATE
    mylib
    GTest::gtest_main
    CUDA::cudart
)
add_test(NAME CudaTests COMMAND cuda_tests)
```

## 8. Cross-Compilation

### 8.1 Toolchain Files
**Always use toolchain files for cross-compilation**

Example toolchain file for Jetson (ARM64):
```cmake
# jetson-toolchain.cmake
set(CMAKE_SYSTEM_NAME Linux)
set(CMAKE_SYSTEM_PROCESSOR aarch64)

set(CMAKE_C_COMPILER /usr/bin/aarch64-linux-gnu-gcc)
set(CMAKE_CXX_COMPILER /usr/bin/aarch64-linux-gnu-g++)

set(CMAKE_FIND_ROOT_PATH /usr/aarch64-linux-gnu)
set(CMAKE_FIND_ROOT_PATH_MODE_PROGRAM NEVER)
set(CMAKE_FIND_ROOT_PATH_MODE_LIBRARY ONLY)
set(CMAKE_FIND_ROOT_PATH_MODE_INCLUDE ONLY)
```

Usage:
```bash
cmake -DCMAKE_TOOLCHAIN_FILE=jetson-toolchain.cmake ..
```

## 9. Installation and Packaging

### 9.1 Installation Rules
```cmake
# Install targets
install(TARGETS mylib myapp
    EXPORT MyLibTargets
    LIBRARY DESTINATION lib
    ARCHIVE DESTINATION lib
    RUNTIME DESTINATION bin
    INCLUDES DESTINATION include
)

# Install headers
install(DIRECTORY include/
    DESTINATION include
    FILES_MATCHING PATTERN "*.hpp"
)

# Install export targets
install(EXPORT MyLibTargets
    FILE MyLibTargets.cmake
    NAMESPACE MyLib::
    DESTINATION lib/cmake/MyLib
)
```

### 9.2 Package Configuration
```cmake
# Generate package config files
include(CMakePackageConfigHelpers)

configure_package_config_file(
    ${CMAKE_CURRENT_SOURCE_DIR}/Config.cmake.in
    ${CMAKE_CURRENT_BINARY_DIR}/MyLibConfig.cmake
    INSTALL_DESTINATION lib/cmake/MyLib
)

write_basic_package_version_file(
    ${CMAKE_CURRENT_BINARY_DIR}/MyLibConfigVersion.cmake
    VERSION ${PROJECT_VERSION}
    COMPATIBILITY AnyNewerVersion
)

install(FILES
    ${CMAKE_CURRENT_BINARY_DIR}/MyLibConfig.cmake
    ${CMAKE_CURRENT_BINARY_DIR}/MyLibConfigVersion.cmake
    DESTINATION lib/cmake/MyLib
)
```

## 10. Build Configuration Best Practices

### 10.1 Out-of-Source Builds
**Always use out-of-source builds**:
```bash
# Good
mkdir build && cd build
cmake ..
cmake --build .

# Bad - in-source build
cmake .
make
```

### 10.2 Build Commands
```bash
# Configure
cmake -B build -DCMAKE_BUILD_TYPE=Release

# Build
cmake --build build -j$(nproc)

# Test
cd build && ctest --output-on-failure

# Install
cmake --install build --prefix /usr/local
```

## 11. CMake Options and Cache Variables

### 11.1 Project Options
```cmake
option(BUILD_TESTS "Build test suite" ON)
option(BUILD_BENCHMARKS "Build benchmarks" OFF)
option(ENABLE_CUDA "Enable CUDA support" ON)

if(BUILD_TESTS)
    enable_testing()
    add_subdirectory(tests)
endif()

if(BUILD_BENCHMARKS)
    add_subdirectory(benchmarks)
endif()
```

### 11.2 Cache Variables
```cmake
set(CUDA_ARCH "87" CACHE STRING "CUDA architecture")
set(MAX_THREADS "1024" CACHE STRING "Maximum thread count")

# Use in code via configure_file
configure_file(
    ${CMAKE_CURRENT_SOURCE_DIR}/config.h.in
    ${CMAKE_CURRENT_BINARY_DIR}/config.h
)
```

## 12. Dependency Documentation

### 12.1 Mandatory Documentation
When adding ANY dependency, Claude Code MUST:
1. Update root `README.md` with:
    - Library name and version
    - Purpose and usage
    - Installation instructions
    - License information
2. Update CMake configuration to find/fetch the dependency
3. Update CI/CD configuration if needed

### 12.2 README.md Dependency Section
```markdown
## Dependencies

### Build Requirements
- CMake 3.20 or later
- C++17 compatible compiler (GCC 9.0+, Clang 10.0+, MSVC 2019+)
- CUDA Toolkit 11.0+ (for CUDA features)

### Runtime Requirements
- CUDA-capable GPU with compute capability 7.0+ (Volta or later)
- CUDA Runtime 11.0+

### Third-Party Libraries
- **Eigen3** (3.4.0+): Linear algebra operations
- **Google Test** (1.12.0+): Unit testing framework
- **spdlog** (1.10.0+): Logging library
```

## 13. Pre-Commit CMake Requirements

### 13.1 Before Committing
Before EVERY commit operation, Claude Code MUST:
1. Verify CMakeLists.txt syntax is correct
2. Ensure project builds successfully
3. Check that all dependencies are documented

### 13.2 Build Verification
```bash
# Clean build
rm -rf build
mkdir build && cd build

# Configure
cmake .. -DCMAKE_BUILD_TYPE=Debug \
         -DCMAKE_CXX_FLAGS="-Wall -Wextra -Wpedantic -Werror"

# Build
cmake --build .

# Test
ctest --output-on-failure
```

## 14. Common CMake Patterns

### 14.1 Conditional Compilation
```cmake
if(ENABLE_CUDA)
    enable_language(CUDA)
    add_definitions(-DUSE_CUDA)
endif()
```

### 14.2 Platform-Specific Configuration
```cmake
if(WIN32)
    # Windows-specific
elseif(APPLE)
    # macOS-specific
elseif(UNIX)
    # Linux-specific
endif()
```

### 14.3 Compiler-Specific Configuration
```cmake
if(CMAKE_CXX_COMPILER_ID STREQUAL "GNU")
    # GCC-specific
elseif(CMAKE_CXX_COMPILER_ID STREQUAL "Clang")
    # Clang-specific
elseif(CMAKE_CXX_COMPILER_ID STREQUAL "MSVC")
    # MSVC-specific
endif()
```

## 15. Enforcement

### 15.1 CMake Standards
- Use modern CMake (3.20+)
- Use target-based approach
- Avoid global commands
- Document all dependencies
- Use out-of-source builds

### 15.2 Code Review Checklist
- [ ] CMakeLists.txt uses modern CMake patterns
- [ ] All dependencies are documented
- [ ] Build succeeds on all platforms
- [ ] Installation rules are correct
- [ ] Tests are integrated with CTest
