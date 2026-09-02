# Dependency Management Skill

A Claude Code skill for comprehensive dependency management in Python,
C++/CUDA, and hybrid projects.

## Overview

This skill provides an automated workflow for adding dependencies to projects.
It enforces Poetry for Python projects, supports scikit-build-core style
hybrid projects, and uses CPM declarations in CMake for C++ projects. It
updates manifest files, installs packages, and reminds you to update
documentation.

## Installation

1. Copy this directory to your Claude Code skills directory:
   ```bash
   cp -r .claude/skills/dependency ~/.claude/skills/
   ```

2. Ensure required tools are installed:
   ```bash
   # Python projects (Python 3.10+ and Poetry are MANDATORY)
   python3.10 --version  # Must be 3.10 or higher
   pipx install poetry
   poetry --version

   # C++/CUDA projects
   cmake --version
   ninja --version
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
.agents/bin/agent-dependency add requests 2.31.0

# Development dependency
.agents/bin/agent-dependency add pytest 7.3.0 --dev
```

### Add a C++/CUDA Dependency

```bash
.agents/bin/agent-dependency add fmtlib/fmt 10.2.1
```

## Features

- **Poetry-First**: Enforces Poetry for all Python projects
- **In-Project Virtual Environments**: Automatically configures Poetry to create `.venv` inside the project directory
- **Automatic Project Detection**: Detects Python, C++/CUDA, and hybrid projects
- **Manifest File Updates**: Updates pyproject.toml, poetry.lock, and cmake/Dependencies.cmake
- **Transactional Hybrid Edits**: Restores manifest and lock state if parsing or locking fails
- **Package Installation**: Installs via Poetry or CMake/CPM configure/build
- **Documentation Reminders**: Prompts to update README.md
- **Version Management**: Supports version constraints (caret ^ for Poetry)
- **Dev Dependencies**: Supports `--dev` flag for development dependencies

## Supported Manifest Files

### Python (Poetry - Default)
- pyproject.toml (dependency declarations)
- poetry.lock (locked versions - MUST be committed)

### C++/CUDA
- CMakeLists.txt
- cmake/CPM.cmake
- cmake/Dependencies.cmake
- cmake/Options.cmake
- 3rdparty/cpm-cache/.gitkeep

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

2.2.0 (2026-09-01) - Transactional hybrid manifest and lock-file updates

## Licence

This skill is part of Agent Foundry and follows the same licence (Creative Commons BY-NC-SA 4.0).
