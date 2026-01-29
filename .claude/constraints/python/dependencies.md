# Python Dependency Management

> **This document defines mandatory dependency management standards for Python projects.**
> All dependency changes must follow these rules to ensure reproducibility and maintainability.

## 1. Dependency Management Tools

### 1.1 Acceptable Tools
All of the following tools are acceptable for virtual environment management:
- **venv** (built-in, recommended for simple projects)
- **poetry** (comprehensive dependency management and packaging)
- **pipenv** (alternative with Pipfile)
- **conda** (for scientific computing with non-Python dependencies)

Choose based on project needs. For simple projects, venv is sufficient. For complex projects with packaging requirements, poetry is recommended.

### 1.2 Virtual Environment Requirement
- **MANDATORY**: ALWAYS use virtual environments (never install to system Python)
- **NEVER** install packages globally
- **ALWAYS** activate virtual environment before installing packages

## 2. Requirements Files

### 2.1 Standard Requirements Files
- **requirements.txt**: Pin exact versions for reproducibility (production dependencies)
- **requirements-dev.txt**: Development dependencies (testing, linting, etc.)
- **pyproject.toml**: Modern Python project metadata (PEP 518)

### 2.2 Requirements.txt Format
```txt
# requirements.txt - Production dependencies
# Pin exact versions for reproducibility
numpy==1.24.3
pandas==2.0.2
requests==2.31.0
python-dateutil==2.8.2

# requirements-dev.txt - Development dependencies
pytest>=7.3.0,<8.0.0
black==23.3.0
mypy>=1.3.0
ruff==0.0.272
isort>=5.12.0
```

### 2.3 Version Pinning Strategy
```txt
# Exact version (production dependencies)
numpy==1.24.3

# Compatible version range (development dependencies)
pytest>=7.3.0,<8.0.0

# Minimum version
mypy>=1.3.0

# Avoid using >= without upper bound in production
# Bad: requests>=2.0.0  (too permissive)
# Good: requests>=2.31.0,<3.0.0
```

## 3. Mandatory Dependency Update Protocol

### 3.1 Critical Requirement
**CRITICAL**: When installing ANY new package, Claude Code MUST:

1. Install the package
2. **IMMEDIATELY** update requirements file
3. Commit the updated requirements file in the SAME commit as code using the package
4. Document the package purpose in README.md if it's a major dependency

### 3.2 Using pip
```bash
# Install new package
pip install package-name

# IMMEDIATELY update requirements
pip freeze > requirements.txt

# Commit both code and requirements together
git add src/module.py requirements.txt
git commit -m "feat: add new feature using package-name"
```

### 3.3 Using poetry
```bash
# Install new package (automatically updates pyproject.toml and poetry.lock)
poetry add package-name

# Install development dependency
poetry add --group dev package-name

# Commit changes
git add pyproject.toml poetry.lock src/module.py
git commit -m "feat: add new feature using package-name"
```

### 3.4 Using pipenv
```bash
# Install new package (automatically updates Pipfile and Pipfile.lock)
pipenv install package-name

# Install development dependency
pipenv install --dev package-name

# Commit changes
git add Pipfile Pipfile.lock src/module.py
git commit -m "feat: add new feature using package-name"
```

## 4. pyproject.toml Structure

### 4.1 Complete pyproject.toml Example
```toml
[project]
name = "project-name"
version = "0.1.0"
description = "Project description"
requires-python = ">=3.9"
authors = [
    {name = "Author Name", email = "author@example.com"}
]
readme = "README.md"
license = {text = "MIT"}
keywords = ["keyword1", "keyword2"]
classifiers = [
    "Development Status :: 3 - Alpha",
    "Intended Audience :: Developers",
    "License :: OSI Approved :: MIT License",
    "Programming Language :: Python :: 3.9",
    "Programming Language :: Python :: 3.10",
    "Programming Language :: Python :: 3.11",
    "Programming Language :: Python :: 3.12",
]

dependencies = [
    "numpy>=1.24.0,<2.0.0",
    "pandas>=2.0.0,<3.0.0",
    "requests>=2.31.0,<3.0.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.3.0,<8.0.0",
    "pytest-cov>=4.0.0",
    "black>=23.3.0",
    "mypy>=1.3.0",
    "ruff>=0.0.272",
    "isort>=5.12.0",
]

[project.urls]
Homepage = "https://github.com/user/project"
Documentation = "https://project.readthedocs.io"
Repository = "https://github.com/user/project"
Issues = "https://github.com/user/project/issues"

[build-system]
requires = ["setuptools>=61.0", "wheel"]
build-backend = "setuptools.build_meta"

[tool.setuptools.packages.find]
where = ["src"]

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

## 5. Virtual Environment Setup

### 5.1 Using venv (Built-in)
```bash
# Create virtual environment
python3.9 -m venv .venv

# Activate (Linux/Mac)
source .venv/bin/activate

# Activate (Windows)
.venv\Scripts\activate

# Verify activation
which python
python --version

# Install dependencies
pip install -r requirements.txt

# Deactivate
deactivate
```

### 5.2 Using poetry
```bash
# Install poetry
curl -sSL https://install.python-poetry.org | python3 -

# Create new project
poetry new project-name

# Or initialise in existing directory
poetry init

# Install dependencies
poetry install

# Install with development dependencies
poetry install --with dev

# Activate virtual environment
poetry shell

# Run command in virtual environment
poetry run python script.py

# Add dependency
poetry add package-name

# Add development dependency
poetry add --group dev package-name

# Update dependencies
poetry update

# Show installed packages
poetry show
```

### 5.3 Using pipenv
```bash
# Install pipenv
pip install pipenv

# Create virtual environment and install dependencies
pipenv install

# Install development dependencies
pipenv install --dev

# Activate virtual environment
pipenv shell

# Run command in virtual environment
pipenv run python script.py

# Add dependency
pipenv install package-name

# Add development dependency
pipenv install --dev package-name

# Update dependencies
pipenv update

# Show dependency graph
pipenv graph
```

## 6. Dependency Documentation

### 6.1 README.md Dependencies Section
Document major dependencies in README.md:

```markdown
## Dependencies

### Production Dependencies
- **numpy** (1.24.0+): Numerical computing library
- **pandas** (2.0.0+): Data manipulation and analysis
- **requests** (2.31.0+): HTTP library for API calls
- **python-dateutil** (2.8.0+): Date and time utilities

### Development Dependencies
- **pytest** (7.3.0+): Testing framework
- **black** (23.3.0+): Code formatter
- **mypy** (1.3.0+): Static type checker
- **ruff** (0.0.272+): Fast Python linter
```

### 6.2 Dependency Justification
For major dependencies, document:
- Why the dependency is needed
- What functionality it provides
- Any alternatives considered
- Version constraints and why

## 7. Dependency Updates

### 7.1 Regular Dependency Updates
```bash
# Check for outdated packages
pip list --outdated

# Or with poetry
poetry show --outdated

# Update specific package
pip install --upgrade package-name
pip freeze > requirements.txt

# Or with poetry
poetry update package-name

# Update all packages (use with caution)
pip install --upgrade -r requirements.txt
pip freeze > requirements.txt
```

### 7.2 Security Updates
```bash
# Check for security vulnerabilities
pip-audit

# Or use safety
pip install safety
safety check

# Update vulnerable packages immediately
pip install --upgrade vulnerable-package
pip freeze > requirements.txt
```

## 8. Dependency Conflicts

### 8.1 Resolving Conflicts
```bash
# Check dependency tree
pip show package-name

# Or with poetry
poetry show --tree

# Or with pipenv
pipenv graph

# Resolve conflicts by specifying compatible versions
# requirements.txt
package-a==1.0.0
package-b>=2.0.0,<3.0.0  # Compatible with package-a
```

### 8.2 Dependency Constraints
```txt
# constraints.txt - Specify version constraints
numpy<2.0.0
pandas>=2.0.0,<3.0.0

# Install with constraints
pip install -r requirements.txt -c constraints.txt
```

## 9. Environment Setup Protocol

### 9.1 Mandatory Setup Steps
When starting work on a project, Claude Code MUST:

1. Check for existing virtual environment
2. If none exists, create one using preferred tool
3. Verify Python version matches requirements
4. Install dependencies from requirements file
5. Verify installation success

```bash
# Check for virtual environment
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    python3.9 -m venv .venv
fi

# Activate virtual environment
source .venv/bin/activate

# Verify Python version
python --version

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Verify installation
pip list
```

## 10. Dependency Best Practices

### 10.1 Version Pinning Guidelines
- **Production**: Pin exact versions for reproducibility
- **Development**: Use version ranges for flexibility
- **Libraries**: Use minimum version with upper bound
- **Applications**: Pin exact versions

### 10.2 Dependency Minimisation
- Only add dependencies when necessary
- Prefer standard library when possible
- Avoid dependencies with many transitive dependencies
- Regularly review and remove unused dependencies

### 10.3 Dependency Security
- Regularly update dependencies for security patches
- Use `pip-audit` or `safety` to check for vulnerabilities
- Subscribe to security advisories for critical dependencies
- Document any pinned versions due to security issues

## 11. Pre-Commit Dependency Checks

### 11.1 Mandatory Checks
Before committing, verify:
- [ ] requirements.txt is updated if packages were installed
- [ ] pyproject.toml is updated if using poetry
- [ ] Pipfile.lock is updated if using pipenv
- [ ] All dependencies are documented
- [ ] No system-wide package installations
- [ ] Virtual environment is activated

## 12. Enforcement

### 12.1 Violations
**STRICTLY FORBIDDEN**:
- Installing packages without updating requirements
- Committing code without updated requirements file
- Installing packages to system Python
- Using undocumented dependencies
- Skipping virtual environment
- Committing with missing dependencies

### 12.2 CI/CD Integration
All pull requests MUST:
- Include updated requirements files
- Pass dependency installation tests
- Have no security vulnerabilities
- Document new dependencies

## 13. Dependency Management Checklist

Before committing, verify:
- [ ] Virtual environment is activated
- [ ] New packages are installed in virtual environment
- [ ] requirements.txt is updated (`pip freeze > requirements.txt`)
- [ ] pyproject.toml is updated (if using poetry)
- [ ] Dependencies are documented in README.md
- [ ] No system-wide installations
- [ ] All dependencies are necessary
- [ ] Version constraints are appropriate
- [ ] No security vulnerabilities (`pip-audit` or `safety check`)