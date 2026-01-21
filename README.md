# Repository Template

A comprehensive repository template with specialized documentation and configuration for C++/CUDA and Python projects. This template provides AI-agent-friendly guidelines and development standards to ensure consistent, high-quality codebases.

## Overview

This template contains language-specific documentation and configuration files that can be copied to new repositories during initialization. It includes formal operating constraints for AI coding agents (like Claude Code) and detailed contribution guidelines for both human and AI developers.

## Contents

### Documentation Files

#### For C++/CUDA Projects
- **CLAUDE_CPP.md** - Agent operating constraints for C++/CUDA development
  - C++17+ standards and compiler requirements
  - CUDA-specific guidelines (memory management, kernel documentation, error handling)
  - CMake build system requirements
  - Static analysis tools (clang-tidy, cppcheck)
  - Testing with Google Test/Catch2
  - Memory safety and RAII principles

- **CONTRIBUTING_CPP.md** - Contribution guidelines for C++/CUDA projects
  - Commit and PR conventions
  - Build system standards
  - Code compilation and static analysis requirements
  - Memory safety checks (valgrind, cuda-memcheck)
  - CUDA-specific testing and profiling
  - Code formatting (clang-format)

#### For Python Projects
- **CLAUDE_PYTHON.md** - Agent operating constraints for Python development
  - Python 3.9+ requirements
  - Virtual environment management
  - Dependency management (pip, poetry)
  - Type hints and mypy configuration
  - Code formatting (black, ruff)
  - Testing with pytest

- **CONTRIBUTING_PYTHON.md** - Contribution guidelines for Python projects
  - Commit and PR conventions
  - PEP 8 compliance
  - Type checking requirements
  - Testing standards with pytest
  - Code formatting (black, isort/ruff)
  - Documentation standards (Google-style docstrings)

### Configuration Files

- **.gitignore_cpp** - Comprehensive .gitignore for C++/CUDA projects
  - Build directories, compiled objects, CMake files
  - IDE configurations (VSCode, CLion, Visual Studio)
  - CUDA compiled files, test outputs, coverage reports

- **.gitignore_python** - Comprehensive .gitignore for Python projects
  - Virtual environments, Python cache, distribution files
  - Testing/coverage outputs, Jupyter checkpoints
  - IDE configurations (VSCode, PyCharm)

### General Files

- **LICENSE** - Creative Commons BY-NC-SA 4.0
  - Open source with attribution requirement
  - Non-commercial use
  - Share-alike for derivatives
  - Encourages forking and contributions

- **CLAUDE.md** - Original general agent constraints (reference)
- **CONTRIBUTING.md** - Original general contribution guidelines (reference)

## Usage

### Creating a New C++/CUDA Project

```bash
# Create new repository
mkdir my-cpp-project && cd my-cpp-project
git init

# Copy template files
cp /path/to/repo_template/CLAUDE_CPP.md ./CLAUDE.md
cp /path/to/repo_template/CONTRIBUTING_CPP.md ./CONTRIBUTING.md
cp /path/to/repo_template/.gitignore_cpp ./.gitignore
cp /path/to/repo_template/LICENSE ./LICENSE

# Initialize project structure
mkdir -p include/project_name src cuda tests docs

# Create initial commit
git add .
git commit -m "chore: initialize project from template"
```

### Creating a New Python Project

```bash
# Create new repository
mkdir my-python-project && cd my-python-project
git init

# Copy template files
cp /path/to/repo_template/CLAUDE_PYTHON.md ./CLAUDE.md
cp /path/to/repo_template/CONTRIBUTING_PYTHON.md ./CONTRIBUTING.md
cp /path/to/repo_template/.gitignore_python ./.gitignore
cp /path/to/repo_template/LICENSE ./LICENSE

# Initialize project structure
mkdir -p src/package_name tests docs

# Create virtual environment
python3.9 -m venv .venv
source .venv/bin/activate

# Create initial commit
git add .
git commit -m "chore: initialize project from template"
```

## Key Features

### AI Agent Integration
- Formal operating constraints for AI coding agents
- Roadmap-based development workflow
- Context7 MCP integration for external knowledge
- Session continuity and state management

### Language-Specific Standards
- Detailed technical requirements with specific versions
- Comprehensive code examples (good vs. bad practices)
- Formal compliance checklists for commits and PRs
- Complete configuration examples

### Quality Assurance
- Mandatory testing requirements with coverage thresholds
- Static analysis and type checking requirements
- Code formatting standards
- Security best practices

### Documentation Standards
- Doxygen-style comments for C++
- Google-style docstrings for Python
- Comprehensive README requirements
- API documentation guidelines

## Roadmap System

Both templates include support for the `agents_roadmaps/` system for managing complex, multi-session development tasks. This system provides:
- Structured task breakdown
- Session continuity across AI agent interactions
- Invariant tracking for critical constraints
- Progress tracking and handoff documentation

## Contributing

This template itself follows the same standards it defines. To contribute improvements:

1. Fork this repository
2. Create a feature branch
3. Make your changes following the appropriate language guidelines
4. Submit a pull request with a clear description

## License

This work is licensed under Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International (CC BY-NC-SA 4.0).

You are free to:
- Share and adapt the material
- Fork and contribute

Under these terms:
- Attribution required
- Non-commercial use only
- Share-alike for derivatives

For commercial use, please contact the maintainers.

## Maintenance

This template is actively maintained and updated with:
- Latest best practices for C++/CUDA and Python development
- New tool integrations and configurations
- Community feedback and improvements
- AI agent capability enhancements

---

**Note**: When using this template, customize the LICENSE file with your project's copyright information and adjust the documentation to match your specific project requirements.
