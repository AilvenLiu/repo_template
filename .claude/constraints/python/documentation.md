# Python Documentation Standards

> **This document defines mandatory documentation standards for Python projects.**
> All code must be properly documented before being committed.

## 1. Docstring Format

### 1.1 Standard Format
Use Google-style or NumPy-style docstrings consistently throughout the project.

### 1.2 Google-Style Docstrings (Recommended)
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

### 1.3 NumPy-Style Docstrings (Alternative)
```python
def complex_function(
    param1: List[int],
    param2: str,
    param3: Optional[float] = None
) -> Tuple[List[int], Dict[str, Any]]:
    """
    Perform a complex operation on the input data.

    This function processes the input parameters and returns
    transformed results along with metadata.

    Parameters
    ----------
    param1 : List[int]
        A list of integers to process. Must not be empty.
    param2 : str
        A string identifier for the operation.
    param3 : Optional[float], default=None
        Optional scaling factor. Defaults to 1.0 if not provided.

    Returns
    -------
    Tuple[List[int], Dict[str, Any]]
        A tuple containing:
        - List of processed integers
        - Dictionary with metadata including 'count', 'mean', 'operation'

    Raises
    ------
    ValueError
        If param1 is empty or param2 is invalid.
    TypeError
        If param1 contains non-integer values.

    Examples
    --------
    >>> result, metadata = complex_function([1, 2, 3], "scale", 2.0)
    >>> print(result)
    [2, 4, 6]
    >>> print(metadata['count'])
    3

    Notes
    -----
    This function modifies the input list in-place if param3 is None.

    See Also
    --------
    simple_function : A simpler version of this operation.
    """
    # Implementation
    pass
```

## 2. Module Documentation

### 2.1 Module Docstring
Every module MUST have a docstring at the top:

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

### 2.2 Module-Level Constants
Document module-level constants:

```python
"""Configuration constants for the application."""

# Maximum number of retry attempts for API calls
MAX_RETRIES: int = 3

# Default timeout in seconds for network requests
DEFAULT_TIMEOUT: int = 30

# Supported file formats for data processing
SUPPORTED_FORMATS: List[str] = ["csv", "json", "parquet"]
```

## 3. Class Documentation

### 3.1 Class Docstring
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
        """Initialise the DataProcessor.

        Args:
            config: Optional configuration dictionary. If None, uses defaults.
        """
        self.config = config or {}
        self.cache: Dict[str, pd.DataFrame] = {}
```

### 3.2 Method Documentation
```python
class DataProcessor:
    """Process data from various file formats."""

    def process_file(
        self,
        file_path: Path,
        validate: bool = True
    ) -> pd.DataFrame:
        """Process a data file and return a DataFrame.

        Args:
            file_path: Path to the input file.
            validate: Whether to validate data after loading. Defaults to True.

        Returns:
            Processed DataFrame with validated data.

        Raises:
            FileNotFoundError: If file_path does not exist.
            ValueError: If file format is not supported or data is invalid.

        Example:
            >>> processor = DataProcessor()
            >>> df = processor.process_file(Path('data.csv'))
            >>> print(df.shape)
            (100, 5)
        """
        # Implementation
        pass
```

## 4. Function Documentation

### 4.1 Simple Function
```python
def add_numbers(a: int, b: int) -> int:
    """Add two numbers and return the result.

    Args:
        a: First number.
        b: Second number.

    Returns:
        Sum of a and b.
    """
    return a + b
```

### 4.2 Complex Function
```python
def process_data(
    data: pd.DataFrame,
    filters: Optional[Dict[str, Any]] = None,
    transformations: Optional[List[Callable]] = None
) -> pd.DataFrame:
    """Process DataFrame with optional filters and transformations.

    This function applies a series of filters and transformations to
    the input DataFrame. Filters are applied first, followed by
    transformations in the order specified.

    Args:
        data: Input DataFrame to process.
        filters: Optional dictionary of column names to filter values.
            Example: {'age': (18, 65), 'status': 'active'}
        transformations: Optional list of transformation functions.
            Each function should accept and return a DataFrame.

    Returns:
        Processed DataFrame with filters and transformations applied.

    Raises:
        ValueError: If data is empty or filters are invalid.
        KeyError: If filter column does not exist in data.

    Examples:
        >>> df = pd.DataFrame({'age': [20, 30, 40], 'status': ['active', 'inactive', 'active']})
        >>> filters = {'age': (25, 35), 'status': 'active'}
        >>> result = process_data(df, filters=filters)
        >>> print(result)
           age  status
        1   30  active

    Note:
        This function does not modify the input DataFrame in-place.
        A copy is created and returned.

    See Also:
        apply_filters: Apply filters to DataFrame.
        apply_transformations: Apply transformations to DataFrame.
    """
    # Implementation
    pass
```

## 5. Inline Comments

### 5.1 Comment Guidelines
- **When to Comment**: Explain WHY, not WHAT
- **Complex Logic**: Explain the approach for non-obvious algorithms
- **Workarounds**: Document why a workaround is necessary
- **TODOs**: Use `# TODO:` for future improvements

### 5.2 Good Comment Examples
```python
# Good: Explains why
# Use binary search because the list is sorted and can be large (>10k items)
index = bisect.bisect_left(sorted_list, target)

# Good: Documents workaround
# Workaround for pandas bug #12345: manually convert timezone
# Remove this when pandas 2.1.0 is released
df['timestamp'] = df['timestamp'].dt.tz_localize(None)

# Good: TODO with context
# TODO: Optimise this function for large datasets (>1M rows)
# Consider using Dask or parallel processing
def process_data(data):
    pass

# Good: Explains complex algorithm
# Use dynamic programming to find longest common subsequence
# Time complexity: O(m*n), Space complexity: O(m*n)
dp = [[0] * (n + 1) for _ in range(m + 1)]
```

### 5.3 Bad Comment Examples
```python
# Bad: States the obvious
# Increment counter by 1
counter += 1

# Bad: Redundant with code
# Loop through items
for item in items:
    process(item)

# Bad: Outdated comment
# This function returns a list (actually returns a dict now)
def get_data():
    return {}
```

## 6. README.md Requirements

### 6.1 Comprehensive README Structure
Every project MUST have a comprehensive README.md:

```markdown
# Project Name

Brief description of the project (1-2 sentences).

## Features

- Feature 1: Description
- Feature 2: Description
- Feature 3: Description

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
print(result)
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

### Production Dependencies
- **numpy** (1.24.0+): Numerical computing library
- **pandas** (2.0.0+): Data manipulation and analysis
- **requests** (2.31.0+): HTTP library for API calls

### Development Dependencies
- **pytest** (7.3.0+): Testing framework
- **black** (23.3.0+): Code formatter
- **mypy** (1.3.0+): Static type checker

## Contributing

Please read CONTRIBUTING.md for details on our code of conduct and the process for submitting pull requests.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Changelog

See CHANGELOG.md for a list of changes in each version.
```

## 7. API Documentation

### 7.1 Public API Documentation
All public APIs MUST be documented:

```python
# __init__.py
"""Public API for the package.

This module exports the main classes and functions for public use.
"""

from package_name.core import DataProcessor, process_file
from package_name.utils import validate_data, transform_data

__all__ = [
    "DataProcessor",
    "process_file",
    "validate_data",
    "transform_data",
]

__version__ = "0.1.0"
```

### 7.2 API Changes Documentation
Document API changes in CHANGELOG.md:

```markdown
# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- New feature X with function `process_data()`

### Changed
- Updated `DataProcessor.process_file()` to accept Path objects

### Deprecated
- `old_function()` is deprecated, use `new_function()` instead

### Removed
- Removed deprecated `legacy_function()`

### Fixed
- Fixed bug in `validate_data()` when handling None values

### Security
- Fixed security vulnerability in authentication module

## [0.1.0] - 2024-01-15

### Added
- Initial release
- Basic data processing functionality
```

## 8. Type Hints as Documentation

### 8.1 Type Hints Enhance Documentation
```python
from typing import List, Dict, Optional, Union
from pathlib import Path

def process_file(
    file_path: Path,
    encoding: str = "utf-8",
    validate: bool = True
) -> Dict[str, Union[int, float, str]]:
    """Process a file and return statistics.

    Type hints provide additional documentation about expected types.

    Args:
        file_path: Path to the input file.
        encoding: File encoding. Defaults to "utf-8".
        validate: Whether to validate data. Defaults to True.

    Returns:
        Dictionary with statistics (keys: 'count', 'mean', 'status').
    """
    # Implementation
    pass
```

## 9. Documentation Tools

### 9.1 Sphinx Documentation
For larger projects, use Sphinx for documentation:

```bash
# Install Sphinx
pip install sphinx sphinx-rtd-theme

# Initialise Sphinx
sphinx-quickstart docs

# Generate API documentation
sphinx-apidoc -o docs/api src/

# Build HTML documentation
cd docs
make html
```

### 9.2 Sphinx Configuration
```python
# docs/conf.py
import os
import sys
sys.path.insert(0, os.path.abspath('../src'))

project = 'Project Name'
copyright = '2024, Author Name'
author = 'Author Name'

extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.napoleon',
    'sphinx.ext.viewcode',
    'sphinx.ext.intersphinx',
]

templates_path = ['_templates']
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']

html_theme = 'sphinx_rtd_theme'
html_static_path = ['_static']

napoleon_google_docstring = True
napoleon_numpy_docstring = True
```

## 10. Documentation Best Practices

### 10.1 Keep Documentation Updated
- Update docstrings when changing function signatures
- Update README.md when adding new features
- Update CHANGELOG.md for every release
- Update API documentation for breaking changes

### 10.2 Documentation Completeness
- All public functions MUST have docstrings
- All classes MUST have docstrings
- All modules MUST have docstrings
- Complex algorithms MUST have explanatory comments
- Workarounds MUST be documented with reasons

### 10.3 Documentation Clarity
- Use clear, concise language
- Provide examples for complex functions
- Document edge cases and limitations
- Explain the "why" not just the "what"

## 11. Pre-Commit Documentation Checks

### 11.1 Mandatory Checks
Before committing, verify:
- [ ] All public functions have docstrings
- [ ] All classes have docstrings
- [ ] All modules have docstrings
- [ ] README.md is updated for new features
- [ ] CHANGELOG.md is updated
- [ ] API changes are documented
- [ ] Examples are provided for complex functions

## 12. Enforcement

### 12.1 Violations
**STRICTLY FORBIDDEN**:
- Committing public functions without docstrings
- Committing classes without docstrings
- Committing modules without docstrings
- Outdated documentation
- Missing README.md
- Undocumented API changes

### 12.2 CI/CD Integration
All pull requests MUST:
- Have complete docstrings for public APIs
- Have updated README.md
- Have updated CHANGELOG.md
- Pass documentation linting

## 13. Character Encoding and Language Requirements

### 13.1 ASCII-Only Requirement
**STRICTLY FORBIDDEN**: Use of ANY non-ASCII characters in documentation:
- Source code comments
- Docstrings (module, class, function, method)
- README.md and other markdown files
- CHANGELOG.md
- Any documentation files

**Allowed**: Only ASCII characters (0x00-0x7F)

### 13.2 British English Requirement
**STRICTLY REQUIRED**: Use British English spelling in all documentation:
- Docstrings
- Comments
- README.md
- CHANGELOG.md
- API documentation
- User guides

**Common British spellings**:
- colour, behaviour, optimise, initialise, analyse, serialise, synchronise, recognise, organise, centre, metre, licence (noun)

Example:
```python
def optimise_performance(colour_scheme: str) -> None:
    """
    Optimise application performance based on colour scheme.

    This function analyses the current behaviour and initialises
    the optimisation process to improve overall performance.

    Args:
        colour_scheme: The colour scheme to optimise for

    Returns:
        None
    """
    pass
```

## 14. Documentation Checklist

Before committing, verify:
- [ ] All public functions have complete docstrings
- [ ] All classes have docstrings with attributes documented
- [ ] All modules have docstrings
- [ ] Complex logic has explanatory comments
- [ ] README.md is updated
- [ ] CHANGELOG.md is updated
- [ ] Examples are provided where appropriate
- [ ] Type hints are complete and accurate
- [ ] API changes are documented
- [ ] Workarounds are documented with reasons
- [ ] British English spelling used
- [ ] ASCII-only characters used