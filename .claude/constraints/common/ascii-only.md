# ASCII-Only Code Compliance

> **This document defines mandatory ASCII-only compliance standards for all code.**
> Non-ASCII characters in code can cause cross-platform compatibility issues and encoding problems.

## 1. ASCII-Only Requirement

### 1.1 Core Principle

**MANDATORY**: All source code files MUST use only ASCII characters (0x00-0x7F) in:
- Variable names
- Function names
- Class names
- Keywords and operators
- Whitespace and control characters

### 1.2 Rationale

ASCII-only code ensures:
- **Cross-platform compatibility**: Works on all systems regardless of locale
- **No encoding issues**: Avoids UTF-8, UTF-16, Latin-1 encoding problems
- **Tool compatibility**: All development tools support ASCII
- **Version control**: Git diffs work correctly without encoding issues
- **Terminal compatibility**: Displays correctly in all terminals

## 2. Allowed Exceptions

### 2.1 Where Non-ASCII IS Allowed

Non-ASCII characters are ONLY permitted in:

1. **String literals** (user-facing text)
   ```python
   # Python - OK
   message = "Hello, 世界"  # Non-ASCII in string literal
   greeting = "Bonjour, café"  # Non-ASCII in string literal
   ```

   ```cpp
   // C++ - OK
   std::string message = "Hello, 世界";  // Non-ASCII in string literal
   const char* greeting = u8"Bonjour, café";  // UTF-8 string literal
   ```

2. **Comments** (documentation and explanations)
   ```python
   # Python - OK
   # This handles Japanese characters: 日本語
   def process_text(text):
       pass
   ```

   ```cpp
   // C++ - OK
   // This handles Japanese characters: 日本語
   void process_text(const std::string& text) {
   }
   ```

3. **Documentation files** (README.md, docs/, etc.)
   - Markdown files can use any Unicode characters
   - API documentation can include examples with non-ASCII

### 2.2 Where Non-ASCII is FORBIDDEN

**NEVER use non-ASCII characters in**:

1. **Variable names**
   ```python
   # Python - FORBIDDEN
   café = "coffee"  # ❌ Non-ASCII in variable name

   # Python - CORRECT
   cafe = "coffee"  # ✅ ASCII-only variable name
   ```

   ```cpp
   // C++ - FORBIDDEN
   int café = 5;  // ❌ Non-ASCII in variable name

   // C++ - CORRECT
   int cafe = 5;  // ✅ ASCII-only variable name
   ```

2. **Function/method names**
   ```python
   # Python - FORBIDDEN
   def calculer_café():  # ❌ Non-ASCII in function name
       pass

   # Python - CORRECT
   def calculate_cafe():  # ✅ ASCII-only function name
       pass
   ```

3. **Class names**
   ```python
   # Python - FORBIDDEN
   class Café:  # ❌ Non-ASCII in class name
       pass

   # Python - CORRECT
   class Cafe:  # ✅ ASCII-only class name
       pass
   ```

4. **Module/file names**
   ```
   # FORBIDDEN
   café.py  # ❌ Non-ASCII in filename

   # CORRECT
   cafe.py  # ✅ ASCII-only filename
   ```

5. **Import statements**
   ```python
   # Python - FORBIDDEN
   from café import brew  # ❌ Non-ASCII in import

   # Python - CORRECT
   from cafe import brew  # ✅ ASCII-only import
   ```

## 3. Checking for Violations

### 3.1 Manual Check

Use `grep` to find non-ASCII characters in code:

```bash
# Find non-ASCII characters in Python files
grep -P '[^\x00-\x7F]' **/*.py

# Find non-ASCII characters in C++ files
grep -P '[^\x00-\x7F]' **/*.cpp **/*.hpp

# Exclude comments and strings (basic check)
grep -P '[^\x00-\x7F]' **/*.py | grep -v '#' | grep -v '"' | grep -v "'"
```

### 3.2 Python: Using isascii()

```python
# Check if identifier is ASCII-only
def is_valid_identifier(name: str) -> bool:
    """Check if identifier uses only ASCII characters."""
    return name.isascii() and name.isidentifier()

# Example
assert is_valid_identifier("cafe")  # ✅ Valid
assert not is_valid_identifier("café")  # ❌ Invalid
```

### 3.3 Pre-Commit Hook

Add to `.git/hooks/pre-commit`:

```bash
#!/bin/bash
# Check for non-ASCII in Python/C++ identifiers

# Find Python files with non-ASCII outside strings/comments
if git diff --cached --name-only | grep -E '\\.py$' > /dev/null; then
    echo "Checking Python files for non-ASCII characters..."
    # This is a simplified check - production version would parse AST
    if git diff --cached | grep -P '^\\+.*[^\\x00-\\x7F]' | grep -v '#' | grep -v '"' | grep -v "'"; then
        echo "ERROR: Non-ASCII characters found in Python code"
        echo "Only ASCII characters are allowed in identifiers"
        exit 1
    fi
fi

# Similar check for C++ files
if git diff --cached --name-only | grep -E '\\.(cpp|hpp|h|cc)$' > /dev/null; then
    echo "Checking C++ files for non-ASCII characters..."
    if git diff --cached | grep -P '^\\+.*[^\\x00-\\x7F]' | grep -v '//' | grep -v '"'; then
        echo "ERROR: Non-ASCII characters found in C++ code"
        echo "Only ASCII characters are allowed in identifiers"
        exit 1
    fi
fi
```

## 4. Common Violations and Fixes

### 4.1 Accented Characters

```python
# WRONG
résumé = "document"  # ❌ Accented characters

# CORRECT
resume = "document"  # ✅ ASCII-only
```

### 4.2 Mathematical Symbols

```python
# WRONG
π = 3.14159  # ❌ Greek letter pi
Δ = 0.001    # ❌ Greek letter delta

# CORRECT
pi = 3.14159    # ✅ ASCII spelling
delta = 0.001   # ✅ ASCII spelling
```

### 4.3 Currency Symbols

```python
# WRONG
price_€ = 100  # ❌ Euro symbol

# CORRECT
price_eur = 100  # ✅ ASCII abbreviation
```

### 4.4 Emoji and Special Characters

```python
# WRONG
def process_✓():  # ❌ Checkmark emoji
    pass

# CORRECT
def process_ok():  # ✅ ASCII word
    pass
```

## 5. Enforcement

### 5.1 Code Review Checklist

Before committing, verify:
- [ ] All variable names use only ASCII characters
- [ ] All function/method names use only ASCII characters
- [ ] All class names use only ASCII characters
- [ ] All file names use only ASCII characters
- [ ] Non-ASCII characters only appear in strings and comments

### 5.2 CI/CD Integration

Add ASCII-only check to CI/CD pipeline:

```yaml
# GitHub Actions example
- name: Check ASCII-only compliance
  run: |
    # Check Python files
    if find . -name "*.py" -exec grep -P '[^\x00-\x7F]' {} + | grep -v '#' | grep -v '"' | grep -v "'"; then
      echo "Non-ASCII characters found in Python code"
      exit 1
    fi

    # Check C++ files
    if find . -name "*.cpp" -o -name "*.hpp" -exec grep -P '[^\x00-\x7F]' {} + | grep -v '//' | grep -v '"'; then
      echo "Non-ASCII characters found in C++ code"
      exit 1
    fi
```

## 6. Best Practices

### 6.1 Use English Names

- Use English words for identifiers
- Avoid transliteration of non-English words
- Use standard abbreviations (e.g., "eur" for Euro, "jpy" for Yen)

### 6.2 Document Non-ASCII Usage

When using non-ASCII in strings or comments, document why:

```python
# This function processes Japanese text (日本語)
# Input must be UTF-8 encoded
def process_japanese_text(text: str) -> str:
    """Process Japanese text.

    Args:
        text: UTF-8 encoded Japanese text (日本語)

    Returns:
        Processed text
    """
    return text.strip()
```

### 6.3 File Encoding

Always use UTF-8 encoding for source files:

```python
# Python - Add encoding declaration if needed
# -*- coding: utf-8 -*-
```

```cpp
// C++ - Ensure files are saved as UTF-8
// Most modern editors default to UTF-8
```

## 7. Exceptions and Waivers

### 7.1 When to Request Exception

Request an exception ONLY if:
- Working with legacy code that cannot be changed
- Interfacing with external systems that require non-ASCII
- Domain-specific requirements (e.g., mathematical notation in scientific code)

### 7.2 Exception Documentation

Document exceptions in code:

```python
# EXCEPTION: Using Greek letter for mathematical accuracy
# This matches the notation in the research paper (DOI: 10.xxxx/xxxxx)
λ = 0.5  # wavelength parameter
```

## 8. Summary

**Golden Rule**: If it's not a string literal or comment, it must be ASCII-only.

**Why**: Cross-platform compatibility, encoding safety, tool compatibility.

**How to Check**: Use `grep -P '[^\x00-\x7F]'` to find violations.

**Enforcement**: Pre-commit hooks, CI/CD checks, code review.
