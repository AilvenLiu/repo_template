# Python Forbidden Practices

> **This document defines absolutely forbidden practices for Python development.**
> These rules apply to all Python projects without exception.
> Violations are considered critical failures.

## Overview

This document consolidates all forbidden practices that Claude Code MUST NEVER perform
when working on Python projects. These are non-negotiable constraints that apply
regardless of context or user instructions.

## 1. Git and Version Control

### 1.1 Protected Branch Commits

**ABSOLUTELY FORBIDDEN**: Committing directly to protected branches.

Protected branches include:
- `master`
- `main`
- `develop`
- `release/*`
- `hotfix/*`

**Always** work on feature branches and create pull requests.

### 1.2 Committing Without Validation

**FORBIDDEN**:
- Committing code without running formatters (black, isort/ruff)
- Committing code with failing tests
- Committing code without type checking (mypy)
- Skipping pre-commit validation

## 2. Environment and Dependencies

### 2.1 System Python Installation

**ABSOLUTELY FORBIDDEN**: Installing packages to system Python.

```python
# FORBIDDEN: Installing to system Python
pip install package-name  # Without virtual environment

# REQUIRED: Always use virtual environments
python -m venv .venv
source .venv/bin/activate
pip install package-name
```

### 2.2 Dependency Management

**FORBIDDEN**:
- Skipping requirements.txt update after installing packages
- Using unpinned dependencies in production
- Installing packages without documenting them

## 3. Import Practices

### 3.1 Wildcard Imports

**FORBIDDEN**: Using `import *` in application code.

```python
# FORBIDDEN: Wildcard imports
from module import *

# ALLOWED: Explicit imports
from module import specific_function, SpecificClass

# EXCEPTION: Only allowed in __init__.py for re-exports
# __init__.py
from .submodule import *  # Acceptable for public API
```

### 3.2 sys.path Modification

**FORBIDDEN**: Modifying `sys.path` in application code.

```python
# FORBIDDEN: Modifying sys.path
import sys
sys.path.insert(0, '/some/path')
sys.path.append('/another/path')

# ALLOWED: Proper package structure and installation
# Use setup.py, pyproject.toml, or pip install -e .
```

## 4. Function and Method Definitions

### 4.1 Mutable Default Arguments

**ABSOLUTELY FORBIDDEN**: Using mutable default arguments.

```python
# FORBIDDEN: Mutable default arguments
def process_items(items=[]):  # BUG: List is shared across calls
    items.append('new')
    return items

def configure(options={}):  # BUG: Dict is shared across calls
    options['key'] = 'value'
    return options

# REQUIRED: Use None and create new objects
def process_items(items=None):
    if items is None:
        items = []
    items.append('new')
    return items

def configure(options=None):
    if options is None:
        options = {}
    options['key'] = 'value'
    return options
```

### 4.2 Missing Type Hints

**FORBIDDEN**: Omitting type hints in public APIs.

```python
# FORBIDDEN: No type hints
def process(data):
    return data.upper()

# REQUIRED: Type hints for all public functions
def process(data: str) -> str:
    return data.upper()
```

## 5. Exception Handling

### 5.1 Bare Except Clauses

**ABSOLUTELY FORBIDDEN**: Using bare `except:` clauses.

```python
# FORBIDDEN: Bare except
try:
    risky_operation()
except:  # Catches everything including SystemExit, KeyboardInterrupt
    pass

# REQUIRED: Specific exception handling
try:
    risky_operation()
except ValueError as e:
    logger.error(f"Invalid value: {e}")
except IOError as e:
    logger.error(f"IO error: {e}")
except Exception as e:  # If you must catch all, be explicit
    logger.error(f"Unexpected error: {e}")
    raise  # Re-raise after logging
```

## 6. Security Practices

### 6.1 Dynamic Code Execution

**ABSOLUTELY FORBIDDEN**: Using `eval()` or `exec()` on untrusted input.

```python
# FORBIDDEN: eval/exec on user input
user_input = request.get('expression')
result = eval(user_input)  # SECURITY VULNERABILITY

user_code = request.get('code')
exec(user_code)  # SECURITY VULNERABILITY

# REQUIRED: Safe alternatives
import ast
# For simple expressions, use ast.literal_eval
user_input = "{'key': 'value'}"
result = ast.literal_eval(user_input)  # Safe for literals only

# For complex needs, use proper parsing or sandboxing
```

### 6.2 Hardcoded Secrets

**ABSOLUTELY FORBIDDEN**: Hardcoding secrets or credentials.

```python
# FORBIDDEN: Hardcoded secrets
API_KEY = "sk-1234567890abcdef"
DATABASE_PASSWORD = "mysecretpassword"
SECRET_KEY = "hardcoded-secret-key"

# REQUIRED: Environment variables or secret management
import os
API_KEY = os.environ.get('API_KEY')
DATABASE_PASSWORD = os.environ.get('DATABASE_PASSWORD')

# Or use a secrets manager
from secrets_manager import get_secret
API_KEY = get_secret('api-key')
```

## 7. API and Compatibility

### 7.1 Deprecated APIs

**FORBIDDEN**: Using deprecated APIs without justification.

```python
# FORBIDDEN: Using deprecated APIs
import imp  # Deprecated since Python 3.4
from collections import Mapping  # Deprecated since Python 3.3

# REQUIRED: Use modern alternatives
import importlib
from collections.abc import Mapping
```

### 7.2 Python Version Compatibility

**FORBIDDEN**: Using features not available in minimum supported Python version.

```python
# If minimum version is Python 3.9:

# FORBIDDEN: Python 3.10+ features
match value:  # Pattern matching (3.10+)
    case 1:
        pass

# REQUIRED: Compatible alternatives
if value == 1:
    pass
```

## 8. Code Quality

### 8.1 Ignoring Linter Warnings

**FORBIDDEN**: Ignoring linter warnings without documented justification.

```python
# FORBIDDEN: Blanket ignore
# type: ignore
# noqa

# ALLOWED: Specific ignore with justification
# type: ignore[arg-type]  # Third-party library has incorrect stubs
# noqa: E501  # URL cannot be shortened
```

### 8.2 Dead Code

**FORBIDDEN**: Leaving dead or unreachable code.

```python
# FORBIDDEN: Dead code
def process():
    return result
    print("This never executes")  # Dead code

# FORBIDDEN: Commented-out code
# def old_function():
#     pass

# REQUIRED: Remove dead code completely
def process():
    return result
```

## 9. Summary Table

| Practice | Status | Alternative |
|----------|--------|-------------|
| Direct commits to protected branches | FORBIDDEN | Use feature branches |
| Installing to system Python | FORBIDDEN | Use virtual environments |
| `import *` in application code | FORBIDDEN | Explicit imports |
| Modifying `sys.path` | FORBIDDEN | Proper package structure |
| Mutable default arguments | FORBIDDEN | Use `None` default |
| Bare `except:` clauses | FORBIDDEN | Specific exceptions |
| `eval()`/`exec()` on untrusted input | FORBIDDEN | Safe parsing |
| Hardcoded secrets | FORBIDDEN | Environment variables |
| Deprecated APIs | FORBIDDEN | Modern alternatives |
| Missing type hints in public APIs | FORBIDDEN | Add type hints |
| Ignoring linter warnings | FORBIDDEN | Fix or document |
| Dead/commented code | FORBIDDEN | Remove completely |

## 10. Enforcement

### 10.1 Pre-Commit Checks

All forbidden practices MUST be caught by pre-commit validation:
- black (formatting)
- ruff (linting, including many forbidden practices)
- mypy (type checking)
- pytest (tests must pass)

### 10.2 Code Review

Pull requests MUST be rejected if they contain any forbidden practices.

### 10.3 CI/CD

CI pipelines MUST fail if any forbidden practice is detected.

## 11. Exceptions

There are NO exceptions to these rules unless:
1. Explicitly documented in the codebase with justification
2. Approved by the project maintainer
3. Tracked in a technical debt register

Even then, the following are NEVER acceptable:
- Hardcoded secrets
- `eval()`/`exec()` on untrusted input
- Direct commits to protected branches
