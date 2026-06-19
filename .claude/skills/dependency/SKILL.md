---
name: dependency
description: "Add dependencies. Poetry for Python, CPM through CMake for C++."
---

# /dependency

Add a project dependency. Handles Python (Poetry) and C++ (CPM through CMake)
projects, including hybrid projects where both apply.

## Execution

```bash
.ai/bin/agent-dependency add <package> [version] [--dev]
```

## Behaviour (guaranteed)

1. Detects project type via `.ai/project.yml` / heuristics.
2. **Python**: runs `poetry add <package>` (or `poetry add --group dev <package>` with `--dev`).
   - Configures in-project virtualenv (`.venv/`) if not already done.
   - Removes external Poetry venvs and recreates in-project when found.
   - Updates both `pyproject.toml` and `poetry.lock`.
3. **C++**: appends a pinned `CPMAddPackage` block to `cmake/Dependencies.cmake`.
4. Prints a reminder to update `README.md` and commit both manifest and lock files.

## Behaviour (best-effort)

- For trivial Python projects (`requirements.txt` only): uses `pip install` and warns to migrate to Poetry.
- C++ dependency input should use `<owner>/<repo> <tag-or-commit>`, for example `fmtlib/fmt 10.2.1`.
- Prints required metadata reminders for reason, target, licence, and dependency scope.

## Absolute prohibitions

| Forbidden | Correct alternative |
|-----------|---------------------|
| `pip install <pkg>` | `.ai/bin/agent-dependency add <pkg>` |
| `poetry add <pkg>` directly | `.ai/bin/agent-dependency add <pkg>` |
| Manual `requirements.txt` edit | `.ai/bin/agent-dependency add <pkg>` |
| `apt install lib<pkg>-dev` | CPM in `cmake/Dependencies.cmake` or documented `find_package` for system SDKs |
| Committing `pyproject.toml` alone | Always commit `poetry.lock` in the same commit |

## Python version requirement

Poetry MUST use Python 3.10+. If the wrong version is active, run
`/python-env-setup fix` first.
