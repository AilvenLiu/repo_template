# dependency — add a project dependency

> Vendor-neutral procedure description. Claude Code dispatches `/dependency`
> to this body via the stub at `.claude/skills/dependency/SKILL.md`. Codex /
> Cursor / Cline consult this file directly via the AGENTS.md procedures table.

Adds a dependency to the project, updates manifest files, installs the
package, and reminds you to update documentation.

## Execution

```bash
.ai/bin/agent-dependency add <package> [version] [--dev]
```

## Behaviour (guaranteed)

1. Detects project type via shared `project_type.py`.
2. Python: runs `poetry add`, updates pyproject.toml + poetry.lock.
   - Configures in-project venvs; removes external venvs if found.
3. C++: adds a pinned `CPMAddPackage` block to `cmake/Dependencies.cmake`.
4. Prints reminder to update README.md and commit manifest files.

## Behaviour (best-effort)

- Trivial Python projects (requirements.txt only): uses pip, warns to migrate to Poetry.
- Native CMake validation after adding C++ dependencies.
