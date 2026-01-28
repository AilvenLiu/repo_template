# Python Type Hints and Static Type Checking

> **This document defines mandatory type hint and type checking standards for Python projects.**
> All public APIs must have complete type hints and pass static type checking.

## 1. Type Hint Requirements

### 1.1 Mandatory Type Hints
- **Mandatory**: All public functions and methods MUST have type hints
- **Preferred**: Internal functions should also have type hints
- **Return Types**: Always specify return types (including `-> None`)
- **Complex Types**: Use `typing` module for complex types

### 1.2 Type Checking Tools
```bash
# Install mypy
pip install mypy

# Or add to requirements-dev.txt
mypy>=1.3.0
```

## 2. Basic Type Hints

### 2.1 Function Type Hints
```python
from typing import List, Dict, Optional, Union, Tuple
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

# Good: Simple function with type hints
def add_numbers(a: int, b: int) -> int:
    """Add two numbers."""
    return a + b

# Good: Function with no return value
def log_message(message: str) -> None:
    """Log a message."""
    print(message)

# Bad: Missing type hints
def process_data(data, threshold=0.5):  # No type hints
    return results, count
```

### 2.2 Variable Type Hints
```python
# Good: Explicit type hints for variables
name: str = "John"
age: int = 30
scores: List[float] = [95.5, 87.3, 92.1]
config: Dict[str, Any] = {"debug": True, "timeout": 30}

# Good: Type hints for class attributes
class User:
    def __init__(self, name: str, age: int) -> None:
        self.name: str = name
        self.age: int = age
        self.scores: List[float] = []
```

## 3. Complex Type Hints

### 3.1 Generic Types
```python
from typing import TypeVar, Generic, List

# Define type variable
T = TypeVar('T')

class Container(Generic[T]):
    """Generic container class."""

    def __init__(self, value: T) -> None:
        self.value = value

    def get(self) -> T:
        return self.value

    def set(self, value: T) -> None:
        self.value = value

# Usage
int_container: Container[int] = Container(42)
str_container: Container[str] = Container("hello")
```

### 3.2 Callable Types
```python
from typing import Callable

# Function that takes a callable
def apply_function(
    func: Callable[[int, int], int],
    a: int,
    b: int
) -> int:
    """Apply a function to two integers."""
    return func(a, b)

# Function that returns a callable
def create_multiplier(factor: int) -> Callable[[int], int]:
    """Create a multiplier function."""
    def multiply(x: int) -> int:
        return x * factor
    return multiply

# Complex callable with multiple arguments
ProcessFunc = Callable[[str, int, bool], Optional[str]]

def process_with_callback(
    data: str,
    callback: ProcessFunc
) -> Optional[str]:
    """Process data with a callback function."""
    return callback(data, 10, True)
```

### 3.3 Protocol for Structural Typing
```python
from typing import Protocol

class Drawable(Protocol):
    """Protocol for objects that can be drawn."""

    def draw(self) -> None:
        """Draw the object."""
        ...

class Circle:
    """Circle class that implements Drawable protocol."""

    def draw(self) -> None:
        print("Drawing circle")

class Square:
    """Square class that implements Drawable protocol."""

    def draw(self) -> None:
        print("Drawing square")

def render(obj: Drawable) -> None:
    """Render any drawable object."""
    obj.draw()

# Both Circle and Square can be passed to render
render(Circle())
render(Square())
```

### 3.4 TypedDict for Structured Dictionaries
```python
from typing import TypedDict, Optional

class UserDict(TypedDict):
    """Type definition for user dictionary."""
    name: str
    age: int
    email: str

class UserDictOptional(TypedDict, total=False):
    """Type definition with optional fields."""
    name: str
    age: int
    email: str
    phone: Optional[str]

def create_user(data: UserDict) -> None:
    """Create a user from dictionary."""
    print(f"Creating user: {data['name']}")

# Usage
user_data: UserDict = {
    "name": "John",
    "age": 30,
    "email": "john@example.com"
}
create_user(user_data)
```

### 3.5 Literal Types
```python
from typing import Literal

def set_mode(mode: Literal["train", "eval", "test"]) -> None:
    """Set the operation mode."""
    print(f"Mode set to: {mode}")

# Good: Valid literal value
set_mode("train")

# Bad: Invalid literal value (type checker will catch this)
# set_mode("invalid")  # Type error

# Multiple literal types
Status = Literal["pending", "running", "completed", "failed"]

def update_status(status: Status) -> None:
    """Update the status."""
    print(f"Status: {status}")
```

## 4. Advanced Type Hints

### 4.1 Union Types
```python
from typing import Union

# Union of multiple types
def process_input(data: Union[str, int, float]) -> str:
    """Process input of various types."""
    return str(data)

# Optional is shorthand for Union[T, None]
def get_user(user_id: int) -> Optional[User]:
    """Get user by ID, return None if not found."""
    # Implementation
    return user if found else None

# Python 3.10+ syntax (use | instead of Union)
def process_input_modern(data: str | int | float) -> str:
    """Process input of various types (Python 3.10+)."""
    return str(data)
```

### 4.2 Iterator and Generator Types
```python
from typing import Iterator, Generator, Iterable
from collections.abc import Iterator as ABCIterator

# Iterator type
def read_lines(file_path: Path) -> Iterator[str]:
    """Read file line by line."""
    with open(file_path, 'r') as f:
        for line in f:
            yield line.strip()

# Generator with send and return types
def counter(start: int) -> Generator[int, None, None]:
    """Generate sequential numbers."""
    current = start
    while True:
        yield current
        current += 1

# Generator with send type
def echo_generator() -> Generator[str, str, None]:
    """Generator that echoes sent values."""
    while True:
        received = yield "Ready"
        yield f"Echo: {received}"

# Iterable type for function parameters
def process_items(items: Iterable[int]) -> List[int]:
    """Process an iterable of integers."""
    return [item * 2 for item in items]
```

### 4.3 Type Aliases
```python
from typing import List, Dict, Tuple, Union

# Simple type alias
UserId = int
UserName = str

# Complex type alias
UserData = Dict[str, Union[str, int, float]]
Coordinates = Tuple[float, float]
Matrix = List[List[float]]

# Using type aliases
def get_user_name(user_id: UserId) -> UserName:
    """Get user name by ID."""
    # Implementation
    return "John"

def process_matrix(matrix: Matrix) -> Matrix:
    """Process a matrix."""
    # Implementation
    return matrix
```

## 5. Mypy Configuration

### 5.1 Strict Mypy Configuration
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

### 5.2 Running Mypy
```bash
# Run mypy on source directory
mypy src/

# Run with stricter checking
mypy --strict src/

# Check specific file
mypy src/module.py

# Show error codes
mypy --show-error-codes src/

# Generate HTML report
mypy --html-report mypy-report src/
```

## 6. Type Checking Best Practices

### 6.1 Avoid Using Any
```python
from typing import Any, Dict, List

# Bad: Using Any loses type safety
def process_data(data: Any) -> Any:
    return data

# Good: Use specific types
def process_data(data: Dict[str, Union[int, float]]) -> List[float]:
    return [float(v) for v in data.values()]

# Acceptable: When type is truly unknown
def serialize(obj: Any) -> str:
    """Serialize any object to JSON string."""
    return json.dumps(obj)
```

### 6.2 Use TYPE_CHECKING for Import Cycles
```python
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    # Imports only used for type checking
    from package_name.models import User

def process_user(user: "User") -> None:
    """Process a user object."""
    # Implementation
    pass
```

### 6.3 Handling Third-Party Libraries Without Types
```python
# Option 1: Use type: ignore comment
import untyped_library  # type: ignore

# Option 2: Create stub file (.pyi)
# untyped_library.pyi
def some_function(arg: str) -> int: ...

# Option 3: Configure mypy to ignore
# pyproject.toml
[[tool.mypy.overrides]]
module = "untyped_library.*"
ignore_missing_imports = true
```

## 7. Type Narrowing

### 7.1 Using isinstance for Type Narrowing
```python
from typing import Union

def process_value(value: Union[int, str]) -> str:
    """Process value based on its type."""
    if isinstance(value, int):
        # Type narrowed to int
        return f"Number: {value * 2}"
    else:
        # Type narrowed to str
        return f"String: {value.upper()}"
```

### 7.2 Using assert for Type Narrowing
```python
from typing import Optional

def process_user(user: Optional[User]) -> str:
    """Process user, assuming user is not None."""
    assert user is not None
    # Type narrowed to User (not Optional[User])
    return user.name
```

## 8. Pre-Commit Type Checking

### 8.1 Mandatory Pre-Commit Checks
Before EVERY commit, Claude Code MUST run:

```bash
# Run mypy on source code
mypy src/

# Run with strict checking
mypy --strict src/

# Check specific module
mypy src/module.py
```

### 8.2 Type Checking Failure Policy
- **NEVER** commit code that fails type checking
- **NEVER** use `# type: ignore` without explanation
- **NEVER** disable type checking to make commits pass
- Fix type errors before committing
- Document any necessary `# type: ignore` comments

## 9. Common Type Checking Patterns

### 9.1 Optional Parameters
```python
from typing import Optional

# Good: Optional parameter with default None
def greet(name: Optional[str] = None) -> str:
    """Greet a person."""
    if name is None:
        return "Hello, stranger!"
    return f"Hello, {name}!"

# Good: Optional return value
def find_user(user_id: int) -> Optional[User]:
    """Find user by ID."""
    # Return None if not found
    return user if found else None
```

### 9.2 Overloading Functions
```python
from typing import overload, Union

@overload
def process(data: str) -> str: ...

@overload
def process(data: int) -> int: ...

def process(data: Union[str, int]) -> Union[str, int]:
    """Process data based on type."""
    if isinstance(data, str):
        return data.upper()
    return data * 2
```

## 10. Enforcement

### 10.1 CI/CD Integration
All pull requests MUST pass:
- Mypy type checking
- No type errors
- All public functions have type hints

### 10.2 Violations
**STRICTLY FORBIDDEN**:
- Committing code without type hints on public APIs
- Committing code that fails mypy checks
- Using `# type: ignore` without explanation
- Disabling type checking to make commits pass
- Using `Any` without justification

## 11. Type Checking Checklist

Before committing, verify:
- [ ] All public functions have type hints
- [ ] All parameters have type hints
- [ ] All return types are specified
- [ ] Mypy passes (`mypy src/`)
- [ ] No `# type: ignore` without explanation
- [ ] Complex types use appropriate typing constructs
- [ ] No use of `Any` without justification
- [ ] Type hints are accurate and complete