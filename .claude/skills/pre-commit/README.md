# Pre-Commit Validation Skill

A Claude Code skill for automated pre-commit validation orchestrating formatters, linters, type checkers, and tests.

## Overview

This skill provides comprehensive code quality validation for Python and C++/CUDA projects. It automatically detects project type and runs appropriate validation tools, providing consolidated error reporting.

## Installation

1. Copy this directory to your Claude Code skills directory:
   ```bash
   cp -r .claude/skills/pre-commit ~/.claude/skills/
   ```

2. Install Python tools (for Python projects):
   ```bash
   pip3 install black isort ruff mypy pytest
   ```

3. Install C++/CUDA tools (for C++/CUDA projects):
   ```bash
   # Ubuntu/Debian
   sudo apt-get install clang-format clang-tidy cppcheck cmake

   # macOS
   brew install clang-format llvm cppcheck cmake
   ```

## Quick Start

### Run Validation

```bash
python3 .claude/skills/pre-commit/scripts/validate.py
```

### Auto-Fix Formatting

```bash
python3 .claude/skills/pre-commit/scripts/fix.py
```

## Features

- **Automatic Project Detection**: Detects Python vs C++/CUDA projects
- **Comprehensive Validation**: Runs formatters, linters, type checkers, and tests
- **Auto-Fix Support**: Automatically fixes formatting issues
- **Consolidated Reporting**: Single view of all validation results
- **Tool Availability Checks**: Warns about missing tools
- **Exit Code Support**: Integrates with CI/CD pipelines

## Validation Tools

### Python Projects
- black (formatter)
- isort (import sorter)
- ruff (linter)
- mypy (type checker)
- pytest (test runner)

### C++/CUDA Projects
- clang-format (formatter)
- clang-tidy (linter)
- cppcheck (static analyser)
- cmake (build verification)

## Documentation

See [skill.md](skill.md) for comprehensive documentation including:
- Detailed command usage
- Project type detection
- Validation checks
- Tool installation
- Git hooks integration
- Configuration files
- Troubleshooting
- Best practices

## Version

1.0.0 (2026-01-25)

## Licence

This skill is part of the repo_template project and follows the same licence (Creative Commons BY-NC-SA 4.0).
