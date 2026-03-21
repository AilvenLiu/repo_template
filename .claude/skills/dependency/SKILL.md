---
name: dependency
description: "Add dependencies. Poetry for Python (mandatory), Conan/vcpkg for C++."
---

# /dependency

Adds a dependency to the project, updates manifest files, installs the
package, and reminds you to update documentation.

## Execution

Run:

```bash
bin/agent-dependency add <package> [version] [--dev]
```

## Behaviour (guaranteed)

1. Detects project type via shared `project_type.py`.
2. Python: runs `poetry add`, updates pyproject.toml + poetry.lock.
   - Configures in-project venvs; removes external venvs if found.
3. C++: adds to conanfile.txt, adds `find_package()` to CMakeLists.txt.
4. Prints reminder to update README.md and commit manifest files.

## Behaviour (best-effort)

- Trivial Python projects (requirements.txt only): uses pip, warns to migrate to Poetry.
- Conan install after adding C++ dependency (requires network + conan).
