# Dependency Management Skill

A Claude Code skill for comprehensive dependency management in Python and C++/CUDA projects.

## Overview

This skill provides an automated workflow for adding dependencies to projects. It updates manifest files, installs packages, and reminds you to update documentation.

## Installation

1. Copy this directory to your Claude Code skills directory:
   ```bash
   cp -r .claude/skills/dependency ~/.claude/skills/
   ```

2. Ensure required tools are installed:
   ```bash
   # Python projects
   pip3 --version

   # C++/CUDA projects
   cmake --version
   conan --version  # Optional but recommended
   ```

## Quick Start

### Add a Python Dependency

```bash
python3 .claude/skills/dependency/scripts/add.py requests 2.31.0
```

### Add a C++/CUDA Dependency

```bash
python3 .claude/skills/dependency/scripts/add.py Eigen 3.4
```

## Features

- **Automatic Project Detection**: Detects Python vs C++/CUDA projects
- **Manifest File Updates**: Updates requirements.txt, conanfile.txt, CMakeLists.txt
- **Package Installation**: Installs via pip3 or conan
- **Documentation Reminders**: Prompts to update README.md
- **Version Management**: Supports version constraints

## Supported Manifest Files

### Python
- requirements.txt (primary)
- pyproject.toml (future)

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

1.0.0 (2026-01-25)

## Licence

This skill is part of the repo_template project and follows the same licence (Creative Commons BY-NC-SA 4.0).
