# Python Dependency Management

> **This document defines mandatory dependency management standards for Python projects.**
> All dependency changes must follow these rules to ensure reproducibility and maintainability.
> These rules are non-negotiable and admit no exceptions.

## 1. Poetry: Mandatory, No Exceptions

### 1.1 Poetry is the Only Permitted Tool

**MANDATORY**: Use **Poetry** for ALL Python dependency management, always, without exception.

There is no "trivial project" exception. There is no "quick prototype" exception. There is no
exception of any kind. Every Python project, regardless of size or purpose, uses Poetry.

Poetry provides:
- Unified virtual environment management
- Deterministic dependency resolution with lock files
- Modern `pyproject.toml`-native configuration
- Reproducible builds via `poetry.lock`
- Clean separation of production and development dependencies

**FORBIDDEN under all circumstances**:
- `pip install` / `pip3 install` — for any reason, any context
- `python -m pip install` — for any reason, any context
- `requirements.txt`-only projects
- manual `venv` creation without Poetry
- direct `python` / `python3` / `pip` / `pip3` invocations for application or test workflows

The only exception is agent infrastructure (`bin/agent-*`, `.ai/scripts/*`) which use
controlled interpreter fallback for bootstrap purposes only.

### 1.2 Environment Check Procedure (MANDATORY at Session Start)

**STOP and ask the user if any check fails. Do not proceed.**

Before any Python work on an existing project, verify all of the following:

#### Check 1 — Poetry installed via pipx at `$HOME/.local/bin`

```bash
# Poetry MUST be at ~/.local/bin/poetry (pipx install location)
ls ~/.local/bin/poetry && echo "OK" || echo "FAIL: poetry not found at ~/.local/bin/poetry"

# Verify it is not a system-level install
which poetry
```

Expected: `~/.local/bin/poetry` exists and `which poetry` returns `~/.local/bin/poetry`.

If poetry is not found at `~/.local/bin/poetry` — **STOP and ask the user to install it via pipx**:

```bash
PIPX_HOME="$HOME/.local/share/pipx" \
PIPX_BIN_DIR="$HOME/.local/bin" \
pipx install poetry
```

#### Check 2 — In-project virtual environment configured

```bash
# Check project-local poetry.toml
cat poetry.toml 2>/dev/null || echo "MISSING"
```

Expected: `poetry.toml` exists and contains `in-project = true` under `[virtualenvs]`.

If missing — **STOP and ask the user**. The correct `poetry.toml` is:

```toml
[virtualenvs]
in-project = true

[virtualenvs.options]
system-site-packages = false
```

Also verify the venv is actually in-project (if it already exists):

```bash
poetry env info --path 2>/dev/null
```

The returned path must be inside the project directory (`.venv/`).
If it is outside — **STOP and ask the user**; do not silently relocate it.

#### Check 3 — TUNA configured as primary PyPI source

```bash
grep -A3 '\[\[tool.poetry.source\]\]' pyproject.toml
```

Expected output must contain:
```
url = "https://pypi.tuna.tsinghua.edu.cn/simple/"
priority = "primary"
```

If TUNA is not configured as primary — **STOP and ask the user**.

Once all three checks pass, proceed with normal workflow.

### 1.3 Python Version Requirement

**CRITICAL**: Poetry MUST use Python 3.10 or higher.

Use pyenv to manage Python versions:

```bash
# Install pyenv
curl https://pyenv.run | bash

# Install required Python version
pyenv install 3.10.12

# Set for this project
pyenv local 3.10.12
```

Do NOT use system Python (`/usr/bin/python3`, `/usr/local/bin/python3`).

### 1.4 Virtual Environment Location

- **MANDATORY**: Poetry MUST create virtual environments inside the project directory (`.venv/`)
- This is controlled by `poetry.toml` with `in-project = true`
- **NEVER** allow Poetry to create venvs in its centralised cache (`~/.cache/pypoetry/`)

If Poetry has already created a venv outside the project, relocate it:

```bash
# Check current location
poetry env info --path

# Remove the external venv
poetry env remove --all

# Ensure poetry.toml exists with in-project = true
# Then recreate
poetry install
```

### 1.5 Dependency Management Procedure

**CRITICAL**: When adding ANY dependency, use the dependency management procedure:

```
+-------------------------------------------------------------+
| DEPENDENCY MANAGEMENT PROTOCOL                              |
|                                                             |
| WHEN: Adding a new package to the project                   |
| USE: The dependency management procedure                    |
|                                                             |
| CORRECT EXAMPLES:                                           |
|   poetry add requests                                       |
|   poetry add pytest --group dev                             |
|                                                             |
| FORBIDDEN COMMANDS (no exceptions):                         |
|   pip install requests          # FORBIDDEN                 |
|   pip3 install requests         # FORBIDDEN                 |
|   python -m pip install         # FORBIDDEN                 |
|   Manual pyproject.toml edit    # use poetry add            |
|                                                             |
| WHY: Ensures pyproject.toml + poetry.lock stay in sync,    |
|      preserves TUNA source config, keeps venv in-project.  |
+-------------------------------------------------------------+
```

## 2. Required File Structure

### 2.1 Mandatory Files

Every Poetry-managed project MUST have:
- **`pyproject.toml`**: Project metadata, dependencies, tool config, TUNA source
- **`poetry.lock`**: Locked dependency versions (MUST be committed)
- **`poetry.toml`**: Local Poetry config with `in-project = true`

### 2.2 pyproject.toml Reference

```toml
[tool.poetry]
name = "my-project"
version = "0.1.0"
description = "Project description"
authors = ["Author Name <author@example.com>"]
readme = "README.md"
packages = [{include = "my_project", from = "src"}]

[tool.poetry.dependencies]
python = "3.10.12"
pydantic = "2.13.4"

[tool.poetry.group.dev.dependencies]
pytest = "9.0.3"
pytest-cov = "7.1.0"
ruff = "0.15.16"
mypy = "2.1.0"

[[tool.poetry.source]]
name = "tuna"
url = "https://pypi.tuna.tsinghua.edu.cn/simple/"
priority = "primary"

[build-system]
requires = ["poetry-core>=1.0.0"]
build-backend = "poetry.core.masonry.api"

[tool.ruff]
line-length = 120
target-version = "py310"

[tool.ruff.lint]
select = ["E", "W", "F", "I", "N", "UP", "B", "SIM", "RUF"]

[tool.mypy]
python_version = "3.10"
strict = true
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true

[tool.pytest.ini_options]
testpaths = ["tests"]
```

Version pinning: use exact versions (`"3.10.12"`) for the Python interpreter, and for
production dependencies when determinism is critical. Use caret (`"^2.0.0"`) for
development tools.

### 2.3 poetry.toml Reference

```toml
[virtualenvs]
in-project = true

[virtualenvs.options]
system-site-packages = false
```

## 3. Poetry Installation

### 3.1 Mandatory Installation Method: pipx

Poetry MUST be installed via pipx into `$HOME/.local`:

```bash
# Step 1: Install pipx (if not present)
python3 -m pip install --user pipx
python3 -m pipx ensurepath

# Step 2: Install Poetry via pipx into $HOME/.local
PIPX_HOME="$HOME/.local/share/pipx" \
PIPX_BIN_DIR="$HOME/.local/bin" \
pipx install poetry

# Step 3: Verify
~/.local/bin/poetry --version
```

**Why pipx?**
- Isolates Poetry from all project environments
- Installs to `$HOME` not system paths — no sudo needed, no system contamination
- Poetry manages its own dependencies without interfering with project venvs
- Deterministic installation location: always `~/.local/bin/poetry`

**FORBIDDEN installation methods**:
- `curl -sSL https://install.python-poetry.org | python3 -` — unpredictable install path
- `pip install poetry` — installs into current Python, causes conflicts
- System package managers (`brew install poetry`, `apt install python3-poetry`) — wrong location

### 3.2 CI/CD Installation

For CI environments, install via pipx in the same way:

```bash
python3 -m pip install pipx
PIPX_HOME="$HOME/.local/share/pipx" \
PIPX_BIN_DIR="$HOME/.local/bin" \
pipx install poetry

export PATH="$HOME/.local/bin:$PATH"
poetry install --with dev
poetry run pytest
```

## 4. TUNA PyPI Mirror Configuration

### 4.1 Why TUNA

TUNA (Tsinghua University Open Source Mirror) provides:
- High-speed access in China and East Asia
- Complete PyPI mirror with all packages
- Reliable uptime and indexing

### 4.2 Required Configuration

Every Python project's `pyproject.toml` MUST include TUNA as the primary source:

```toml
[[tool.poetry.source]]
name = "tuna"
url = "https://pypi.tuna.tsinghua.edu.cn/simple/"
priority = "primary"
```

This MUST appear before any `[tool.poetry.dependencies]` sections take effect.

### 4.3 Verify Source Configuration

```bash
poetry config --list | grep source
# Should show: repositories.tuna.url = "https://pypi.tuna.tsinghua.edu.cn/simple/"
```

## 5. Poetry Commands Reference

### 5.1 Project Setup

```bash
# Create new project
poetry new project-name --src
cd project-name

# Configure in-project venv (create poetry.toml)
poetry config virtualenvs.in-project true --local

# Install all dependencies
poetry install --with dev
```

### 5.2 Dependency Management

```bash
# Add production dependency
poetry add package-name

# Add pinned production dependency
poetry add "package-name==2.0.0"

# Add development dependency
poetry add --group dev package-name

# Remove dependency
poetry remove package-name

# Update specific package
poetry update package-name

# Update all packages (within constraints)
poetry update

# Show installed packages
poetry show --tree

# Check for outdated packages
poetry show --outdated
```

### 5.3 Running Commands

```bash
# Run in virtual environment (CORRECT way)
poetry run python script.py
poetry run pytest
poetry run ruff format .
poetry run ruff check .
poetry run mypy src/

# Activate shell (for interactive sessions)
poetry shell

# WRONG — never use these for project work:
# python script.py
# python3 script.py
# pytest (without poetry run)
```

### 5.4 Lock File Management

```bash
# Regenerate lock file after manual pyproject.toml edits
poetry lock

# Install from lock file only (CI/CD)
poetry install --no-root

# Install specific groups
poetry install --only main
poetry install --with dev
```

## 6. Mandatory Dependency Update Protocol

When installing ANY new package:

1. Use `poetry add package-name` (or `poetry add --group dev package-name`)
2. Verify `pyproject.toml` reflects the new dependency
3. Verify `poetry.lock` is regenerated
4. Commit both files in the SAME commit as the code that uses the package

```bash
poetry add requests
git add pyproject.toml poetry.lock src/module_using_requests.py
git commit -m "feat: add requests for HTTP client"
```

## 7. Pre-Commit Dependency Checks

Before committing, verify:
- [ ] `poetry.toml` exists with `in-project = true`
- [ ] `pyproject.toml` has TUNA as `[[tool.poetry.source]]` with `priority = "primary"`
- [ ] `pyproject.toml` is updated if packages were added/removed
- [ ] `poetry.lock` is updated and staged alongside `pyproject.toml`
- [ ] No system-wide package installations occurred
- [ ] All `poetry run` commands confirm the venv is `.venv/` inside project

## 8. Enforcement

### 8.1 Violations — ABSOLUTELY FORBIDDEN

- Using `pip` / `pip3` / `python3 -m pip` for any package operation
- Using `python` / `python3` directly for application or test workflows
- Installing packages to system Python
- Omitting TUNA from `[[tool.poetry.source]]` with `primary` priority
- Creating venvs outside the project directory
- Installing Poetry via the curl installer or system package manager
- Omitting `poetry.toml` from the project
- Committing `pyproject.toml` without committing `poetry.lock`
- Skipping the environment check procedure at session start

### 8.2 On Check Failure

If any environment check (Section 1.2) fails:
1. Report clearly which check failed and why
2. STOP — do not attempt to auto-fix silently
3. Present the exact remediation command
4. Wait for the user to confirm the fix before continuing
