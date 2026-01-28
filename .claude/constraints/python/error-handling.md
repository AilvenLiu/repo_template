# Python Error Handling and Exceptions

> **This document defines mandatory error handling standards for Python projects.**
> All code must follow these exception handling practices for robustness and maintainability.

## 1. Exception Handling Best Practices

### 1.1 Core Principles
- **Specific Exceptions**: Catch specific exceptions, not bare `except:`
- **Custom Exceptions**: Define custom exceptions for domain-specific errors
- **Context**: Provide meaningful error messages
- **Logging**: Log exceptions with context
- **Re-raising**: Use `raise` without arguments to preserve traceback

### 1.2 Never Use Bare Except
```python
# Bad: Bare except catches everything including KeyboardInterrupt
try:
    risky_operation()
except:  # FORBIDDEN
    pass

# Good: Catch specific exceptions
try:
    risky_operation()
except ValueError as e:
    logger.error(f"Invalid value: {e}")
    raise
except IOError as e:
    logger.error(f"IO error: {e}")
    raise
```

## 2. Specific Exception Handling

### 2.1 Catch Specific Exceptions
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
    except PermissionError:
        logger.error(f"Permission denied reading config: {path}")
        raise

# Good: Multiple specific exceptions
def process_data(data: str) -> Dict[str, Any]:
    """Process data string."""
    try:
        parsed = json.loads(data)
        return validate(parsed)
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON data: {e}") from e
    except KeyError as e:
        raise ValueError(f"Missing required field: {e}") from e
    except TypeError as e:
        raise ValueError(f"Invalid data type: {e}") from e
```

### 2.2 Exception Chaining
```python
# Good: Chain exceptions to preserve context
def load_user_data(user_id: int) -> Dict[str, Any]:
    """Load user data from database."""
    try:
        data = database.query(user_id)
        return parse_user_data(data)
    except DatabaseError as e:
        raise UserDataError(f"Failed to load user {user_id}") from e
    except ParseError as e:
        raise UserDataError(f"Failed to parse user data") from e

# Good: Suppress exception context when not relevant
def safe_operation():
    """Perform operation with error handling."""
    try:
        risky_operation()
    except SpecificError:
        # Raise new exception without showing original context
        raise NewError("Operation failed") from None
```

## 3. Custom Exceptions

### 3.1 Define Custom Exception Classes
```python
# Good: Custom exception hierarchy
class ApplicationError(Exception):
    """Base exception for application errors."""
    pass

class DataValidationError(ApplicationError):
    """Raised when data validation fails."""
    pass

class ConfigurationError(ApplicationError):
    """Raised when configuration is invalid."""
    pass

class DatabaseError(ApplicationError):
    """Raised when database operation fails."""
    pass

class AuthenticationError(ApplicationError):
    """Raised when authentication fails."""
    pass

# Good: Custom exception with attributes
class ValidationError(ApplicationError):
    """Raised when validation fails with details."""

    def __init__(self, message: str, field: str, value: Any) -> None:
        """Initialise validation error.

        Args:
            message: Error message.
            field: Field name that failed validation.
            value: Invalid value.
        """
        super().__init__(message)
        self.field = field
        self.value = value

    def __str__(self) -> str:
        return f"{self.args[0]} (field: {self.field}, value: {self.value})"
```

### 3.2 Using Custom Exceptions
```python
def validate_data(data: pd.DataFrame) -> None:
    """Validate input data.

    Args:
        data: DataFrame to validate.

    Raises:
        DataValidationError: If data is invalid.
    """
    if data.empty:
        raise DataValidationError("Data cannot be empty")

    if 'required_column' not in data.columns:
        raise DataValidationError("Missing required column: required_column")

    if data['age'].min() < 0:
        raise DataValidationError("Age cannot be negative")

def validate_user(user: Dict[str, Any]) -> None:
    """Validate user data.

    Args:
        user: User dictionary to validate.

    Raises:
        ValidationError: If validation fails with field details.
    """
    if 'email' not in user:
        raise ValidationError("Missing email field", "email", None)

    if not is_valid_email(user['email']):
        raise ValidationError(
            "Invalid email format",
            "email",
            user['email']
        )
```

## 4. Error Messages

### 4.1 Meaningful Error Messages
```python
# Good: Descriptive error messages
def divide(a: float, b: float) -> float:
    """Divide two numbers.

    Args:
        a: Numerator.
        b: Denominator.

    Returns:
        Result of division.

    Raises:
        ValueError: If b is zero.
    """
    if b == 0:
        raise ValueError(f"Cannot divide {a} by zero")
    return a / b

# Good: Include context in error messages
def load_file(path: Path) -> str:
    """Load file contents.

    Args:
        path: Path to file.

    Returns:
        File contents.

    Raises:
        FileNotFoundError: If file does not exist.
        ValueError: If file is empty.
    """
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")

    content = path.read_text()
    if not content:
        raise ValueError(f"File is empty: {path}")

    return content

# Bad: Vague error messages
def process(data):
    if not data:
        raise ValueError("Invalid input")  # Too vague
```

## 5. Logging Exceptions

### 5.1 Log Exceptions with Context
```python
import logging

logger = logging.getLogger(__name__)

def process_data(data: pd.DataFrame) -> pd.DataFrame:
    """Process data with logging.

    Args:
        data: Input DataFrame.

    Returns:
        Processed DataFrame.

    Raises:
        DataValidationError: If data is invalid.
    """
    logger.info(f"Processing data with shape {data.shape}")

    try:
        result = transform(data)
        logger.debug(f"Transformation complete: {result.shape}")
        return result
    except Exception as e:
        logger.error(f"Processing failed: {e}", exc_info=True)
        raise

# Good: Log with different levels
def fetch_data(url: str) -> Dict[str, Any]:
    """Fetch data from URL.

    Args:
        url: URL to fetch from.

    Returns:
        Fetched data.

    Raises:
        requests.RequestException: If request fails.
    """
    logger.info(f"Fetching data from {url}")

    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        logger.debug(f"Response status: {response.status_code}")
        return response.json()
    except requests.Timeout:
        logger.warning(f"Request timeout for {url}")
        raise
    except requests.RequestException as e:
        logger.error(f"Request failed for {url}: {e}", exc_info=True)
        raise
```

## 6. Context Managers

### 6.1 Use Context Managers for Resource Management
```python
from contextlib import contextmanager
from typing import Iterator

@contextmanager
def database_connection(url: str) -> Iterator[Connection]:
    """Context manager for database connections.

    Args:
        url: Database URL.

    Yields:
        Database connection.

    Example:
        >>> with database_connection(DB_URL) as conn:
        ...     conn.execute(query)
    """
    conn = connect(url)
    try:
        yield conn
    except DatabaseError as e:
        logger.error(f"Database error: {e}")
        conn.rollback()
        raise
    else:
        conn.commit()
    finally:
        conn.close()

@contextmanager
def temporary_file(suffix: str = ".tmp") -> Iterator[Path]:
    """Context manager for temporary files.

    Args:
        suffix: File suffix.

    Yields:
        Path to temporary file.

    Example:
        >>> with temporary_file(".txt") as tmp:
        ...     tmp.write_text("data")
    """
    tmp = Path(tempfile.mktemp(suffix=suffix))
    try:
        yield tmp
    finally:
        if tmp.exists():
            tmp.unlink()
```

### 6.2 Built-in Context Managers
```python
# Good: Use context managers for file operations
def process_file(input_path: Path, output_path: Path) -> None:
    """Process file with proper resource management.

    Args:
        input_path: Input file path.
        output_path: Output file path.
    """
    with open(input_path, 'r') as fin:
        with open(output_path, 'w') as fout:
            for line in fin:
                fout.write(process_line(line))

# Good: Multiple context managers
def copy_file(src: Path, dst: Path) -> None:
    """Copy file with proper resource management.

    Args:
        src: Source file path.
        dst: Destination file path.
    """
    with open(src, 'rb') as fsrc, open(dst, 'wb') as fdst:
        fdst.write(fsrc.read())

# Bad: Manual resource management
def process_file_bad(path: Path) -> str:
    """Process file without context manager (BAD)."""
    f = open(path, 'r')
    try:
        data = f.read()
        return process(data)
    finally:
        f.close()  # Should use context manager instead
```

## 7. Exception Handling Patterns

### 7.1 Try-Except-Else-Finally
```python
def process_transaction(transaction: Dict[str, Any]) -> None:
    """Process transaction with complete error handling.

    Args:
        transaction: Transaction data.

    Raises:
        ValidationError: If transaction is invalid.
        DatabaseError: If database operation fails.
    """
    try:
        # Try block: code that might raise exceptions
        validate_transaction(transaction)
        result = database.execute(transaction)
    except ValidationError as e:
        # Except block: handle specific exceptions
        logger.error(f"Invalid transaction: {e}")
        raise
    except DatabaseError as e:
        # Handle database errors
        logger.error(f"Database error: {e}")
        database.rollback()
        raise
    else:
        # Else block: executed if no exception occurred
        logger.info(f"Transaction successful: {result}")
        database.commit()
    finally:
        # Finally block: always executed
        database.close()
```

### 7.2 Retry Pattern
```python
import time
from typing import Callable, TypeVar

T = TypeVar('T')

def retry(
    func: Callable[..., T],
    max_attempts: int = 3,
    delay: float = 1.0,
    exceptions: Tuple[Type[Exception], ...] = (Exception,)
) -> T:
    """Retry function on exception.

    Args:
        func: Function to retry.
        max_attempts: Maximum number of attempts.
        delay: Delay between attempts in seconds.
        exceptions: Tuple of exceptions to catch.

    Returns:
        Function result.

    Raises:
        Exception: If all attempts fail.
    """
    for attempt in range(max_attempts):
        try:
            return func()
        except exceptions as e:
            if attempt == max_attempts - 1:
                logger.error(f"All {max_attempts} attempts failed")
                raise
            logger.warning(f"Attempt {attempt + 1} failed: {e}, retrying...")
            time.sleep(delay)

# Usage
def fetch_data_with_retry(url: str) -> Dict[str, Any]:
    """Fetch data with retry logic.

    Args:
        url: URL to fetch from.

    Returns:
        Fetched data.
    """
    return retry(
        lambda: requests.get(url).json(),
        max_attempts=3,
        delay=2.0,
        exceptions=(requests.RequestException,)
    )
```

## 8. Silent Failures (FORBIDDEN)

### 8.1 Never Silently Ignore Exceptions
```python
# Bad: Silent failure
try:
    important_operation()
except Exception:
    pass  # Error is lost - FORBIDDEN

# Good: Log and re-raise
try:
    important_operation()
except Exception as e:
    logger.error(f"Operation failed: {e}", exc_info=True)
    raise

# Good: Handle with fallback
try:
    result = risky_operation()
except SpecificError as e:
    logger.warning(f"Operation failed, using fallback: {e}")
    result = fallback_value
```

## 9. Exception Documentation

### 9.1 Document Exceptions in Docstrings
```python
def divide_numbers(a: float, b: float) -> float:
    """Divide two numbers.

    Args:
        a: Numerator.
        b: Denominator.

    Returns:
        Result of division.

    Raises:
        ValueError: If b is zero.
        TypeError: If a or b are not numeric.

    Example:
        >>> divide_numbers(10, 2)
        5.0
        >>> divide_numbers(10, 0)
        Traceback (most recent call last):
        ...
        ValueError: Cannot divide by zero
    """
    if not isinstance(a, (int, float)) or not isinstance(b, (int, float)):
        raise TypeError("Arguments must be numeric")

    if b == 0:
        raise ValueError("Cannot divide by zero")

    return a / b
```

## 10. Error Recovery

### 10.1 Graceful Degradation
```python
def load_config(path: Path) -> Dict[str, Any]:
    """Load configuration with fallback to defaults.

    Args:
        path: Path to configuration file.

    Returns:
        Configuration dictionary.
    """
    default_config = {
        'timeout': 30,
        'retries': 3,
        'debug': False
    }

    try:
        with open(path, 'r') as f:
            config = json.load(f)
        logger.info(f"Loaded config from {path}")
        return {**default_config, **config}
    except FileNotFoundError:
        logger.warning(f"Config file not found: {path}, using defaults")
        return default_config
    except json.JSONDecodeError as e:
        logger.error(f"Invalid config file: {e}, using defaults")
        return default_config
```

## 11. Pre-Commit Error Handling Checks

### 11.1 Mandatory Checks
Before committing, verify:
- [ ] No bare `except:` clauses
- [ ] All exceptions are specific
- [ ] Custom exceptions are defined for domain errors
- [ ] Error messages are meaningful
- [ ] Exceptions are logged with context
- [ ] No silent failures
- [ ] Resources are managed with context managers
- [ ] Exceptions are documented in docstrings

## 12. Enforcement

### 12.1 Violations
**STRICTLY FORBIDDEN**:
- Using bare `except:` clauses
- Silent exception handling (catching without logging or re-raising)
- Catching `Exception` or `BaseException` without justification
- Vague error messages
- Not using context managers for resources
- Not documenting raised exceptions

### 12.2 CI/CD Integration
All pull requests MUST:
- Pass linting checks for exception handling
- Have no bare except clauses
- Have documented exceptions in docstrings
- Use context managers for resource management

## 13. Error Handling Checklist

Before committing, verify:
- [ ] No bare `except:` clauses
- [ ] All exceptions are specific (not `Exception` or `BaseException`)
- [ ] Custom exceptions are defined where appropriate
- [ ] Error messages include context
- [ ] Exceptions are logged before re-raising
- [ ] No silent failures
- [ ] Context managers are used for resources
- [ ] Exceptions are documented in docstrings
- [ ] Exception chaining preserves context
- [ ] Retry logic is implemented where appropriate