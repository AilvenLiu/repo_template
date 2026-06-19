# build — build orchestration

> Vendor-neutral procedure description. Claude Code dispatches `/build` to this
> body via the stub at `.claude/skills/build/SKILL.md`. Codex / Cursor / Cline
> consult this file directly via the AGENTS.md procedures table.

Automates the full build lifecycle for Python, C++/CUDA, and hybrid projects.

## Execution

```bash
.ai/bin/agent-build <setup|compile|test|full|doctor|clean>
```

## Subcommands

- `setup` — create venv / install deps / configure toolchain
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
