# Development & Collaboration Guidelines for Python Projects

> **This document defines mandatory contribution standards for Python repositories.**
> All contributors (human or AI) must follow these rules.

## Quick Start for Contributors

Before making any changes:

1. **Run `/init` at session start** - Loads relevant constraints based on your work
2. **Create a feature branch** - Never commit directly to protected branches
3. **Follow loaded constraints** - Technical requirements are in `.claude/constraints/`
4. **Run `/pre-commit validate`** - Before committing to check formatting, linting, tests
5. **Open a pull request** - Follow the PR template below

For detailed technical requirements, see `.claude/constraints/python/` and run `/init`.

## 1. General Principles

- Prefer **clarity over cleverness**
- Prefer **explicit decisions over implicit assumptions**
- Prefer **small, reviewable changes over large, opaque ones**
- Never trade correctness or safety for speed
- Follow PEP 8 and modern Python best practices (Python 3.9+)
- Prioritise readability and maintainability

If unsure, ask before acting.

## 2. Constraint System

This repository uses a modular constraint system. Instead of duplicating all technical requirements here, detailed constraints are organised in `.claude/constraints/`:

### Python-Specific Constraints
- `python/testing.md` - pytest, coverage (80%+), test organisation
- `python/formatting.md` - black, ruff, PEP 8, naming conventions
- `python/type-checking.md` - Type hints (mandatory), mypy configuration
- `python/dependencies.md` - pip, poetry, requirements.txt management
- `python/documentation.md` - Docstrings (Google-style), README, API docs
- `python/error-handling.md` - Exception handling, context managers
- `python/security.md` - Input validation, secrets management

### Common Constraints (All Projects)
- `common/git-workflow.md` - Branch policy, commit conventions, PR guidelines
- `common/roadmap-awareness.md` - Roadmap execution discipline
- `common/session-discipline.md` - Session continuity, decision hygiene

### Loading Constraints Automatically

At the start of every session, run:

```bash
/init
```

This skill will:
- Detect project type (Python)
- Check for active roadmaps
- Analyse git status and modified files
- Load only relevant constraints based on your current work
- Warn if you're on a protected branch

See CLAUDE.md for details on the constraint system and authority hierarchy.

## 3. Branching and Commits

### Protected Branches

**ABSOLUTE PROHIBITION**: Never commit directly to:
- `master` or `main`
- `develop`
- `release/*`
- `hotfix/*`

Always work on feature branches: `feat/<description>`, `fix/<description>`, etc.

### Commit Message Format

```
<type>(optional-scope): <short summary>

[optional body]
```

Types: `feat`, `fix`, `refactor`, `perf`, `docs`, `test`, `chore`, `style`

Rules:
- Less than 72 characters
- Imperative mood ("add", not "added")
- ASCII-only characters
- British English spelling

See `.claude/constraints/common/git-workflow.md` for detailed commit conventions.

## 4. Pull Request Guidelines

### PR Title

Follow commit message format:
```
<type>(optional-scope): <short description>
```

### PR Description Template

```markdown
## Summary
Brief description of what this PR does (2-3 sentences).

## Motivation
Why is this change necessary? What problem does it solve?

## Changes
- Bullet list of key changes
- New modules/functions added
- Modified interfaces
- Deprecated functionality

## Testing
- Unit tests added/modified
- Test coverage: X%
- How to verify the changes

## Dependencies
- New packages added (with versions)
- Updated packages

## Breaking Changes
- List any breaking changes
- Migration guide (if needed)

## Related
- Related issues: #123, #456
- Related PRs
```

### Before Opening a PR

Run the pre-commit validation:

```bash
/pre-commit validate
```

This checks:
- Code formatting (black, isort/ruff)
- Linting (ruff)
- Type checking (mypy)
- Tests (pytest)
- Coverage threshold

Fix any issues before opening the PR.

## 5. Code Review Process

### For Authors

**Before requesting review**:
1. Self-review your changes
2. Run `/pre-commit validate` and fix all issues
3. Write comprehensive PR description
4. Ensure commits are clean and logical
5. Update documentation and requirements.txt

**During review**:
- Respond to feedback constructively
- Make requested changes in new commits
- Mark conversations as resolved when addressed

**After approval**:
- Ensure CI passes
- Merge using appropriate strategy

### For Reviewers

Review for:
- **Correctness**: Does the code do what it claims?
- **Type Safety**: Are type hints complete and correct?
- **Testing**: Adequate test coverage (80%+)?
- **Readability**: Clear code, good naming, documentation?
- **Security**: No SQL injection, XSS, hardcoded secrets?

**Review checklist**:
- [ ] Tests pass and provide good coverage
- [ ] Type checking passes (mypy)
- [ ] Code is formatted (black, isort/ruff)
- [ ] Linting passes (ruff)
- [ ] Documentation is clear and complete
- [ ] requirements.txt updated if needed
- [ ] No secrets or credentials

## 6. Technical Standards Quick Reference

For detailed requirements, see `.claude/constraints/python/` and run `/init`.

### Python Version
- **Minimum**: Python 3.9
- **Recommended**: Python 3.11+
- Always use virtual environments

### Code Quality Tools
- **Formatter**: black (line length 100)
- **Linter**: ruff
- **Type checker**: mypy (strict mode)
- **Test framework**: pytest
- **Coverage**: pytest-cov (minimum 80%)

### Type Hints
- **Mandatory** for all public functions, methods, and class attributes
- Use `from typing import` for complex types
- Configure mypy in pyproject.toml

### Testing
- **Minimum coverage**: 80%
- **Target coverage**: 90%+
- Test file naming: `test_<module>.py`
- Use fixtures for setup/teardown

### Documentation
- **Docstrings**: Google-style for all public functions/classes
- **README.md**: Installation, usage, examples
- **Type hints**: Serve as inline documentation

## 7. Versioning and Releases

Follow Semantic Versioning (semver.org):
```
v<MAJOR>.<MINOR>.<PATCH>
```

- **MAJOR**: Incompatible API changes
- **MINOR**: Backward-compatible functionality additions
- **PATCH**: Backward-compatible bug fixes

Update version in:
- `pyproject.toml` or `setup.py`
- `__version__` in `__init__.py`
- `CHANGELOG.md`

## 8. Continuous Integration

All PRs MUST pass CI checks:
- All tests pass
- Type checking passes (mypy)
- Code formatting check (black, isort/ruff)
- Linting passes (ruff)
- Coverage threshold met (80%+)

## 9. Forbidden Practices

**STRICTLY FORBIDDEN**:
- Committing code without running tests
- Committing code without type hints on public APIs
- Committing unformatted code (must run black/isort)
- Installing packages without updating requirements.txt
- Using `import *` (except in `__init__.py` for re-exports)
- Using mutable default arguments
- Using bare `except:` clauses
- Hardcoding secrets or credentials
- Using `eval()` or `exec()` on untrusted input
- Committing to master/main without PR
- Force-pushing to master/main
- Merging your own PRs without approval
- Skipping code review

**STRICTLY FORBIDDEN: User or Author Attribution**
- **NEVER** include user or author information in commit messages
- **NEVER** include "Generated with", "Co-Authored-By", or any attribution lines
- **NEVER** include tool names, AI assistant names, or generation metadata
- Commit messages and PR descriptions must contain ONLY technical content
- This is a STRICT requirement with NO exceptions

**STRICTLY FORBIDDEN: Non-ASCII Characters**
- **NEVER** use Non-ASCII characters in any files, code, comments, or commit/PR messages
- **NEVER** use emoji, special symbols (checkmark, crossmark, arrows, etc.)
- **NEVER** use non-English characters (Chinese, Japanese, Arabic, Cyrillic, etc.)
- **NEVER** use accented characters (e, a, o, etc.)
- **NEVER** use typographic quotes (" " ' ') - use straight quotes (" ')
- **ONLY** ASCII characters (0x00-0x7F) are allowed
- Configure pre-commit hooks and CI/CD to reject Non-ASCII content

**STRICTLY REQUIRED: British English**
- **ALWAYS** use British English spelling in all text
- Examples: colour (not color), optimise (not optimize), initialise (not initialize)
- Applies to: code, comments, docstrings, commit messages, PR descriptions, documentation
- Configure spell-checkers to use British English (en_GB)
- Document exceptions for third-party library names

## 10. Working With Roadmaps and AI Agents

If this repository uses `agent_roadmaps/`:
- Do NOT bypass an active roadmap
- Large or multi-session changes MUST follow the roadmap process
- PRs related to a roadmap SHOULD reference:
    - Roadmap name
    - Phase / task identifier
    - Link to roadmap documentation

AI agents MUST follow CLAUDE.md and roadmap constraints at all times.

## 11. Skills and Tools

This repository provides skills to streamline development:

- **`/init`** - Session initialisation (MANDATORY at session start)
- **`/roadmap`** - Multi-session workflow management
- **`/pre-commit`** - Code quality validation before commits
- **`/dependency`** - Dependency management

See `.claude/skills/*/README.md` for documentation.

## 12. Final Rule

> **If a contribution does not clearly improve the codebase,**
> **it should not be merged.**

When in doubt, ask for clarification before proceeding.

---

**Remember**: These guidelines exist to maintain code quality, type safety, and maintainability. Following them ensures a healthy, sustainable Python codebase.

For detailed technical requirements, see:
- `.claude/constraints/python/` - Python-specific constraints
- `.claude/constraints/common/` - Common constraints
- CLAUDE.md - Agent operating constraints and authority hierarchy
