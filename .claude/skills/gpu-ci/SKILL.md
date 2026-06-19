---
name: gpu-ci
description: "GPU CI patterns for CUDA compilation caching, manylinux wheels, and multi-arch builds. Use when distribution=pypi-wheel or hardware_targets includes cuda."
version: 1.0.0
---

# /gpu-ci

Guidance-only skill. No `.ai/bin/agent-gpu-ci` wrapper exists. Applies when
`.ai/project.yml` declares `distribution: pypi-wheel` or `hardware_targets: [cuda]`.

Covers: sccache compilation caching, auditwheel manylinux validation,
multi-CUDA wheel matrices, and GPU test gating patterns.

---

## 1. sccache for CUDA compilation caching

sccache wraps `nvcc` and `g++`. Set these before `cmake`:

```bash
export SCCACHE_BUCKET=my-build-cache   # S3 bucket
export SCCACHE_REGION=us-west-2
export CUDAHOSTCXX=/usr/bin/g++        # separate host/device compilation
sccache --start-server
```

In `CMakeLists.txt`:
```cmake
set(CMAKE_CUDA_COMPILER_LAUNCHER sccache)
set(CMAKE_CXX_COMPILER_LAUNCHER  sccache)
```

GitHub Actions — use `mozilla-actions/sccache-action@v0.0.3`.
Cache-hit optimisation: pin compiler versions in Docker, avoid timestamp-dependent
flags, and keep CUDA Toolkit versions consistent across matrix jobs.

---

## 2. auditwheel — manylinux wheel validation

CUDA runtime libraries MUST be excluded from bundling (user provides them):

```bash
auditwheel repair dist/*.whl \
  --exclude libcuda.so.1      \
  --exclude libcudart.so.11.0 \
  --exclude libcudart.so.12.0 \
  --exclude libcublas.so.11   \
  --exclude libcublas.so.12   \
  --exclude libcublasLt.so.11 \
  --exclude libcublasLt.so.12 \
  --exclude libcudnn.so.8     \
  --exclude libnccl.so.2      \
  --plat manylinux2014_x86_64 \
  -w dist/repaired/
```

**Always exclude**: `libcuda`, `libcudart`, `libnvrtc`, `libcublas*`, `libcudnn`,
`libnccl`. **May bundle**: custom CUDA kernels compiled as `.so`.

---

## 3. Multi-CUDA wheel build matrix

Use PEP 440 local version identifiers: `mypackage-0.1.0+cu118-cp310-…whl`

Typical GitHub Actions matrix:
```yaml
strategy:
  matrix:
    cuda: [cu118, cu121, cu124]
    python: ['3.9', '3.10', '3.11', '3.12']
```

CUDA version map: `cu118` → `11.8.0`, `cu121` → `12.1.0`, `cu124` → `12.4.0`.
Use `Jimver/cuda-toolkit@v0.2.11` to install. Inject the `+cuXYZ` suffix before
uploading to avoid overwriting wheels of different CUDA variants.

---

## 4. GPU test gating patterns

### pytest markers (`conftest.py`)

```python
def pytest_runtest_setup(item):
    gpu = _get_gpu_type()   # nvidia-smi --query-gpu=name
    if item.get_closest_marker('gpu') and gpu is None:
        pytest.skip("GPU not available")
    if item.get_closest_marker('h100') and 'H100' not in (gpu or ''):
        pytest.skip("H100 not available")
    if item.get_closest_marker('a100') and 'A100' not in (gpu or ''):
        pytest.skip("A100 not available")
```

Usage:
```python
@pytest.mark.gpu
def test_basic_cuda(): ...

@pytest.mark.h100
def test_h100_fp8(): ...
```

### Self-hosted runner labels

```yaml
jobs:
  test-h100:
    runs-on: [self-hosted, gpu, h100]
  test-a100:
    runs-on: [self-hosted, gpu, a100]
```

---

## 5. Common pitfalls

| Problem | Solution |
|---------|---------|
| auditwheel bundles `libcudart` | Always pass `--exclude libcudart.so.*` |
| Inconsistent CUDA patch versions break sccache | Pin exact versions: `11.8.0` not `11.8` |
| Multiple CUDA variants overwrite each other | Inject `+cu118` suffix before upload |
| GPU tests fail on CPU-only runners | Use pytest markers + skip logic (section 4) |

---

## 6. Constraints respected

- `.ai/constraints/hybrid/python-cpp-build.md` — wheel build patterns
- `.ai/constraints/hybrid/system-deps.md` — CUDA Toolkit discovery
- `.ai/constraints/cpp/cuda-modern.md` — CUDA compilation flags
