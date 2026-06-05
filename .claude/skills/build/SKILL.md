---
name: build
description: "Orchestrate build workflows. Environment setup, compilation, and testing."
---

# /build

Build orchestration for Python, C++/CUDA, hybrid (scikit-build-core), and Bazel projects.

## Execution

```bash
bin/agent-build <setup|compile|test|full|doctor|clean>
```

## Subcommands

| Subcommand | What it does |
|------------|--------------|
| `setup` | Create venv / install deps / configure toolchain |
| `compile` | Compile C++/CUDA extensions (no-op for pure Python) |
| `test` | Run test suite |
| `full` | `setup` + `compile` + `test` |
| `doctor` | Diagnose environment issues (missing tools, wrong versions) |
| `clean` | Remove build artefacts (`build/`, `dist/`, `__pycache__`) |

## Behaviour (guaranteed)

1. Detects project type via `.ai/project.yml` / heuristics.
2. **Python**: `poetry install --with dev`, then `poetry run pytest`.
3. **C++**: `conan install .`, `cmake -B build`, `cmake --build build`, `ctest`.
4. **Hybrid** (scikit-build-core): `pip install -e . --no-build-isolation` inside the Poetry venv, then `pytest`.
5. **Bazel**: `bazel build //...`, `bazel test //...` (delegates to `/bazel`).

## Behaviour (best-effort)

- Mixed Python+C++ projects beyond scikit-build-core.
- Cross-compilation and parallel build flags.
- Tool installation guidance when compilers/tools are missing.

## Common workflow

```bash
# First time or after dependency changes
/build setup

# After editing C++/CUDA source
/build compile

# Run tests only (deps already installed)
/build test

# Full clean build
/build full

# Debug a broken environment
/build doctor
```
