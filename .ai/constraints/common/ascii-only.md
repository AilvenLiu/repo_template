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
   ```

   ```cpp
   // C++ - OK
   std::string message = "Hello, 世界";  // Non-ASCII in string literal
   ```

2. **Comments** (documentation and explanations)
   ```python
   # This handles Japanese characters: 日本語
   def process_text(text):
       pass
   ```

3. **Documentation files** (README.md, docs/, etc.)

### 2.2 Where Non-ASCII is FORBIDDEN

**NEVER use non-ASCII characters in**:
- Variable names
- Function/method names
- Class names
- Module/file names
- Import statements

## 3. Checking for Violations

Use `grep` to find non-ASCII characters in code:

```bash
# Find non-ASCII characters in Python files
grep -P '[^\x00-\x7F]' **/*.py

# Find non-ASCII characters in C++ files
grep -P '[^\x00-\x7F]' **/*.cpp **/*.hpp
```

## 4. Summary

**Golden Rule**: If it's not a string literal or comment, it must be ASCII-only.

**Why**: Cross-platform compatibility, encoding safety, tool compatibility.

**Enforcement**: Pre-commit hooks, CI/CD checks, code review.
