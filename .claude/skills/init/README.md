# Session Initialization Skill

Intelligent, context-aware session initialization for Claude Code that automatically loads relevant constraints based on your current work.

## Overview

The `/init` skill solves the problem of loading large constraint files (2000+ lines) at every session start by intelligently detecting your context and loading only the relevant sections you need (typically 500-1000 lines).

## Quick Start

At the start of every Claude Code session, run:

```bash
/init
```

That's it! The skill will:
- Detect your project type (Python or C++/CUDA)
- Check for active roadmaps
- Analyze your git status
- Load only relevant constraints based on what you're working on

## Features

### Automatic Project Detection

Detects whether you're working on Python or C++/CUDA projects by analyzing:
- Configuration files (requirements.txt, CMakeLists.txt, etc.)
- Source file extensions (*.py, *.cpp, *.cu)
- Project structure

### Smart Constraint Loading

Loads constraints based on:
- **Project type**: Python vs C++/CUDA specific constraints
- **Modified files**: Only loads constraints for file types you're actually working on
- **Git context**: Warns about protected branches, analyzes changes
- **Active roadmaps**: Loads roadmap discipline if roadmap is active

### Context-Aware Analysis

The skill analyzes:
- Current git branch (warns if on protected branch)
- Modified files (determines which constraints are needed)
- Active roadmaps (loads roadmap awareness if needed)
- Project structure (detects project type)

## Installation

The skill is included in the repository template. When you copy the template to a new project:

```bash
# The skill is already included in .claude/skills/init/
# No additional installation needed
```

## Usage

### Basic Usage

```bash
/init
```

### Verbose Mode (for debugging)

```bash
python3 .claude/skills/init/scripts/init.py --verbose
```

## Constraint Files

Constraints are organized by topic in `.claude/constraints/`:

### Python Constraints
- `python/testing.md` - pytest, coverage, test organization
- `python/formatting.md` - black, ruff, PEP 8, naming conventions
- `python/type-checking.md` - Type hints, mypy configuration
- `python/dependencies.md` - pip, poetry, requirements.txt
- `python/documentation.md` - Docstrings, README, API docs
- `python/error-handling.md` - Exception handling, context managers
- `python/security.md` - Input validation, secrets management
- `python/forbidden-practices.md` - Absolutely forbidden practices (always loaded)

### C++/CUDA Constraints
- `cpp/testing.md` - Google Test, Catch2, coverage
- `cpp/formatting.md` - clang-format, naming conventions
- `cpp/cmake.md` - CMake best practices, CUDA support
- `cpp/cuda.md` - CUDA memory management, kernels, error checking
- `cpp/memory-safety.md` - RAII, smart pointers, ownership
- `cpp/static-analysis.md` - clang-tidy, cppcheck
- `cpp/documentation.md` - Doxygen, comments, README
- `cpp/forbidden-practices.md` - Absolutely forbidden practices (always loaded)

### Common Constraints
- `common/git-workflow.md` - Branch policy, commit conventions
- `common/mcp-integration.md` - Context7 MCP for external documentation
- `common/roadmap-awareness.md` - Roadmap execution discipline
- `common/session-discipline.md` - Session continuity, decision hygiene

## How It Works

1. **Project Detection**: Scans for project indicators (requirements.txt, CMakeLists.txt, etc.)
2. **Git Analysis**: Checks current branch and modified files
3. **Roadmap Check**: Looks for active roadmaps using `/roadmap` skill
4. **Context Analysis**: Determines which constraints are needed based on modified files
5. **Constraint Loading**: Loads and displays relevant constraint files
6. **Guidance**: Provides next steps for the session

## Example Session

```bash
$ /init

======================================================================
SESSION INITIALIZATION
======================================================================

[OK] Project type: PYTHON
[OK] Active roadmap detected
[OK] Current branch: feature/add-authentication
[OK] Found 3 modified file(s)

======================================================================
LOADED CONSTRAINTS
======================================================================

[CONSTRAINT] common/git-workflow
   # Git Workflow Constraints

[CONSTRAINT] common/roadmap-awareness
   # Roadmap Awareness and Execution Discipline

[CONSTRAINT] python/formatting
   # Python Code Style and Formatting Constraints

[CONSTRAINT] python/type-checking
   # Python Type Hints and Static Type Checking Constraints

[CONSTRAINT] python/testing
   # Python Testing Requirements

======================================================================
Total constraints loaded: 5
======================================================================

NEXT STEPS:
1. Review the loaded constraints above
2. If working on a roadmap, read roadmap files in authority order
3. Proceed with your work following the loaded constraints
```

## Integration with Other Skills

### `/roadmap` Skill
- `/init` checks for active roadmaps
- Loads `common/roadmap-awareness.md` if roadmap is active
- Reminds you to read roadmap files in authority order

### `/pre-commit` Skill
- Use `/pre-commit` before committing to validate against loaded constraints
- Ensures code meets formatting, linting, type checking, and testing requirements

### `/dependency` Skill
- When you add dependencies with `/dependency`, next `/init` will load dependency constraints
- Ensures you follow proper dependency management practices

## Benefits

### Reduced Context Usage
- Load only 500-1000 lines instead of 2000+ lines
- Faster session starts
- More efficient use of context window

### Intelligent and Dynamic
- Adapts to your current work
- No manual decision about which constraints to load
- Always loads what you need, nothing you don't

### Prevents Omissions
- Mandatory at session start
- Ensures constraints are never forgotten
- Consistent enforcement across sessions

### Clear Visibility
- See exactly which constraints are active
- Understand what rules apply to your current work
- Easy reference during development

## Troubleshooting

### Skill Not Found

If `/init` is not recognized:
1. Ensure `.claude/skills/init/` directory exists
2. Check that `skill.md` is present
3. Restart Claude Code

### Project Type Not Detected

The skill defaults to Python if detection fails. You can:
- Add project indicators (requirements.txt for Python, CMakeLists.txt for C++)
- Manually read constraint files from `.claude/constraints/`

### Roadmap Check Fails

If roadmap checking fails:
- Ensure `/roadmap` skill is installed
- Check that `.claude/skills/roadmap/scripts/check.py` exists
- This is optional - `/init` will continue without it

### Git Commands Fail

If not in a git repository:
- Some features (branch checking, file analysis) will be skipped
- The skill will still work for project detection and basic constraint loading

## Relationship to Main Documentation

The `/init` skill extracts and loads sections from:
- `CLAUDE.md`
- `CONTRIBUTING.md`

The main documentation files remain as comprehensive references. The `/init` skill provides on-demand, context-aware loading.

## Version History

- **1.0.0** (2026-01-28): Initial release
  - Automatic project type detection (Python/C++/CUDA)
  - Smart constraint loading based on context
  - Git status analysis and protected branch warnings
  - Active roadmap detection
  - Verbose mode for debugging
  - Integration with `/roadmap`, `/pre-commit`, `/dependency` skills

## Contributing

To improve the `/init` skill:
1. Modify `.claude/skills/init/scripts/init.py` for detection logic
2. Update `.claude/skills/init/skill.md` for documentation
3. Add new constraint files to `.claude/constraints/` as needed
4. Test with both Python and C++/CUDA projects

## License

This skill is part of the repository template and follows the same license (CC BY-NC-SA 4.0).
