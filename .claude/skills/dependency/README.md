# Dependency Management Skill

A Claude Code skill for comprehensive dependency management in Python and C++/CUDA projects.

## Overview

This skill provides an automated workflow for adding dependencies to projects. It enforces **Poetry** for Python projects (with Python 3.10+ requirement) and Conan/vcpkg for C++ projects. It updates manifest files, installs packages, and reminds you to update documentation.

## Installation

1. Copy this directory to your Claude Code skills directory:
   ```bash
   cp -r .claude/skills/dependency ~/.claude/skills/
   ```

2. Ensure required tools are installed:
   ```bash
   # Python projects (Python 3.10+ and Poetry are MANDATORY)
   python3.10 --version  # Must be 3.10 or higher
   curl -sSL https://install.python-poetry.org | python3 -
   poetry --version

   # C++/CUDA projects
   cmake --version
   conan --version  # Optional but recommended
   ```

## Python 3.10+ Requirement

**CRITICAL**: This skill requires Python 3.10 or higher for Poetry-based projects.

If Python 3.10+ is not available, install it first:

**Option 1: Using pyenv (Recommended)**
```bash
curl https://pyenv.run | bash
pyenv install 3.10
pyenv global 3.10
```

**Option 2: Using system package manager**
```bash
# macOS
brew install python@3.10

# Ubuntu/Debian
sudo apt update
sudo apt install python3.10 python3.10-venv

# Fedora/RHEL
sudo dnf install python3.10
```

**Option 3: Download from python.org**
- Visit: https://www.python.org/downloads/

## Quick Start

### Add a Python Dependency (Poetry)

```bash
# Production dependency
python3 .ai/scripts/dependency/add.py requests 2.31.0

# Development dependency
python3 .ai/scripts/dependency/add.py pytest 7.3.0 --dev
```

### Add a C++/CUDA Dependency

```bash
python3 .ai/scripts/dependency/add.py Eigen 3.4
```

## Features

- **Poetry-First**: Enforces Poetry for all Python projects
- **In-Project Virtual Environments**: Automatically configures Poetry to create `.venv` inside the project directory
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

See [SKILL.md](SKILL.md) for comprehensive documentation including:
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
