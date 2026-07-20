# Python Code Style and Formatting

> **This document defines mandatory code formatting standards for Python projects.**
> All code must be formatted according to these rules before being committed.

## 1. Mandatory Formatting Tools

### 1.1 Required Tools

The Python toolchain for this repository is intentionally minimal. Only two
tools are permitted for code style, linting, and import management:

- **Formatter**: `ruff format` (the only sanctioned code formatter)
- **Linter**: `ruff check` (covers pyflakes, pycodestyle, bugbear, naming, etc.)
- **Import sorting**: `ruff check --select I` (handled by ruff's isort rules)

The following tools are **explicitly forbidden** and MUST NOT be added to
`pyproject.toml`, CI pipelines, pre-commit hooks, or developer documentation:

- `black`
- `isort`
- `flake8`
- `pylint`
- `autopep8`, `yapf`, or any other formatter

The only static-analysis companion to ruff in this repository is `mypy`
(see `python/type-checking.md`).

### 1.2 Installation

```bash
# Add ruff through the guarded dependency workflow
.agents/bin/agent-dependency add ruff --dev
```

## 2. Ruff Configuration

### 2.1 Canonical pyproject.toml Block

```toml
# pyproject.toml
[tool.ruff]
line-length = 100
target-version = "py310"
extend-exclude = [
    ".eggs",
    ".git",
    ".venv",
    "build",
    "dist",
]

[tool.ruff.lint]
select = [
    "E",   # pycodestyle errors
    "W",   # pycodestyle warnings
    "F",   # pyflakes
    "I",   # isort (import ordering)
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
ignore = []

[tool.ruff.lint.per-file-ignores]
"__init__.py" = ["F401"]            # Re-exports legitimately appear "unused"
"tests/*"     = ["S101", "ARG"]     # `assert` and unused fixtures are fine in tests

[tool.ruff.lint.isort]
known-first-party = ["src"]

[tool.ruff.format]
quote-style = "double"
indent-style = "space"
skip-magic-trailing-comma = false
line-ending = "lf"
```

### 2.2 Line Length

`line-length = 100`. This applies to both the formatter and the linter; do not
introduce per-tool overrides.

### 2.3 Target Version

Use `target-version = "py310"` (or the project's true minimum, never lower
than `py310` since this repository mandates Python 3.10+).

## 3. Running Ruff

### 3.1 Format

```bash
# Format all files in-place
ruff format .

# Check formatting without writing changes (CI / pre-commit)
ruff format --check .

# Show the formatting diff
ruff format --diff .

# Format a single file or directory
ruff format src/module.py
ruff format src/
```

### 3.2 Lint

```bash
# Lint everything
ruff check .

# Auto-fix safe violations
ruff check --fix .

# Lint a single path
ruff check src/module.py

# Show the rule code with each violation (handy when triaging)
ruff check --output-format=full .
```

### 3.3 Import Sorting

Import sorting is part of `ruff check` via the `I` rule code; there is **no
separate import-sorting tool**.

```bash
# Check import order only
ruff check --select I .

# Fix import order in place
ruff check --select I --fix .
```

### 3.4 Combined Workflow

The canonical "format + lint" sequence is:

```bash
ruff format .
ruff check --fix .
```

The canonical "verify only" sequence (CI / pre-commit) is:

```bash
ruff format --check .
ruff check .
```

## 4. Style Rules Enforced by Ruff

`ruff format` and the rule set above enforce the following without manual
intervention:

- 100-character line length, automatic line breaking
- Double-quoted strings, straight quotes only
- 4-space indentation, never tabs
- Trailing commas in multi-line literals and call sites
- Two blank lines between top-level definitions, one between methods
- pyupgrade rewrites for modern Python idioms
- bugbear catches for the most common correctness traps

Do not hand-format around the formatter; if a rule needs adjustment, change
the configuration in `pyproject.toml` rather than fighting the tool locally.

## 5. PEP 8 Compliance

### 5.1 Core Rules (also enforced by ruff)

- **Line length**: 100 characters
- **Indentation**: 4 spaces (never tabs)
- **Blank lines**:
  - 2 blank lines between top-level functions and classes
  - 1 blank line between methods in a class
- **Whitespace**: standard PEP 8 whitespace rules
- **Comments**: complete sentences, kept up to date with the code

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

The `N` rule code in ruff enforces these naming patterns automatically.

## 6. Module Organization

### 6.1 Standard Module Structure

```python
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
from package_name import constants
from package_name.subpackage import helper

# Constants
DEFAULT_TIMEOUT = 30
MAX_RETRIES = 3


class MyClass:
    """Class docstring."""

    pass


def my_function() -> None:
    """Function docstring."""
    pass


if __name__ == "__main__":
    main()
```

Import grouping (stdlib / third-party / local), blank-line separation, and
ordering inside each group are all enforced by `ruff check --select I`.

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

# Bad: Too complex, use a regular loop
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
with open(file_path, "r") as f:
    data = f.read()

# Good: Multiple context managers
with open(input_file, "r") as fin, open(output_file, "w") as fout:
    fout.write(fin.read())

# Bad: Manual resource management
f = open(file_path, "r")
data = f.read()
f.close()
```

## 8. Pre-Commit Formatting

### 8.1 Mandatory Pre-Commit Checks

Before committing, the agent MUST run:

```bash
# Format and auto-fix in place
ruff format .
ruff check --fix .

# Verify nothing remains to format or fix
ruff format --check .
ruff check .
```

### 8.2 Pre-Commit Hook Configuration

```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.6.9
    hooks:
      - id: ruff-format
      - id: ruff
        args: [--fix, --exit-non-zero-on-fix]
```

There must not be entries for `black`, `isort`, `flake8`, or `pylint` in any
pre-commit configuration.

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
df["timestamp"] = df["timestamp"].dt.tz_localize(None)

# Good: TODO with context
# TODO: Optimise this function for large datasets (>1M rows)
# Consider using Dask or parallel processing
def process_data(data):
    pass
```

## 10. Line Length and Breaking

### 10.1 Line Length Rules

- Maximum line length: 100 characters
- `ruff format` will automatically break long lines
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

- `ruff format --check .`
- `ruff check .`
- `mypy` (see `python/type-checking.md`)

### 11.2 Violations

**STRICTLY FORBIDDEN**:

- Committing unformatted code
- Adding `black`, `isort`, `flake8`, or `pylint` as project dependencies
- Configuring any formatter or linter other than `ruff` and `mypy`
- Ignoring linting errors without justification
- Using `# noqa` without an explicit rule code and explanation
- Disabling formatter or linter rules in code without documentation

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
- Currency symbols beyond `$` (dollar sign)
- Typographic quotes - use straight quotes (`"` `'`)
- Special dashes (em dash, en dash) - use hyphen (`-`)
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
- User-facing generated text
- Skill output and slash-command output

**Skill variant requirement**:

- If a skill offers multiple language variants, choose the British-English-
  compliant variant
- Prefer bundled local skills that already comply with the repository's
  British-English requirement when producing English output

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

- [ ] Code is formatted (`ruff format .`)
- [ ] Imports and lints are clean (`ruff check .`)
- [ ] Format check passes (`ruff format --check .`)
- [ ] No `black`, `isort`, `flake8`, or `pylint` configuration or dependencies remain
- [ ] Line length is within limits (100 characters)
- [ ] Naming conventions are followed
- [ ] Comments are clear and explain WHY, not WHAT
- [ ] British English spelling used
- [ ] ASCII-only characters used
