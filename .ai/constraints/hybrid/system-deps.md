---
status: draft
load_as: advisory
applies_to: [cpp, cuda]
activation_rule: external_dependencies=system_cuda
---

# System Dependencies Discovery (DRAFT)

**Status**: DRAFT -- advisory only, does not block commits.

This constraint covers discovery of system-installed CUDA Toolkit, cuDNN, NCCL,
and TensorRT via CMake, version assertion at configure time, and fail-fast
guidance for hybrid Python/C++/CUDA projects.

## 1. CUDA Toolkit Discovery

### 1.1 Modern CMake Pattern (3.18+)

Use `find_package(CUDAToolkit)` for CUDA library discovery:

```cmake
cmake_minimum_required(VERSION 3.18)
project(my_cuda_extension LANGUAGES CXX CUDA)

find_package(CUDAToolkit REQUIRED)

if(NOT CUDAToolkit_FOUND)
    message(FATAL_ERROR "CUDA Toolkit not found. Set CUDA_HOME or install CUDA.")
endif()

message(STATUS "CUDA Toolkit version: ${CUDAToolkit_VERSION}")
message(STATUS "CUDA include dirs: ${CUDAToolkit_INCLUDE_DIRS}")
message(STATUS "CUDA libraries: ${CUDAToolkit_LIBRARY_DIR}")
```

### 1.2 Version Assertion

Assert minimum CUDA version at configure time:

```cmake
find_package(CUDAToolkit 11.8 REQUIRED)

if(CUDAToolkit_VERSION VERSION_LESS "11.8")
    message(FATAL_ERROR 
        "CUDA Toolkit ${CUDAToolkit_VERSION} found, but >= 11.8 required. "
        "Please upgrade CUDA or set CUDA_HOME to a newer installation.")
endif()
```

### 1.3 Environment Variable Fallback

CMake automatically checks `CUDA_HOME` and `CUDA_PATH`. Explicit fallback:

```cmake
if(NOT CUDAToolkit_FOUND AND DEFINED ENV{CUDA_HOME})
    set(CMAKE_CUDA_COMPILER "$ENV{CUDA_HOME}/bin/nvcc")
    find_package(CUDAToolkit REQUIRED)
endif()
```

## 2. PyTorch Discovery

### 2.1 find_package(Torch)

PyTorch provides CMake config files via `torch.utils.cmake_prefix_path`:

```cmake
# In CMakeLists.txt
execute_process(
    COMMAND python -c "import torch; print(torch.utils.cmake_prefix_path)"
    OUTPUT_VARIABLE TORCH_CMAKE_PREFIX
    OUTPUT_STRIP_TRAILING_WHITESPACE
)

list(APPEND CMAKE_PREFIX_PATH "${TORCH_CMAKE_PREFIX}")
find_package(Torch REQUIRED)

message(STATUS "PyTorch version: ${TORCH_VERSION}")
message(STATUS "PyTorch CXX11 ABI: ${TORCH_CXX11_ABI}")
```

### 2.2 CUDA Compatibility Check

Verify PyTorch CUDA version matches system CUDA:

```cmake
if(Torch_FOUND AND CUDAToolkit_FOUND)
    execute_process(
        COMMAND python -c "import torch; print(torch.version.cuda)"
        OUTPUT_VARIABLE TORCH_CUDA_VERSION
        OUTPUT_STRIP_TRAILING_WHITESPACE
    )
    
    if(NOT TORCH_CUDA_VERSION VERSION_EQUAL CUDAToolkit_VERSION_MAJOR.CUDAToolkit_VERSION_MINOR)
        message(WARNING 
            "PyTorch built with CUDA ${TORCH_CUDA_VERSION}, "
            "but system CUDA is ${CUDAToolkit_VERSION}. "
            "This may cause runtime errors.")
    endif()
endif()
```

## 3. cuDNN Discovery

### 3.1 Manual Discovery Pattern

cuDNN does not provide CMake config files. Manual discovery:

```cmake
find_path(CUDNN_INCLUDE_DIR cudnn.h
    HINTS
        ${CUDAToolkit_INCLUDE_DIRS}
        $ENV{CUDNN_ROOT}/include
        /usr/include
        /usr/local/include
)

find_library(CUDNN_LIBRARY cudnn
    HINTS
        ${CUDAToolkit_LIBRARY_DIR}
        $ENV{CUDNN_ROOT}/lib64
        $ENV{CUDNN_ROOT}/lib
        /usr/lib64
        /usr/local/lib64
)

if(NOT CUDNN_INCLUDE_DIR OR NOT CUDNN_LIBRARY)
    message(FATAL_ERROR 
        "cuDNN not found. Set CUDNN_ROOT environment variable or install cuDNN.")
endif()

message(STATUS "cuDNN include: ${CUDNN_INCLUDE_DIR}")
message(STATUS "cuDNN library: ${CUDNN_LIBRARY}")
```

### 3.2 Version Extraction

Extract cuDNN version from header:

```cmake
if(CUDNN_INCLUDE_DIR)
    file(READ "${CUDNN_INCLUDE_DIR}/cudnn_version.h" CUDNN_VERSION_FILE)
    string(REGEX MATCH "define CUDNN_MAJOR ([0-9]+)" _ "${CUDNN_VERSION_FILE}")
    set(CUDNN_VERSION_MAJOR ${CMAKE_MATCH_1})
    string(REGEX MATCH "define CUDNN_MINOR ([0-9]+)" _ "${CUDNN_VERSION_FILE}")
    set(CUDNN_VERSION_MINOR ${CMAKE_MATCH_1})
    string(REGEX MATCH "define CUDNN_PATCHLEVEL ([0-9]+)" _ "${CUDNN_VERSION_FILE}")
    set(CUDNN_VERSION_PATCH ${CMAKE_MATCH_1})
    
    set(CUDNN_VERSION "${CUDNN_VERSION_MAJOR}.${CUDNN_VERSION_MINOR}.${CUDNN_VERSION_PATCH}")
    message(STATUS "cuDNN version: ${CUDNN_VERSION}")
    
    if(CUDNN_VERSION VERSION_LESS "8.0")
        message(FATAL_ERROR "cuDNN ${CUDNN_VERSION} found, but >= 8.0 required.")
    endif()
endif()
```

## 4. NCCL Discovery

### 4.1 Manual Discovery Pattern

NCCL discovery follows cuDNN pattern:

```cmake
find_path(NCCL_INCLUDE_DIR nccl.h
    HINTS
        ${CUDAToolkit_INCLUDE_DIRS}
        $ENV{NCCL_ROOT}/include
        /usr/include
        /usr/local/include
)

find_library(NCCL_LIBRARY nccl
    HINTS
        ${CUDAToolkit_LIBRARY_DIR}
        $ENV{NCCL_ROOT}/lib64
        $ENV{NCCL_ROOT}/lib
        /usr/lib64
        /usr/local/lib64
)

if(NOT NCCL_INCLUDE_DIR OR NOT NCCL_LIBRARY)
    message(FATAL_ERROR 
        "NCCL not found. Set NCCL_ROOT environment variable or install NCCL.")
endif()

message(STATUS "NCCL include: ${NCCL_INCLUDE_DIR}")
message(STATUS "NCCL library: ${NCCL_LIBRARY}")
```

### 4.2 Version Extraction

Extract NCCL version from header:

```cmake
if(NCCL_INCLUDE_DIR)
    file(READ "${NCCL_INCLUDE_DIR}/nccl.h" NCCL_VERSION_FILE)
    string(REGEX MATCH "define NCCL_MAJOR ([0-9]+)" _ "${NCCL_VERSION_FILE}")
    set(NCCL_VERSION_MAJOR ${CMAKE_MATCH_1})
    string(REGEX MATCH "define NCCL_MINOR ([0-9]+)" _ "${NCCL_VERSION_FILE}")
    set(NCCL_VERSION_MINOR ${CMAKE_MATCH_1})
    string(REGEX MATCH "define NCCL_PATCH ([0-9]+)" _ "${NCCL_VERSION_FILE}")
    set(NCCL_VERSION_PATCH ${CMAKE_MATCH_1})
    
    set(NCCL_VERSION "${NCCL_VERSION_MAJOR}.${NCCL_VERSION_MINOR}.${NCCL_VERSION_PATCH}")
    message(STATUS "NCCL version: ${NCCL_VERSION}")
    
    if(NCCL_VERSION VERSION_LESS "2.10")
        message(FATAL_ERROR "NCCL ${NCCL_VERSION} found, but >= 2.10 required.")
    endif()
endif()
```

## 5. TensorRT Discovery

### 5.1 Manual Discovery Pattern

TensorRT discovery:

```cmake
find_path(TENSORRT_INCLUDE_DIR NvInfer.h
    HINTS
        $ENV{TENSORRT_ROOT}/include
        /usr/include/x86_64-linux-gnu
        /usr/include
        /usr/local/include
)

find_library(TENSORRT_LIBRARY nvinfer
    HINTS
        $ENV{TENSORRT_ROOT}/lib64
        $ENV{TENSORRT_ROOT}/lib
        /usr/lib/x86_64-linux-gnu
        /usr/lib64
        /usr/local/lib64
)

if(NOT TENSORRT_INCLUDE_DIR OR NOT TENSORRT_LIBRARY)
    message(FATAL_ERROR 
        "TensorRT not found. Set TENSORRT_ROOT environment variable or install TensorRT.")
endif()

message(STATUS "TensorRT include: ${TENSORRT_INCLUDE_DIR}")
message(STATUS "TensorRT library: ${TENSORRT_LIBRARY}")
```

### 5.2 Version Extraction

Extract TensorRT version from header:

```cmake
if(TENSORRT_INCLUDE_DIR)
    file(READ "${TENSORRT_INCLUDE_DIR}/NvInferVersion.h" TENSORRT_VERSION_FILE)
    string(REGEX MATCH "define NV_TENSORRT_MAJOR ([0-9]+)" _ "${TENSORRT_VERSION_FILE}")
    set(TENSORRT_VERSION_MAJOR ${CMAKE_MATCH_1})
    string(REGEX MATCH "define NV_TENSORRT_MINOR ([0-9]+)" _ "${TENSORRT_VERSION_FILE}")
    set(TENSORRT_VERSION_MINOR ${CMAKE_MATCH_1})
    string(REGEX MATCH "define NV_TENSORRT_PATCH ([0-9]+)" _ "${TENSORRT_VERSION_FILE}")
    set(TENSORRT_VERSION_PATCH ${CMAKE_MATCH_1})
    
    set(TENSORRT_VERSION "${TENSORRT_VERSION_MAJOR}.${TENSORRT_VERSION_MINOR}.${TENSORRT_VERSION_PATCH}")
    message(STATUS "TensorRT version: ${TENSORRT_VERSION}")
    
    if(TENSORRT_VERSION VERSION_LESS "8.0")
        message(FATAL_ERROR "TensorRT ${TENSORRT_VERSION} found, but >= 8.0 required.")
    endif()
endif()
```

## 6. Fail-Fast Patterns

### 6.1 Configure-Time vs Build-Time

**ALWAYS fail at configure time, NEVER at build time.**

Bad (fails at build time):
```cmake
# Don't do this - error happens during compilation
target_include_directories(my_target PRIVATE ${CUDNN_INCLUDE_DIR})
```

Good (fails at configure time):
```cmake
# Do this - error happens during cmake configuration
if(NOT CUDNN_INCLUDE_DIR)
    message(FATAL_ERROR "cuDNN not found")
endif()
target_include_directories(my_target PRIVATE ${CUDNN_INCLUDE_DIR})
```

### 6.2 Clear Error Messages

Provide actionable error messages:

```cmake
if(NOT CUDAToolkit_FOUND)
    message(FATAL_ERROR 
        "CUDA Toolkit not found.\n"
        "Solutions:\n"
        "  1. Install CUDA Toolkit from https://developer.nvidia.com/cuda-downloads\n"
        "  2. Set CUDA_HOME environment variable: export CUDA_HOME=/usr/local/cuda\n"
        "  3. Add CUDA to PATH: export PATH=/usr/local/cuda/bin:$PATH\n"
    )
endif()
```

### 6.3 Dependency Summary

Print dependency summary at end of configuration:

```cmake
message(STATUS "=== Dependency Summary ===")
message(STATUS "CUDA Toolkit: ${CUDAToolkit_VERSION}")
message(STATUS "PyTorch: ${TORCH_VERSION}")
message(STATUS "cuDNN: ${CUDNN_VERSION}")
message(STATUS "NCCL: ${NCCL_VERSION}")
message(STATUS "TensorRT: ${TENSORRT_VERSION}")
message(STATUS "==========================")
```

## 7. Integration with scikit-build-core

### 7.1 pyproject.toml Configuration

Pass environment variables to CMake via scikit-build-core:

```toml
[tool.scikit-build]
cmake.minimum-version = "3.18"
cmake.args = [
    "-DCUDA_HOME=${CUDA_HOME}",
    "-DCUDNN_ROOT=${CUDNN_ROOT}",
    "-DNCCL_ROOT=${NCCL_ROOT}",
    "-DTENSORRT_ROOT=${TENSORRT_ROOT}",
]

[tool.scikit-build.cmake.define]
CMAKE_CUDA_ARCHITECTURES = "80;86;89;90"
```

### 7.2 Build Script

Wrapper script for consistent environment:

```bash
#!/bin/bash
set -e

# Detect CUDA installation
if [ -z "$CUDA_HOME" ]; then
    if [ -d "/usr/local/cuda" ]; then
        export CUDA_HOME=/usr/local/cuda
    else
        echo "Error: CUDA_HOME not set and /usr/local/cuda not found"
        exit 1
    fi
fi

# Build with scikit-build-core
python -m build --wheel
```

## 8. Testing Discovery Logic

### 8.1 Dry-Run Configuration

Test CMake configuration without building:

```bash
cmake -S . -B build \
    -DCUDA_HOME=/usr/local/cuda \
    -DCUDNN_ROOT=/usr/local/cudnn \
    -DNCCL_ROOT=/usr/local/nccl \
    -DTENSORRT_ROOT=/usr/local/tensorrt
```

### 8.2 CI Environment

GitHub Actions example for testing discovery:

```yaml
- name: Configure CMake
  run: |
    cmake -S . -B build \
      -DCUDA_HOME=$CUDA_HOME \
      -DCUDNN_ROOT=$CUDNN_ROOT \
      -DNCCL_ROOT=$NCCL_ROOT
  env:
    CUDA_HOME: /usr/local/cuda-11.8
    CUDNN_ROOT: /usr/local/cudnn-8.6
    NCCL_ROOT: /usr/local/nccl-2.15
```

## 9. Common Pitfalls

### 9.1 Mixing CUDA Versions

**Problem**: System has multiple CUDA versions, CMake finds wrong one.

**Solution**: Explicitly set `CMAKE_CUDA_COMPILER`:

```cmake
set(CMAKE_CUDA_COMPILER "${CUDA_HOME}/bin/nvcc")
find_package(CUDAToolkit REQUIRED)
```

### 9.2 Missing Library Symlinks

**Problem**: Library found but symlink missing (e.g., `libcudnn.so` exists but `libcudnn.so.8` missing).

**Solution**: Check for versioned library:

```cmake
find_library(CUDNN_LIBRARY 
    NAMES cudnn libcudnn.so.8 libcudnn.so
    HINTS ${CUDAToolkit_LIBRARY_DIR}
)
```

### 9.3 Header-Only Detection

**Problem**: Header found but library missing.

**Solution**: Always check both header and library:

```cmake
if(CUDNN_INCLUDE_DIR AND NOT CUDNN_LIBRARY)
    message(FATAL_ERROR 
        "cuDNN header found at ${CUDNN_INCLUDE_DIR}, "
        "but library not found. Install complete cuDNN package.")
endif()
```

## 10. References

- CMake CUDAToolkit: https://cmake.org/cmake/help/latest/module/FindCUDAToolkit.html
- PyTorch C++ API: https://pytorch.org/cppdocs/installing.html
- cuDNN Installation: https://docs.nvidia.com/deeplearning/cudnn/install-guide/
- NCCL Installation: https://docs.nvidia.com/deeplearning/nccl/install-guide/
- TensorRT Installation: https://docs.nvidia.com/deeplearning/tensorrt/install-guide/

---

**Activation**: This constraint loads when `external_dependencies=system_cuda`
in the project profile.

**Draft Status**: Advisory only. Does not block commits. Promotion to stable
requires validation against a real consuming project (Phase 2, task-2-10).
