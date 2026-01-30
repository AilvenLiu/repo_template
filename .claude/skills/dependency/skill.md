---
name: dependency
description: Comprehensive dependency management workflow for adding dependencies to Python and C++/CUDA projects. Automatically updates manifest files, installs packages, and provides documentation reminders.
version: 1.0.0
---

# Dependency Management Skill

This skill provides a comprehensive workflow for adding dependencies to Python and C++/CUDA projects. It automatically updates manifest files, installs packages, and reminds you to update documentation.

## Requirements

This skill requires Python 3.9+ and project-specific tools:

**For Python projects:**
- pip3 (package installer)

**For C++/CUDA projects:**
- cmake (build system)
- conan (optional, for package management)

## Available Commands

### `/dependency add <package> [version]`

Add a dependency to the project.

**Usage:**
```bash
python3 .claude/skills/dependency/scripts/add.py <package> [version]
```

**Arguments:**
- `<package>`: Required. Package name (e.g., requests, Eigen)
- `[version]`: Optional. Minimum version (e.g., 2.31.0, 3.4)

**Behaviour:**

For Python projects:
1. Adds package to requirements.txt
2. Installs package via pip3
3. Reminds to update README.md

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

Python project:
```bash
$ python3 .claude/skills/dependency/scripts/add.py requests 2.31.0

Dependency Management
==================================================
Project Type: python
Package: requests
Version: 2.31.0

Adding Python dependency: requests
--------------------------------------------------
[OK] Added requests to requirements.txt

Installing requests...
[OK] requests installed successfully

REMINDER: Update README.md to document requests
Add to Dependencies section:
  - requests >= 2.31.0

Dependency added successfully!

Next steps:
1. Update README.md with dependency documentation
2. Run tests to verify compatibility
3. Commit changes to version control
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

**Python indicators:**
- setup.py
- pyproject.toml
- requirements.txt
- CLAUDE.md

**C++/CUDA indicators:**
- CMakeLists.txt
- conanfile.txt
- conanfile.py
- CLAUDE.md

---

## Manifest Files

### Python Projects

The skill updates the following files:

1. **requirements.txt**
   - Adds package with version constraint
   - Creates file if it doesn't exist
   - Format: `package>=version`

2. **pyproject.toml** (future support)
   - Not yet implemented
   - Will add to dependencies section

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

### Python

Uses pip3 to install packages:
```bash
pip3 install package>=version
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
   - Include manifest file updates
   - Include README.md updates
   - Use descriptive commit message

---

## Best Practices

1. **Always specify versions**
   - Ensures reproducible builds
   - Prevents breaking changes
   - Documents requirements clearly

2. **Update README.md immediately**
   - Don't skip documentation
   - Explain dependency purpose
   - Note any special configuration

3. **Test after adding**
   - Run full test suite
   - Check for conflicts
   - Verify build succeeds

4. **Commit atomically**
   - One dependency per commit
   - Include all related changes
   - Write clear commit message

---

## Troubleshooting

### "ERROR: Unknown project type"

The skill couldn't detect Python or C++/CUDA indicators. Ensure you have:
- Python: `requirements.txt`, `pyproject.toml`, or `CLAUDE.md`
- C++/CUDA: `CMakeLists.txt`, `conanfile.txt`, or `CLAUDE.md`

### "Package already in requirements.txt"

The package is already listed. To update version:
1. Manually edit requirements.txt
2. Run: `pip3 install --upgrade package`

### "Conan install failed"

Check:
- Conan is installed: `pip3 install conan`
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

This skill follows constraints from CLAUDE.md and CONTRIBUTING.md:

**Python projects:**
- Respects dependency priority order
- Follows version pinning guidelines
- Updates all required manifest files

**C++/CUDA projects:**
- Uses Conan for dependency management
- Updates CMakeLists.txt correctly
- Follows build system conventions

---

## Version History

- **1.0.0** (2026-01-25): Initial release
  - Python dependency management (requirements.txt, pip3)
  - C++/CUDA dependency management (conanfile.txt, CMakeLists.txt, conan)
  - Automatic project type detection
  - Documentation reminders
  - Installation automation