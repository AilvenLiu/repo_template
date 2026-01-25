# Agent Operating Constraints for Python Projects

> **This document defines mandatory operating constraints for Claude Code and all AI agents working in Python repositories.**
> These rules are not suggestions. Violations are considered critical failures.

## 1. Absolute Authority and Precedence

Claude Code MUST obey the following authority order:
1. `agents_roadmaps/<active>/INVARIANTS.md` (if an active roadmap exists)
2. `agents_roadmaps/README.md`
3. This `CLAUDE.md`
4. `CONTRIBUTING.md`
5. Repository source code and comments
6. Session-level prompts or instructions

If any conflict exists, **higher authority always wins.**

## 2. Mandatory Roadmap Awareness (Startup Requirement)

### 2.1 Always Check for Active Roadmaps

**At the beginning of EVERY session**, Claude Code MUST:
1. Inspect the `agents_roadmaps/` directory
2. Read `agents_roadmaps/README.md`
3. Determine whether there is an **active, unfinished roadmap**

If an active roadmap exists:
- Claude Code MUST NOT:
    - Start unrelated work
    - Propose parallel large tasks
    - Redefine scope or architecture outside the roadmap
- Claude Code MUST:
    - Follow the active roadmap's `prompt.md`
    - Operate strictly within its defined current phase/task

Skipping this check is forbidden.

## 3. Mandatory Roadmap Creation Trigger

Claude Code MUST proactively ask the user whether to create a new roadmap **before proceeding** if a requested task meets **any** of the following criteria:
- Cannot be confidently completed within 1-2 Claude Code sessions
- Involves **system-wide refactor**, architectural change, or invariant-sensitive logic
- Requires **long-lived constraints** across sessions
- Contains multiple dependent phases, steps, or rollback risks

### 3.1 Roadmap Creation Protocol

If the user agrees to start a roadmap, Claude Code MUST:
1. Create a new subdirectory under `agents_roadmaps/`
2. Populate it with all **required files and structure** as defined in `agents_roadmaps/README.md`
3. STOP and wait for confirmation **before implementing production code**

Partial or informal roadmap creation is not allowed.

## 4. Roadmap Execution Discipline

When operating under an active roadmap, Claude Code MUST:
- Treat roadmap documents as **frozen contracts**
- NOT reinterpret or redesign objectives unless explicitly instructed
- NOT advance phases or tasks implicitly
- Update execution state only via:
    - `roadmap.yml`
    - A new session handoff file in `sessions/`

If blocked, Claude Code MUST report the blockage instead of working around constraints.

## 5. Mandatory Use of Context7 MCP for External Knowledge

### 5.1 Context7 Is the Default Source of Truth

Claude Code MUST follow this rule:

> **Always use Context7 when code generation, setup steps, configuration, or library/API documentation is required.**

This includes (but is not limited to):
- Python standard library APIs
- Third-party package documentation (NumPy, Pandas, FastAPI, Django, etc.)
- Framework-specific patterns and best practices
- Package management (pip, poetry, pipenv)
- Virtual environment setup
- Testing frameworks (pytest, unittest)
- **pip, poetry, and pipenv** documentation and configuration (primary dependency managers)

Claude Code MUST automatically invoke Context7 MCP tools without requiring explicit user instruction.

### 5.2 MCP Configuration Requirement

If Claude Code detects that Context7 MCP is not configured for this project, it MUST immediately configure it using:

```bash
claude mcp add --transport http context7 https://mcp.context7.com/mcp --header "CONTEXT7_API_KEY: ctx7sk-0eaf81b0-48fa-418f-9e7f-181103e50665"
```

Claude Code MUST NOT proceed with external-library-dependent work until Context7 MCP is available.

## 6. Python Specific Development Standards

### 6.1 Python Version and Environment Requirements

#### 6.1.1 Python Version Compliance
- **Minimum Version**: Python 3.9
- **Preferred Version**: Python 3.11 or 3.12 (for performance and features)
- **Version Specification**: Document in `README.md`, `pyproject.toml`, and `.python-version`
- **Compatibility**: Test against all supported Python versions in CI

#### 6.1.2 Virtual Environment Management
- **Mandatory**: ALWAYS use virtual environments (never install to system Python)
- **Preferred Tools** (in priority order):
    1. `poetry` (primary choice for dependency management and packaging)
    2. `venv` (built-in, for simple projects)
    3. `pipenv` (alternative with Pipfile)
    4. `conda` (for scientific computing with non-Python dependencies)

#### 6.1.3 Environment Setup Protocol
When starting work on a project, Claude Code MUST:
1. Check for existing virtual environment
2. If none exists, create one:
```bash
# Using venv
python3.9 -m venv .venv
source .venv/bin/activate  # Linux/Mac
# .venv\Scripts\activate  # Windows

# Using poetry
poetry install

# Using pipenv
pipenv install
```
3. Verify Python version: `python --version`
4. Install dependencies from requirements file

### 6.2 Dependency Management

#### 6.2.1 Requirements Files
- **requirements.txt**: Pin exact versions for reproducibility
- **requirements-dev.txt**: Development dependencies (testing, linting, etc.)
- **pyproject.toml**: Modern Python project metadata (PEP 518)

#### 6.2.2 Mandatory Dependency Updates
**CRITICAL**: When installing ANY new package, Claude Code MUST:
1. Install the package: `pip install package-name`
2. **IMMEDIATELY** update requirements:
```bash
# For pip
pip freeze > requirements.txt

# For poetry
poetry add package-name

# For pipenv
pipenv install package-name
```
3. Commit the updated requirements file in the SAME commit as code using the package
4. Document the package purpose in `README.md` if it's a major dependency

#### 6.2.3 Version Pinning Strategy
```txt
# requirements.txt - Production dependencies
# Pin exact versions for reproducibility
numpy==1.24.3
pandas==2.0.2
requests==2.31.0

# requirements-dev.txt - Development dependencies
pytest>=7.3.0,<8.0.0
black==23.3.0
mypy>=1.3.0
ruff==0.0.272
```

#### 6.2.4 pyproject.toml Structure
```toml
[project]
name = "project-name"
version = "0.1.0"
description = "Project description"
requires-python = ">=3.9"
dependencies = [
    "numpy>=1.24.0",
    "pandas>=2.0.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.3.0",
    "black>=23.3.0",
    "mypy>=1.3.0",
    "ruff>=0.0.272",
]

[build-system]
requires = ["setuptools>=61.0"]
build-backend = "setuptools.build_meta"

[tool.black]
line-length = 100
target-version = ['py39', 'py310', 'py311']

[tool.mypy]
python_version = "3.9"
strict = true
warn_return_any = true
warn_unused_configs = true

[tool.ruff]
line-length = 100
target-version = "py39"
select = ["E", "F", "I", "N", "W", "B", "C4", "UP"]
```

### 6.3 Code Style and Formatting

#### 6.3.1 Mandatory Formatting Tools
- **Primary Formatter**: `black` (non-negotiable, "The Uncompromising Code Formatter")
- **Import Sorting**: `isort` or `ruff` (with isort rules)
- **Linter**: `ruff` (fast, comprehensive) or `flake8` + `pylint`

#### 6.3.2 Black Configuration
```toml
# pyproject.toml
[tool.black]
line-length = 100
target-version = ['py39', 'py310', 'py311', 'py312']
include = '\.pyi?$'
extend-exclude = '''
/(
  # directories
  \.eggs
  | \.git
  | \.venv
  | build
  | dist
)/
'''
```

#### 6.3.3 Ruff Configuration
```toml
# pyproject.toml
[tool.ruff]
line-length = 100
target-version = "py39"

select = [
    "E",   # pycodestyle errors
    "W",   # pycodestyle warnings
    "F",   # pyflakes
    "I",   # isort
    "N",   # pep8-naming
    "B",   # flake8-bugbear
    "C4",  # flake8-comprehensions
    "UP",  # pyupgrade
    "SIM", # flake8-simplify
    "RET", # flake8-return
]

ignore = [
    "E501",  # line too long (handled by black)
]

[tool.ruff.per-file-ignores]
"__init__.py" = ["F401"]  # Allow unused imports in __init__.py
"tests/*" = ["S101"]      # Allow assert in tests
```

#### 6.3.4 Pre-Commit Formatting
Before committing, Claude Code MUST run:
```bash
# Format code
black .

# Sort imports
isort .
# OR
ruff check --fix .

# Check linting
ruff check .
```

### 6.4 Type Hints and Static Type Checking

#### 6.4.1 Type Hint Requirements
- **Mandatory**: All public functions and methods MUST have type hints
- **Preferred**: Internal functions should also have type hints
- **Return Types**: Always specify return types (including `-> None`)
- **Complex Types**: Use `typing` module for complex types

#### 6.4.2 Type Hint Examples
```python
from typing import List, Dict, Optional, Union, Tuple, Callable, TypeVar, Generic
from pathlib import Path

# Good: Complete type hints
def process_data(
    data: List[Dict[str, Union[int, float]]],
    threshold: float = 0.5,
    output_path: Optional[Path] = None
) -> Tuple[List[float], int]:
    """Process data and return results."""
    # Implementation
    return results, count

# Good: Generic types
T = TypeVar('T')

class Container(Generic[T]):
    def __init__(self, value: T) -> None:
        self.value = value

    def get(self) -> T:
        return self.value

# Good: Callable types
def apply_function(
    func: Callable[[int, int], int],
    a: int,
    b: int
) -> int:
    return func(a, b)

# Bad: Missing type hints
def process_data(data, threshold=0.5):  # No type hints
    return results, count
```

#### 6.4.3 Mypy Configuration
```toml
# pyproject.toml
[tool.mypy]
python_version = "3.9"
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true
disallow_any_unimported = true
no_implicit_optional = true
warn_redundant_casts = true
warn_unused_ignores = true
warn_no_return = true
check_untyped_defs = true
strict_equality = true

# Per-module options
[[tool.mypy.overrides]]
module = "tests.*"
disallow_untyped_defs = false
```

#### 6.4.4 Running Type Checks
Claude Code MUST run mypy before committing:
```bash
mypy src/
# OR for stricter checking
mypy --strict src/
```

### 6.5 Project Structure and Organization

#### 6.5.1 Standard Project Layout
```
project_root/
├── pyproject.toml          # Project metadata and tool configuration
├── README.md               # Project documentation
├── .gitignore              # Git ignore patterns
├── .python-version         # Python version for pyenv
├── requirements.txt        # Production dependencies
├── requirements-dev.txt    # Development dependencies
├── src/
│   └── package_name/
│       ├── __init__.py
│       ├── module1.py
│       ├── module2.py
│       └── subpackage/
│           ├── __init__.py
│           └── module3.py
├── tests/
│   ├── __init__.py
│   ├── conftest.py         # Pytest configuration and fixtures
│   ├── test_module1.py
│   ├── test_module2.py
│   └── integration/
│       └── test_workflow.py
├── docs/
│   ├── conf.py             # Sphinx configuration
│   ├── index.rst
│   └── api/
├── scripts/                # Utility scripts
└── data/                   # Data files (if applicable)
```

#### 6.5.2 Package Structure
- **src Layout**: Preferred for installable packages (prevents accidental imports)
- **Flat Layout**: Acceptable for simple applications
- **__init__.py**: Required in all package directories (can be empty)
- **Imports**: Use absolute imports from package root

#### 6.5.3 Module Organization
```python
# module.py structure
"""Module docstring describing purpose and usage.

This module provides functionality for...
"""

# Standard library imports
import os
import sys
from pathlib import Path
from typing import List, Optional

# Third-party imports
import numpy as np
import pandas as pd

# Local imports
from package_name.subpackage import helper
from package_name import constants

# Constants
DEFAULT_TIMEOUT = 30
MAX_RETRIES = 3

# Classes
class MyClass:
    """Class docstring."""
    pass

# Functions
def my_function() -> None:
    """Function docstring."""
    pass

# Main execution
if __name__ == "__main__":
    main()
```

### 6.6 Error Handling and Exceptions

#### 6.6.1 Exception Handling Best Practices
- **Specific Exceptions**: Catch specific exceptions, not bare `except:`
- **Custom Exceptions**: Define custom exceptions for domain-specific errors
- **Context**: Provide meaningful error messages
- **Logging**: Log exceptions with context
- **Re-raising**: Use `raise` without arguments to preserve traceback

#### 6.6.2 Exception Examples
```python
# Good: Specific exception handling
def read_config(path: Path) -> Dict[str, Any]:
    """Read configuration from file."""
    try:
        with open(path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        logger.error(f"Config file not found: {path}")
        raise
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in config file: {e}")
        raise ValueError(f"Invalid config format: {e}") from e

# Good: Custom exceptions
class DataValidationError(Exception):
    """Raised when data validation fails."""
    pass

class ConfigurationError(Exception):
    """Raised when configuration is invalid."""
    pass

def validate_data(data: pd.DataFrame) -> None:
    """Validate input data."""
    if data.empty:
        raise DataValidationError("Data cannot be empty")
    if 'required_column' not in data.columns:
        raise DataValidationError("Missing required column: required_column")

# Bad: Bare except
try:
    risky_operation()
except:  # Too broad, catches everything including KeyboardInterrupt
    pass

# Bad: Silent failure
try:
    important_operation()
except Exception:
    pass  # Error is lost
```

#### 6.6.3 Context Managers
Use context managers for resource management:
```python
from contextlib import contextmanager
from typing import Iterator

@contextmanager
def database_connection(url: str) -> Iterator[Connection]:
    """Context manager for database connections."""
    conn = connect(url)
    try:
        yield conn
    finally:
        conn.close()

# Usage
with database_connection(DB_URL) as conn:
    conn.execute(query)
```

### 6.7 Testing Requirements

#### 6.7.1 Testing Framework
- **Primary**: pytest (preferred for its simplicity and power)
- **Alternative**: unittest (standard library, for simple cases)
- **Coverage**: pytest-cov for coverage reporting

#### 6.7.2 Test Organization
```
tests/
├── conftest.py              # Shared fixtures and configuration
├── test_module1.py          # Unit tests for module1
├── test_module2.py          # Unit tests for module2
├── integration/
│   ├── conftest.py          # Integration test fixtures
│   └── test_workflow.py     # Integration tests
└── fixtures/
    └── sample_data.json     # Test data files
```

#### 6.7.3 Test Naming Convention
```python
# test_module.py
import pytest
from package_name.module import function_to_test

class TestFunctionName:
    """Tests for function_to_test."""

    def test_function_with_valid_input_returns_expected_output(self):
        """Test that function returns correct output for valid input."""
        # Arrange
        input_data = [1, 2, 3]
        expected = 6

        # Act
        result = function_to_test(input_data)

        # Assert
        assert result == expected

    def test_function_with_empty_input_raises_value_error(self):
        """Test that function raises ValueError for empty input."""
        with pytest.raises(ValueError, match="Input cannot be empty"):
            function_to_test([])

    @pytest.mark.parametrize("input_val,expected", [
        (1, 2),
        (2, 4),
        (3, 6),
    ])
    def test_function_with_various_inputs(self, input_val, expected):
        """Test function with multiple input values."""
        assert function_to_test(input_val) == expected
```

#### 6.7.4 Fixtures and Conftest
```python
# conftest.py
import pytest
from pathlib import Path
import tempfile

@pytest.fixture
def sample_data():
    """Provide sample data for tests."""
    return {
        'values': [1, 2, 3, 4, 5],
        'labels': ['a', 'b', 'c', 'd', 'e']
    }

@pytest.fixture
def temp_directory():
    """Provide a temporary directory for tests."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)

@pytest.fixture(scope="session")
def database_connection():
    """Provide a database connection for the test session."""
    conn = create_test_database()
    yield conn
    conn.close()
```

#### 6.7.5 Coverage Requirements
- **Minimum Coverage**: 80% line coverage
- **Critical Paths**: 95%+ coverage for core business logic
- **Exclusions**: Document any excluded code with `# pragma: no cover`

```bash
# Run tests with coverage
pytest --cov=src --cov-report=html --cov-report=term

# Coverage configuration in pyproject.toml
[tool.coverage.run]
source = ["src"]
omit = ["*/tests/*", "*/test_*.py"]

[tool.coverage.report]
exclude_lines = [
    "pragma: no cover",
    "def __repr__",
    "raise AssertionError",
    "raise NotImplementedError",
    "if __name__ == .__main__.:",
    "if TYPE_CHECKING:",
]
```

### 6.8 Documentation Standards

#### 6.8.1 Docstring Format
Use Google-style or NumPy-style docstrings consistently:

```python
def complex_function(
    param1: List[int],
    param2: str,
    param3: Optional[float] = None
) -> Tuple[List[int], Dict[str, Any]]:
    """Perform a complex operation on the input data.

    This function processes the input parameters and returns
    transformed results along with metadata.

    Args:
        param1: A list of integers to process. Must not be empty.
        param2: A string identifier for the operation.
        param3: Optional scaling factor. Defaults to 1.0 if not provided.

    Returns:
        A tuple containing:
            - List of processed integers
            - Dictionary with metadata including 'count', 'mean', 'operation'

    Raises:
        ValueError: If param1 is empty or param2 is invalid.
        TypeError: If param1 contains non-integer values.

    Examples:
        >>> result, metadata = complex_function([1, 2, 3], "scale", 2.0)
        >>> print(result)
        [2, 4, 6]
        >>> print(metadata['count'])
        3

    Note:
        This function modifies the input list in-place if param3 is None.

    See Also:
        simple_function: A simpler version of this operation.
    """
    # Implementation
    pass
```

#### 6.8.2 Module and Class Documentation
```python
"""Module for data processing utilities.

This module provides functions and classes for processing various
data formats including CSV, JSON, and Parquet files.

Typical usage example:
    from package_name import data_processor

    processor = data_processor.DataProcessor()
    result = processor.process_file('data.csv')
"""

class DataProcessor:
    """Process data from various file formats.

    This class provides methods to read, validate, and transform
    data from different sources.

    Attributes:
        config: Configuration dictionary for processing options.
        cache: Internal cache for processed data.

    Example:
        >>> processor = DataProcessor(config={'validate': True})
        >>> data = processor.process_file('input.csv')
        >>> processor.save_results('output.json')
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None) -> None:
        """Initialize the DataProcessor.

        Args:
            config: Optional configuration dictionary. If None, uses defaults.
        """
        self.config = config or {}
        self.cache: Dict[str, pd.DataFrame] = {}
```

#### 6.8.3 Inline Comments
- **When to Comment**: Explain WHY, not WHAT
- **Complex Logic**: Explain the approach for non-obvious algorithms
- **Workarounds**: Document why a workaround is necessary
- **TODOs**: Use `# TODO:` for future improvements

```python
# Good: Explains why
# Use binary search because the list is sorted and can be large (>10k items)
index = bisect.bisect_left(sorted_list, target)

# Bad: States the obvious
# Increment counter by 1
counter += 1

# Good: Documents workaround
# Workaround for pandas bug #12345: manually convert timezone
# Remove this when pandas 2.1.0 is released
df['timestamp'] = df['timestamp'].dt.tz_localize(None)
```

### 6.9 Logging and Debugging

#### 6.9.1 Logging Configuration
```python
import logging
from pathlib import Path

def setup_logging(
    level: int = logging.INFO,
    log_file: Optional[Path] = None
) -> None:
    """Configure logging for the application.

    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL).
        log_file: Optional file path for log output.
    """
    handlers: List[logging.Handler] = [logging.StreamHandler()]

    if log_file:
        handlers.append(logging.FileHandler(log_file))

    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=handlers
    )

# Usage in modules
logger = logging.getLogger(__name__)

def process_data(data: pd.DataFrame) -> pd.DataFrame:
    """Process data with logging."""
    logger.info(f"Processing data with shape {data.shape}")

    try:
        result = transform(data)
        logger.debug(f"Transformation complete: {result.shape}")
        return result
    except Exception as e:
        logger.error(f"Processing failed: {e}", exc_info=True)
        raise
```

#### 6.9.2 Debug Logging
```python
# Use appropriate log levels
logger.debug("Detailed information for debugging")
logger.info("General information about program execution")
logger.warning("Warning about potential issues")
logger.error("Error that needs attention")
logger.critical("Critical error that may cause program failure")

# Include context in log messages
logger.info(f"Processing file: {filename}, size: {file_size} bytes")
logger.error(f"Failed to connect to {host}:{port} - {error}")
```

### 6.10 Performance Considerations

#### 6.10.1 General Performance Guidelines
- **Profiling**: Profile before optimizing (`cProfile`, `line_profiler`)
- **Vectorization**: Use NumPy/Pandas vectorized operations over loops
- **Generators**: Use generators for large datasets to save memory
- **Caching**: Use `functools.lru_cache` for expensive pure functions
- **Lazy Evaluation**: Defer computation until needed

#### 6.10.2 Performance Examples
```python
from functools import lru_cache
from typing import Iterator

# Good: Generator for memory efficiency
def read_large_file(path: Path) -> Iterator[str]:
    """Read large file line by line."""
    with open(path, 'r') as f:
        for line in f:
            yield line.strip()

# Good: Caching expensive computations
@lru_cache(maxsize=128)
def expensive_computation(n: int) -> int:
    """Compute expensive result with caching."""
    # Expensive operation
    return result

# Good: Vectorized operations
import numpy as np

# Fast: Vectorized
result = np.sum(array * 2 + 1)

# Slow: Loop
result = sum(x * 2 + 1 for x in array)

# Good: Use appropriate data structures
from collections import defaultdict, Counter

# Fast: Counter for counting
counts = Counter(items)

# Slow: Manual counting
counts = {}
for item in items:
    counts[item] = counts.get(item, 0) + 1
```

### 6.11 Security Considerations

#### 6.11.1 Input Validation
```python
from pathlib import Path
import re

def validate_filename(filename: str) -> Path:
    """Validate and sanitize filename to prevent path traversal."""
    # Remove any path separators
    safe_name = Path(filename).name

    # Validate against allowed pattern
    if not re.match(r'^[a-zA-Z0-9_\-\.]+$', safe_name):
        raise ValueError(f"Invalid filename: {filename}")

    return Path(safe_name)

def validate_email(email: str) -> str:
    """Validate email format."""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(pattern, email):
        raise ValueError(f"Invalid email: {email}")
    return email
```

#### 6.11.2 Secrets Management
```python
import os
from pathlib import Path

# Good: Load secrets from environment variables
API_KEY = os.environ.get('API_KEY')
if not API_KEY:
    raise ValueError("API_KEY environment variable not set")

# Good: Load from secure file
def load_secrets(secrets_file: Path) -> Dict[str, str]:
    """Load secrets from file outside repository."""
    if not secrets_file.exists():
        raise FileNotFoundError(f"Secrets file not found: {secrets_file}")

    # Ensure file has restrictive permissions
    if secrets_file.stat().st_mode & 0o077:
        raise PermissionError(f"Secrets file has insecure permissions: {secrets_file}")

    # Load secrets
    with open(secrets_file) as f:
        return json.load(f)

# Bad: Hardcoded secrets
API_KEY = "sk-1234567890abcdef"  # NEVER do this
```

#### 6.11.3 SQL Injection Prevention
```python
import sqlite3

# Good: Parameterized queries
def get_user(conn: sqlite3.Connection, user_id: int) -> Optional[Dict]:
    """Get user by ID using parameterized query."""
    cursor = conn.execute(
        "SELECT * FROM users WHERE id = ?",
        (user_id,)
    )
    return cursor.fetchone()

# Bad: String formatting (SQL injection risk)
def get_user_bad(conn: sqlite3.Connection, user_id: int) -> Optional[Dict]:
    """UNSAFE: Vulnerable to SQL injection."""
    cursor = conn.execute(f"SELECT * FROM users WHERE id = {user_id}")
    return cursor.fetchone()
```

## 7. Session Continuity and State Discipline

Claude Code MUST:
- Assume **no memory across sessions**
- Externalize all long-lived decisions, constraints, and progress into files
- Never rely on conversational memory for:
    - Architecture decisions
    - Constraints and invariants
    - Roadmap state
    - Dependency versions
    - Configuration choices

For roadmap work, every session MUST end with:
- A new handoff record under `agents_roadmaps/<active>/sessions/`

## 8. Decision Hygiene

Claude Code MUST:
- Avoid re-discussing previously settled decisions
- Record irreversible or high-impact decisions explicitly in:
    - Architecture Decision Records (ADRs) if project uses them
    - Roadmap INVARIANTS.md
    - Code comments for local decisions
- Ask before changing:
    - Public API interfaces
    - Architectural boundaries
    - Dependency versions (major updates)
    - Python version requirements
    - Testing framework

Silent reinterpretation is forbidden.

## 9. Git Workflow Constraints

### 9.1 Protected Branch Policy

**CRITICAL REQUIREMENT**: Claude Code MUST NEVER commit directly to protected branches.

**Protected branches include:**
- `master`
- `main`
- `develop`
- Any branch matching `release/*` or `hotfix/*`

**This prohibition is absolute and applies to:**
- All code changes (features, fixes, refactors, documentation)
- Configuration file updates
- Dependency updates
- Emergency fixes
- Trivial changes (typos, formatting)
- ANY modification whatsoever

### 9.2 Mandatory Branch-Based Workflow

**REQUIRED WORKFLOW**: All changes MUST follow this process:

1. **Check current branch**:
   ```bash
   git branch --show-current
   ```
   If on a protected branch, STOP immediately and create a feature branch.

2. **Create a feature branch**:
   ```bash
   git checkout -b <type>/<description>
   ```
   Branch naming convention:
   - `feat/<description>` — new features
   - `fix/<description>` — bug fixes
   - `refactor/<description>` — code restructuring
   - `perf/<description>` — performance improvements
   - `docs/<description>` — documentation only
   - `chore/<description>` — tooling, dependencies, non-code changes

3. **Make changes on the feature branch**

4. **Commit changes**:
   ```bash
   git add <files>
   git commit -m "type(scope): description"
   ```

5. **Push feature branch**:
   ```bash
   git push -u origin <branch-name>
   ```

6. **Create pull request** (if user requests):
   ```bash
   gh pr create --title "..." --body "..."
   ```

### 9.3 Pre-Commit Verification

Before EVERY commit operation, Claude Code MUST:

1. Verify current branch is NOT a protected branch
2. If on protected branch:
   - STOP immediately
   - Inform user of the violation
   - Ask user to confirm creation of feature branch
   - Create feature branch and switch to it
   - ONLY THEN proceed with changes

**Example verification**:
```bash
CURRENT_BRANCH=$(git branch --show-current)
if [[ "$CURRENT_BRANCH" == "master" ]] || \
   [[ "$CURRENT_BRANCH" == "main" ]] || \
   [[ "$CURRENT_BRANCH" == "develop" ]]; then
    echo "ERROR: Cannot commit directly to protected branch: $CURRENT_BRANCH"
    exit 1
fi
```

### 9.4 Enforcement and Violations

**If Claude Code detects it is on a protected branch:**
- MUST refuse to make any commits
- MUST inform the user immediately
- MUST offer to create a feature branch
- MUST NOT proceed until on a valid feature branch

**Violation consequences:**
- Session should be terminated
- All changes should be reverted
- User should be notified of the policy violation

**The ONLY exception:**
- Merge commits created by pull request merges (handled by GitHub/GitLab, not by Claude Code)

### 9.5 Branch Lifecycle

**Feature branches MUST be:**
- Short-lived (ideally < 1 week)
- Scoped to a single logical change
- Deleted after merge (Claude Code should suggest this)

**After PR merge, Claude Code should:**
1. Switch back to master/main
2. Pull latest changes
3. Suggest deleting the merged feature branch:
   ```bash
   git branch -d <feature-branch>
   git push origin --delete <feature-branch>
   ```

## 10. Safety Rule: When in Doubt, Stop

> **If Claude Code is unsure whether an action is allowed,**
> **it MUST stop and ask the user.**

Guessing, inferring intent, or "doing what seems reasonable" is not acceptable.

This applies especially to:
- Dependency updates
- API changes
- Database migrations
- Configuration changes
- Security-related code

## 11. Enforcement Statement

Failure to follow this document indicates that:
- The agent is operating outside its mandate
- Output should not be trusted
- The session may need to be restarted

## 12. Python Specific Forbidden Practices

Claude Code MUST NEVER:
- **Commit directly to protected branches** (master, main, develop) - see Section 9
- Install packages to system Python (always use virtual environments)
- Use `import *` (except in `__init__.py` for re-exports)
- Use mutable default arguments (`def func(arg=[]):`)
- Ignore type hints in public APIs
- Commit code without running formatters (black, isort/ruff)
- Skip type checking with mypy
- Use bare `except:` clauses
- Hardcode secrets or credentials
- Use `eval()` or `exec()` on untrusted input
- Modify `sys.path` in application code
- Use deprecated APIs without justification
- Commit code with failing tests
- Skip updating requirements.txt after installing packages

## 13. Character Encoding and Language Requirements

### 13.1 ASCII-Only Requirement

**STRICTLY FORBIDDEN**: Use of ANY Non-ASCII characters in:
- Source code files (`.py`, `.pyi`)
- Comments (inline, block, or docstring comments)
- Commit messages
- Pull request titles and descriptions
- Documentation files
- Configuration files (`.toml`, `.yaml`, `.ini`, `.cfg`)
- Any text content in the repository

This includes but is not limited to:
- Non-English characters (Chinese, Japanese, Arabic, Cyrillic, etc.)
- Special marks and symbols (checkmark, crossmark, bullet points, arrows)
- Emoji and emoticons
- Accented characters (e, a, o, etc.)
- Mathematical symbols beyond basic ASCII
- Currency symbols beyond $ (dollar sign)
- Typographic quotes (" " ' ') - use straight quotes (" ')

**Allowed**: Only ASCII characters (0x00-0x7F)

**Enforcement**:
- Claude Code MUST verify all generated content is ASCII-only
- Use `python -c "import sys; sys.exit(0 if all(ord(c) < 128 for c in open('file.py').read()) else 1)"` to verify
- Configure pre-commit hooks to reject Non-ASCII content
- CI/CD pipelines MUST include ASCII validation

Example violations:
```python
# FORBIDDEN: Non-ASCII characters
# TODO: Fix this bug  (contains special dash)
result = 42  # checkmark emoji

# FORBIDDEN: Non-English comments
# Zhe shi yi ge han shu (This is a function in Chinese)
def function():
    pass

# ALLOWED: ASCII only
# TODO: Fix this bug
result = 42  # Correct implementation

# ALLOWED: ASCII comments
# This is a function
def function():
    pass
```

### 13.2 British English Requirement

**MANDATORY**: All English text MUST use British English spelling and conventions:

**Spelling differences** (British vs American):
- colour (not color)
- behaviour (not behavior)
- optimise (not optimize)
- initialise (not initialize)
- analyse (not analyze)
- centre (not center)
- metre (not meter) - for measurement
- licence (noun), license (verb)
- practise (verb), practice (noun)
- defence (not defense)
- organise (not organize)
- serialise (not serialize)
- finalise (not finalize)

**Applies to**:
- Code comments and docstrings
- Variable and function names where words are spelled out
- Commit messages
- Pull request descriptions
- README and documentation files
- Error messages and user-facing strings
- Log messages

**Examples**:
```python
# CORRECT: British English
def initialise_colour_buffer() -> None:
    """Initialise the colour buffer with default values.

    This optimises memory usage by pre-allocating the buffer.
    """
    pass

# INCORRECT: American English
def initialize_color_buffer() -> None:
    """Initialize the color buffer with default values.

    This optimizes memory usage by pre-allocating the buffer.
    """
    pass

# CORRECT: British English in commit message
# feat(renderer): optimise colour buffer initialisation

# INCORRECT: American English in commit message
# feat(renderer): optimize color buffer initialization

# CORRECT: British English in error messages
raise ValueError("Failed to initialise colour buffer")

# INCORRECT: American English in error messages
raise ValueError("Failed to initialize color buffer")
```

**Enforcement**:
- Claude Code MUST use British English in all generated text
- Code review MUST check for British English compliance
- Use spell-checkers configured for British English (en_GB)
- Configure IDE spell-checkers to use British English dictionary
- Document any exceptions (e.g., third-party library names that use American spelling)
