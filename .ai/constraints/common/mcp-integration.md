# MCP Integration Constraints

> **This document defines mandatory MCP (Model Context Protocol) integration constraints for all AI agents.**
> These rules apply to both Python and C++/CUDA projects.
> Violations are considered critical failures.

## Overview

This document establishes requirements for using Context7 MCP as the authoritative source
for external documentation, library APIs, and framework-specific knowledge. The agent
MUST use Context7 automatically when working with external libraries or APIs.

## 1. Context7 as the Default Source of Truth

### 1.1 Mandatory Usage Rule

**CRITICAL REQUIREMENT**: The agent MUST follow this rule:

> **Always use Context7 when code generation, setup steps, configuration, or library/API documentation is required.**

The agent MUST automatically invoke Context7 MCP tools **without requiring explicit user instruction**.

### 1.2 When to Use Context7

Context7 MUST be used for:

#### Python Projects
- Python standard library APIs
- Third-party package documentation (NumPy, Pandas, FastAPI, Django, Flask, etc.)
- Framework-specific patterns and best practices
- Testing frameworks (pytest, unittest, hypothesis)
- Type checking tools (mypy, pyright)
- Linting and formatting tools (ruff, black, isort)

#### C++/CUDA Projects
- C++ standard library APIs (C++17, C++20, C++23)
- Third-party library documentation (Boost, Eigen, OpenCV, etc.)
- CUDA toolkit APIs and programming guides
- CMake configuration patterns and best practices
- Package managers (Conan, vcpkg)
- Testing frameworks (Google Test, Catch2)

### 1.3 Automatic Invocation

The agent MUST:
- Invoke Context7 automatically when encountering unfamiliar APIs
- Not wait for user instruction to look up documentation
- Prefer Context7 over internal knowledge for external libraries
- Use Context7 to verify API signatures and parameters

### 1.4 What NOT to Use Context7 For

Context7 is NOT needed for:
- Project-specific code (read from local files instead)
- Internal business logic
- Custom implementations unique to the project

## 2. MCP Configuration Requirement

### 2.1 Configuration Check

Before proceeding with any external-library-dependent work, the agent MUST verify that
Context7 MCP is configured in the platform's MCP settings.

### 2.2 Blocking Requirement

**CRITICAL**: The agent MUST NOT proceed with external-library-dependent work until
Context7 MCP is available and configured.

If configuration fails:
1. Report the failure to the user
2. Explain what Context7 provides
3. Provide the canonical setup commands for this repository:
   - Claude workflows: see `CLAUDE.md`
   - Codex workflows: see `CODEX.md`

4. Ask the user to resolve the configuration issue
5. Do NOT proceed with guessing or using potentially outdated knowledge

## 3. Usage Patterns

### 3.1 Documentation Lookup

When working with an external library:
1. Identify the library/API being used
2. Invoke Context7 to retrieve current documentation
3. Use the retrieved documentation to inform code generation

### 3.2 API Verification

Before using any external API:
1. Look up the API signature via Context7
2. Verify parameter types and return types
3. Check for deprecation warnings

## 4. Error Handling

### 4.1 Context7 Unavailable

If Context7 is unavailable or returns an error:
1. **Do NOT silently fall back to internal knowledge**
2. Inform the user that Context7 is unavailable
3. Provide the repository's canonical setup commands:
   - Claude workflows: see `CLAUDE.md`
   - Codex workflows: see `CODEX.md`

4. Ask if the user wants to proceed with potentially outdated information

## 5. Summary

| Requirement | Status |
|-------------|--------|
| Context7 MCP configured | MANDATORY |
| Automatic invocation for external APIs | MANDATORY |
| Verification before API usage | MANDATORY |
| Fallback without user consent | FORBIDDEN |
| Proceeding without MCP when needed | FORBIDDEN |
