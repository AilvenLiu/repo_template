# Dependency Management Skill

A Claude Code skill for comprehensive dependency management in Python and C++/CUDA projects.

## Overview

This skill provides an automated workflow for adding dependencies to projects. It enforces **Poetry** for Python projects and Conan/vcpkg for C++ projects. It updates manifest files, installs packages, and reminds you to update documentation.

## Installation

1. Copy this directory to your Claude Code skills directory:
   ```bash
   cp -r .claude/skills/dependency ~/.claude/skills/
   ```

2. Ensure required tools are installed:
   ```bash
   # Python projects (Poetry is MANDATORY)
   curl -sSL https://install.python-poetry.org | python3 -
   poetry --version

   # C++/CUDA projects
   cmake --version
   conan --version  # Optional but recommended
   ```

## Quick Start

### Add a Python Dependency (Poetry)

```bash
# Production dependency
python3 .claude/skills/dependency/scripts/add.py requests 2.31.0

# Development dependency
python3 .claude/skills/dependency/scripts/add.py pytest 7.3.0 --dev
```

### Add a C++/CUDA Dependency

```bash
python3 .claude/skills/dependency/scripts/add.py Eigen 3.4
```

## Features

- **Poetry-First**: Enforces Poetry for all Python projects
- **Automatic Project Detection**: Detects Python vs C++/CUDA projects
- **Manifest File Updates**: Updates pyproject.toml, poetry.lock, conanfile.txt, CMakeLists.txt
- **Package Installation**: Installs via Poetry or Conan
- **Documentation Reminders**: Prompts to update README.md
- **Version Management**: Supports version constraints (caret ^ for Poetry)
- **Dev Dependencies**: Supports `--dev` flag for development dependencies

## Supported Manifest Files

### Python (Poetry - Default)
- pyproject.toml (dependency declarations)
- poetry.lock (locked versions - MUST be committed)

### Python (Trivial Projects Only)
- requirements.txt (for single-file scripts with 1-2 deps)

### C++/CUDA
- conanfile.txt
- CMakeLists.txt

## Documentation

See [skill.md](skill.md) for comprehensive documentation including:
- Detailed command usage
- Project type detection
- Manifest file formats
- Installation behaviour
- Documentation reminders
- Best practices
- Troubleshooting

## Version

2.0.0 (2026-01-30) - Poetry-first approach

## Licence

This skill is part of the repo_template project and follows the same licence (Creative Commons BY-NC-SA 4.0).
