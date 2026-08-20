# Development & Collaboration Guidelines for Hybrid Python/C++/CUDA Projects

> **This document defines mandatory contribution standards for hybrid repositories.**
> All contributors (human or AI) must follow these rules.

## Quick Start for Contributors

Before making any changes:

1. **Run `/init` at session start** - Loads relevant constraints based on your work
2. **Create a feature branch** - Never commit directly to protected branches
3. **Follow loaded constraints** - Technical requirements are in `.agents/constraints/`
4. **Run `/pre-commit validate`** - Before committing to check formatting, linting, tests
5. **Open a pull request** - Follow the PR template below

For detailed technical requirements, see `.agents/constraints/python/`, `.agents/constraints/cpp/`, and `.agents/constraints/hybrid/`, then run `/init`.

## 1. General Principles

- Prefer **clarity over cleverness**
- Prefer **explicit decisions over implicit assumptions**
- Prefer **small, reviewable changes over large, opaque ones**
- Never trade correctness or safety for speed
- Follow modern Python (3.10+) and C++ (C++17+) best practices
- Prioritise readability and maintainability
- Respect the FFI boundary - keep Python and C++ concerns separate

If unsure, ask before acting.

## 2. Constraint System

This repository uses a modular constraint system. Instead of duplicating all technical requirements here, detailed constraints are organised in `.agents/constraints/`:

### Python-Specific Constraints
- `python/testing.md` - pytest, coverage (80%+), test organisation
- `python/formatting.md` - ruff (sole formatter, linter, and import sorter), PEP 8, naming conventions
- `python/type-checking.md` - Type hints (mandatory), mypy configuration
- `python/dependencies.md` - poetry-managed dependency workflow
- `python/documentation.md` - Docstrings (Google-style), README, API docs
- `python/error-handling.md` - Exception handling, context managers
- `python/security.md` - Input validation, secrets management

### C++/CUDA-Specific Constraints
- `cpp/testing.md` - GoogleTest, test organisation, GPU test gating
- `cpp/formatting.md` - clang-format, naming conventions
- `cpp/static-analysis.md` - clang-tidy, compiler warnings
- `cpp/dependencies.md` - CMake/CPM-first dependency workflow
- `cpp/documentation.md` - Doxygen, inline comments
- `cpp/error-handling.md` - Exception safety, RAII
- `cpp/memory-safety.md` - Smart pointers, ownership semantics
- `cpp/cuda.md` - CUDA API usage, error checking
- `cpp/cuda-modern.md` - Modern CUDA patterns (Thrust, CUB, cuBLAS)
- `cpp/kernel-correctness.md` - Kernel launch bounds, shared memory, synchronisation
- `cpp/cmake.md` - CMake best practices, target-based configuration

### Hybrid-Specific Constraints
- `hybrid/ffi-boundary.md` - GIL management, DLPack, error propagation
- `hybrid/python-cpp-build.md` - scikit-build-core, PyTorch ABI, manylinux wheels
- `hybrid/system-deps.md` - CUDA Toolkit, cuDNN, NCCL, TensorRT discovery

### Common Constraints (All Projects)
- `common/git-workflow.md` - Branch policy, commit conventions, PR guidelines
- `common/roadmap-awareness.md` - Roadmap execution discipline
- `common/session-discipline.md` - Session continuity, decision hygiene
- `common/agentic-team.md` - Parallel agent launch policy

### Loading Constraints Automatically

At the start of every session, run:

```bash
/init
```

This skill will:
- Detect project profile (hybrid Python/C++/CUDA)
- Check for active roadmaps
- Analyse git status and modified files
- Load only relevant constraints based on your current work
- Warn if you're on a protected branch
- Run capability audit (plugins, skills, integrations)

See AGENTS.md for details on the constraint system and authority hierarchy.

## 3. Branching and Commits

### Protected Branches

**ABSOLUTE PROHIBITION**: Never commit directly to:
- `master` or `main`
- `develop`
- `release/*`
- `hotfix/*`

Always work on feature branches: `feat/<description>`, `fix/<description>`, etc.

### Master PR/MR Policy

A PR/MR targeting `master` may originate only from same-repository `release/*` or `hotfix/*`; `develop` is categorically invalid because its required tooling cannot pass the presence-based tree check. An ordinary release MUST be created from a recorded `develop` SHA and may contain only deletions of master-forbidden paths relative to that SHA. `develop` MUST NOT merge from or rebase onto `master`. Prefer the same develop-to-release path for urgent fixes. Reserve a master-origin `hotfix/*` for emergencies where `develop` has diverged too far, record its reduced local validation, and return its functional fix to `develop` through a reviewed merge or cherry-pick PR, never through rebase.

### Commit Message Format

```
<type>(optional-scope): <short summary>

[optional body]
```

Types: `feat`, `fix`, `refactor`, `perf`, `docs`, `test`, `chore`, `style`, `build`

Rules:
- Less than 72 characters
- Imperative mood ("add", not "added")
- ASCII-only characters
- British English spelling
- NO AI attribution (no `Co-Authored-By:` lines)

See `.agents/constraints/common/git-workflow.md` for detailed commit conventions.

## 4. Pull Request Guidelines

### PR Title

Follow commit message format:
```
<type>(optional-scope): <short description>
```

### PR Description Template

```markdown
## Summary
Brief description of what this PR does (2-3 sentences).

## Motivation
Why is this change necessary? What problem does it solve?

## Changes
- Bullet list of key changes
- New modules/functions/kernels added
- Modified interfaces
- Deprecated functionality

## Testing
- Python unit tests added/modified (pytest)
- C++/CUDA unit tests added/modified (GoogleTest)
- GPU tests gated with appropriate markers
- Test coverage: X%
- How to verify the changes

## Dependencies
- New Python packages added (with versions in pyproject.toml)
- New C++ packages added (with pinned versions in cmake/Dependencies.cmake)
- Updated packages

## Performance
- Benchmark results (if applicable)
- GPU memory usage
- Kernel launch overhead

## Breaking Changes
- List any breaking changes
- Migration guide (if needed)

## Related
- Related issues: #123, #456
- Related PRs

## Master Promotion (master-bound PRs only)
Develop-Source-SHA:
Hotfix-Validation-Tradeoff:
```

### Before Opening a PR

For a PR/MR targeting `master`, confirm all of the following before requesting review:
- The source is same-repository `release/v<MAJOR>.<MINOR>.<PATCH>` or `hotfix/v<MAJOR>.<MINOR>.<PATCH>`; it is not `develop`.
- The complete source tree contains no development-stage paths; only `docs/changelog/` may exist below `docs/`.
- A release PR records `Develop-Source-SHA` and differs from that SHA only by forbidden-path deletions.
- A hotfix PR records `Hotfix-Validation-Tradeoff`, including checks run and omissions.
- `master-merge-gate` and profile validation are configured as required hosted checks.
- A normal promotion uses a validated `release/v<MAJOR>.<MINOR>.<PATCH>` buffer branch, and a master-origin hotfix has a reviewed back-merge plan for `develop`.
- The branch version equals the authoritative manifest version at the recorded source commit, carries no pre-release or build suffix, and is strictly greater than the version on `master`.

Run the pre-commit validation:

```bash
/pre-commit validate
```

This checks:
- Python formatting (`ruff format --check`)
- Python linting and import order (`ruff check`)
- Python type checking (mypy)
- C++ formatting (`clang-format --dry-run`)
- C++ static analysis (`clang-tidy`)
- Python tests (pytest)
- C++/CUDA tests (ctest)
- Coverage threshold

## 5. Development Environment Setup

### Prerequisites

- Python 3.10+ with Poetry
- C++17-compatible compiler (GCC 9+, Clang 10+, MSVC 2019+)
- CMake 3.24+
- CUDA Toolkit 11.8+ (if building GPU extensions)
- Optional: cuDNN, NCCL, TensorRT (for specific features)

### Initial Setup

```bash
# Install Python dependencies
poetry install

# Configure native CMake build
CUDA_HOME=/usr/local/cuda \
TORCH_CUDA_ARCH_LIST="8.0;8.6;8.9;9.0" \
cmake -S . -B build -G Ninja -DCMAKE_BUILD_TYPE=RelWithDebInfo -DPROJECT_ENABLE_PYTHON=ON

# Build C++/CUDA extensions
cmake --build build -j

# Run native tests
ctest --test-dir build --output-on-failure

# Expose the CMake-governed project to Python
poetry run pip install -e . --no-build-isolation

# Run Python tests
poetry run pytest tests/python/
```

### Using Agent Commands

The repository provides `.agents/bin/agent-*` commands for common workflows:

```bash
# Full build (setup + compile + test)
.agents/bin/agent-build full

# Just compile
.agents/bin/agent-build compile

# Run pre-commit checks
.agents/bin/agent-precommit

# Add Python dependency
.agents/bin/agent-dependency add numpy ">=1.24.0"

# Add C++ dependency (via CPM)
.agents/bin/agent-dependency add fmtlib/fmt 10.2.1
```

## 6. Testing Requirements

### Python Tests

- Use pytest for all Python tests
- Minimum 80% code coverage
- Place tests in `tests/python/`
- Use descriptive test names: `test_<function>_<scenario>_<expected>`
- Use fixtures for common setup
- Mock external dependencies

Example:
```python
import pytest
from mypackage import compute

def test_compute_with_valid_input_returns_correct_result():
    result = compute([1, 2, 3])
    assert result == 6

@pytest.mark.gpu
def test_compute_on_gpu_matches_cpu():
    cpu_result = compute([1, 2, 3], device='cpu')
    gpu_result = compute([1, 2, 3], device='cuda')
    assert cpu_result == gpu_result
```

### C++/CUDA Tests

- Use GoogleTest for all C++/CUDA tests
- Place tests in `tests/cpp/`
- Use descriptive test names: `TEST(TestSuite, TestName)`
- Check CUDA errors after every kernel launch
- Gate GPU tests with runtime checks

Example:
```cpp
#include <gtest/gtest.h>
#include "mypackage/kernel.hpp"

TEST(KernelTest, ComputeWithValidInputReturnsCorrectResult) {
    std::vector<float> input = {1.0f, 2.0f, 3.0f};
    float result = compute_kernel(input);
    EXPECT_FLOAT_EQ(result, 6.0f);
}

TEST(KernelTest, ComputeOnGPUMatchesCPU) {
    if (!torch::cuda::is_available()) {
        GTEST_SKIP() << "CUDA not available";
    }
    // GPU test logic
}
```

### GPU Test Gating

Use pytest markers to gate GPU tests:

```python
@pytest.mark.gpu  # Requires any GPU
@pytest.mark.h100  # Requires H100
@pytest.mark.a100  # Requires A100
```

Run GPU tests selectively:
```bash
# Run all tests
pytest

# Run only GPU tests
pytest -m gpu

# Run only H100 tests
pytest -m h100

# Skip GPU tests
pytest -m "not gpu"
```

## 7. Code Style

### Python

- Follow PEP 8
- Use ruff for formatting, linting, and import sorting
- Maximum line length: 100 characters
- Use type hints on all public functions
- Use Google-style docstrings

### C++

- Follow C++ Core Guidelines
- Use clang-format with project configuration
- Maximum line length: 100 characters
- Use Doxygen-style comments for public APIs
- Prefer `snake_case` for functions, `PascalCase` for classes

### CUDA

- Follow NVIDIA CUDA C++ Programming Guide
- Use `__device__`, `__host__`, `__global__` annotations explicitly
- Check errors after every CUDA API call
- Use `cudaGetLastError()` after kernel launches
- Prefer Thrust/CUB over raw CUDA when possible

## 8. FFI Boundary Guidelines

### GIL Management

Release the GIL for long-running C++/CUDA operations:

```python
# nanobind
m.def("compute", [](nb::ndarray<double> data) {
    nb::gil_scoped_release release;
    // Long computation - GIL released
    return expensive_cuda_kernel(data.data());
});
```

### Error Propagation

Always convert C++ exceptions to Python exceptions:

```cpp
m.def("risky_operation", []() {
    try {
        cuda_kernel_that_might_fail();
    } catch (const std::runtime_error& e) {
        throw nb::runtime_error(e.what());
    }
});
```

### Zero-Copy Tensor Exchange

Use DLPack for zero-copy tensor exchange:

```python
import torch
tensor = torch.randn(1000, 1000, device='cuda')
capsule = torch.utils.dlpack.to_dlpack(tensor)
result = my_extension.process_dlpack(capsule)
```

## 9. Dependency Management

### Python Dependencies

- Use Poetry for all Python dependencies
- Pin exact versions in `poetry.lock`
- Use version ranges in `pyproject.toml`
- Separate dev dependencies with `--group dev`

```bash
# Add runtime dependency
.agents/bin/agent-dependency add numpy

# Add dev dependency
.agents/bin/agent-dependency add pytest --dev

# The wrapper updates and validates pyproject.toml plus poetry.lock
```

### C++ Dependencies

- Use CPM in `cmake/Dependencies.cmake` for lightweight C++ source dependencies
- Pin every dependency by immutable tag, commit, or archive hash
- Record reason, linked CMake target, licence note, and scope
- CUDA/cuDNN/NCCL/TensorRT are discovered as external system SDKs

```cmake
CPMAddPackage(
  NAME fmt
  GITHUB_REPOSITORY fmtlib/fmt
  GIT_TAG 10.2.1
)

find_package(CUDAToolkit REQUIRED)

target_link_libraries(mylib PRIVATE fmt::fmt CUDA::cudart)
```

## 10. Documentation

### Python Docstrings

Use Google-style docstrings:

```python
def compute(data: list[float], device: str = 'cpu') -> float:
    """Compute the sum of elements.

    Args:
        data: Input data as a list of floats.
        device: Device to run on ('cpu' or 'cuda').

    Returns:
        Sum of all elements.

    Raises:
        ValueError: If device is not 'cpu' or 'cuda'.
    """
    pass
```

### C++ Documentation

Use Doxygen-style comments:

```cpp
/**
 * @brief Compute the sum of elements on GPU.
 *
 * @param data Input data pointer (device memory).
 * @param size Number of elements.
 * @return Sum of all elements.
 *
 * @throws std::runtime_error if CUDA kernel fails.
 */
float compute_kernel(const float* data, size_t size);
```

## 11. Performance Considerations

### Python

- Use NumPy/PyTorch for numerical operations
- Avoid Python loops for large arrays
- Profile with `cProfile` or `py-spy`
- Use `@functools.lru_cache` for expensive pure functions

### C++/CUDA

- Profile with `nvprof` or Nsight Systems
- Minimise host-device transfers
- Use pinned memory for faster transfers
- Coalesce global memory accesses
- Maximise occupancy (check with `--ptxas-options=-v`)
- Use shared memory for frequently accessed data

## 12. Security

### Python

- Never use `eval()` or `exec()` on untrusted input
- Never use `shell=True` with user-controlled input
- Validate all external input
- Use `secrets` module for cryptographic randomness

### C++/CUDA

- Validate array bounds before access
- Use smart pointers to prevent memory leaks
- Check CUDA API return codes
- Sanitise file paths before opening

## 13. Wheel Distribution

### Building Wheels

```bash
# Build wheel for current platform
poetry build

# Build manylinux wheel with CUDA 12.1
docker run --rm -v $(pwd):/io \
  quay.io/pypa/manylinux2014_x86_64 \
  /io/scripts/build-wheel.sh cu121
```

### Wheel Naming Convention

Use PEP 440 local version identifiers:

```
mypackage-0.1.0+cu118-cp39-cp39-manylinux2014_x86_64.whl
mypackage-0.1.0+cu121-cp310-cp310-manylinux2014_x86_64.whl
```

### auditwheel

Always exclude CUDA runtime libraries:

```bash
auditwheel repair dist/*.whl \
  --exclude libcuda.so.1 \
  --exclude libcudart.so.11.0 \
  --exclude libcudart.so.12.0 \
  --plat manylinux2014_x86_64 \
  -w dist/repaired/
```

## 14. Versioning and Releases

Follow Semantic Versioning (semver.org):
```
<MAJOR>.<MINOR>.<PATCH>
```

- **MAJOR**: Incompatible API changes
- **MINOR**: Backward-compatible functionality additions
- **PATCH**: Backward-compatible bug fixes

The root `CMakeLists.txt` is the authoritative version manifest, because CMake
owns the native build graph under the C++ First policy. `pyproject.toml` MUST
declare the identical version; a disagreement is a hard gate failure, because
the wheel and the native artefact would otherwise claim different versions.

Update all of these in the same reviewed pull request:
- `project(... VERSION ...)` in the root `CMakeLists.txt`
- `[project].version`, or `[tool.poetry].version`, in `pyproject.toml`
- `__version__` in the Python package `__init__.py`
- `CHANGELOG.md`

Release naming is derived from that version, never typed by hand:

| Artefact | Name |
|---|---|
| Release shim branch | `release/v<MAJOR>.<MINOR>.<PATCH>` |
| Deletion-only staging branch | `chore/release-v<MAJOR>.<MINOR>.<PATCH>` |
| Hotfix branch | `hotfix/v<MAJOR>.<MINOR>.<PATCH>` |
| Tag on the merged `master` commit | `release-v<MAJOR>.<MINOR>.<PATCH>` |

Bump the version on `develop` **before** selecting the release source commit. A
release tree may differ from its source commit only by deleting development-stage
paths, so a bump made after the cut would violate that invariant. A promoted
version carries no `-dev`, `-rc`, or `+build` suffix and MUST be strictly greater
than the version currently on `master`. The `master-merge-gate` enforces all of
this; see `.agents/constraints/common/master-merge-policy.md` section 8.

Keep promotions cheap without weakening the gate (section 9 of the same
policy): bump the version in the same pull request as the change it describes
rather than in a dedicated bump PR; batch reviewed `develop` merges into
release trains instead of promoting every merge; rehearse locally with
`poetry run python .github/scripts/master-merge-gate.py --rehearse` before
cutting any release ref; and satisfy the release-PR validation requirement by provenance of
the validated source SHA instead of a rebuild where the gate is configured with
`REQUIRED_SOURCE_CHECKS`. The staging PR needs only the deletion-only
projection check, never a rebuild.

## 15. Continuous Integration

### Required Checks

- Python formatting (ruff)
- Python linting (ruff)
- Python type checking (mypy)
- C++ formatting (clang-format)
- C++ static analysis (clang-tidy)
- Python tests (pytest)
- C++/CUDA tests (ctest)
- Coverage report (80%+ required)

Exception: for an identity-proved release PR and its deletion-only staging PR,
the promotion rules in section 14 apply instead -- the required validation
status may be satisfied by verified provenance of the validated source SHA,
and the staging PR runs the deletion-only projection check rather than a
rebuild (`.agents/constraints/common/master-merge-policy.md` section 9).

### GPU CI

- Use self-hosted runners with GPUs or cloud GPU instances
- Gate GPU tests with `@pytest.mark.gpu`
- Build multi-CUDA wheel matrix (cu118, cu121, cu124)
- Cache CUDA compilation with sccache

## 16. Getting Help

- Check `.agents/constraints/` for detailed technical requirements
- Run `/init` to load relevant constraints
- Run `/check-constraints` to verify compliance
- Open an issue for questions or clarifications
- Tag maintainers for urgent reviews

## 17. License

[Specify your license here]

## 18. Code of Conduct

[Specify your code of conduct here or link to one]
