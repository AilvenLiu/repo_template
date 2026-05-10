# C++/CUDA Dependency Management

> **This document defines mandatory dependency management standards for C++/CUDA projects.**
> All dependency changes must follow these rules to ensure reproducibility and cross-platform compatibility.

## 1. Dependency Management: Documented Mechanisms

### 1.1 CMake Version Requirement

**CRITICAL**: CMake 3.20 or higher is REQUIRED for all C++/CUDA projects.

**Why CMake 3.20+ is mandatory:**
- Modern target-based approach
- Better CUDA support
- Improved package finding
- Consistent cross-platform builds

**Before starting work, verify CMake 3.20+ is available:**
```bash
# Check CMake version
cmake --version  # Must be 3.20 or higher
```

**If CMake 3.20+ is not available, install it first:**

Option 1: Using system package manager (if recent enough)
```bash
# Ubuntu 22.04+
sudo apt update
sudo apt install cmake

# macOS
brew install cmake

# Fedora/RHEL 9+
sudo dnf install cmake
```

Option 2: Download from cmake.org (Recommended for older systems)
- Visit: https://cmake.org/download/
- Download CMake 3.20 or higher

Option 3: Using pip (Alternative)
```bash
pip install cmake
```

### 1.2 Core Requirement: Documented Mechanism

**MANDATORY**: Every dependency MUST be declared in a documented, reproducible mechanism.

**Acceptable mechanisms** (in recommended priority order):

1. **Conan** (recommended for most projects)
   - Best for complex dependency graphs
   - Excellent cross-platform support (Linux, Windows, macOS, embedded)
   - Superior version pinning and conflict resolution
   - Active community and extensive package repository
   - Use when: building general-purpose C++/CUDA applications

2. **vcpkg** (alternative package manager)
   - Microsoft-maintained, good Windows support
   - Use when: package unavailable in Conan, or Windows-specific requirements

3. **CPM (CMake Package Manager)**
   - Lightweight, CMake-native dependency management
   - Downloads and builds dependencies at configure time
   - Use when: need source-level control or package not in Conan/vcpkg

4. **FetchContent** (CMake built-in)
   - Downloads source at configure time
   - Use when: header-only libraries, small dependencies without complex transitive deps
   - Example: nlohmann/json, spdlog (header-only mode)

5. **Git submodules**
   - Tracks specific commits of vendored dependencies
   - Use when: need to modify dependency source, or track unreleased versions
   - Requires manual updates

6. **System-installed NVIDIA libraries**
   - CUDA Toolkit, cuDNN, NCCL, TensorRT, cuBLAS, cuFFT
   - Use when: official NVIDIA distribution provides the library
   - Must document required versions in README.md

**Selection criteria:**
- **Conan first** for general C++ libraries (Boost, Eigen, OpenCV, fmt, spdlog)
- **System install** for NVIDIA CUDA ecosystem libraries
- **FetchContent/CPM** for header-only or simple libraries
- **Git submodules** when you need source-level control
- **vcpkg** as fallback when Conan unavailable

### 1.3 System Package Manager Restrictions

**FORBIDDEN**: Installing general C++ libraries via system package managers.

```bash
# FORBIDDEN: System package manager for C++ libraries
apt install libboost-dev          # WRONG - breaks reproducibility
yum install opencv-devel          # WRONG - version mismatch risk
brew install eigen                # WRONG - not portable
pacman -S fmt                     # WRONG - system-wide pollution

# REQUIRED: Use documented mechanism
conan install . --build=missing   # CORRECT - Conan
vcpkg install fmt                 # CORRECT - vcpkg
# Or FetchContent/CPM in CMakeLists.txt
```

**ALLOWED system installations:**
- **NVIDIA libraries**: CUDA Toolkit, cuDNN, NCCL, TensorRT (official NVIDIA channels)
- **Build tools**: CMake, compilers (gcc, clang, nvcc), build systems
- **ROCm libraries**: ROCm toolkit and libraries (official AMD channels)

**Rationale**: NVIDIA and AMD provide official system packages for their GPU libraries.
These are designed for system-wide installation and are not typically available via
Conan/vcpkg. General C++ libraries must use package managers for reproducibility.

### 1.4 Dependency Addition Protocol

**CRITICAL**: When adding ANY C++/CUDA dependency, the agent MUST follow the appropriate workflow for the chosen mechanism:

+-------------------------------------------------------------+
| DEPENDENCY MANAGEMENT PROTOCOL                              |
|                                                             |
| WHEN: Adding a new library to the project                   |
|                                                             |
| FOR CONAN/VCPKG:                                            |
|   1. Add to conanfile.txt (or vcpkg.json)                   |
|   2. Run conan install . --build=missing (or vcpkg install) |
|   3. Update CMakeLists.txt with find_package()              |
|   4. Update CMakeLists.txt with target_link_libraries()     |
|   5. Document in README.md                                  |
|                                                             |
| FOR FETCHCONTENT/CPM:                                       |
|   1. Add FetchContent_Declare() or CPMAddPackage() to CMake |
|   2. Update target_link_libraries()                         |
|   3. Document in README.md                                  |
|                                                             |
| FOR GIT SUBMODULES:                                         |
|   1. git submodule add <url> third_party/<name>             |
|   2. Add add_subdirectory() to CMakeLists.txt               |
|   3. Update target_link_libraries()                         |
|   4. Document in README.md and .gitmodules                  |
|                                                             |
| FOR NVIDIA SYSTEM LIBRARIES:                                |
|   1. Document required version in README.md                 |
|   2. Add find_package(CUDAToolkit) to CMakeLists.txt        |
|   3. Link with CUDA::<library> targets                      |
|                                                             |
| FORBIDDEN:                                                  |
|   apt install libfmt-dev        # WRONG - undocumented      |
|   brew install eigen             # WRONG - not reproducible |
|   Manual dependency without CMake integration                |
+-------------------------------------------------------------+

## 2. Conan Project Structure

### 2.1 Required Files

Every Conan-managed project MUST have:
- **conanfile.txt** or **conanfile.py**: Dependency specification
- **CMakeLists.txt**: Build configuration with Conan integration

### 2.2 conanfile.txt Structure

```ini
[requires]
fmt/10.1.1
spdlog/1.12.0
nlohmann_json/3.11.2
gtest/1.14.0

[generators]
CMakeDeps
CMakeToolchain

[options]
fmt/*:header_only=False
```

### 2.3 conanfile.py Structure (Advanced)

```python
from conan import ConanFile
from conan.tools.cmake import cmake_layout

class MyProjectConan(ConanFile):
    settings = "os", "compiler", "build_type", "arch"
    generators = "CMakeDeps", "CMakeToolchain"

    def requirements(self):
        self.requires("fmt/10.1.1")
        self.requires("spdlog/1.12.0")
        self.requires("gtest/1.14.0", test=True)

    def layout(self):
        cmake_layout(self)
```

### 2.4 CMake Integration

```cmake
cmake_minimum_required(VERSION 3.20)
project(MyProject)

# Find Conan-installed packages
find_package(fmt REQUIRED)
find_package(spdlog REQUIRED)

add_executable(myapp main.cpp)
target_link_libraries(myapp PRIVATE fmt::fmt spdlog::spdlog)
```

## 3. Conan Commands Reference

### 3.1 Project Setup

```bash
# Install Conan (if not installed)
pip install conan

# Create default profile
conan profile detect

# Install dependencies
conan install . --build=missing

# Install with specific build type
conan install . --build=missing -s build_type=Debug
conan install . --build=missing -s build_type=Release
```

### 3.2 Dependency Management

```bash
# Search for packages
conan search fmt -r conancenter

# Add dependency to conanfile.txt
# Edit conanfile.txt and add to [requires] section

# Install new dependencies
conan install . --build=missing

# Update dependencies
conan install . --build=missing --update

# List installed packages
conan list "*"
```

### 3.3 Building with Conan

```bash
# Standard CMake workflow with Conan
conan install . --build=missing -of=build
cd build
cmake .. -DCMAKE_TOOLCHAIN_FILE=conan_toolchain.cmake -DCMAKE_BUILD_TYPE=Release
cmake --build .
```

## 4. vcpkg Alternative (When Conan Unsuitable)

### 4.1 vcpkg Setup

```bash
# Clone vcpkg
git clone https://github.com/microsoft/vcpkg.git
cd vcpkg && ./bootstrap-vcpkg.sh

# Install packages
./vcpkg install fmt spdlog nlohmann-json

# Integrate with CMake
cmake -B build -S . -DCMAKE_TOOLCHAIN_FILE=/path/to/vcpkg/scripts/buildsystems/vcpkg.cmake
```

### 4.2 vcpkg.json Manifest

```json
{
  "name": "my-project",
  "version": "1.0.0",
  "dependencies": [
    "fmt",
    "spdlog",
    "nlohmann-json",
    {
      "name": "gtest",
      "features": ["gmock"]
    }
  ]
}
```

## 5. FetchContent (CMake Built-in)

### 5.1 When to Use FetchContent

Use FetchContent for:
- Header-only libraries (nlohmann/json, magic_enum)
- Small libraries without complex dependencies
- Libraries not available in Conan/vcpkg

### 5.2 FetchContent Example

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

## 6. CPM (CMake Package Manager)

### 6.1 When to Use CPM

Use CPM for:
- Source-level dependency control
- Projects that need to build dependencies from source
- Lightweight alternative to Conan/vcpkg

### 6.2 CPM Setup

```cmake
# Download CPM.cmake
include(cmake/CPM.cmake)

# Add dependencies
CPMAddPackage(
    NAME fmt
    GITHUB_REPOSITORY fmtlib/fmt
    GIT_TAG 10.1.1
)

target_link_libraries(mylib PRIVATE fmt::fmt)
```

## 7. Git Submodules

### 7.1 When to Use Git Submodules

Use git submodules for:
- Vendored dependencies you need to modify
- Tracking specific commits of unreleased versions
- Projects with few dependencies

### 7.2 Git Submodule Workflow

```bash
# Add submodule
git submodule add https://github.com/fmtlib/fmt.git third_party/fmt

# Update submodules
git submodule update --init --recursive

# CMakeLists.txt integration
add_subdirectory(third_party/fmt)
target_link_libraries(mylib PRIVATE fmt::fmt)
```

## 8. NVIDIA System Libraries

### 8.1 Allowed NVIDIA System Installations

The following NVIDIA libraries are designed for system-wide installation:
- **CUDA Toolkit**: nvcc, cudart, device runtime
- **cuDNN**: Deep learning primitives
- **NCCL**: Multi-GPU communication
- **TensorRT**: Inference optimization
- **cuBLAS, cuFFT, cuSPARSE**: CUDA math libraries

### 8.2 NVIDIA Library Integration

```cmake
# Find CUDA Toolkit
find_package(CUDAToolkit 11.0 REQUIRED)

# Link CUDA libraries
target_link_libraries(myapp PRIVATE
    CUDA::cudart
    CUDA::cublas
    CUDA::cufft
)
```

### 8.3 Documentation Requirement

When using NVIDIA system libraries, document in README.md:

```markdown
## NVIDIA Dependencies

- CUDA Toolkit 12.0+
- cuDNN 8.9+
- NCCL 2.18+

### Installation

```bash
# Ubuntu
wget https://developer.download.nvidia.com/compute/cuda/repos/...
sudo apt install cuda-toolkit-12-0 libcudnn8 libnccl2
```
```

## 9. Mandatory Dependency Update Protocol

### 9.1 Critical Requirement

**CRITICAL**: When adding ANY new C++ library, the agent MUST:

1. Choose appropriate mechanism (Conan, vcpkg, FetchContent, CPM, submodule, or NVIDIA system)
2. Follow the mechanism's integration workflow
3. Update CMakeLists.txt with find_package() or add_subdirectory()
4. Update target_link_libraries()
5. Commit dependency manifest and CMakeLists.txt together
6. Document the library purpose and installation in README.md

### 9.2 Standard Workflow Examples

**Conan:**
```bash
# 1. Add dependency to conanfile.txt
echo "fmt/10.1.1" >> conanfile.txt

# 2. Install dependencies
conan install . --build=missing

# 3. Update CMakeLists.txt
# Add: find_package(fmt REQUIRED)
# Add: target_link_libraries(myapp PRIVATE fmt::fmt)

# 4. Commit changes
git add conanfile.txt CMakeLists.txt
git commit -m "feat: add fmt library for string formatting"
```

**FetchContent:**
```cmake
# In CMakeLists.txt
include(FetchContent)
FetchContent_Declare(json
    GIT_REPOSITORY https://github.com/nlohmann/json.git
    GIT_TAG v3.11.2
)
FetchContent_MakeAvailable(json)
target_link_libraries(myapp PRIVATE nlohmann_json::nlohmann_json)
```

### 9.3 Version Pinning Strategy

```ini
# Exact version (RECOMMENDED for stability)
fmt/10.1.1

# Version range (use sparingly)
fmt/[>=10.0.0 <11.0.0]

# Latest (FORBIDDEN in production)
fmt/*  # NEVER use in production
```

**Guidelines:**
- **Production dependencies**: Use exact versions for reproducibility
- **Development dependencies**: Exact versions recommended
- **Testing dependencies**: Exact versions for CI consistency

## 10. CUDA-Specific Dependencies

### 10.1 CUDA Toolkit (System Installation)

CUDA toolkit is typically system-installed. Document required version:

```cmake
# CMakeLists.txt
cmake_minimum_required(VERSION 3.20)
project(MyCudaProject LANGUAGES CXX CUDA)

# Require specific CUDA version
find_package(CUDAToolkit 11.0 REQUIRED)

# Link CUDA libraries
target_link_libraries(myapp PRIVATE CUDA::cudart CUDA::cublas)
```

### 10.2 CUDA Libraries via Package Managers

Some CUDA-related libraries are available via Conan:

```ini
[requires]
thrust/1.17.2
cub/1.17.2
```

### 10.3 NVIDIA System Libraries

Document NVIDIA system library requirements in README.md with installation instructions.

## 11. Environment Setup Protocol

### 11.1 Mandatory Setup Steps

When starting work on a C++/CUDA project, the agent MUST:

1. Check for dependency mechanism indicators:
   - `conanfile.txt` or `conanfile.py` (Conan)
   - `vcpkg.json` (vcpkg)
   - `cmake/CPM.cmake` (CPM)
   - `.gitmodules` (git submodules)
2. Run appropriate setup command
3. If no mechanism exists, recommend Conan for new projects

```bash
# Check for dependency manager
if [ -f "conanfile.txt" ] || [ -f "conanfile.py" ]; then
    echo "Conan project detected"
    conan install . --build=missing
elif [ -f "vcpkg.json" ]; then
    echo "vcpkg project detected"
    vcpkg install
elif [ -f ".gitmodules" ]; then
    echo "Git submodules detected"
    git submodule update --init --recursive
fi
```

## 12. Dependency Documentation

### 12.1 README.md Dependencies Section

Document dependencies in README.md with installation instructions for the chosen mechanism:

```markdown
## Dependencies

This project uses Conan for dependency management.

### Prerequisites

- CMake 3.20+
- Conan 2.0+
- C++17 compatible compiler
- CUDA Toolkit 12.0+ (for GPU features)

### Installation

```bash
# Install Conan (if not installed)
pip install conan

# Install dependencies
conan install . --build=missing -of=build

# Build
cd build
cmake .. -DCMAKE_TOOLCHAIN_FILE=conan_toolchain.cmake
cmake --build .
```

### Dependencies

| Library | Version | Mechanism | Purpose |
|---------|---------|-----------|---------|
| fmt | 10.1.1 | Conan | String formatting |
| spdlog | 1.12.0 | Conan | Logging |
| gtest | 1.14.0 | Conan | Unit testing |
| CUDA Toolkit | 12.0+ | System | GPU computation |
```

## 13. Security and Updates

### 13.1 Security Scanning

```bash
# Check for known vulnerabilities (manual process)
# Review Conan Center advisories
# Check library changelogs for security fixes
```

### 13.2 Regular Updates

```bash
# Check for outdated packages
conan search fmt -r conancenter  # Check latest version

# Update specific package
# Edit conanfile.txt with new version
# Run: conan install . --build=missing
```

## 14. Enforcement

### 14.1 Violations

**STRICTLY FORBIDDEN**:
- Installing general C++ libraries via apt, yum, brew, or other system package managers (NVIDIA/AMD GPU libraries excepted)
- Using libraries without declaring them in a documented mechanism (conanfile.txt, vcpkg.json, CMakeLists.txt FetchContent, .gitmodules)
- Committing code without updated dependency manifests
- Using unpinned versions in production
- Skipping CMake integration for new dependencies
- Not documenting new dependencies

### 14.2 CI/CD Integration

All pull requests MUST:
- Include updated dependency manifest if dependencies changed
- Pass dependency installation tests
- Have no missing dependencies
- Document new dependencies in README.md

## 15. Dependency Management Checklist

Before committing, verify:
- [ ] New libraries added via documented mechanism (Conan, vcpkg, FetchContent, CPM, submodule, or NVIDIA system)
- [ ] Dependency manifest reflects all dependencies (conanfile.txt, vcpkg.json, CMakeLists.txt, or .gitmodules)
- [ ] CMakeLists.txt has find_package() or add_subdirectory() for new dependencies
- [ ] CMakeLists.txt has target_link_libraries() for new dependencies
- [ ] Dependencies are documented in README.md with mechanism and version
- [ ] No undocumented system-wide installations (except NVIDIA/AMD GPU libraries)
- [ ] All dependencies are necessary
- [ ] Version constraints are exact (not ranges) for production
- [ ] Build succeeds with fresh dependency installation
