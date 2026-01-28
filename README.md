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

### Claude Code Skills

- **.claude/skills/init/** - Session Initialization skill for context-aware constraint loading
  - MANDATORY at session start - run `/init` before any other action
  - Automatic project type detection (Python vs C++/CUDA)
  - Smart constraint loading based on current context (modified files, git status)
  - Active roadmap detection and protected branch warnings
  - Loads only relevant constraints (500-1000 lines vs 2000+ lines)
  - See [.claude/skills/init/README.md](.claude/skills/init/README.md) for details

- **.claude/skills/roadmap/** - Agent Roadmaps skill for managing multi-session workflows
  - Automatic session-start checks for active roadmaps
  - Structured commands for roadmap creation and management
  - State validation and transition enforcement
  - Session handoff generation for continuity
  - See [.claude/skills/roadmap/README.md](.claude/skills/roadmap/README.md) for details

- **.claude/skills/pre-commit/** - Pre-Commit Validation skill for automated code quality checks
  - Automatic project type detection (Python vs C++/CUDA)
  - Comprehensive validation (formatters, linters, type checkers, tests)
  - Auto-fix support for formatting issues
  - Consolidated error reporting
  - See [.claude/skills/pre-commit/README.md](.claude/skills/pre-commit/README.md) for details

- **.claude/skills/dependency/** - Dependency Management skill for adding dependencies
  - Automatic manifest file updates (requirements.txt, CMakeLists.txt, conanfile.txt)
  - Package installation automation (pip3, conan)
  - Documentation reminders for README.md updates
  - Version constraint management
  - See [.claude/skills/dependency/README.md](.claude/skills/dependency/README.md) for details

### Constraint Files

- **.claude/constraints/** - Topic-specific constraint files for on-demand loading
  - **python/** - Python-specific constraints (testing, formatting, type-checking, dependencies, documentation, error-handling, security)
  - **cpp/** - C++/CUDA-specific constraints (testing, formatting, cmake, cuda, memory-safety, static-analysis, documentation)
  - **common/** - Language-agnostic constraints (git-workflow, roadmap-awareness, session-discipline)
  - Loaded automatically by `/init` skill based on context
  - Each file is self-contained and focused on a single topic (150-700 lines)
  - See [.claude/constraints/python/README.md](.claude/constraints/python/README.md) and [.claude/constraints/cpp/README.md](.claude/constraints/cpp/README.md) for details

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

# Copy Claude Code configuration and skills
cp -r /path/to/repo_template/.claude ./.claude

# Install skill dependencies
pip3 install -r .claude/skills/roadmap/requirements.txt

# Copy agent_roadmaps system
cp -r /path/to/repo_template/agent_roadmaps ./agent_roadmaps

# Initialize project structure
mkdir -p include/project_name src cuda tests docs

# Create initial commit
git add .
git commit -m "chore: initialise project from template"
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

# Copy Claude Code configuration and skills
cp -r /path/to/repo_template/.claude ./.claude

# Copy agent_roadmaps system
cp -r /path/to/repo_template/agent_roadmaps ./agent_roadmaps

# Initialize project structure
mkdir -p src/package_name tests docs

# Create virtual environment
python3.9 -m venv .venv
source .venv/bin/activate

# Install skill dependencies
pip3 install -r .claude/skills/roadmap/requirements.txt

# Create initial commit
git add .
git commit -m "chore: initialise project from template"
```

### Using the Template in Your Workflow

Once you've initialized a project from the template, start every Claude Code session with:

```bash
/init
```

This will:
1. Detect your project type (Python or C++/CUDA)
2. Check for active roadmaps
3. Analyze your current git status
4. Load only the relevant constraints for your current work
5. Warn about protected branches

Example session:
```bash
# Start Claude Code session
$ /init

[OK] Project type: PYTHON
[OK] Current branch: feature/add-api
[OK] Found 2 modified file(s)

Loaded constraints: git-workflow, session-discipline, formatting, type-checking

# Now proceed with your work
$ # Make changes, run tests, commit, etc.
```

## Key Features

### AI Agent Integration
- Formal operating constraints for AI coding agents
- Session initialization with context-aware constraint loading (`/init` skill)
- Roadmap-based development workflow
- Context7 MCP integration for external knowledge
- Session continuity and state management
- On-demand constraint loading (500-1000 lines vs 2000+ lines)

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

Both templates include support for the `agent_roadmaps/` system for managing complex, multi-session development tasks. This system provides:
- Structured task breakdown with phases and tasks
- Session continuity across AI agent interactions
- Invariant tracking for critical constraints
- Progress tracking and handoff documentation
- Authority hierarchy (INVARIANTS.md > ROADMAP.md > roadmap.yml)

### Roadmap Skill

The template includes a Claude Code skill ([.claude/skills/roadmap/](.claude/skills/roadmap/)) that provides structured commands for roadmap management:

**Available Commands:**
- `/roadmap check` - Check for active roadmaps (mandatory at session start)
- `/roadmap create <name>` - Create new roadmap directory structure
- `/roadmap status` - Display detailed roadmap status with progress
- `/roadmap update <action>` - Update state (complete-task, block-task, etc.)
- `/roadmap handoff` - Generate session handoff files
- `/roadmap complete` - Mark roadmap as completed and deactivate

**Key Features:**
- Automatic session-start checks for active roadmaps
- Single active roadmap rule enforcement
- State machine validation for transitions
- YAML-based state management
- Session handoff generation for continuity

See [.claude/skills/roadmap/README.md](.claude/skills/roadmap/README.md) for comprehensive documentation.

### When to Use Roadmaps

Create a roadmap when a task meets ANY of these criteria:
- Cannot be completed within 1-2 Claude Code sessions
- Involves system-wide refactor or architectural change
- Requires long-lived constraints that must survive context resets
- Has multiple dependent phases or non-trivial rollback risk

### Pre-Commit Validation Skill

The template includes a Claude Code skill ([.claude/skills/pre-commit/](.claude/skills/pre-commit/)) for automated code quality validation:

**Available Commands:**
- `/pre-commit validate` - Run all validation checks (formatters, linters, type checkers, tests)
- `/pre-commit fix` - Auto-fix formatting issues

**Supported Tools:**

Python projects:
- black (formatter)
- isort (import sorter)
- ruff (linter)
- mypy (type checker)
- pytest (test runner)

C++/CUDA projects:
- clang-format (formatter)
- clang-tidy (linter)
- cppcheck (static analyser)
- cmake (build verification)

**Key Features:**
- Automatic project type detection
- Comprehensive validation with consolidated reporting
- Auto-fix support for formatters
- Tool availability checks with installation guidance
- Exit codes for CI/CD integration

See [.claude/skills/pre-commit/README.md](.claude/skills/pre-commit/README.md) for comprehensive documentation.

### Dependency Management Skill

The template includes a Claude Code skill ([.claude/skills/dependency/](.claude/skills/dependency/)) for managing project dependencies:

**Available Commands:**
- `/dependency add <package> [version]` - Add a dependency to the project

**Behaviour:**

Python projects:
- Updates requirements.txt
- Installs via pip3
- Reminds to update README.md

C++/CUDA projects:
- Updates conanfile.txt (if exists)
- Updates CMakeLists.txt with find_package()
- Installs via conan (if configured)
- Reminds to update README.md

**Key Features:**
- Automatic project type detection
- Manifest file updates (requirements.txt, CMakeLists.txt, conanfile.txt)
- Package installation automation
- Version constraint management
- Documentation reminders

See [.claude/skills/dependency/README.md](.claude/skills/dependency/README.md) for comprehensive documentation.

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
