# Python Dependency Management

> **This document defines mandatory dependency management standards for Python projects.**
> All dependency changes must follow these rules to ensure reproducibility and maintainability.

## 1. Mandatory Tool: Poetry

### 1.1 Poetry as the Default Standard

**MANDATORY**: Use **Poetry** for all Python dependency management.

Poetry provides:
- Unified virtual environment management
- Dependency resolution with lock files
- Modern pyproject.toml-native configuration
- Reproducible builds via `poetry.lock`
- Clean separation of production and development dependencies

### 1.2 Exception: Manual venv for Trivial Projects

**ONLY** for extremely simple projects (single-file scripts, quick prototypes with 1-2 dependencies), manual venv with requirements.txt is acceptable.

**Criteria for "trivial project" exception:**
- Single Python file or fewer than 3 files
- Fewer than 3 dependencies total
- No packaging or distribution requirements
- No development dependencies needed
- Explicitly approved by project owner

**If in doubt, use Poetry.** The overhead is minimal and the benefits are significant.

### 1.3 Virtual Environment Requirement

- **MANDATORY**: ALWAYS use virtual environments (never install to system Python)
- **NEVER** install packages globally
- **NEVER** use `pip install` directly without Poetry or activated venv
- **NEVER** use raw `python` or `python3` commands - always use `poetry run`

**CRITICAL EXAMPLES**:

```bash
# FORBIDDEN: Direct system Python usage
python script.py                    # WRONG - uses system Python
python3 -m pytest                   # WRONG - uses system Python
pip install requests                # WRONG - installs to system Python

# REQUIRED: Always use Poetry
poetry run python script.py         # CORRECT
poetry run pytest                   # CORRECT
poetry add requests                 # CORRECT
```

## 2. Poetry Project Structure

### 2.1 Required Files

Every Poetry-managed project MUST have:
- **pyproject.toml**: Project metadata and dependencies
- **poetry.lock**: Locked dependency versions (auto-generated, MUST be committed)

### 2.2 pyproject.toml Structure

```toml
[tool.poetry]
name = "project-name"
version = "0.1.0"
description = "Project description"
authors = ["Author Name <author@example.com>"]
readme = "README.md"
license = "MIT"
packages = [{include = "src"}]

[tool.poetry.dependencies]
python = "^3.9"
numpy = "^1.24.0"
pandas = "^2.0.0"
requests = "^2.31.0"

[tool.poetry.group.dev.dependencies]
pytest = "^7.3.0"
pytest-cov = "^4.0.0"
black = "^23.3.0"
mypy = "^1.3.0"
ruff = "^0.0.272"

[build-system]
requires = ["poetry-core"]
build-backend = "poetry.core.masonry.api"

[tool.black]
line-length = 100
target-version = ['py39', 'py310', 'py311', 'py312']

[tool.mypy]
python_version = "3.9"
strict = true
warn_return_any = true
warn_unused_configs = true

[tool.ruff]
line-length = 100
target-version = "py39"
select = ["E", "F", "I", "N", "W", "B", "C4", "UP"]

[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py"]
addopts = ["--strict-markers", "--cov=src"]

[tool.coverage.run]
source = ["src"]
omit = ["*/tests/*", "*/test_*.py"]

[tool.coverage.report]
exclude_lines = [
    "pragma: no cover",
    "def __repr__",
    "if __name__ == .__main__.:",
]
```

## 3. Poetry Commands Reference

### 3.1 Project Setup

```bash
# Install Poetry (if not installed)
curl -sSL https://install.python-poetry.org | python3 -

# Create new project
poetry new project-name

# Or initialise in existing directory
poetry init

# Install all dependencies (creates virtual environment automatically)
poetry install

# Install with development dependencies
poetry install --with dev
```

### 3.2 Dependency Management

```bash
# Add production dependency
poetry add package-name

# Add production dependency with version constraint
poetry add "package-name^2.0.0"

# Add development dependency
poetry add --group dev package-name

# Remove dependency
poetry remove package-name

# Update specific package
poetry update package-name

# Update all packages
poetry update

# Show installed packages
poetry show

# Show dependency tree
poetry show --tree

# Check for outdated packages
poetry show --outdated
```

### 3.3 Running Commands

```bash
# Activate virtual environment
poetry shell

# Run command in virtual environment (without activating)
poetry run python script.py
poetry run pytest
poetry run black .

# Exit virtual environment
exit
```

### 3.4 Lock File Management

```bash
# Regenerate lock file (after manual pyproject.toml edits)
poetry lock

# Install from lock file only (CI/CD)
poetry install --no-root

# Export to requirements.txt (for compatibility)
poetry export -f requirements.txt --output requirements.txt
```

## 4. Mandatory Dependency Update Protocol

### 4.1 Critical Requirement

**CRITICAL**: When installing ANY new package, Claude Code MUST:

1. Use `poetry add` to install the package
2. Verify both `pyproject.toml` and `poetry.lock` are updated
3. Commit both files in the SAME commit as code using the package
4. Document the package purpose in README.md if it's a major dependency

### 4.2 Standard Workflow

```bash
# Install new package (automatically updates pyproject.toml and poetry.lock)
poetry add package-name

# Install development dependency
poetry add --group dev package-name

# Commit changes
git add pyproject.toml poetry.lock src/module.py
git commit -m "feat: add new feature using package-name"
```

### 4.3 Version Pinning Strategy

Poetry uses semantic versioning constraints:

```toml
# Caret (^) - Allow minor and patch updates (RECOMMENDED)
numpy = "^1.24.0"  # Allows 1.24.x, 1.25.x, but not 2.0.0

# Tilde (~) - Allow patch updates only
numpy = "~1.24.0"  # Allows 1.24.x only

# Exact version (use sparingly)
numpy = "1.24.3"  # Exactly this version

# Range
numpy = ">=1.24.0,<2.0.0"  # Explicit range
```

**Guidelines:**
- **Production dependencies**: Use caret (^) for flexibility with safety
- **Development dependencies**: Use caret (^) for latest tooling
- **Critical dependencies**: Use tilde (~) or exact version if stability is paramount

## 5. Environment Setup Protocol

### 5.1 Mandatory Setup Steps

When starting work on a project, Claude Code MUST:

1. Check for `pyproject.toml` (Poetry project indicator)
2. If exists, run `poetry install` to set up environment
3. If not exists, initialise with `poetry init`
4. Verify installation success with `poetry show`

```bash
# Check for Poetry project
if [ -f "pyproject.toml" ]; then
    echo "Poetry project detected"
    poetry install --with dev
else
    echo "Initialising Poetry project..."
    poetry init
fi

# Verify installation
poetry show
```

### 5.2 CI/CD Setup

```bash
# Install Poetry in CI
curl -sSL https://install.python-poetry.org | python3 -

# Install dependencies (production only)
poetry install --only main

# Install with dev dependencies (for testing)
poetry install --with dev

# Run tests
poetry run pytest
```

## 6. Dependency Documentation

### 6.1 README.md Dependencies Section

Document major dependencies in README.md:

```markdown
## Dependencies

This project uses Poetry for dependency management.

### Installation

```bash
# Install Poetry (if not installed)
curl -sSL https://install.python-poetry.org | python3 -

# Install project dependencies
poetry install

# Install with development dependencies
poetry install --with dev
```

### Production Dependencies
- **numpy** (^1.24.0): Numerical computing library
- **pandas** (^2.0.0): Data manipulation and analysis
- **requests** (^2.31.0): HTTP library for API calls

### Development Dependencies
- **pytest** (^7.3.0): Testing framework
- **black** (^23.3.0): Code formatter
- **mypy** (^1.3.0): Static type checker
- **ruff** (^0.0.272): Fast Python linter
```

### 6.2 Dependency Justification

For major dependencies, document:
- Why the dependency is needed
- What functionality it provides
- Any alternatives considered
- Version constraints and why

## 7. Security and Updates

### 7.1 Security Scanning

```bash
# Check for security vulnerabilities
poetry run pip-audit

# Or use safety
poetry add --group dev safety
poetry run safety check
```

### 7.2 Regular Updates

```bash
# Check for outdated packages
poetry show --outdated

# Update all packages (within constraints)
poetry update

# Update lock file after manual pyproject.toml changes
poetry lock
```

## 8. Trivial Project Exception (Manual venv)

**ONLY** for projects meeting ALL criteria in Section 1.2:

### 8.1 Manual venv Setup

```bash
# Create virtual environment
python3 -m venv .venv

# Activate (Linux/Mac)
source .venv/bin/activate

# Activate (Windows)
.venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Deactivate
deactivate
```

### 8.2 requirements.txt Format

```txt
# requirements.txt - Pin exact versions
numpy==1.24.3
requests==2.31.0
```

### 8.3 Update Protocol for Manual venv

```bash
# Install new package
pip install package-name

# IMMEDIATELY update requirements
pip freeze > requirements.txt

# Commit both code and requirements together
git add src/module.py requirements.txt
git commit -m "feat: add new feature using package-name"
```

## 9. Pre-Commit Dependency Checks

### 9.1 Mandatory Checks

Before committing, verify:
- [ ] `pyproject.toml` is updated if packages were added/removed
- [ ] `poetry.lock` is updated and committed
- [ ] All dependencies are documented in README.md
- [ ] No system-wide package installations
- [ ] Virtual environment is active (Poetry or manual)

## 10. Enforcement

### 10.1 Violations

**STRICTLY FORBIDDEN**:
- Installing packages without updating pyproject.toml/poetry.lock
- Committing code without updated dependency files
- Installing packages to system Python
- Using pip directly instead of Poetry (except for trivial projects)
- Skipping virtual environment
- Committing with missing dependencies
- Not committing poetry.lock file

### 10.2 CI/CD Integration

All pull requests MUST:
- Include updated pyproject.toml and poetry.lock
- Pass dependency installation tests
- Have no security vulnerabilities
- Document new dependencies

## 11. Dependency Management Checklist

Before committing, verify:
- [ ] Poetry virtual environment is active (`poetry shell` or `poetry run`)
- [ ] New packages added via `poetry add`
- [ ] `pyproject.toml` reflects all dependencies
- [ ] `poetry.lock` is updated and staged
- [ ] Dependencies are documented in README.md
- [ ] No system-wide installations
- [ ] All dependencies are necessary
- [ ] Version constraints are appropriate (prefer ^)
- [ ] No security vulnerabilities (`poetry run pip-audit`)
