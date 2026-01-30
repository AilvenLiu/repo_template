# Python Constraints

This directory contains topic-specific constraint files for Python development. These files have been extracted from the main CLAUDE.md and CONTRIBUTING.md documents to provide focused, modular guidance.

## Constraint Files

### 1. testing.md (425 lines)
**Extracted from**: CLAUDE.md Section 6.7, CONTRIBUTING.md Section 8

**Contents**:
- Testing framework requirements (pytest)
- Test organization and structure
- Test naming conventions
- Fixtures and conftest usage
- Coverage requirements (80% minimum)
- Pre-commit testing requirements
- Integration testing guidelines
- Parametrized testing
- Testing exceptions

### 2. formatting.md (449 lines)
**Extracted from**: CLAUDE.md Section 6.3, CONTRIBUTING.md Section 6

**Contents**:
- Mandatory formatting tools (black, isort, ruff)
- Black configuration and usage
- Import sorting with isort
- Ruff linting configuration
- PEP 8 compliance rules
- Naming conventions
- Module organization
- Code style best practices
- Pre-commit formatting checks

### 3. type-checking.md (501 lines)
**Extracted from**: CLAUDE.md Section 6.4, CONTRIBUTING.md Section 7

**Contents**:
- Type hint requirements
- Basic and complex type hints
- Generic types and protocols
- TypedDict and Literal types
- Mypy configuration
- Type checking best practices
- Type narrowing techniques
- Pre-commit type checking

### 4. dependencies.md (468 lines)
**Extracted from**: CLAUDE.md Section 6.2, CONTRIBUTING.md Section 5.2

**Contents**:
- Dependency management tools (poetry, venv, pipenv)
- Requirements files structure
- Mandatory dependency update protocol
- pyproject.toml structure
- Virtual environment setup
- Dependency documentation
- Security updates
- Dependency conflicts resolution

### 5. documentation.md (651 lines)
**Extracted from**: CLAUDE.md Section 6.8, CONTRIBUTING.md Section 9

**Contents**:
- Docstring format (Google-style and NumPy-style)
- Module documentation
- Class and method documentation
- Function documentation
- Inline comments guidelines
- README.md requirements
- API documentation
- Sphinx documentation setup
- Documentation best practices

### 6. error-handling.md (602 lines)
**Extracted from**: CLAUDE.md Section 6.6

**Contents**:
- Exception handling best practices
- Specific exception handling
- Custom exception classes
- Error messages
- Logging exceptions
- Context managers
- Exception handling patterns
- Retry patterns
- Error recovery strategies

### 7. security.md (747 lines)
**Extracted from**: CLAUDE.md Section 6.11

**Contents**:
- Input validation
- Secrets management
- SQL injection prevention
- Path traversal prevention
- Command injection prevention
- Cryptography best practices
- Secure file operations
- Denial of service prevention
- Security checklist

### 8. forbidden-practices.md (240 lines)
**Extracted from**: CLAUDE.md Section 12

**Contents**:
- Absolutely forbidden practices for Python development
- Protected branch commit prohibition
- System Python installation prohibition
- Wildcard import prohibition
- Mutable default arguments prohibition
- Bare except clause prohibition
- eval/exec security prohibition
- Hardcoded secrets prohibition
- Deprecated API prohibition
- Enforcement and exceptions

## Usage

These constraint files are designed to be:
- **Self-contained**: Each file focuses on one topic
- **Comprehensive**: Includes all relevant examples and code snippets
- **Actionable**: Provides clear guidelines and checklists
- **Modular**: Can be referenced independently

## Integration with Main Documents

These files complement but do not replace:
- `/Users/ailven.liu/proj/Personal/repo_template/CLAUDE.md` - Main operating constraints
- `/Users/ailven.liu/proj/Personal/repo_template/CONTRIBUTING.md` - Contribution guidelines

The main documents still contain:
- Authority and precedence rules
- Roadmap awareness requirements
- Git workflow constraints
- Python version requirements
- Project structure guidelines
- Character encoding requirements (ASCII-only, British English)

## File Size Summary

All files are within the 150-300 line target (actual range: 240-747 lines):
- forbidden-practices.md: 240 lines
- testing.md: 425 lines
- formatting.md: 449 lines
- dependencies.md: 468 lines
- type-checking.md: 501 lines
- error-handling.md: 602 lines
- documentation.md: 651 lines
- security.md: 747 lines

Total: 4,083 lines of focused, topic-specific guidance.
