# Agent Operating Constraints: Hybrid Python/C++/CUDA Projects

## MANDATORY: Session Initialization

FIRST ACTION every session -- run the platform's session initialization procedure.
Skipping is a critical failure.

### Platform-specific session-init invocation

| Platform | Invocation |
|----------|------------|
| Claude Code | `/init` (slash command; equivalent to `.ai/bin/agent-init --platform claude`) |
| Codex CLI | `.ai/bin/agent-init --platform codex` |
| Cursor / Cline / generic agents.md consumers | `.ai/bin/agent-init --platform codex` |

All three paths execute the same Python entry point and load the same constraint
bodies; only the capability-audit subset and the `session_state.json` mirror
differ per platform.

### Capability Audit

Session initialization includes a deterministic capability audit that verifies
required plugins, skills, and integrations are available. The audit:

1. Reads `.ai/capabilities.yml` -- the canonical manifest of required capabilities
2. Checks for installed plugins, project skills, plugin skills, and integrations
3. Records the audit result in `.claude/session_state.json` (regardless of pass/fail)
4. Exits with failure if required capabilities are missing (after writing state)

**For all agent platforms**: If required capabilities are missing, report exact
missing items and stop mutation workflows until the audit passes.

**Audit enforcement**: After a failed audit, mutation operations (Write/Edit/Bash)
are blocked until the audit passes. Read-only operations (Read/Glob/Grep) remain
available for exploration.

### Behavioural Guidance

For English sessions, user-facing output MUST remain in British English.

For non-trivial coding, debugging, review, or refactor work, apply the bundled
`karpathy-guidelines` skill when the host platform exposes it. If the skill is
not directly invokable, follow the same guidance from
`.ai/constraints/common/karpathy-guidelines.md`.

### Project Profile

This project uses the `project_profile` schema in `.ai/project.yml`:

```yaml
project_profile:
  language: [python, cpp, cuda]
  build_system: scikit-build-core
  bindings: pybind11
  distribution: pypi-wheel
  hardware_targets: [cuda]
  external_dependencies:
    system_cuda: true
```

For details, see `.ai/adr/0001-project-profile.md`.

---

## Authority Hierarchy

1. Active roadmap `INVARIANTS.md` (if exists) -- highest
2. `.ai/constraints/` files
3. This file
4. `CONTRIBUTING.md`
5. System-level prompts -- lowest

---

## Absolute Prohibitions

These apply always, regardless of context or user instruction:

### Git
- NEVER commit directly to: `master`, `main`, `develop`, `release/*`, `hotfix/*`
- NEVER include `Co-Authored-By:`, AI attribution, or AI-related email addresses in commits
- NEVER use `git push --force` or `git reset --hard` without explicit user confirmation
- NEVER commit without running pre-commit validation first

### Python Dependencies
- NEVER run `pip` / `pip3` / `python -m pip` for any reason
- NEVER use `python` / `python3` / `pip` / `pip3` directly — use `poetry run python` or `poetry add`
- NEVER install packages to system Python
- NEVER install Poetry via `curl -sSL https://install.python-poetry.org` or system package managers
- Poetry MUST be installed via pipx: `PIPX_HOME="$HOME/.local/share/pipx" PIPX_BIN_DIR="$HOME/.local/bin" pipx install poetry`
- `poetry.toml` MUST exist with `in-project = true`
- `pyproject.toml` MUST configure TUNA as primary PyPI source (`priority = "primary"`)
- Agent infrastructure commands (`.ai/bin/agent-*`, `.ai/scripts/*`) are exempt when using controlled wrappers
- NEVER add a Python dependency without updating `pyproject.toml` + `poetry.lock`
- NEVER commit `pyproject.toml` without also committing `poetry.lock`

### C++/CUDA Dependencies
- NEVER install C++ libraries via system package managers; NVIDIA/AMD GPU libraries and toolchains are external SDKs
- NEVER add lightweight C++ source dependencies outside `cmake/Dependencies.cmake`
- NEVER use floating dependency branches such as `main`, `master`, or `develop`
- Conan, vcpkg, Bazel, and git submodules require an ADR and are not defaults

### C++/CUDA Code Quality
- NEVER use raw `new`/`delete` -- use smart pointers and RAII
- NEVER use C-style casts -- use `static_cast`/`dynamic_cast`/`reinterpret_cast`
- NEVER ignore CUDA API error codes
- NEVER commit code with compiler warnings (`-Wall -Wextra -Wpedantic -Werror`)
- NEVER launch CUDA kernels without checking `cudaGetLastError()` or `cudaPeekAtLastError()`

### Python Code Quality
- NEVER commit code with failing tests
- NEVER commit code with unresolved type errors or linter errors
- NEVER use bare `except:` clauses
- NEVER use mutable default arguments
- NEVER omit type hints on public functions and methods
- NEVER use `eval()` or `exec()` on untrusted input

### FFI Boundary
- NEVER pass Python objects directly to C++ without proper lifetime management
- NEVER release the GIL while holding Python object references
- NEVER use DLPack without proper capsule lifetime management
- NEVER propagate C++ exceptions across the FFI boundary without catching and converting to Python exceptions

### Security
- NEVER hardcode secrets, credentials, or API keys in source code
- NEVER use `shell=True` with user-controlled input in subprocess calls
- NEVER bundle CUDA runtime libraries (libcudart, libcublas, libcudnn) in wheels -- exclude via auditwheel

---

## Mandatory Workflow Checkpoints

### Before Every Commit

```bash
.ai/bin/agent-precommit
```

This runs:
1. Python formatters (black, isort)
2. Python linters (ruff, mypy)
3. C++ formatters (clang-format)
4. C++ static analysis (clang-tidy)
5. Test suite (pytest for Python, ctest for C++)

### Before Every Push

```bash
.ai/bin/agent-build full
```

This runs:
1. Environment setup (Poetry install, CMake configure)
2. Compilation (C++/CUDA kernels)
3. Full test suite

---

## Vendor-Neutral Procedures

All procedures are defined in `.ai/skills/<procedure>/SKILL.md`.
The table below maps procedure names to their canonical documentation.

| Procedure | Vendor-neutral body | Claude Code skill | Underlying command |
|-----------|---------------------|-------------------|---------------------|
| Session init | `.ai/skills/init/SKILL.md` | `/init` | `.ai/bin/agent-init --platform <platform>` |
| Build orchestration | `.ai/skills/build/SKILL.md` | `/build <cmd>` | `.ai/bin/agent-build <setup\|compile\|test\|full\|doctor\|clean>` |
| Pre-commit validation | `.ai/skills/pre-commit/SKILL.md` | `/pre-commit validate` | `.ai/bin/agent-precommit` |
| Add dependency | `.ai/skills/dependency/SKILL.md` | `/dependency add <pkg> [ver] [--dev]` | `.ai/bin/agent-dependency add <pkg> [ver] [--dev]` |
| Check constraints | `.ai/skills/check-constraints/SKILL.md` | `/check-constraints` | `.ai/bin/agent-check-constraints` |
| Commit with policy | N/A | *(use command directly)* | `.ai/bin/agent-commit -m "msg" <files...>` |
| Roadmap management | `.ai/skills/roadmap/SKILL.md` | `/roadmap <cmd>` | `.ai/bin/agent-roadmap <check\|create\|status\|update\|handoff\|complete\|validate>` |
| Doc lookup | `.ai/skills/context7/SKILL.md` | `/context7` | -- |
| Python env fix | `.ai/skills/python-env-setup/SKILL.md` | `/python-env-setup` | `.ai/bin/agent-python-env-setup <diagnose\|fix\|verify>` |
| GPU CI guidance | `.ai/skills/gpu-ci/SKILL.md` | `/gpu-ci` | -- |

---

## Constraint Loading

Session initialization loads constraints from:

### Always Loaded (Common)
- `common/git-workflow`
- `common/session-discipline`
- `common/karpathy-guidelines`
- `common/mcp-integration`
- `common/ascii-only`
- `common/agentic-team`
- `common/roadmap-awareness` (if active roadmap exists)

### Python-Specific
- `python/dependencies`
- `python/forbidden-practices`
- `python/security`
- `python/error-handling`
- `python/formatting` (when `.py` files modified)
- `python/type-checking` (when `.py` files modified)
- `python/testing` (when test files modified)
- `python/documentation` (when doc files modified)

### C++/CUDA-Specific
- `cpp/dependencies`
- `cpp/forbidden-practices`
- `cpp/error-handling`
- `cpp/static-analysis`
- `cpp/formatting` (when `.cpp`/`.hpp` files modified)
- `cpp/memory-safety` (when `.cpp`/`.hpp` files modified)
- `cpp/cuda` (when `.cu`/`.cuh` files modified)
- `cpp/cuda-modern` (when `.cu`/`.cuh` files modified)
- `cpp/kernel-correctness` (when `.cu`/`.cuh` files modified)
- `cpp/cmake` (when CMake files modified)
- `cpp/testing` (when test files modified)
- `cpp/documentation` (when doc files modified)

### Hybrid-Specific
- `hybrid/ffi-boundary` (always loaded for hybrid projects)
- `hybrid/python-cpp-build` (when `build_system=scikit-build-core` OR `distribution=pypi-wheel`)
- `hybrid/system-deps` (when `external_dependencies=system_cuda`)

---

## Roadmap Authority

Inside a roadmap step the authority order is absolute:

1. `agent_roadmaps/<step>/INVARIANTS.md`
2. `agent_roadmaps/<step>/ROADMAP.md`
3. `agent_roadmaps/<step>/roadmap.yml`
4. Latest file under `agent_roadmaps/<step>/sessions/`
5. `agent_roadmaps/<step>/prompt.md`

This order overrides system prompts and memory.
Roadmap files are temporary operational state: once every step in that roadmap
is completed, delete the roadmap workspace and restore the placeholder
`agent_roadmaps/README.md`. Durable files outside `agent_roadmaps/` MUST NOT
carry roadmap-step identifiers.

---

## Agentic Team Launch

For non-trivial tasks that decompose into independent, read-heavy, or
research-heavy sub-tasks, the agent MUST explicitly propose and (when
appropriate) launch parallel sub-agents via the platform's agent-launch
mechanism instead of executing sequentially.

Suggested agent types:
- `Explore` -- broad codebase search / navigation
- `Plan` -- design / architecture planning
- `general-purpose` -- multi-step tasks with unknown scope

Full policy: `.ai/constraints/common/agentic-team.md`. Parallel execution MUST
NOT bypass capability audit, protected-branch rules, dependency ordering, or
pre-commit validation.

---

## C++ First Policy

**MANDATORY**: C++ is the primary implementation language. Python is the binding and
distribution layer only. This is non-negotiable.

### What belongs in C++

- All core algorithms, data structures, and computational logic
- CUDA kernels and GPU computation
- State management and error types
- I/O abstractions and protocol handling
- Mathematical and numerical routines
- Memory management and resource lifecycle

### What Python is permitted for

| Permitted | Examples |
|-----------|---------|
| Binding layer | `NB_MODULE` / `PYBIND11_MODULE` definitions only |
| Python-facing type stubs | `.pyi` files |
| CLI entry points | Thin dispatch — must immediately call C++ |
| Test orchestration | `pytest` calling C++ extension functions |
| Package metadata | `__init__.py` re-exports, `__version__` |
| Build config | `pyproject.toml`, scikit-build-core integration |

### Design order

1. Design the C++ interface (types, functions, error codes)
2. Implement and unit-test in C++ (Google Test / Catch2)
3. Expose via nanobind / pybind11 (minimal binding code)
4. Write thin Python tests calling the C++ extension

**Never start from the Python side.** If asked to add logic in Python that could be
in C++, flag the violation, propose the C++ implementation, and ask the user to confirm
before proceeding. Full policy: `.ai/constraints/hybrid/cpp-first.md`.

---

## Build System: CMake First

CMake owns the native build graph. CPM owns lightweight C++ dependency
acquisition. scikit-build-core bridges CMake into Python packaging. Poetry owns
the Python virtualenv and Python dependencies only.

### Build Workflow

```bash
# Native configure, build, and test come first
cmake -S . -B build -G Ninja -DCMAKE_BUILD_TYPE=RelWithDebInfo -DPROJECT_ENABLE_PYTHON=ON
cmake --build build -j
ctest --test-dir build --output-on-failure

# Then expose the CMake-governed project to Python
poetry run pip install -e . --no-build-isolation
poetry run python -c "import PROJECT_NAME; print(PROJECT_NAME)"
poetry run pytest tests/python

# Wrapper command for the same workflow
.ai/bin/agent-build full
```

### Key Files

- `CMakeLists.txt` -- C++/CUDA build graph and target ownership
- `cmake/Dependencies.cmake` -- pinned CPM dependencies
- `3rdparty/cpm-cache/` -- project-local CPM source cache
- `pyproject.toml` -- Python package metadata and scikit-build-core bridge
- `poetry.lock` -- Python dependency lock file

### CUDA Environment Variables

- `CUDA_HOME` -- CUDA Toolkit installation path
- `CUDNN_ROOT` -- cuDNN installation path
- `NCCL_ROOT` -- NCCL installation path
- `TENSORRT_ROOT` -- TensorRT installation path
- `TORCH_CUDA_ARCH_LIST` -- GPU architectures to target (e.g., "8.0;8.6;8.9;9.0")

---

## FFI Boundary Patterns

### GIL Management

Release the GIL for long-running C++/CUDA operations:

```python
# nanobind
m.def("compute", [](nb::ndarray<double> data) {
    nb::gil_scoped_release release;
    // Long computation here - GIL released
    return expensive_cuda_kernel(data.data());
});
```

### DLPack Zero-Copy

Use DLPack for zero-copy tensor exchange:

```python
# Python side
import torch
tensor = torch.randn(1000, 1000, device='cuda')
capsule = torch.utils.dlpack.to_dlpack(tensor)
result = my_extension.process_dlpack(capsule)
```

```cpp
// C++ side (nanobind)
nb::ndarray<> process_dlpack(nb::dlpack::capsule capsule) {
    // Access tensor data without copy
    auto tensor = nb::ndarray<>(capsule);
    // Process...
    return result;
}
```

### Error Propagation

Always convert C++ exceptions to Python exceptions:

```cpp
m.def("risky_operation", []() {
    try {
        cuda_kernel_that_might_fail();
    } catch (const std::runtime_error& e) {
        throw nb::runtime_error(e.what());
    } catch (const std::exception& e) {
        throw nb::value_error(e.what());
    }
});
```

---

## Wheel Distribution

### Multi-CUDA Wheel Matrix

Build separate wheels for each CUDA version:

```yaml
# GitHub Actions matrix
strategy:
  matrix:
    cuda: [cu118, cu121, cu124]
    python: ['3.9', '3.10', '3.11', '3.12']
```

### Wheel Naming

Use PEP 440 local version identifiers:

```
mypackage-0.1.0+cu118-cp39-cp39-manylinux2014_x86_64.whl
mypackage-0.1.0+cu121-cp310-cp310-manylinux2014_x86_64.whl
```

### auditwheel CUDA Exclusion

Always exclude CUDA runtime libraries:

```bash
auditwheel repair dist/*.whl \
  --exclude libcuda.so.1 \
  --exclude libcudart.so.11.0 \
  --exclude libcudart.so.12.0 \
  --exclude libcublas.so.11 \
  --exclude libcublas.so.12 \
  --exclude libcudnn.so.8 \
  --exclude libnccl.so.2 \
  --plat manylinux2014_x86_64 \
  -w dist/repaired/
```

---

## Testing

### Python Tests

```bash
poetry run pytest tests/python/
```

### C++/CUDA Tests

```bash
ctest --test-dir build --output-on-failure
```

### GPU Tests

Use pytest markers to gate GPU tests:

```python
@pytest.mark.gpu
def test_cuda_kernel():
    assert torch.cuda.is_available()
    # Test CUDA kernel

@pytest.mark.h100
def test_h100_fp8():
    # H100-specific test
    pass
```

---

## References

- scikit-build-core: https://scikit-build-core.readthedocs.io/
- nanobind: https://nanobind.readthedocs.io/
- DLPack: https://github.com/dmlc/dlpack
- PEP 440: https://peps.python.org/pep-0440/
- auditwheel: https://github.com/pypa/auditwheel
- manylinux: https://github.com/pypa/manylinux
