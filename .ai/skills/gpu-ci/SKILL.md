# gpu-ci -- GPU CI patterns and guidance

> Vendor-neutral procedure description. Claude Code dispatches `/gpu-ci` to this
> body via the stub at `.claude/skills/gpu-ci/SKILL.md`. Codex / Cursor / Cline
> consult this file directly via the AGENTS.md procedures table.

Guidance for GPU-accelerated CI/CD pipelines covering CUDA compilation caching,
manylinux wheel validation, multi-arch builds, and GPU gating patterns.

## Purpose

This skill is guidance-only. No executable wrapper is provided.
It documents CI patterns for hybrid Python/C++/CUDA projects that distribute
wheels to PyPI or private package indices.

## When to Use

This skill applies when:
- `distribution=pypi-wheel` in project profile
- `hardware_targets` includes `cuda`
- Building CUDA-accelerated Python extensions
- Distributing wheels with CUDA dependencies

## 1. sccache for CUDA Compilation Caching

### 1.1 Overview

sccache is a compiler cache that supports nvcc. It dramatically reduces CI build
times by caching compiled object files across builds.

### 1.2 S3 Backend Configuration

```bash
# Environment variables
export SCCACHE_BUCKET=my-build-cache
export SCCACHE_REGION=us-west-2
export SCCACHE_S3_USE_SSL=true
export AWS_ACCESS_KEY_ID=<key>
export AWS_SECRET_ACCESS_KEY=<secret>

# CUDA-specific: separate host and device compilation
export CUDAHOSTCXX=/usr/bin/g++
export CUDA_NVCC_EXECUTABLE=/usr/local/cuda/bin/nvcc

# Start sccache daemon
sccache --start-server

# Wrap compiler in CMakeLists.txt
set(CMAKE_CUDA_COMPILER_LAUNCHER sccache)
set(CMAKE_CXX_COMPILER_LAUNCHER sccache)
```

### 1.3 Redis Backend Configuration

```bash
export SCCACHE_REDIS=redis://localhost:6379
export SCCACHE_REDIS_TTL=86400  # 24 hours
```

### 1.4 GitHub Actions Integration

```yaml
- name: Setup sccache
  uses: mozilla-actions/sccache-action@v0.0.3
  with:
    version: "v0.5.4"

- name: Configure sccache
  run: |
    echo "SCCACHE_BUCKET=${{ secrets.SCCACHE_BUCKET }}" >> $GITHUB_ENV
    echo "SCCACHE_REGION=us-west-2" >> $GITHUB_ENV
    echo "CUDAHOSTCXX=/usr/bin/g++" >> $GITHUB_ENV

- name: Build with sccache
  run: |
    export CMAKE_CUDA_COMPILER_LAUNCHER=sccache
    export CMAKE_CXX_COMPILER_LAUNCHER=sccache
    python -m build --wheel

- name: Show sccache stats
  run: sccache --show-stats
```

### 1.5 Cache Hit Rate Optimization

- Separate host and device compilation via `CUDAHOSTCXX`
- Use consistent CUDA Toolkit versions across builds
- Pin compiler versions (gcc, nvcc) in Docker images
- Avoid timestamp-dependent compilation flags

## 2. auditwheel for manylinux Wheels

### 2.1 Overview

auditwheel validates and repairs Python wheels for manylinux compatibility.
For CUDA wheels, system-provided libraries (CUDA runtime, cuDNN, NCCL) must
be excluded from bundling.

### 2.2 Basic Usage

```bash
# Repair wheel for manylinux2014
auditwheel repair dist/mypackage-0.1.0-cp39-cp39-linux_x86_64.whl \
  --plat manylinux2014_x86_64 \
  -w dist/
```

### 2.3 CUDA Library Exclusion

```bash
auditwheel repair dist/mypackage-*.whl \
  --exclude libcuda.so.1 \
  --exclude libcudart.so.11.0 \
  --exclude libcudart.so.12.0 \
  --exclude libnvrtc.so.11.2 \
  --exclude libnvrtc.so.12.0 \
  --exclude libcublas.so.11 \
  --exclude libcublas.so.12 \
  --exclude libcublasLt.so.11 \
  --exclude libcublasLt.so.12 \
  --exclude libcudnn.so.8 \
  --exclude libnccl.so.2 \
  --plat manylinux2014_x86_64 \
  -w dist/
```

### 2.4 Exclusion Policy

**Always exclude:**
- `libcuda.so.*` -- CUDA driver (user-provided)
- `libcudart.so.*` -- CUDA runtime (user-provided)
- `libnvrtc.so.*` -- NVRTC runtime compiler
- `libcublas*.so.*` -- cuBLAS libraries
- `libcudnn.so.*` -- cuDNN (user-provided)
- `libnccl.so.*` -- NCCL (user-provided)

**May bundle:**
- Custom CUDA kernels compiled into `.so` files
- CUTLASS header-only library (no runtime dependency)

### 2.5 GitHub Actions Integration

```yaml
- name: Install auditwheel
  run: pip install auditwheel

- name: Repair wheel
  run: |
    auditwheel repair dist/*.whl \
      --exclude libcuda.so.1 \
      --exclude libcudart.so.11.0 \
      --exclude libcudart.so.12.0 \
      --plat manylinux2014_x86_64 \
      -w dist/repaired/

- name: Upload repaired wheels
  uses: actions/upload-artifact@v3
  with:
    name: wheels
    path: dist/repaired/*.whl
```

## 3. Multi-Arch Wheel Build Matrix

### 3.1 Overview

CUDA libraries are not ABI-compatible across major versions. Projects typically
build separate wheel variants for each CUDA version (cu118, cu121, cu124) using
PEP 440 local version identifiers.

### 3.2 Wheel Naming Convention

```
mypackage-0.1.0+cu118-cp39-cp39-manylinux2014_x86_64.whl
mypackage-0.1.0+cu121-cp310-cp310-manylinux2014_x86_64.whl
mypackage-0.1.0+cu124-cp311-cp311-manylinux2014_x86_64.whl
```

Format: `{name}-{version}+{local}-{python}-{abi}-{platform}.whl`

The `+cu118` suffix is a local version identifier (PEP 440).

### 3.3 GitHub Actions Matrix

```yaml
name: Build CUDA Wheels

on: [push, pull_request]

jobs:
  build:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        cuda: [cu118, cu121, cu124]
        python: ['3.9', '3.10', '3.11', '3.12']
    
    steps:
      - uses: actions/checkout@v3
      
      - name: Set CUDA version
        id: cuda-version
        run: |
          case "${{ matrix.cuda }}" in
            cu118) echo "version=11.8.0" >> $GITHUB_OUTPUT ;;
            cu121) echo "version=12.1.0" >> $GITHUB_OUTPUT ;;
            cu124) echo "version=12.4.0" >> $GITHUB_OUTPUT ;;
          esac
      
      - name: Setup CUDA
        uses: Jimver/cuda-toolkit@v0.2.11
        with:
          cuda: ${{ steps.cuda-version.outputs.version }}
      
      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: ${{ matrix.python }}
      
      - name: Build wheel
        env:
          CUDA_VERSION: ${{ steps.cuda-version.outputs.version }}
        run: |
          pip install build
          python -m build --wheel
      
      - name: Rename wheel with CUDA suffix
        run: |
          cd dist
          for whl in *.whl; do
            # Insert +cu118 before first hyphen after version
            new_name=$(echo $whl | sed "s/-\(cp[0-9]*\)/-+${{ matrix.cuda }}-\1/")
            mv "$whl" "$new_name"
          done
      
      - name: Repair wheel
        run: |
          pip install auditwheel
          auditwheel repair dist/*.whl \
            --exclude libcuda.so.1 \
            --exclude libcudart.so.* \
            --plat manylinux2014_x86_64 \
            -w dist/repaired/
      
      - name: Upload wheels
        uses: actions/upload-artifact@v3
        with:
          name: wheels-${{ matrix.cuda }}-py${{ matrix.python }}
          path: dist/repaired/*.whl
```

### 3.4 Docker-Based Build

```dockerfile
# Multi-stage build for cu118
FROM nvidia/cuda:11.8.0-devel-centos7 as builder

# Install Python build tools
RUN yum install -y python39 python39-devel
RUN python3.9 -m pip install build

# Build wheel
COPY . /workspace
WORKDIR /workspace
RUN python3.9 -m build --wheel

# Repair wheel
RUN pip install auditwheel
RUN auditwheel repair dist/*.whl \
    --exclude libcuda.so.1 \
    --exclude libcudart.so.11.0 \
    --plat manylinux2014_x86_64 \
    -w /output

FROM scratch
COPY --from=builder /output/*.whl /
```

### 3.5 Local Version Identifier Injection

```python
# setup.py or pyproject.toml dynamic version
import os

cuda_version = os.environ.get('CUDA_VERSION', '11.8.0')
cuda_suffix = f"+cu{cuda_version.replace('.', '')[:4]}"  # 11.8.0 -> +cu118

# In pyproject.toml with setuptools_scm:
[tool.setuptools_scm]
local_scheme = "no-local-version"  # Disable default local version
version_scheme = "post-release"

# Then append CUDA suffix manually in build script
```

## 4. H100/A100/L40 GPU Gating Patterns

### 4.1 Overview

GPU tests should only run when appropriate hardware is available. Gating patterns
detect GPU type and skip tests gracefully when hardware is unavailable.

### 4.2 GitHub Actions GPU Detection

```yaml
- name: Detect GPU
  id: gpu-check
  run: |
    if command -v nvidia-smi &> /dev/null; then
      GPU_NAME=$(nvidia-smi --query-gpu=name --format=csv,noheader | head -n1)
      echo "gpu_available=true" >> $GITHUB_OUTPUT
      echo "gpu_type=$GPU_NAME" >> $GITHUB_OUTPUT
      echo "Detected GPU: $GPU_NAME"
    else
      echo "gpu_available=false" >> $GITHUB_OUTPUT
      echo "No GPU detected"
    fi

- name: Run GPU tests
  if: steps.gpu-check.outputs.gpu_available == 'true'
  run: pytest tests/gpu/

- name: Skip GPU tests
  if: steps.gpu-check.outputs.gpu_available == 'false'
  run: echo "Skipping GPU tests (no GPU available)"
```

### 4.3 GPU-Specific Test Gating

```yaml
- name: Run H100-specific tests
  if: contains(steps.gpu-check.outputs.gpu_type, 'H100')
  run: pytest tests/gpu/h100/

- name: Run A100-specific tests
  if: contains(steps.gpu-check.outputs.gpu_type, 'A100')
  run: pytest tests/gpu/a100/

- name: Run L40-specific tests
  if: contains(steps.gpu-check.outputs.gpu_type, 'L40')
  run: pytest tests/gpu/l40/
```

### 4.4 pytest GPU Markers

```python
# conftest.py
import pytest
import subprocess

def get_gpu_type():
    try:
        result = subprocess.run(
            ['nvidia-smi', '--query-gpu=name', '--format=csv,noheader'],
            capture_output=True, text=True, check=True
        )
        return result.stdout.strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None

def pytest_configure(config):
    config.addinivalue_line("markers", "gpu: mark test as requiring GPU")
    config.addinivalue_line("markers", "h100: mark test as requiring H100")
    config.addinivalue_line("markers", "a100: mark test as requiring A100")
    config.addinivalue_line("markers", "l40: mark test as requiring L40")

def pytest_runtest_setup(item):
    gpu_type = get_gpu_type()
    
    if item.get_closest_marker('gpu') and gpu_type is None:
        pytest.skip("GPU not available")
    
    if item.get_closest_marker('h100') and 'H100' not in (gpu_type or ''):
        pytest.skip("H100 GPU not available")
    
    if item.get_closest_marker('a100') and 'A100' not in (gpu_type or ''):
        pytest.skip("A100 GPU not available")
    
    if item.get_closest_marker('l40') and 'L40' not in (gpu_type or ''):
        pytest.skip("L40 GPU not available")
```

Usage:

```python
@pytest.mark.gpu
def test_basic_cuda():
    assert torch.cuda.is_available()

@pytest.mark.h100
def test_h100_fp8():
    # H100-specific FP8 features
    pass

@pytest.mark.a100
def test_a100_mma():
    # A100-specific MMA features
    pass
```

### 4.5 Self-Hosted Runner Labels

```yaml
jobs:
  test-h100:
    runs-on: [self-hosted, gpu, h100]
    steps:
      - run: pytest tests/gpu/h100/
  
  test-a100:
    runs-on: [self-hosted, gpu, a100]
    steps:
      - run: pytest tests/gpu/a100/
```

## 5. Docker Images for GPU CI

### 5.1 Base Images

**NVIDIA CUDA Official Images:**
- `nvidia/cuda:11.8.0-devel-ubuntu20.04`
- `nvidia/cuda:12.1.0-devel-ubuntu22.04`
- `nvidia/cuda:12.4.0-devel-centos7` (manylinux2014-compatible)

**manylinux with CUDA:**
```dockerfile
FROM quay.io/pypa/manylinux2014_x86_64:latest
COPY --from=nvidia/cuda:11.8.0-devel-centos7 /usr/local/cuda /usr/local/cuda
ENV PATH=/usr/local/cuda/bin:$PATH
ENV LD_LIBRARY_PATH=/usr/local/cuda/lib64:$LD_LIBRARY_PATH
```

### 5.2 Multi-Stage Build Pattern

```dockerfile
# Stage 1: Build environment
FROM nvidia/cuda:11.8.0-devel-centos7 as builder

RUN yum install -y python39 python39-devel gcc gcc-c++
RUN python3.9 -m pip install build scikit-build-core

COPY . /workspace
WORKDIR /workspace

ENV CUDA_HOME=/usr/local/cuda
ENV TORCH_CUDA_ARCH_LIST="8.0;8.6;8.9;9.0"

RUN python3.9 -m build --wheel

# Stage 2: Repair wheel
FROM quay.io/pypa/manylinux2014_x86_64:latest as repairer

COPY --from=builder /workspace/dist/*.whl /input/
RUN pip install auditwheel
RUN auditwheel repair /input/*.whl \
    --exclude libcuda.so.1 \
    --exclude libcudart.so.11.0 \
    --plat manylinux2014_x86_64 \
    -w /output

# Stage 3: Final artifact
FROM scratch
COPY --from=repairer /output/*.whl /
```

### 5.3 GitHub Actions with Docker

```yaml
- name: Build wheel in Docker
  run: |
    docker build \
      --target repairer \
      --build-arg CUDA_VERSION=11.8.0 \
      --build-arg PYTHON_VERSION=3.9 \
      -t wheel-builder .
    
    docker create --name extract wheel-builder
    docker cp extract:/output/. dist/
    docker rm extract
```

## 6. Integration with Constraints

This skill respects the following constraints:

- `.ai/constraints/hybrid/python-cpp-build.md` -- wheel build patterns
- `.ai/constraints/hybrid/system-deps.md` -- CUDA Toolkit discovery
- `.ai/constraints/cpp/cuda-modern.md` -- CUDA compilation flags

## 7. Common Pitfalls

### 7.1 Bundling CUDA Runtime

**Problem**: auditwheel bundles `libcudart.so`, causing version conflicts.

**Solution**: Always exclude CUDA runtime libraries:

```bash
auditwheel repair --exclude libcudart.so.* dist/*.whl
```

### 7.2 Inconsistent CUDA Versions

**Problem**: Build matrix uses different CUDA patch versions, breaking cache.

**Solution**: Pin exact CUDA versions in matrix:

```yaml
cuda: ['11.8.0', '12.1.0', '12.4.0']  # Not ['11.8', '12.1', '12.4']
```

### 7.3 Missing Local Version Identifier

**Problem**: Multiple CUDA variants overwrite each other (same wheel name).

**Solution**: Inject `+cu118` suffix before uploading:

```bash
mv mypackage-0.1.0-cp39-linux.whl mypackage-0.1.0+cu118-cp39-linux.whl
```

### 7.4 GPU Tests Fail on CPU-Only Runners

**Problem**: GPU tests run on CPU-only runners and fail.

**Solution**: Use pytest markers and skip when GPU unavailable (see section 4.4).

## 8. References

- sccache: https://github.com/mozilla/sccache
- auditwheel: https://github.com/pypa/auditwheel
- PEP 440 (Local Version Identifiers): https://peps.python.org/pep-0440/
- manylinux: https://github.com/pypa/manylinux
- NVIDIA CUDA Docker: https://hub.docker.com/r/nvidia/cuda
- PyTorch wheel builds: https://github.com/pytorch/pytorch/tree/main/.github/workflows
