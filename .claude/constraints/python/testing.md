# Python Testing Requirements

> **This document defines mandatory testing standards for Python projects.**
> All code must meet these testing requirements before being committed.

## 1. Testing Framework

### 1.1 Primary Framework
- **Primary**: pytest (preferred for its simplicity and power)
- **Alternative**: unittest (standard library, for simple cases)
- **Coverage**: pytest-cov for coverage reporting

### 1.2 Required Testing Tools
```bash
# Install testing dependencies
pip install pytest pytest-cov pytest-mock

# Or add to requirements-dev.txt
pytest>=7.3.0,<8.0.0
pytest-cov>=4.0.0
pytest-mock>=3.10.0
```

## 2. Test Organization

### 2.1 Directory Structure
```
tests/
|-- __init__.py
|-- conftest.py              # Shared fixtures and configuration
|-- test_module1.py          # Unit tests for module1
|-- test_module2.py          # Unit tests for module2
|-- integration/
|   |-- __init__.py
|   |-- conftest.py          # Integration test fixtures
|   `-- test_workflow.py     # Integration tests
|-- fixtures/
|   |-- sample_data.json     # Test data files
|   `-- test_config.yaml
`-- utils.py                 # Test utilities
```

### 2.2 Test File Naming
- Test files MUST be named `test_*.py` or `*_test.py`
- Test functions MUST be named `test_*`
- Test classes MUST be named `Test*`

## 3. Test Naming Convention

### 3.1 Descriptive Test Names
Test names should clearly describe what is being tested and the expected outcome:

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

### 3.2 Test Structure: Arrange-Act-Assert
All tests should follow the Arrange-Act-Assert pattern:

```python
def test_user_creation():
    # Arrange - Set up test data and preconditions
    username = "testuser"
    email = "test@example.com"

    # Act - Execute the code being tested
    user = User(username=username, email=email)

    # Assert - Verify the results
    assert user.username == username
    assert user.email == email
    assert user.is_active is True
```

## 4. Fixtures and Conftest

### 4.1 Shared Fixtures
Define reusable fixtures in `conftest.py`:

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

### 4.2 Fixture Scopes
- `function` (default): Run once per test function
- `class`: Run once per test class
- `module`: Run once per test module
- `session`: Run once per test session

## 5. Test Best Practices

### 5.1 Test One Thing Per Test
```python
# Good: Test one thing per test
def test_user_validation_rejects_invalid_email():
    with pytest.raises(ValueError, match="Invalid email"):
        User(username="test", email="invalid")

def test_user_validation_rejects_empty_username():
    with pytest.raises(ValueError, match="Username cannot be empty"):
        User(username="", email="test@example.com")

# Bad: Testing multiple things in one test
def test_user_validation():
    # Too many assertions, hard to debug failures
    with pytest.raises(ValueError):
        User(username="test", email="invalid")
    with pytest.raises(ValueError):
        User(username="", email="test@example.com")
```

### 5.2 Use Fixtures for Setup
```python
# Good: Use fixtures for setup
def test_data_processing(sample_dataframe):
    result = process_data(sample_dataframe)
    assert len(result) == 3

# Bad: Duplicate setup in every test
def test_data_processing():
    df = pd.DataFrame({'col1': [1, 2, 3], 'col2': ['a', 'b', 'c']})
    result = process_data(df)
    assert len(result) == 3
```

### 5.3 Mock External Dependencies
```python
from unittest.mock import Mock, patch, MagicMock

# Good: Mock external API calls
def test_api_call():
    with patch('module.requests.get') as mock_get:
        mock_get.return_value.json.return_value = {'status': 'ok'}
        result = fetch_data()
        assert result['status'] == 'ok'
        mock_get.assert_called_once()

# Good: Mock database connections
def test_database_query():
    mock_conn = Mock()
    mock_conn.execute.return_value.fetchall.return_value = [
        (1, 'test'),
        (2, 'data')
    ]
    result = query_database(mock_conn)
    assert len(result) == 2
```

## 6. Coverage Requirements

### 6.1 Minimum Coverage Thresholds
- **Minimum Coverage**: 80% line coverage
- **Target Coverage**: 90%+ line coverage
- **Critical Paths**: 95%+ coverage for core business logic
- **Exclusions**: Document any excluded code with `# pragma: no cover`

### 6.2 Running Tests with Coverage
```bash
# Run tests with coverage
pytest --cov=src --cov-report=html --cov-report=term-missing

# Run tests with coverage and fail if below threshold
pytest --cov=src --cov-fail-under=80

# Generate detailed HTML coverage report
pytest --cov=src --cov-report=html
# Open htmlcov/index.html in browser
```

### 6.3 Coverage Configuration
```toml
# pyproject.toml
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

[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py", "*_test.py"]
python_classes = ["Test*"]
python_functions = ["test_*"]
addopts = [
    "--strict-markers",
    "--strict-config",
    "--cov=src",
    "--cov-report=term-missing",
]
```

## 7. Pre-Commit Testing Requirements

### 7.1 Mandatory Pre-Commit Checks
Before EVERY commit, Claude Code MUST run:

```bash
# Run all tests
pytest

# Run tests with coverage
pytest --cov=src --cov-report=term-missing

# Run specific test file
pytest tests/test_module.py

# Run with verbose output
pytest -v

# Run tests matching a pattern
pytest -k "test_validation"
```

### 7.2 Test Failure Policy
- **NEVER** commit code with failing tests
- **NEVER** skip tests to make commits pass
- **NEVER** mark tests as `@pytest.mark.skip` without justification
- Fix failing tests before committing
- If tests cannot be fixed immediately, create a separate branch

## 8. Integration Testing

### 8.1 Integration Test Organization
```python
# tests/integration/test_workflow.py
import pytest
from package_name import workflow

class TestDataProcessingWorkflow:
    """Integration tests for complete data processing workflow."""

    def test_end_to_end_data_processing(self, temp_directory):
        """Test complete workflow from input to output."""
        # Arrange
        input_file = temp_directory / "input.csv"
        output_file = temp_directory / "output.json"
        input_file.write_text("col1,col2\n1,a\n2,b\n3,c")

        # Act
        workflow.process_file(input_file, output_file)

        # Assert
        assert output_file.exists()
        result = json.loads(output_file.read_text())
        assert len(result) == 3
```

### 8.2 Integration Test Best Practices
- Use temporary directories for file operations
- Clean up resources after tests
- Test realistic scenarios
- Verify end-to-end functionality
- Use appropriate fixtures for setup/teardown

## 9. Parametrized Testing

### 9.1 Using pytest.mark.parametrize
```python
@pytest.mark.parametrize("input_val,expected", [
    (1, 2),
    (2, 4),
    (3, 6),
    (0, 0),
    (-1, -2),
])
def test_function_with_various_inputs(input_val, expected):
    """Test function with multiple input values."""
    assert function_to_test(input_val) == expected

@pytest.mark.parametrize("invalid_input", [
    None,
    "",
    [],
    {},
])
def test_function_rejects_invalid_inputs(invalid_input):
    """Test that function rejects various invalid inputs."""
    with pytest.raises((ValueError, TypeError)):
        function_to_test(invalid_input)
```

## 10. Testing Exceptions

### 10.1 Testing Raised Exceptions
```python
# Test that specific exception is raised
def test_function_raises_value_error():
    with pytest.raises(ValueError):
        function_that_raises()

# Test exception message
def test_function_raises_with_message():
    with pytest.raises(ValueError, match="Invalid input"):
        function_that_raises("bad")

# Test exception attributes
def test_custom_exception_attributes():
    with pytest.raises(CustomError) as exc_info:
        function_that_raises()
    assert exc_info.value.error_code == 42
```

## 11. Enforcement

### 11.1 CI/CD Integration
All pull requests MUST pass:
- All tests must pass
- Coverage threshold must be met (80%+)
- No skipped tests without justification

### 11.2 Violations
**STRICTLY FORBIDDEN**:
- Committing code without running tests
- Committing code with failing tests
- Reducing test coverage without justification
- Skipping tests to make commits pass
- Removing tests to increase coverage percentage

## 12. Testing Checklist

Before committing, verify:
- [ ] All tests pass (`pytest`)
- [ ] Coverage meets threshold (`pytest --cov=src --cov-fail-under=80`)
- [ ] New code has corresponding tests
- [ ] Edge cases are tested
- [ ] Error conditions are tested
- [ ] Integration tests pass (if applicable)
- [ ] No tests are skipped without justification
- [ ] Test names are descriptive
- [ ] Tests follow Arrange-Act-Assert pattern
