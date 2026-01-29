# Python Code Style and Formatting

> **This document defines mandatory code formatting standards for Python projects.**
> All code must be formatted according to these rules before being committed.

## 1. Mandatory Formatting Tools

### 1.1 Required Tools
- **Primary Formatter**: `black` (non-negotiable, "The Uncompromising Code Formatter")
- **Import Sorting**: `isort` (primary) or `ruff` with isort rules (alternative)
- **Linter**: `ruff` (primary, fast and comprehensive) or `flake8` + `pylint` (alternative)

### 1.2 Installation
```bash
# Install formatting tools
pip install black isort ruff

# Or add to requirements-dev.txt
black>=23.3.0
isort>=5.12.0
ruff>=0.0.272
```

## 2. Black Configuration

### 2.1 Standard Configuration
```toml
# pyproject.toml
[tool.black]
line-length = 100
target-version = ['py39', 'py310', 'py311', 'py312']
include = '\\.pyi?$'
extend-exclude = '''
/(
  # directories
  \\.eggs
  | \\.git
  | \\.venv
  | build
  | dist
)/
'''
```

### 2.2 Running Black
```bash
# Format all Python files in current directory
black .

# Format specific file or directory
black src/

# Check formatting without making changes
black --check .

# Show diff of what would be changed
black --diff .
```

### 2.3 Black Rules
- Line length: 100 characters (configurable but must be consistent)
- Use double quotes for strings
- Trailing commas in multi-line structures
- Consistent indentation (4 spaces)
- Automatic line breaking for long lines

## 3. Import Sorting

### 3.1 Import Organization
Imports MUST be organized in three groups:
1. Standard library imports
2. Third-party imports
3. Local/application imports

Each group separated by a blank line.

### 3.2 isort Configuration
```toml
# pyproject.toml
[tool.isort]
profile = "black"
line_length = 100
multi_line_output = 3
include_trailing_comma = true
force_grid_wrap = 0
use_parentheses = true
ensure_newline_before_comments = true
```

### 3.3 Running isort
```bash
# Sort imports in all files
isort .

# Sort imports in specific file
isort src/module.py

# Check import sorting without making changes
isort --check .

# Show diff of what would be changed
isort --diff .
```

### 3.4 Import Sorting Example
```python
# Good: Properly sorted imports
# Standard library imports
import os
import sys
from pathlib import Path
from typing import List, Optional

# Third-party imports
import numpy as np
import pandas as pd
import requests

# Local imports
from package_name import constants
from package_name.subpackage import helper

# Bad: Unsorted imports
import pandas as pd
from package_name import constants
import os
import numpy as np
```

## 4. Ruff Configuration

### 4.1 Comprehensive Ruff Setup
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
    "ARG", # flake8-unused-arguments
    "PTH", # flake8-use-pathlib
    "ERA", # eradicate (commented-out code)
]

ignore = [
    "E501",  # line too long (handled by black)
]

[tool.ruff.per-file-ignores]
"__init__.py" = ["F401"]  # Allow unused imports in __init__.py
"tests/*" = ["S101", "ARG"]  # Allow assert and unused fixtures in tests
```

### 4.2 Running Ruff
```bash
# Check all files
ruff check .

# Fix auto-fixable issues
ruff check --fix .

# Check specific file
ruff check src/module.py

# Show all violations
ruff check --show-files .
```

## 5. PEP 8 Compliance

### 5.1 Core PEP 8 Rules
- **Line length**: 100 characters (configurable, but consistent)
- **Indentation**: 4 spaces (never tabs)
- **Blank lines**:
  - 2 blank lines between top-level functions and classes
  - 1 blank line between methods in a class
- **Whitespace**: Follow PEP 8 whitespace rules
- **Comments**: Use complete sentences, update when code changes

### 5.2 Naming Conventions
```python
# snake_case for functions, variables, modules
def calculate_total(item_count: int) -> float:
    total_price = 0.0
    return total_price

# PascalCase for classes
class DataProcessor:
    pass

# UPPER_CASE for constants
MAX_RETRIES = 3
DEFAULT_TIMEOUT = 30

# _leading_underscore for internal/private
def _internal_helper():
    pass

class MyClass:
    def __init__(self):
        self._private_attribute = None
```

## 6. Module Organization

### 6.1 Standard Module Structure
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

## 7. Code Style Best Practices

### 7.1 String Formatting
```python
# Good: Use f-strings (Python 3.6+)
name = "World"
message = f"Hello, {name}!"

# Good: For complex formatting
value = 42
formatted = f"The answer is {value:05d}"

# Acceptable: str.format() for templates
template = "Hello, {name}!"
message = template.format(name="World")

# Bad: Old-style % formatting
message = "Hello, %s!" % name
```

### 7.2 List Comprehensions
```python
# Good: Simple list comprehension
squares = [x**2 for x in range(10)]

# Good: With condition
even_squares = [x**2 for x in range(10) if x % 2 == 0]

# Bad: Too complex, use regular loop
result = [
    process_item(x, y, z)
    for x in items
    if x.is_valid()
    for y in x.children
    if y.is_active()
    for z in y.data
]
```

### 7.3 Context Managers
```python
# Good: Use context managers for resources
with open(file_path, 'r') as f:
    data = f.read()

# Good: Multiple context managers
with open(input_file, 'r') as fin, open(output_file, 'w') as fout:
    fout.write(fin.read())

# Bad: Manual resource management
f = open(file_path, 'r')
data = f.read()
f.close()
```

## 8. Pre-Commit Formatting

### 8.1 Mandatory Pre-Commit Checks
Before committing, Claude Code MUST run:

```bash
# Format code with black
black .

# Sort imports
isort .
# OR use ruff for import sorting
ruff check --select I --fix .

# Check linting
ruff check .

# Verify formatting
black --check .
isort --check .
```

### 8.2 Pre-Commit Hook Configuration
```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/psf/black
    rev: 23.3.0
    hooks:
      - id: black
        language_version: python3.9

  - repo: https://github.com/pycqa/isort
    rev: 5.12.0
    hooks:
      - id: isort
        args: ["--profile", "black"]

  - repo: https://github.com/charliermarsh/ruff-pre-commit
    rev: v0.0.272
    hooks:
      - id: ruff
        args: [--fix, --exit-non-zero-on-fix]
```

## 9. Inline Comments

### 9.1 Comment Guidelines
- **When to Comment**: Explain WHY, not WHAT
- **Complex Logic**: Explain the approach for non-obvious algorithms
- **Workarounds**: Document why a workaround is necessary
- **TODOs**: Use `# TODO:` for future improvements

### 9.2 Comment Examples
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

# Good: TODO with context
# TODO: Optimise this function for large datasets (>1M rows)
# Consider using Dask or parallel processing
def process_data(data):
    pass
```

## 10. Line Length and Breaking

### 10.1 Line Length Rules
- Maximum line length: 100 characters
- Black will automatically break long lines
- Use parentheses for implicit line continuation

### 10.2 Line Breaking Examples
```python
# Good: Implicit line continuation with parentheses
result = some_function(
    argument1,
    argument2,
    argument3,
    argument4,
)

# Good: Breaking long strings
message = (
    "This is a very long message that needs to be broken "
    "across multiple lines for better readability."
)

# Good: Breaking long conditions
if (
    condition1
    and condition2
    and condition3
    and condition4
):
    do_something()

# Bad: Using backslash for continuation
result = some_function(argument1, argument2, \
                      argument3, argument4)
```

## 11. Enforcement

### 11.1 CI/CD Integration
All pull requests MUST pass:
- Black formatting check
- isort import sorting check
- Ruff linting check

### 11.2 Violations
**STRICTLY FORBIDDEN**:
- Committing unformatted code
- Skipping black formatting
- Ignoring linting errors without justification
- Using `# noqa` without explanation
- Disabling formatters in code

## 12. Character Encoding and Language Requirements

### 12.1 ASCII-Only Requirement
**STRICTLY FORBIDDEN**: Use of ANY non-ASCII characters in:
- Source code files (`.py`, `.pyi`)
- Comments (inline, block, or docstring comments)
- String literals (except test data and user-facing strings)
- Variable names, function names, class names
- Any Python code

**Forbidden characters include**:
- Non-English characters (Chinese, Japanese, Arabic, Cyrillic, etc.)
- Emoji and emoticons
- Accented characters (e, a, o, etc.)
- Mathematical symbols beyond basic ASCII
- Currency symbols beyond $ (dollar sign)
- Typographic quotes (" " ' ') - use straight quotes (" ')
- Special dashes (em dash, en dash) - use hyphen (-)
- Box-drawing characters
- Special symbols (checkmark, crossmark, arrows, etc.)

**Allowed**: Only ASCII characters (0x00-0x7F)

Example violations:
```python
# FORBIDDEN: Non-ASCII characters
# TODO: Fix this bug  (contains em dash)
result = 42  # checkmark emoji
name = "Francois"  # accented character

# ALLOWED: ASCII only
# TODO: Fix this bug
result = 42  # Correct implementation
name = "Francois"  # ASCII only
```

### 12.2 British English Requirement
**STRICTLY REQUIRED**: Use British English spelling in all:
- Code comments
- Docstrings
- Variable names
- Function names
- Documentation

**Common British vs American spellings**:
- colour (not color)
- behaviour (not behavior)
- optimise (not optimize)
- initialise (not initialize)
- analyse (not analyze)
- serialise (not serialize)
- synchronise (not synchronize)
- recognise (not recognize)
- organise (not organize)
- centre (not center)
- metre (not meter)
- licence (noun, not license)

Example:
```python
# Good: British English
def initialise_colour_scheme(behaviour: str) -> None:
    """Initialise the colour scheme based on user behaviour."""
    pass

# Bad: American English
def initialize_color_scheme(behavior: str) -> None:
    """Initialize the color scheme based on user behavior."""
    pass
```

## 13. Formatting Checklist

Before committing, verify:
- [ ] Code is formatted with black (`black .`)
- [ ] Imports are sorted (`isort .`)
- [ ] Linting passes (`ruff check .`)
- [ ] No formatting violations (`black --check .`)
- [ ] No import sorting violations (`isort --check .`)
- [ ] Line length is within limits (100 characters)
- [ ] Naming conventions are followed
- [ ] Comments are clear and explain WHY, not WHAT
- [ ] British English spelling used
- [ ] ASCII-only characters used