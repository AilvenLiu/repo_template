---
name: build
description: "Orchestrate build workflows. Environment setup, compilation, and testing."
---

# /build

Automates the full build lifecycle for Python and C++ projects.

## Commands

- `/build setup` — create venv / install deps / configure toolchain
- `/build compile` — compile C++ (no-op for Python)
- `/build test` — run test suite
- `/build full` — setup + compile + test
- `/build clean` — remove build artifacts
- `/build doctor` — diagnose build environment issues

## Behaviour (guaranteed)

1. Detects project type via shared `project_type.py`.
2. Python: Poetry install, pytest.
3. C++: Conan install, CMake configure + build, ctest.

## Behaviour (best-effort)

- Mixed Python+C++ projects (builds C++ extensions then installs Python).
- Cross-compilation and parallel build flags.
- Tool installation guidance when compilers/tools are missing.

## Execution

Prefer the shared wrapper when invoking build work directly:

```bash
bin/agent-build <setup|compile|test|full|doctor|clean>
```
