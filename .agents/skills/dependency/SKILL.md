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
3. C++: adds a pinned `CPMAddPackage` block to `cmake/Dependencies.cmake`.
4. Prints reminder to update README.md and commit manifest files.

## Validation

- Python projects must be Poetry-managed; unsupported manifests are a blocking policy error.
- C++ dependency changes require direct CMake configure, build, and CTest validation.

## Detailed reference

Read [references/guide.md](references/guide.md) for expanded dependency
examples and troubleshooting.
