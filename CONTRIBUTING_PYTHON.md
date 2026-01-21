# Development & Collaboration Guidelines for Python Projects

> **This document defines mandatory contribution standards for Python repositories.**
> All contributors (human or AI) must follow these rules.

## 1. General Principles

- Prefer **clarity over cleverness**
- Prefer **explicit decisions over implicit assumptions**
- Prefer **small, reviewable changes over large, opaque ones**
- Never trade correctness or safety for speed
- Follow PEP 8 and modern Python best practices (Python 3.9+)
- Prioritize readability and maintainability

If unsure, ask before acting.

## 2. Branching Model

### 2.1 Main Branches

The repository follows a **trunk-based development model** with the following conventions:

- **master** (or **main**)
    - Always stable
    - Always releasable
    - Protected branch (no direct commits)
    - All tests must pass
    - Type checking must pass
    - Code must be formatted

Optional long-lived branches (if applicable):
- `release/*` — release stabilization
- `hotfix/*` — urgent fixes on released versions

### 2.2 Feature / Work Branches

All work MUST be done on a dedicated branch.

Naming convention:
```
<type>/<short-description>
```

Allowed types:
- `feat/` — new features
- `fix/` — bug fixes
- `refactor/` — structural changes without behavior change
- `perf/` — performance improvements
- `chore/` — tooling, infra, non-code changes
- `docs/` — documentation only
- `test/` — test additions or improvements

Examples:
```
feat/add-async-api-client
refactor/decouple-data-processing
fix/handle-empty-dataframe
perf/optimize-batch-processing
test/add-integration-tests
```

Branches MUST be:
- Short-lived (ideally < 1 week)
- Scoped to a single logical change
- Deleted after merge

## 3. Commit Message Convention

### 3.1 Format

All commits MUST follow this format:
```
<type>(optional-scope): <short summary>

[optional body]
```

Types:
- `feat` — new feature
- `fix` — bug fix
- `refactor` — code restructuring without behavior change
- `perf` — performance improvement
- `docs` — documentation changes
- `test` — adding or updating tests
- `chore` — build system, dependencies, tooling
- `style` — formatting changes (no code logic change)

Examples:
```
feat(api): add async support for data fetching
fix(parser): handle edge case with empty strings
refactor(core): split validation into separate module
perf(processing): vectorize batch operations with numpy
docs(readme): add installation instructions
test(api): add unit tests for error handling
chore(deps): update pandas to 2.0.2
```

### 3.2 Rules

- **Summary line**:
    - Less than 72 characters
    - Imperative mood ("add", not "added" or "adds")
    - No period at the end
    - Lowercase after type prefix
    - **ASCII-only characters** (no emoji, special symbols, or non-English characters)
    - **British English spelling** (e.g., "optimise" not "optimize", "colour" not "color")
- **Body** (if present):
    - Explains **why**, not just what
    - Wrap at 72 characters
    - Separate from summary with blank line
    - **ASCII-only characters**
    - **British English spelling**
- **One logical change per commit**
- **Atomic commits**: Each commit should pass tests

### 3.3 Commit Message Examples

Good:
```
feat(api): add rate limiting to API client

Implement exponential backoff with configurable retry limits
to handle API rate limits gracefully. This prevents request
failures during high-traffic periods.

Includes tests for retry logic and backoff calculation.
```

```
fix(parser): handle None values in data validation

The validator was raising AttributeError when encountering
None values in optional fields. Added explicit None checks
before validation.

Fixes issue #123
```

Bad:
```
update
fix stuff
wip
changes
```

## 4. Pull Request (PR) Guidelines

### 4.1 When to Open a PR

Open a PR when:
- A logical unit of work is complete
- All tests are passing
- Type checking passes (mypy)
- Code is formatted (black, isort/ruff)
- Linting passes (ruff/flake8)
- The change is ready for review

Draft PRs are encouraged for early feedback on architecture or approach.

### 4.2 PR Title

PR titles MUST follow the same convention as commit messages:
```
<type>(optional-scope): <short description>
```

Examples:
```
feat(api): add async support for data fetching
refactor(processing): split data pipeline into stages
fix(validation): handle edge cases in input parsing
```

### 4.3 PR Description (Required Sections)

Each PR MUST include:

```markdown
## Summary
Brief description of what this PR does (2-3 sentences).

## Motivation
Why is this change necessary? What problem does it solve?

## Changes
- Bullet list of key changes
- New modules/functions added
- Modified interfaces
- Deprecated functionality

## Technical Details
### Implementation
- Key implementation decisions
- Algorithm or approach used
- External libraries added

### API Changes (if applicable)
- New public functions/classes
- Modified signatures
- Breaking changes

## Testing
- Unit tests added/modified
- Integration tests
- Test coverage: X%
- How to verify the changes

## Dependencies
- New packages added (with versions)
- Updated packages
- Removed packages

## Performance Impact (if applicable)
- Benchmark results
- Memory usage changes
- Scalability considerations

## Breaking Changes
- List any breaking changes
- Migration guide (if needed)

## Related
- Related issues: #123, #456
- Related PRs
- Related ADRs or roadmaps
```

### 4.4 PR Size and Scope Control

- A PR SHOULD address one concern
- **Avoid mixing**:
    - Refactors + new features
    - Behavior changes + formatting
    - Multiple unrelated bug fixes
- **Size guidelines**:
    - Small: < 200 lines changed (preferred)
    - Medium: 200-500 lines changed
    - Large: > 500 lines (requires justification)
- Large changes should be split into multiple PRs when possible
- Use stacked PRs for dependent changes

### 4.5 Code Review Checklist

Before requesting review, ensure:
- [ ] All tests pass (`pytest`)
- [ ] Type checking passes (`mypy`)
- [ ] Code is formatted (`black`, `isort`/`ruff`)
- [ ] Linting passes (`ruff`/`flake8`)
- [ ] Test coverage meets threshold (typically 80%)
- [ ] Documentation updated (docstrings, README)
- [ ] `requirements.txt` updated if dependencies added
- [ ] No secrets or credentials committed
- [ ] Type hints added to all public functions

## 5. Python Specific Commit Standards

### 5.1 Virtual Environment

**MANDATORY**: Always work in a virtual environment:

```bash
# Create virtual environment
python3.9 -m venv .venv

# Activate (Linux/Mac)
source .venv/bin/activate

# Activate (Windows)
.venv\Scripts\activate

# Verify
python --version
which python
```

### 5.2 Dependency Management

**MANDATORY**: Update requirements.txt when adding packages:

```bash
# Install new package
pip install package-name

# IMMEDIATELY update requirements
pip freeze > requirements.txt

# Commit both code and requirements together
git add src/module.py requirements.txt
git commit -m "feat: add new feature using package-name"
```

For poetry:
```bash
poetry add package-name
# pyproject.toml and poetry.lock are automatically updated
```

### 5.3 Code Formatting

**MANDATORY**: Format code before committing:

```bash
# Format with black
black .

# Sort imports
isort .
# OR
ruff check --select I --fix .

# Verify formatting
black --check .
isort --check .
```

### 5.4 Type Checking

**MANDATORY**: Run type checking before committing:

```bash
# Run mypy
mypy src/

# For stricter checking
mypy --strict src/
```

### 5.5 Linting

**MANDATORY**: Run linting before committing:

```bash
# Using ruff (recommended)
ruff check .

# Fix auto-fixable issues
ruff check --fix .

# Using flake8 (alternative)
flake8 src/
```

### 5.6 Testing

**MANDATORY**: Run tests before committing:

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html --cov-report=term

# Run specific test file
pytest tests/test_module.py

# Run with verbose output
pytest -v
```

## 6. Code Style and Quality Standards

### 6.1 PEP 8 Compliance

Follow PEP 8 with these specifications:
- **Line length**: 100 characters (configurable, but consistent)
- **Indentation**: 4 spaces (never tabs)
- **Imports**: Grouped and sorted (stdlib, third-party, local)
- **Naming**:
    - `snake_case` for functions, variables, modules
    - `PascalCase` for classes
    - `UPPER_CASE` for constants
    - `_leading_underscore` for internal/private

### 6.2 Black Configuration

```toml
# pyproject.toml
[tool.black]
line-length = 100
target-version = ['py39', 'py310', 'py311', 'py312']
include = '\.pyi?$'
extend-exclude = '''
/(
  \.eggs
  | \.git
  | \.venv
  | build
  | dist
)/
'''
```

### 6.3 Ruff Configuration

```toml
# pyproject.toml
[tool.ruff]
line-length = 100
target-version = "py39"

select = [
    "E",     # pycodestyle errors
    "W",     # pycodestyle warnings
    "F",     # pyflakes
    "I",     # isort
    "N",     # pep8-naming
    "B",     # flake8-bugbear
    "C4",    # flake8-comprehensions
    "UP",    # pyupgrade
    "SIM",   # flake8-simplify
    "RET",   # flake8-return
    "ARG",   # flake8-unused-arguments
    "PTH",   # flake8-use-pathlib
    "ERA",   # eradicate (commented-out code)
]

ignore = [
    "E501",  # line too long (handled by black)
]

[tool.ruff.per-file-ignores]
"__init__.py" = ["F401"]  # Allow unused imports
"tests/*" = ["S101", "ARG"]  # Allow assert and unused fixtures
```

### 6.4 Mypy Configuration

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

[[tool.mypy.overrides]]
module = "third_party_without_types.*"
ignore_missing_imports = true
```

## 7. Type Hints Requirements

### 7.1 Type Hint Standards

**MANDATORY**: All public functions MUST have complete type hints:

```python
from typing import List, Dict, Optional, Union, Tuple, Callable, Any
from pathlib import Path

# Good: Complete type hints
def process_data(
    data: List[Dict[str, Union[int, float]]],
    threshold: float = 0.5,
    output_path: Optional[Path] = None
) -> Tuple[List[float], int]:
    """Process data and return results.

    Args:
        data: List of dictionaries containing numeric values.
        threshold: Minimum threshold for filtering. Defaults to 0.5.
        output_path: Optional path to save results.

    Returns:
        Tuple of processed results and count of items processed.
    """
    # Implementation
    return results, count

# Bad: Missing type hints
def process_data(data, threshold=0.5):
    return results, count
```

### 7.2 Complex Type Hints

```python
from typing import TypeVar, Generic, Protocol, Literal, TypedDict
from collections.abc import Iterable, Iterator

# Generic types
T = TypeVar('T')

class Container(Generic[T]):
    def __init__(self, value: T) -> None:
        self.value = value

    def get(self) -> T:
        return self.value

# Protocol for structural typing
class Drawable(Protocol):
    def draw(self) -> None: ...

# TypedDict for structured dictionaries
class UserDict(TypedDict):
    name: str
    age: int
    email: str

# Literal types
def set_mode(mode: Literal["train", "eval", "test"]) -> None:
    pass

# Callable types
def apply_function(
    func: Callable[[int, int], int],
    values: Iterable[int]
) -> Iterator[int]:
    for val in values:
        yield func(val, val)
```

## 8. Testing Standards

### 8.1 Test Organization

```
tests/
├── __init__.py
├── conftest.py              # Shared fixtures
├── test_module1.py          # Unit tests
├── test_module2.py
├── integration/
│   ├── __init__.py
│   ├── conftest.py          # Integration fixtures
│   └── test_workflow.py
├── fixtures/
│   ├── sample_data.json
│   └── test_config.yaml
└── utils.py                 # Test utilities
```

### 8.2 Test Naming Convention

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

    def test_function_with_none_input_raises_type_error(self):
        """Test that function raises TypeError for None input."""
        with pytest.raises(TypeError):
            function_to_test(None)

    @pytest.mark.parametrize("input_val,expected", [
        (1, 2),
        (2, 4),
        (3, 6),
        (0, 0),
        (-1, -2),
    ])
    def test_function_with_various_inputs(self, input_val, expected):
        """Test function with multiple input values."""
        assert function_to_test(input_val) == expected
```

### 8.3 Fixtures and Conftest

```python
# conftest.py
import pytest
from pathlib import Path
import tempfile
import pandas as pd

@pytest.fixture
def sample_data():
    """Provide sample data for tests."""
    return {
        'values': [1, 2, 3, 4, 5],
        'labels': ['a', 'b', 'c', 'd', 'e']
    }

@pytest.fixture
def sample_dataframe():
    """Provide sample pandas DataFrame."""
    return pd.DataFrame({
        'col1': [1, 2, 3],
        'col2': ['a', 'b', 'c']
    })

@pytest.fixture
def temp_directory():
    """Provide a temporary directory for tests."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)

@pytest.fixture
def temp_file(temp_directory):
    """Provide a temporary file for tests."""
    file_path = temp_directory / "test_file.txt"
    file_path.write_text("test content")
    return file_path

@pytest.fixture(scope="session")
def database_connection():
    """Provide a database connection for the test session."""
    conn = create_test_database()
    yield conn
    conn.close()

@pytest.fixture(autouse=True)
def reset_state():
    """Reset global state before each test."""
    # Setup
    yield
    # Teardown
    clear_global_state()
```

### 8.4 Test Coverage Requirements

- **Minimum**: 80% line coverage
- **Target**: 90%+ line coverage
- **Critical paths**: 95%+ coverage

```bash
# Run tests with coverage
pytest --cov=src --cov-report=html --cov-report=term-missing

# Coverage configuration
[tool.coverage.run]
source = ["src"]
omit = ["*/tests/*", "*/test_*.py", "*/__init__.py"]

[tool.coverage.report]
exclude_lines = [
    "pragma: no cover",
    "def __repr__",
    "raise AssertionError",
    "raise NotImplementedError",
    "if __name__ == .__main__.:",
    "if TYPE_CHECKING:",
    "@abstractmethod",
]
```

### 8.5 Test Best Practices

```python
# Good: Clear arrange-act-assert structure
def test_user_creation():
    # Arrange
    username = "testuser"
    email = "test@example.com"

    # Act
    user = User(username=username, email=email)

    # Assert
    assert user.username == username
    assert user.email == email
    assert user.is_active is True

# Good: Test one thing per test
def test_user_validation_rejects_invalid_email():
    with pytest.raises(ValueError, match="Invalid email"):
        User(username="test", email="invalid")

def test_user_validation_rejects_empty_username():
    with pytest.raises(ValueError, match="Username cannot be empty"):
        User(username="", email="test@example.com")

# Good: Use fixtures for setup
def test_data_processing(sample_dataframe):
    result = process_data(sample_dataframe)
    assert len(result) == 3

# Good: Mock external dependencies
from unittest.mock import Mock, patch

def test_api_call():
    with patch('module.requests.get') as mock_get:
        mock_get.return_value.json.return_value = {'status': 'ok'}
        result = fetch_data()
        assert result['status'] == 'ok'
        mock_get.assert_called_once()
```

## 9. Documentation Standards

### 9.1 Docstring Format

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

### 9.2 Module Documentation

```python
"""Module for data processing utilities.

This module provides functions and classes for processing various
data formats including CSV, JSON, and Parquet files.

Typical usage example:
    from package_name import data_processor

    processor = data_processor.DataProcessor()
    result = processor.process_file('data.csv')
"""

import logging
from pathlib import Path
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)
```

### 9.3 Class Documentation

```python
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

### 9.4 README.md Requirements

Every project MUST have a comprehensive README.md:

```markdown
# Project Name

Brief description of the project.

## Requirements

- Python 3.9 or later
- pip or poetry for dependency management

## Installation

### Using pip

```bash
# Clone repository
git clone https://github.com/user/project.git
cd project

# Create virtual environment
python3.9 -m venv .venv
source .venv/bin/activate  # Linux/Mac
# .venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt

# Install in development mode
pip install -e .
```

### Using poetry

```bash
# Clone repository
git clone https://github.com/user/project.git
cd project

# Install dependencies
poetry install
```

## Usage

```python
from project_name import main_module

# Example usage
result = main_module.process_data(input_data)
```

## Development

### Setup Development Environment

```bash
# Install development dependencies
pip install -r requirements-dev.txt

# Or with poetry
poetry install --with dev
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html
```

### Code Quality

```bash
# Format code
black .
isort .

# Type checking
mypy src/

# Linting
ruff check .
```

## Dependencies

- **pandas** (2.0.0+): Data manipulation
- **numpy** (1.24.0+): Numerical operations
- **requests** (2.31.0+): HTTP client

## License

MIT License - see LICENSE file for details.
```

## 10. Code Review Process

### 10.1 For Authors

**Before requesting review**:
1. Self-review your changes
2. Run all checks (tests, type checking, formatting, linting)
3. Write comprehensive PR description
4. Ensure commits are clean and logical
5. Update documentation
6. Update requirements.txt if needed

**During review**:
- Respond to feedback constructively
- Make requested changes in new commits
- Mark conversations as resolved when addressed
- Request re-review when ready

**After approval**:
- Squash fixup commits if needed
- Ensure CI passes
- Merge using appropriate strategy

### 10.2 For Reviewers

Review for:
- **Correctness**: Does the code do what it claims?
- **Type Safety**: Are type hints complete and correct?
- **Testing**: Adequate test coverage?
- **Readability**: Clear code, good naming, documentation?
- **Performance**: Efficient algorithms, no obvious bottlenecks?
- **Security**: No SQL injection, XSS, hardcoded secrets?

**Review checklist**:
- [ ] Tests pass and provide good coverage
- [ ] Type checking passes (mypy)
- [ ] Code is formatted (black, isort)
- [ ] Linting passes (ruff)
- [ ] Documentation is clear and complete
- [ ] No breaking changes without justification
- [ ] requirements.txt updated if needed
- [ ] No secrets or credentials

## 11. Versioning and Releases

### 11.1 Semantic Versioning

Follow Semantic Versioning (semver.org):
```
v<MAJOR>.<MINOR>.<PATCH>
```

- **MAJOR**: Incompatible API changes
- **MINOR**: Backward-compatible functionality additions
- **PATCH**: Backward-compatible bug fixes

Examples:
```
v1.0.0 - Initial release
v1.1.0 - Add new feature
v1.1.1 - Fix bug
v2.0.0 - Breaking API change
```

### 11.2 Version Management

Update version in:
- `pyproject.toml` or `setup.py`
- `__version__` in `__init__.py`
- `CHANGELOG.md`

## 12. Continuous Integration

### 12.1 CI Requirements

All PRs MUST pass CI checks:
- All tests pass
- Type checking passes (mypy)
- Code formatting check (black, isort)
- Linting passes (ruff)
- Coverage threshold met

### 12.2 Example GitHub Actions Workflow

```yaml
name: CI

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ['3.9', '3.10', '3.11', '3.12']

    steps:
    - uses: actions/checkout@v3

    - name: Set up Python ${{ matrix.python-version }}
      uses: actions/setup-python@v4
      with:
        python-version: ${{ matrix.python-version }}

    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
        pip install -r requirements-dev.txt

    - name: Format check
      run: |
        black --check .
        isort --check .

    - name: Lint
      run: ruff check .

    - name: Type check
      run: mypy src/

    - name: Test
      run: pytest --cov=src --cov-report=xml

    - name: Upload coverage
      uses: codecov/codecov-action@v3
```

## 13. Forbidden Practices

**STRICTLY FORBIDDEN**:
- Committing code without running tests
- Committing code without type hints on public APIs
- Committing unformatted code (must run black/isort)
- Installing packages without updating requirements.txt
- Using `import *` (except in `__init__.py` for re-exports)
- Using mutable default arguments
- Using bare `except:` clauses
- Hardcoding secrets or credentials
- Using `eval()` or `exec()` on untrusted input
- Committing to master/main without PR
- Force-pushing to master/main
- Merging your own PRs without approval
- Skipping code review

**STRICTLY FORBIDDEN: User or Author Attribution**
- **NEVER** include user or author information in commit messages
- **NEVER** include "Generated with", "Co-Authored-By", or any attribution lines
- **NEVER** include tool names, AI assistant names, or generation metadata
- Commit messages and PR descriptions must contain ONLY technical content
- This is a STRICT requirement with NO exceptions

**STRICTLY FORBIDDEN: Non-ASCII Characters**
- **NEVER** use Non-ASCII characters in any files, code, comments, or commit/PR messages
- **NEVER** use emoji, special symbols (checkmark, crossmark, arrows, etc.)
- **NEVER** use non-English characters (Chinese, Japanese, Arabic, Cyrillic, etc.)
- **NEVER** use accented characters (e, a, o, etc.)
- **NEVER** use typographic quotes (" " ' ') - use straight quotes (" ')
- **ONLY** ASCII characters (0x00-0x7F) are allowed
- Configure pre-commit hooks and CI/CD to reject Non-ASCII content

**STRICTLY REQUIRED: British English**
- **ALWAYS** use British English spelling in all text
- Examples: colour (not color), optimise (not optimize), initialise (not initialize)
- Applies to: code, comments, docstrings, commit messages, PR descriptions, documentation
- Configure spell-checkers to use British English (en_GB)
- Document exceptions for third-party library names

## 14. Working With Roadmaps and AI Agents

If this repository uses `agents_roadmaps/`:
- Do NOT bypass an active roadmap
- Large or multi-session changes MUST follow the roadmap process
- PRs related to a roadmap SHOULD reference:
    - Roadmap name
    - Phase / task identifier
    - Link to roadmap documentation

AI agents MUST follow CLAUDE.md and roadmap constraints at all times.

## 15. Final Rule

> **If a contribution does not clearly improve the codebase,**
> **it should not be merged.**

When in doubt, ask for clarification before proceeding.

---

**Remember**: These guidelines exist to maintain code quality, type safety, and maintainability. Following them ensures a healthy, sustainable Python codebase.
