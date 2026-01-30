---
name: dependency
description: Comprehensive dependency management workflow for adding dependencies to Python and C++/CUDA projects. Uses Poetry for Python (mandatory) and Conan/vcpkg for C++. Automatically updates manifest files, installs packages, and provides documentation reminders.
version: 2.0.0
---

# Dependency Management Skill

This skill provides a comprehensive workflow for adding dependencies to Python and C++/CUDA projects. It enforces Poetry for Python projects and Conan/vcpkg for C++ projects.

## Requirements

This skill requires Python 3.9+ and project-specific tools:

**For Python projects:**
- **Poetry** (mandatory) - Install: `curl -sSL https://install.python-poetry.org | python3 -`

**For C++/CUDA projects:**
- cmake (build system)
- conan or vcpkg (package management)

## Available Commands

### `/dependency add <package> [version] [--dev]`

Add a dependency to the project.

**Usage:**
```bash
python3 .claude/skills/dependency/scripts/add.py <package> [version] [--dev]
```

**Arguments:**
- `<package>`: Required. Package name (e.g., requests, Eigen)
- `[version]`: Optional. Minimum version (e.g., 2.31.0, 3.4)
- `[--dev]`: Optional. Add as development dependency (Poetry only)

**Behaviour:**

For Python projects (Poetry - default):
1. Ensures Poetry is installed
2. Initialises Poetry project if needed
3. Adds package via `poetry add`
4. Automatically updates pyproject.toml and poetry.lock
5. Reminds to update README.md

For Python projects (trivial - requirements.txt only):
1. Creates virtual environment if needed
2. Adds package to requirements.txt
3. Installs package via pip
4. Reminds to update README.md
5. Warns to consider migrating to Poetry

For C++/CUDA projects:
1. Adds package to conanfile.txt (if exists)
2. Adds find_package() to CMakeLists.txt
3. Runs conan install (if conanfile.txt exists)
4. Reminds to update README.md

**When to use:**
- Adding a new dependency to the project
- Ensuring consistent dependency documentation
- Automating dependency installation

**Examples:**

Python project (Poetry):
```bash
$ python3 .claude/skills/dependency/scripts/add.py requests 2.31.0

Dependency Management
==================================================
Project Type: python
Package: requests
Version: 2.31.0

Adding Python dependency via Poetry: requests
--------------------------------------------------
Installing requests...
[OK] requests installed successfully via Poetry

Poetry automatically updated:
  - pyproject.toml (dependency declaration)
  - poetry.lock (locked versions)

IMPORTANT: Commit BOTH files:
  git add pyproject.toml poetry.lock

REMINDER: Update README.md to document requests
Add to Dependencies section:
  - **requests** (^2.31.0): [description]

Dependency added successfully!

Next steps:
1. Update README.md with dependency documentation
2. Run tests to verify compatibility
3. Commit changes to version control
   git add pyproject.toml poetry.lock <your-code>
```

Python project (development dependency):
```bash
$ python3 .claude/skills/dependency/scripts/add.py pytest 7.3.0 --dev

Dependency Management
==================================================
Project Type: python
Package: pytest
Version: 7.3.0
Group: dev

Adding Python dependency via Poetry: pytest
--------------------------------------------------
Installing pytest (dev)...
[OK] pytest installed successfully via Poetry

Poetry automatically updated:
  - pyproject.toml (dependency declaration)
  - poetry.lock (locked versions)

IMPORTANT: Commit BOTH files:
  git add pyproject.toml poetry.lock
```

C++/CUDA project:
```bash
$ python3 .claude/skills/dependency/scripts/add.py Eigen 3.4

Dependency Management
==================================================
Project Type: cpp_cuda
Package: Eigen
Version: 3.4

Adding C++/CUDA dependency: Eigen
--------------------------------------------------
[OK] Added Eigen to conanfile.txt

Installing Eigen via Conan...
[OK] Conan install successful
[OK] Added find_package(Eigen) to CMakeLists.txt

REMINDER: Update README.md to document Eigen
Add to Dependencies section:
  - Eigen >= 3.4

Dependency added successfully!

Next steps:
1. Update README.md with dependency documentation
2. Run tests to verify compatibility
3. Commit changes to version control
```

---

## Project Type Detection

The skill automatically detects project type based on indicator files:

**Python indicators (checked in order):**
- pyproject.toml (Poetry project)
- requirements.txt (trivial project)
- setup.py

**C++/CUDA indicators:**
- CMakeLists.txt
- conanfile.txt
- conanfile.py

**Python project type detection:**
- If pyproject.toml contains `[tool.poetry]` or `poetry-core` -> Poetry project
- If only requirements.txt exists -> Trivial project (manual venv)
- Otherwise -> New project (will initialise Poetry)

---

## Manifest Files

### Python Projects (Poetry - Default)

The skill updates the following files:

1. **pyproject.toml**
   - Adds package to `[tool.poetry.dependencies]` or `[tool.poetry.group.dev.dependencies]`
   - Uses caret (^) version constraints by default
   - Format: `package = "^version"`

2. **poetry.lock**
   - Automatically updated by Poetry
   - Contains locked versions of all dependencies
   - **MUST be committed** for reproducible builds

### Python Projects (Trivial)

For trivial projects (requirements.txt only):

1. **requirements.txt**
   - Adds package with version constraint
   - Creates file if it doesn't exist
   - Format: `package>=version`

### C++/CUDA Projects

The skill updates the following files:

1. **conanfile.txt**
   - Adds package to [requires] section
   - Creates file if it doesn't exist
   - Format: `package/version`

2. **CMakeLists.txt**
   - Adds find_package() call
   - Inserts after existing find_package() calls
   - Format: `find_package(package version REQUIRED)`

---

## Installation Behaviour

### Python (Poetry - Default)

Uses Poetry to install packages:
```bash
poetry add package
poetry add "package^version"
poetry add --group dev package
```

Poetry automatically:
- Creates/manages virtual environment
- Resolves dependencies
- Updates pyproject.toml
- Updates poetry.lock

### Python (Trivial)

Uses pip in virtual environment:
```bash
.venv/bin/pip install package>=version
```

### C++/CUDA

If conanfile.txt exists, runs:
```bash
conan install . --build=missing
```

This downloads and builds dependencies via Conan.

---

## Documentation Reminders

After adding a dependency, the skill reminds you to:

1. **Update README.md**
   - Add to Dependencies section
   - Document version requirements
   - Explain why dependency is needed

2. **Run tests**
   - Verify compatibility
   - Check for conflicts
   - Ensure functionality

3. **Commit changes**
   - Include pyproject.toml and poetry.lock (Poetry)
   - Include requirements.txt (trivial)
   - Include README.md updates
   - Use descriptive commit message

---

## Best Practices

1. **Use Poetry for all Python projects**
   - Only use manual venv for truly trivial projects
   - Poetry provides better dependency resolution
   - Lock files ensure reproducibility

2. **Always specify versions**
   - Ensures reproducible builds
   - Prevents breaking changes
   - Documents requirements clearly

3. **Commit lock files**
   - poetry.lock MUST be committed
   - Ensures all developers use same versions
   - Required for reproducible CI/CD

4. **Update README.md immediately**
   - Don't skip documentation
   - Explain dependency purpose
   - Note any special configuration

5. **Test after adding**
   - Run full test suite
   - Check for conflicts
   - Verify build succeeds

6. **Commit atomically**
   - One dependency per commit
   - Include all related changes
   - Write clear commit message

---

## Troubleshooting

### "Poetry is not installed"

Install Poetry:
```bash
curl -sSL https://install.python-poetry.org | python3 -
```

Or see: https://python-poetry.org/docs/#installation

### "ERROR: Unknown project type"

The skill couldn't detect Python or C++/CUDA indicators. Ensure you have:
- Python: `pyproject.toml` (recommended) or `requirements.txt`
- C++/CUDA: `CMakeLists.txt`, `conanfile.txt`, or `vcpkg.json`

### "Development dependencies require Poetry"

Trivial projects (requirements.txt only) don't support `--dev` flag.
Migrate to Poetry:
```bash
poetry init
poetry add --group dev package-name
```

### "Conan install failed"

Check:
- Conan is installed: `pip install conan`
- Package name is correct
- Version is available
- Network connectivity

### "Could not find [requires] section"

The conanfile.txt is malformed. Ensure it has:
```
[requires]

[generators]
cmake
```

---

## Integration with Constraints

This skill follows constraints from `.claude/constraints/python/dependencies.md`:

**Python projects:**
- Enforces Poetry as the default tool
- Allows manual venv only for trivial projects
- Requires committing poetry.lock
- Follows version pinning guidelines (caret ^)

**C++/CUDA projects:**
- Uses Conan for dependency management
- Updates CMakeLists.txt correctly
- Follows build system conventions

---

## Version History

- **2.0.0** (2026-01-30): Poetry-first approach
  - Poetry is now mandatory for Python projects
  - Manual venv only for trivial projects
  - Added --dev flag for development dependencies
  - Improved error messages and guidance

- **1.0.0** (2026-01-25): Initial release
  - Python dependency management (requirements.txt, pip3)
  - C++/CUDA dependency management (conanfile.txt, CMakeLists.txt, conan)
  - Automatic project type detection
  - Documentation reminders
  - Installation automation
