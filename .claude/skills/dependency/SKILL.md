---
name: dependency
description: "Add dependencies. Poetry for Python (mandatory), Conan/vcpkg for C++."
---

# /dependency

Add a project dependency. Handles Python (Poetry) and C++ (Conan/vcpkg/FetchContent)
projects, including hybrid projects where both apply.

## Execution

```bash
bin/agent-dependency add <package> [version] [--dev]
```

## Behaviour (guaranteed)

1. Detects project type via `.ai/project.yml` / heuristics.
2. **Python**: runs `poetry add <package>` (or `poetry add --group dev <package>` with `--dev`).
   - Configures in-project virtualenv (`.venv/`) if not already done.
   - Removes external Poetry venvs and recreates in-project when found.
   - Updates both `pyproject.toml` and `poetry.lock`.
3. **C++**: appends the library to `conanfile.txt` and adds `find_package()` to `CMakeLists.txt`.
4. Prints a reminder to update `README.md` and commit both manifest and lock files.

## Behaviour (best-effort)

- For trivial Python projects (`requirements.txt` only): uses `pip install` and warns to migrate to Poetry.
- Runs `conan install` after adding a C++ dependency (requires network and Conan installed).

## Absolute prohibitions

| Forbidden | Correct alternative |
|-----------|---------------------|
| `pip install <pkg>` | `bin/agent-dependency add <pkg>` |
| `poetry add <pkg>` directly | `bin/agent-dependency add <pkg>` |
| Manual `requirements.txt` edit | `bin/agent-dependency add <pkg>` |
| `apt install lib<pkg>-dev` | Conan / vcpkg / FetchContent |
| Committing `pyproject.toml` alone | Always commit `poetry.lock` in the same commit |

## Python version requirement

Poetry MUST use Python 3.10+. If the wrong version is active, run
`/python-env-setup fix` first.
