---
name: dependency
description: Add or change project dependencies through the repository-owned dependency workflow. Use for Poetry dependencies, CMake/CPM native dependencies, hybrid dependency changes, version constraints, or dependency-policy troubleshooting.
---

# dependency — add a project dependency

> Canonical repository skill. Codex discovers it natively from `.agents/skills/`;
> Claude Code reaches it through the matching `.claude/skills/` delegate.

Adds a dependency to the project, updates manifest files, installs the
package, and reminds you to update documentation.

## Execution

```bash
.agents/bin/agent-dependency add <package> [version] [--dev]
```

## Behaviour (guaranteed)

1. Detects project type via shared `project_type.py`.
2. Python: runs `poetry add`, updates pyproject.toml + poetry.lock.
   - Configures in-project venvs; removes external venvs if found.
3. Hybrid Python: safely extends single-line or multi-line PEP 621 dependency
   arrays, validates the candidate TOML, and runs `poetry lock`.
   - If parsing or locking fails, restores both `pyproject.toml` and
     `poetry.lock`; partial dependency state is never retained.
4. C++: adds a pinned `CPMAddPackage` block to `cmake/Dependencies.cmake`.
5. Prints reminder to update README.md and commit manifest files.

## Validation

- Python projects must be Poetry-managed; unsupported manifests are a blocking policy error.
- Hybrid manifest and lock-file updates are transactional and must be reviewed together.
- C++ dependency changes require direct CMake configure, build, and CTest validation.

## Detailed reference

Read [references/guide.md](references/guide.md) for expanded dependency
examples and troubleshooting.
