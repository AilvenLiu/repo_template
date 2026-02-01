# C++/CUDA Dependency Management

> **This document defines mandatory dependency management standards for C++/CUDA projects.**
> All dependency changes must follow these rules to ensure reproducibility and cross-platform compatibility.

## 1. Mandatory Tool: Conan (Primary) or vcpkg (Alternative)

### 1.1 Conan as the Default Standard

**MANDATORY**: Use **Conan** as the primary dependency manager for all C++/CUDA projects.

Conan provides:
- Cross-platform package management
- Binary caching for faster builds
- Integration with CMake
- Reproducible builds via conanfile.txt/conanfile.py
- Support for custom package repositories

### 1.2 vcpkg as Alternative

**ONLY** use vcpkg if Conan genuinely cannot meet your needs (rare cases):
- Specific library not available in Conan
- Project already uses vcpkg extensively
- Explicit user request

**If in doubt, use Conan.** It has better cross-platform support and binary caching.

### 1.3 System Package Manager Prohibition

**ABSOLUTELY FORBIDDEN**: Installing C++ libraries via system package managers.

```bash
# FORBIDDEN: System package manager usage
apt install libboost-dev          # WRONG - breaks reproducibility
yum install opencv-devel          # WRONG - version mismatch risk
brew install eigen                # WRONG - not portable
pacman -S fmt                     # WRONG - system-wide pollution

# REQUIRED: Use Conan
conan install . --build=missing   # CORRECT
```

**CRITICAL EXAMPLES**:

```bash
# FORBIDDEN: Direct system installation
sudo apt install libfmt-dev       # WRONG - system Python
brew install nlohmann-json        # WRONG - not reproducible

# REQUIRED: Always use Conan or vcpkg
conan install . --build=missing   # CORRECT - Conan
vcpkg install fmt                 # CORRECT - vcpkg (if Conan unsuitable)
```

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

## 5. Mandatory Dependency Update Protocol

### 5.1 Critical Requirement

**CRITICAL**: When adding ANY new C++ library, Claude Code MUST:

1. Add the dependency to conanfile.txt (or vcpkg.json)
2. Run `conan install . --build=missing` to install
3. Update CMakeLists.txt with `find_package()` and `target_link_libraries()`
4. Commit conanfile.txt and CMakeLists.txt together
5. Document the library purpose in README.md

### 5.2 Standard Workflow

```bash
# 1. Add dependency to conanfile.txt
echo "fmt/10.1.1" >> conanfile.txt  # Or edit manually

# 2. Install dependencies
conan install . --build=missing

# 3. Update CMakeLists.txt
# Add: find_package(fmt REQUIRED)
# Add: target_link_libraries(myapp PRIVATE fmt::fmt)

# 4. Commit changes
git add conanfile.txt CMakeLists.txt src/module.cpp
git commit -m "feat: add fmt library for string formatting"
```

### 5.3 Version Pinning Strategy

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

## 6. CUDA-Specific Dependencies

### 6.1 CUDA Toolkit

CUDA toolkit is typically system-installed but should be version-controlled:

```cmake
# CMakeLists.txt
cmake_minimum_required(VERSION 3.20)
project(MyCudaProject LANGUAGES CXX CUDA)

# Require specific CUDA version
find_package(CUDAToolkit 11.0 REQUIRED)

# Link CUDA libraries
target_link_libraries(myapp PRIVATE CUDA::cudart CUDA::cublas)
```

### 6.2 CUDA Libraries via Conan

Some CUDA-related libraries are available via Conan:

```ini
[requires]
thrust/1.17.2
cub/1.17.2
```

## 7. Environment Setup Protocol

### 7.1 Mandatory Setup Steps

When starting work on a C++/CUDA project, Claude Code MUST:

1. Check for `conanfile.txt` or `conanfile.py` (Conan project indicator)
2. Check for `vcpkg.json` (vcpkg project indicator)
3. If Conan project, run `conan install . --build=missing`
4. If vcpkg project, ensure vcpkg toolchain is configured
5. If neither exists, initialise with Conan: create conanfile.txt

```bash
# Check for dependency manager
if [ -f "conanfile.txt" ] || [ -f "conanfile.py" ]; then
    echo "Conan project detected"
    conan install . --build=missing
elif [ -f "vcpkg.json" ]; then
    echo "vcpkg project detected"
    # Ensure vcpkg toolchain is set
else
    echo "No dependency manager found"
    echo "Initialising Conan project..."
    # Create conanfile.txt
fi
```

## 8. Dependency Documentation

### 8.1 README.md Dependencies Section

Document dependencies in README.md:

```markdown
## Dependencies

This project uses Conan for dependency management.

### Prerequisites

- CMake 3.20+
- Conan 2.0+
- C++17 compatible compiler

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

| Library | Version | Purpose |
|---------|---------|---------|
| fmt | 10.1.1 | String formatting |
| spdlog | 1.12.0 | Logging |
| gtest | 1.14.0 | Unit testing |
```

## 9. Security and Updates

### 9.1 Security Scanning

```bash
# Check for known vulnerabilities (manual process)
# Review Conan Center advisories
# Check library changelogs for security fixes
```

### 9.2 Regular Updates

```bash
# Check for outdated packages
conan search fmt -r conancenter  # Check latest version

# Update specific package
# Edit conanfile.txt with new version
# Run: conan install . --build=missing
```

## 10. Enforcement

### 10.1 Violations

**STRICTLY FORBIDDEN**:
- Installing libraries via apt, yum, brew, or other system package managers
- Using libraries without adding them to conanfile.txt/vcpkg.json
- Committing code without updated dependency files
- Using unpinned versions in production
- Skipping CMake integration for new dependencies
- Not documenting new dependencies

### 10.2 CI/CD Integration

All pull requests MUST:
- Include updated conanfile.txt (or vcpkg.json) if dependencies changed
- Pass dependency installation tests
- Have no missing dependencies
- Document new dependencies in README.md

## 11. Dependency Management Checklist

Before committing, verify:
- [ ] New libraries added via Conan (or vcpkg if justified)
- [ ] conanfile.txt reflects all dependencies
- [ ] CMakeLists.txt has find_package() for new dependencies
- [ ] CMakeLists.txt has target_link_libraries() for new dependencies
- [ ] Dependencies are documented in README.md
- [ ] No system-wide installations (apt, yum, brew)
- [ ] All dependencies are necessary
- [ ] Version constraints are exact (not ranges)
- [ ] Build succeeds with fresh conan install
