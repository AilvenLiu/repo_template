---
id: hybrid/python-cpp-build
name: Python/C++ Build System Patterns
description: Build system patterns for hybrid Python/C++/CUDA projects
category: hybrid
status: draft
applies_to:
  - "pyproject.toml"
  - "CMakeLists.txt"
  - "setup.py"
severity: advisory
---

# Python/C++ Build System Patterns

**Status**: DRAFT (advisory only, does not block commits)

This constraint defines build system patterns for hybrid Python/C++/CUDA projects in AI infrastructure. It covers scikit-build-core integration, PyTorch extension building, CXX11 ABI compatibility, manylinux compliance, auditwheel workflows, and multi-CUDA toolkit wheel matrices.

## Scope

This constraint applies to:
- Python packages with C++/CUDA extensions
- PyTorch/JAX/TensorFlow custom operators
- Wheel distribution for multiple platforms and CUDA versions
- CMake-based Python extension builds

## 1. scikit-build-core: Modern CMake Integration

### 1.1 Why scikit-build-core

**scikit-build-core** is the modern replacement for setuptools when building CMake-based Python extensions. It provides:
- Native CMake integration without distutils
- PEP 517/518 compliance (pyproject.toml-based)
- Editable installs with proper CMake rebuilds
- Automatic CMake/Ninja dependency management
- Better Windows support than legacy scikit-build

**Use scikit-build-core when**:
- Building multi-file C++/CUDA extensions
- Integrating with existing CMake projects
- Need complex build logic (conditional compilation, multiple targets)
- Distributing wheels for multiple platforms

**Use torch.utils.cpp_extension when**:
- Single-file prototypes or simple extensions
- JIT compilation during development
- No need for wheel distribution

### 1.2 Basic pyproject.toml Configuration

```toml
[build-system]
requires = ["scikit-build-core>=0.8.0", "nanobind>=1.0.0"]
build-backend = "scikit_build_core.build"

[project]
name = "my_extension"
version = "1.0.0"
requires-python = ">=3.8"
dependencies = ["torch>=2.0.0", "numpy>=1.20.0"]

[tool.scikit-build]
cmake.build-type = "Release"
cmake.verbose = true
wheel.packages = ["my_extension"]
wheel.py-api = "cp38"

# Pass CMake arguments
cmake.args = ["-DUSE_CUDA=ON"]

# Define preprocessor macros
cmake.define = {USE_CUDA = "ON", CUDA_ARCH = "80;86;89;90"}

# Editable install mode
editable.mode = "redirect"  # or "inplace" for faster rebuilds
```

### 1.3 CMake Integration Pattern

**CMakeLists.txt**:
```cmake
cmake_minimum_required(VERSION 3.18)
project(my_extension LANGUAGES CXX CUDA)

# Find dependencies
find_package(Python3 REQUIRED COMPONENTS Interpreter Development.Module)
find_package(Torch REQUIRED)
find_package(CUDAToolkit REQUIRED)

# Create extension module
add_library(my_extension MODULE
    src/extension.cpp
    src/kernels.cu
)

# Link libraries
target_link_libraries(my_extension PRIVATE
    Python3::Module
    torch
    CUDA::cudart
    CUDA::cublas
)

# Set CUDA architectures
set_target_properties(my_extension PROPERTIES
    CUDA_ARCHITECTURES "70;75;80;86;89;90"
    CXX_STANDARD 17
    CUDA_STANDARD 17
)

# Install target
install(TARGETS my_extension LIBRARY DESTINATION my_extension)
```

### 1.4 Advanced Configuration

**Conditional CUDA support**:
```toml
[tool.scikit-build]
cmake.args = ["-DUSE_CUDA=ON"]

[[tool.scikit-build.overrides]]
if.platform-system = "darwin"
cmake.args = ["-DUSE_CUDA=OFF"]  # No CUDA on macOS
```

**Custom install paths**:
```toml
[tool.scikit-build]
wheel.install-dir = "my_extension"
wheel.packages = ["my_extension"]
wheel.exclude = ["*.h", "*.hpp"]  # Don't include headers in wheel
```

## 2. PyTorch Extension Building

### 2.1 CXX11 ABI Compatibility

**CRITICAL**: PyTorch wheels are built with specific C++ ABI. Mismatched ABI causes runtime symbol errors.

**Check PyTorch ABI**:
```python
import torch
print(torch.compiled_with_cxx11_abi())  # True or False
```

**Match ABI in CMake**:
```cmake
# Query PyTorch ABI
execute_process(
    COMMAND python -c "import torch; print(int(torch.compiled_with_cxx11_abi()))"
    OUTPUT_VARIABLE TORCH_CXX11_ABI
    OUTPUT_STRIP_TRAILING_WHITESPACE
)

# Set compiler flag
if(TORCH_CXX11_ABI EQUAL 0)
    target_compile_definitions(my_extension PRIVATE _GLIBCXX_USE_CXX11_ABI=0)
else()
    target_compile_definitions(my_extension PRIVATE _GLIBCXX_USE_CXX11_ABI=1)
endif()
```

**Match ABI in setup.py (legacy)**:
```python
import torch
from torch.utils.cpp_extension import BuildExtension, CUDAExtension

cxx11_abi = torch.compiled_with_cxx11_abi()
extra_compile_args = {
    'cxx': [f'-D_GLIBCXX_USE_CXX11_ABI={int(cxx11_abi)}'],
    'nvcc': [f'-D_GLIBCXX_USE_CXX11_ABI={int(cxx11_abi)}']
}

setup(
    ext_modules=[
        CUDAExtension(
            'my_extension',
            ['extension.cpp', 'kernels.cu'],
            extra_compile_args=extra_compile_args
        )
    ],
    cmdclass={'build_ext': BuildExtension}
)
```

### 2.2 Linking Against libtorch

**CMake pattern**:
```cmake
find_package(Torch REQUIRED)

# Link against torch libraries
target_link_libraries(my_extension PRIVATE torch)

# Include torch headers
target_include_directories(my_extension PRIVATE ${TORCH_INCLUDE_DIRS})

# Add torch definitions
target_compile_definitions(my_extension PRIVATE ${TORCH_CXX_FLAGS})
```

**Common pitfall**: Don't mix torch C++ API with Python C API in the same translation unit. Use separate files:
- `extension.cpp`: Python bindings (pybind11/nanobind)
- `kernels.cu`: CUDA kernels
- `torch_ops.cpp`: Torch C++ API operations

### 2.3 TORCH_CUDA_ARCH_LIST

Control which GPU architectures to compile for:

**Environment variable**:
```bash
export TORCH_CUDA_ARCH_LIST="7.0;7.5;8.0;8.6;8.9;9.0"
python -m pip install .
```

**CMake**:
```cmake
if(DEFINED ENV{TORCH_CUDA_ARCH_LIST})
    set(CMAKE_CUDA_ARCHITECTURES $ENV{TORCH_CUDA_ARCH_LIST})
else()
    set(CMAKE_CUDA_ARCHITECTURES "70;75;80;86;89;90")
endif()
```

**Trade-off**: More architectures = larger binary, longer compile time. Typical choices:
- **Development**: `"native"` (local GPU only)
- **Distribution**: `"70;75;80;86;89;90"` (Volta through Hopper)
- **Minimal**: `"80;90"` (Ampere and Hopper only)

## 3. manylinux Compliance

### 3.1 manylinux Standards

| Standard | Base OS | glibc | Use Case |
|----------|---------|-------|----------|
| manylinux2014 | CentOS 7 | 2.17 | Maximum compatibility |
| manylinux_2_28 | AlmaLinux 8 | 2.28 | Modern dependencies |

**Selection criteria**:
- Use **manylinux2014** for maximum compatibility (default)
- Use **manylinux_2_28** when you need:
  - glibc 2.28+ features
  - Modern system libraries (newer OpenSSL, etc.)
  - C++17 filesystem support

### 3.2 Building manylinux Wheels

**Docker-based build**:
```bash
# Use official manylinux image
docker run --rm -v $(pwd):/io \
    quay.io/pypa/manylinux_2_28_x86_64 \
    /io/build_wheels.sh
```

**build_wheels.sh**:
```bash
#!/bin/bash
set -e

# Install CUDA toolkit
yum install -y cuda-toolkit-12-1

# Build wheels for multiple Python versions
for PYBIN in /opt/python/cp{38,39,310,311,312}*/bin; do
    "${PYBIN}/pip" wheel /io/ -w /io/dist/
done

# Repair wheels with auditwheel
for whl in /io/dist/*.whl; do
    auditwheel repair "$whl" --plat manylinux_2_28_x86_64 -w /io/dist/
done
```

### 3.3 auditwheel Workflow

**auditwheel** vendors external `.so` files into the wheel and fixes RPATH.

**Basic usage**:
```bash
# Check wheel compliance
auditwheel show my_extension-1.0.0-cp310-cp310-linux_x86_64.whl

# Repair wheel
auditwheel repair my_extension-1.0.0-cp310-cp310-linux_x86_64.whl \
    --plat manylinux_2_28_x86_64 \
    -w dist/
```

**Exclude CUDA libraries** (too large to vendor):
```bash
auditwheel repair wheel.whl \
    --plat manylinux_2_28_x86_64 \
    --exclude libcudart.so.12 \
    --exclude libcublas.so.12 \
    --exclude libcublasLt.so.12 \
    -w dist/
```

**pyproject.toml configuration**:
```toml
[tool.cibuildwheel]
manylinux-x86_64-image = "manylinux_2_28"
repair-wheel-command = "auditwheel repair --exclude libcudart.so.12 --exclude libcublas.so.12 -w {dest_dir} {wheel}"
```

### 3.4 Common Pitfalls

**Issue**: `auditwheel repair` fails with "cannot repair wheel"
- **Cause**: Wheel links against libraries not in manylinux policy
- **Fix**: Use `--exclude` for CUDA libraries, or upgrade to manylinux_2_28

**Issue**: Wheel works locally but fails on other machines
- **Cause**: Linked against system libraries not in wheel
- **Fix**: Run `auditwheel show` to identify external dependencies

**Issue**: Wheel size explodes after repair
- **Cause**: auditwheel vendored large libraries (e.g., libstdc++)
- **Fix**: Exclude CUDA libraries, use static linking for small deps

## 4. Multi-CUDA Toolkit Wheel Matrix

### 4.1 Wheel Naming Convention

Use **local version identifiers** (PEP 440) to distinguish CUDA versions:

```
my_extension-1.0.0+cu118-cp310-cp310-manylinux_2_28_x86_64.whl
my_extension-1.0.0+cu121-cp310-cp310-manylinux_2_28_x86_64.whl
my_extension-1.0.0+cu124-cp310-cp310-manylinux_2_28_x86_64.whl
```

**Set version in pyproject.toml**:
```toml
[project]
version = "1.0.0"
dynamic = ["version"]

[tool.scikit-build]
metadata.version.provider = "scikit_build_core.metadata.setuptools_scm"
```

**Set local version via environment**:
```bash
export SETUPTOOLS_SCM_PRETEND_VERSION="1.0.0+cu118"
python -m build
```

### 4.2 CI Build Matrix

**GitHub Actions example**:
```yaml
name: Build Wheels

on: [push, pull_request]

jobs:
  build:
    runs-on: ubuntu-latest
    container: quay.io/pypa/manylinux_2_28_x86_64
    strategy:
      matrix:
        python: ["3.8", "3.9", "3.10", "3.11", "3.12"]
        cuda: ["11.8", "12.1", "12.4"]
    
    steps:
      - uses: actions/checkout@v3
      
      - name: Install CUDA
        run: |
          yum install -y cuda-toolkit-$(echo ${{ matrix.cuda }} | tr '.' '-')
      
      - name: Build wheel
        env:
          CUDA_VERSION: ${{ matrix.cuda }}
          SETUPTOOLS_SCM_PRETEND_VERSION: "1.0.0+cu$(echo ${{ matrix.cuda }} | tr -d '.')"
        run: |
          /opt/python/cp${{ matrix.python }}/bin/pip wheel . -w dist/
      
      - name: Repair wheel
        run: |
          auditwheel repair dist/*.whl \
            --plat manylinux_2_28_x86_64 \
            --exclude libcudart.so.* \
            --exclude libcublas.so.* \
            -w wheelhouse/
      
      - uses: actions/upload-artifact@v3
        with:
          name: wheels
          path: wheelhouse/*.whl
```

### 4.3 Runtime CUDA Version Detection

**User installation**:
```bash
# Install specific CUDA version
pip install my_extension==1.0.0+cu118

# Or use index URL
pip install my_extension --index-url https://download.pytorch.org/whl/cu118
```

**Runtime detection**:
```python
import torch

def get_cuda_version():
    """Get CUDA version as integer (e.g., 118 for 11.8)."""
    if not torch.cuda.is_available():
        return None
    version_str = torch.version.cuda  # "11.8"
    major, minor = version_str.split('.')
    return int(major) * 10 + int(minor)

# Check compatibility
cuda_version = get_cuda_version()
if cuda_version and cuda_version < 118:
    raise RuntimeError(f"CUDA 11.8+ required, found {torch.version.cuda}")
```

### 4.4 Dependency Specification

**Conditional dependencies**:
```toml
[project]
dependencies = [
    "numpy>=1.20.0",
    "torch>=2.0.0",
]

[project.optional-dependencies]
cu118 = ["torch>=2.0.0+cu118"]
cu121 = ["torch>=2.0.0+cu121"]
cu124 = ["torch>=2.0.0+cu124"]
```

**Installation**:
```bash
pip install my_extension[cu118] --extra-index-url https://download.pytorch.org/whl/cu118
```

### 4.5 Common Pitfalls

**Issue**: Local version doesn't upgrade automatically
- **Cause**: pip treats `1.0.0+cu118` and `1.0.0+cu121` as same version
- **Fix**: Users must specify exact version or use `--force-reinstall`

**Issue**: Wrong CUDA version installed
- **Cause**: pip doesn't validate CUDA compatibility
- **Fix**: Add runtime check in `__init__.py`

**Issue**: Multiple CUDA versions conflict
- **Cause**: User installed both cu118 and cu121 wheels
- **Fix**: Document that only one CUDA variant should be installed

## 5. CMake Best Practices

### 5.1 Modern CMake (3.18+)

**Minimum version**:
```cmake
cmake_minimum_required(VERSION 3.18)  # CUDA_ARCHITECTURES support
```

**Enable CUDA language**:
```cmake
project(my_extension LANGUAGES CXX CUDA)
# Or conditionally:
enable_language(CUDA)
```

**Don't use deprecated FindCUDA**:
```cmake
# WRONG (deprecated)
find_package(CUDA REQUIRED)

# RIGHT (modern)
enable_language(CUDA)
find_package(CUDAToolkit REQUIRED)
```

### 5.2 Target-Based Linking

**Modern pattern**:
```cmake
add_library(my_extension MODULE extension.cpp kernels.cu)

target_link_libraries(my_extension PRIVATE
    Python3::Module
    torch
    CUDA::cudart
    CUDA::cublas
)

target_include_directories(my_extension PRIVATE
    ${CMAKE_CURRENT_SOURCE_DIR}/include
)

target_compile_features(my_extension PRIVATE cxx_std_17)
```

**Avoid global commands**:
```cmake
# WRONG (global, affects all targets)
include_directories(${TORCH_INCLUDE_DIRS})
link_libraries(torch)

# RIGHT (target-specific)
target_include_directories(my_extension PRIVATE ${TORCH_INCLUDE_DIRS})
target_link_libraries(my_extension PRIVATE torch)
```

### 5.3 Finding Dependencies

**Python**:
```cmake
find_package(Python3 REQUIRED COMPONENTS Interpreter Development.Module)
target_link_libraries(my_extension PRIVATE Python3::Module)
```

**PyTorch**:
```cmake
# Set CMAKE_PREFIX_PATH to torch cmake directory
execute_process(
    COMMAND python -c "import torch; print(torch.utils.cmake_prefix_path)"
    OUTPUT_VARIABLE TORCH_CMAKE_PREFIX
    OUTPUT_STRIP_TRAILING_WHITESPACE
)
list(APPEND CMAKE_PREFIX_PATH ${TORCH_CMAKE_PREFIX})

find_package(Torch REQUIRED)
target_link_libraries(my_extension PRIVATE torch)
```

**CUDA Toolkit**:
```cmake
find_package(CUDAToolkit REQUIRED)
target_link_libraries(my_extension PRIVATE
    CUDA::cudart
    CUDA::cublas
    CUDA::cublasLt
)
```

### 5.4 CUDA Architecture Selection

**Explicit list**:
```cmake
set_target_properties(my_extension PROPERTIES
    CUDA_ARCHITECTURES "70;75;80;86;89;90"
)
```

**From environment**:
```cmake
if(DEFINED ENV{TORCH_CUDA_ARCH_LIST})
    string(REPLACE "." "" ARCH_LIST $ENV{TORCH_CUDA_ARCH_LIST})
    string(REPLACE ";" ";" ARCH_LIST ${ARCH_LIST})
    set_target_properties(my_extension PROPERTIES
        CUDA_ARCHITECTURES ${ARCH_LIST}
    )
endif()
```

**Native (local GPU only)**:
```cmake
set_target_properties(my_extension PROPERTIES
    CUDA_ARCHITECTURES "native"
)
```

## 6. Wheel Metadata and Distribution

### 6.1 Platform Tags

**Common platform tags**:
- `manylinux_2_28_x86_64`: Linux x86_64, glibc 2.28+
- `manylinux2014_x86_64`: Linux x86_64, glibc 2.17+
- `win_amd64`: Windows 64-bit
- `macosx_11_0_arm64`: macOS ARM64 (Apple Silicon)

**CUDA version goes in local identifier**, not platform tag:
```
# CORRECT
my_extension-1.0.0+cu118-cp310-cp310-manylinux_2_28_x86_64.whl

# WRONG (don't invent platform tags)
my_extension-1.0.0-cp310-cp310-manylinux_2_28_x86_64_cu118.whl
```

### 6.2 Dependency Specification

**Basic dependencies**:
```toml
[project]
dependencies = [
    "torch>=2.0.0",
    "numpy>=1.20.0",
]
```

**Platform-specific dependencies**:
```toml
[project]
dependencies = [
    "torch>=2.0.0; platform_system=='Linux'",
    "numpy>=1.20.0",
]
```

**Optional dependencies**:
```toml
[project.optional-dependencies]
dev = ["pytest>=7.0", "black>=23.0"]
cuda = ["nvidia-cuda-runtime-cu12>=12.1"]
```

### 6.3 Distribution Strategies

**PyPI**:
- Upload all CUDA variants to PyPI
- Users select via local version identifier
- Requires separate upload for each variant

**Custom index**:
```bash
# Host wheels on custom server
pip install my_extension --index-url https://wheels.myproject.org/
```

**PyTorch-style index**:
```bash
# Separate index per CUDA version
pip install my_extension --index-url https://download.pytorch.org/whl/cu118
```

## 7. Testing and Validation

### 7.1 Build Validation

**Test wheel installation**:
```bash
# Create clean environment
python -m venv test_env
source test_env/bin/activate

# Install wheel
pip install dist/my_extension-1.0.0+cu118-*.whl

# Test import
python -c "import my_extension; print(my_extension.__version__)"

# Test CUDA availability
python -c "import my_extension; print(my_extension.cuda_available())"
```

### 7.2 ABI Validation

**Check symbols**:
```bash
# List undefined symbols
nm -u my_extension.so | grep GLIBCXX

# Should see either:
# GLIBCXX_3.4.21 (old ABI)
# GLIBCXX_3.4.26 (new ABI)
# But not both!
```

### 7.3 manylinux Validation

**Check compliance**:
```bash
auditwheel show dist/my_extension-*.whl

# Should output:
# my_extension-1.0.0+cu118-cp310-cp310-linux_x86_64.whl is consistent
# with the following platform tag: "manylinux_2_28_x86_64"
```

## 8. Enforcement

**Status**: DRAFT - advisory only, does not block commits.

This constraint is enforced through:
- Code review (manual verification of build patterns)
- CI validation (wheel building and testing)
- Documentation (this constraint serves as reference)

When this constraint graduates from DRAFT to ACTIVE, enforcement will include:
- Pre-commit checks for pyproject.toml/CMakeLists.txt structure
- CI gates requiring successful wheel builds for all CUDA variants
- Automated ABI compatibility validation
