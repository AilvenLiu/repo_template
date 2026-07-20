---
name: build
description: Run or troubleshoot the repository-owned build workflow for Python, C++/CUDA, or hybrid projects. Use for environment setup, compilation, tests, full builds, build diagnosis, or cleaning build outputs while preserving the declared build authority.
---

# build — build orchestration

> Canonical repository skill. Codex discovers it natively from `.agents/skills/`;
> Claude Code reaches it through the matching `.claude/skills/` delegate.

Automates the full build lifecycle for Python, C++/CUDA, and hybrid projects.

## Execution

```bash
.agents/bin/agent-build <setup|compile|test|full|doctor|clean>
```

## Subcommands

- `setup` — configure the declared Poetry environment and/or native toolchain
- `compile` — compile C++ (no-op for Python)
- `test` — run test suite
- `full` — setup + compile + test
- `clean` — remove build artefacts
- `doctor` — diagnose build environment issues

## Behaviour (guaranteed)

1. Detects project type via shared `project_type.py`.
2. Python: Poetry install, pytest.
3. C++: direct CMake configure with Ninja, build, then `ctest`.
4. Hybrid: direct CMake configure/build/test first, then scikit-build-core editable install through Poetry.

## Behaviour (best-effort)

- Mixed Python+C++ projects beyond scikit-build-core.
- Cross-compilation and parallel build flags.
- Tool installation guidance when compilers/tools are missing.
