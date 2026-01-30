# MCP Integration Constraints

> **This document defines mandatory MCP (Model Context Protocol) integration constraints for all AI agents.**
> These rules apply to both Python and C++/CUDA projects.
> Violations are considered critical failures.

## Overview

This document establishes requirements for using Context7 MCP as the authoritative source
for external documentation, library APIs, and framework-specific knowledge. Claude Code
MUST use Context7 automatically when working with external libraries or APIs.

## 1. Context7 as the Default Source of Truth

### 1.1 Mandatory Usage Rule

**CRITICAL REQUIREMENT**: Claude Code MUST follow this rule:

> **Always use Context7 when code generation, setup steps, configuration, or library/API documentation is required.**

Claude Code MUST automatically invoke Context7 MCP tools **without requiring explicit user instruction**.

### 1.2 When to Use Context7

Context7 MUST be used for:

#### Python Projects
- Python standard library APIs
- Third-party package documentation (NumPy, Pandas, FastAPI, Django, Flask, etc.)
- Framework-specific patterns and best practices
- Package management (pip, poetry, pipenv)
- Virtual environment setup and configuration
- Testing frameworks (pytest, unittest, hypothesis)
- Type checking tools (mypy, pyright)
- Linting and formatting tools (ruff, black, isort)
- Async frameworks (asyncio, aiohttp, httpx)
- Database ORMs (SQLAlchemy, Django ORM, Tortoise)
- API frameworks (FastAPI, Flask, Django REST)

#### C++/CUDA Projects
- C++ standard library APIs (C++17, C++20, C++23)
- Third-party library documentation (Boost, Eigen, OpenCV, etc.)
- CUDA toolkit APIs and programming guides
- CMake configuration patterns and best practices
- Build system setup and toolchain configuration
- Compiler-specific features and extensions (GCC, Clang, MSVC)
- Package managers (Conan, vcpkg)
- Testing frameworks (Google Test, Catch2)
- Static analysis tools (clang-tidy, cppcheck)

### 1.3 Automatic Invocation

Claude Code MUST:
- Invoke Context7 automatically when encountering unfamiliar APIs
- Not wait for user instruction to look up documentation
- Prefer Context7 over internal knowledge for external libraries
- Use Context7 to verify API signatures and parameters
- Consult Context7 for best practices and recommended patterns

### 1.4 What NOT to Use Context7 For

Context7 is NOT needed for:
- Project-specific code (read from local files instead)
- Internal business logic
- Custom implementations unique to the project
- Code that has already been read from the repository

## 2. MCP Configuration Requirement

### 2.1 Configuration Check

Before proceeding with any external-library-dependent work, Claude Code MUST verify that Context7 MCP is configured.

### 2.2 Configuration Command

If Claude Code detects that Context7 MCP is not configured for this project, it MUST immediately configure it using:

```bash
claude mcp add context7 -- npx -y @anthropic-ai/context7-mcp@latest
```

### 2.3 Blocking Requirement

**CRITICAL**: Claude Code MUST NOT proceed with external-library-dependent work until Context7 MCP is available and configured.

If configuration fails:
1. Report the failure to the user
2. Explain what Context7 provides
3. Ask the user to resolve the configuration issue
4. Do NOT proceed with guessing or using potentially outdated knowledge

## 3. Usage Patterns

### 3.1 Documentation Lookup

When working with an external library:

```
1. Identify the library/API being used
2. Invoke Context7 to retrieve current documentation
3. Use the retrieved documentation to inform code generation
4. Cite the documentation source when relevant
```

### 3.2 API Verification

Before using any external API:

```
1. Look up the API signature via Context7
2. Verify parameter types and return types
3. Check for deprecation warnings
4. Note any version-specific behaviour
```

### 3.3 Best Practices Retrieval

When implementing patterns:

```
1. Query Context7 for recommended patterns
2. Check for framework-specific conventions
3. Verify compatibility with project's version requirements
4. Apply patterns consistent with retrieved documentation
```

## 4. Error Handling

### 4.1 Context7 Unavailable

If Context7 is unavailable or returns an error:

1. **Do NOT silently fall back to internal knowledge**
2. Inform the user that Context7 is unavailable
3. Explain the limitation this creates
4. Ask if the user wants to proceed with potentially outdated information
5. Document any assumptions made if proceeding

### 4.2 Documentation Not Found

If Context7 cannot find documentation for a specific library:

1. Report that documentation was not found
2. Ask the user for alternative documentation sources
3. Check if the library name or version is correct
4. Consider if the library is too obscure or new for Context7

## 5. Integration with Other Constraints

### 5.1 Dependency Management

When using the `/dependency` skill:
- Use Context7 to verify package names and versions
- Check for known compatibility issues
- Retrieve installation instructions

### 5.2 Testing

When writing tests for external libraries:
- Use Context7 to find testing patterns for the library
- Check for mock/stub recommendations
- Verify test fixture patterns

### 5.3 Type Checking

When adding type hints for external libraries:
- Use Context7 to find type stub packages
- Verify generic type parameters
- Check for typing extensions requirements

## 6. Compliance Verification

### 6.1 Self-Check

Claude Code MUST periodically verify:
- [ ] Context7 MCP is configured and accessible
- [ ] External library documentation is being retrieved
- [ ] API signatures are being verified before use
- [ ] Best practices are being consulted for new patterns

### 6.2 Violation Examples

**VIOLATION**: Using an external library API without consulting Context7
```python
# BAD: Guessing API without verification
import pandas as pd
df = pd.read_csv(file, parse_dates=True)  # Is this the correct parameter?
```

**CORRECT**: Consulting Context7 first
```python
# GOOD: After verifying via Context7 that parse_dates accepts bool or list
import pandas as pd
df = pd.read_csv(file, parse_dates=True)  # Verified: parse_dates accepts bool
```

## 7. Summary

| Requirement | Status |
|-------------|--------|
| Context7 MCP configured | MANDATORY |
| Automatic invocation for external APIs | MANDATORY |
| Verification before API usage | MANDATORY |
| Fallback without user consent | FORBIDDEN |
| Proceeding without MCP when needed | FORBIDDEN |
