---
name: init
description: MANDATORY session initialization. Run at the start of EVERY session to load context, check roadmaps, verify branch, and load constraints. THIS MUST BE THE FIRST ACTION IN EVERY SESSION.
version: 1.0.0
---

# Session Initialization Skill

This skill provides intelligent, context-aware session initialization for Claude Code. It automatically detects project type, analyzes current context, and loads only the relevant constraint files needed for your current work.

## [WARNING] CRITICAL: Mandatory Session-Start Execution

**THIS IS NON-NEGOTIABLE:**

At the start of EVERY Claude Code session, before any other action, this skill MUST be invoked:

```bash
/init
```

**Skipping this initialization is a critical agent failure.**

## What This Skill Does

When invoked, the `/init` skill:

1. **Detects project type** (Python or C++/CUDA)
2. **Checks for active roadmaps** and alerts if one exists
3. **Analyzes git status** (current branch, modified files)
4. **Warns about protected branches** (master, main, develop)
5. **Intelligently loads relevant constraints** based on context
6. **Displays loaded constraints** for reference

## How It Works

### Automatic Project Detection

The skill automatically detects whether you're working on:
- **Python project**: Looks for requirements.txt, pyproject.toml, .venv, *.py files
- **C++/CUDA project**: Looks for CMakeLists.txt, conanfile.txt, *.cpp, *.cu files

### Smart Constraint Loading

Based on your current context, the skill loads only relevant constraint files:

**Always loaded (common):**
- `common/git-workflow` - Git workflow and commit conventions
- `common/session-discipline` - Session continuity and decision hygiene
- `common/mcp-integration` - MCP server integration guidelines
- `common/ascii-only` - ASCII-only code compliance

**Loaded when active roadmap detected:**
- `common/roadmap-awareness` - Roadmap execution discipline

**Always loaded (Python projects):**
- `python/dependencies` - Poetry enforcement (ALWAYS loaded to prevent system Python usage)
- `python/forbidden-practices` - Absolute prohibitions (ALWAYS loaded)
- `python/security` - Security best practices (ALWAYS loaded)
- `python/error-handling` - Exception handling patterns (ALWAYS loaded)

**Always loaded (C++/CUDA projects):**
- `cpp/dependencies` - Conan/vcpkg enforcement (ALWAYS loaded to prevent system-wide installation)
- `cpp/forbidden-practices` - Absolute prohibitions (ALWAYS loaded)
- `cpp/error-handling` - Error handling patterns (ALWAYS loaded)
- `cpp/static-analysis` - Static analysis requirements (ALWAYS loaded)

**Loaded based on modified files:**

For Python projects:
- `python/testing` - When test files are modified
- `python/formatting` - When .py files are modified
- `python/type-checking` - When .py files are modified
- `python/documentation` - When .md or doc files modified

For C++/CUDA projects:
- `cpp/testing` - When test files are modified
- `cpp/formatting` - When .cpp/.hpp files are modified
- `cpp/memory-safety` - When .cpp/.hpp files are modified
- `cpp/cuda` - When .cu/.cuh files are modified
- `cpp/cmake` - When CMakeLists.txt modified
- `cpp/documentation` - When .md or doc files modified

**Note**: Critical constraints (dependencies, forbidden-practices, security, error-handling, static-analysis) are ALWAYS loaded to ensure fundamental rules are enforced from the start of every session, even before any files are modified.

## Usage

### Basic Usage

Simply run at the start of every session:

```bash
/init
```

The skill will automatically:
- Detect your project type
- Check for active roadmaps
- Analyze your current git status
- Load relevant constraints based on context

### Verbose Mode

For debugging or detailed information:

```bash
python3 .claude/skills/init/scripts/init.py --verbose
```

## Example Output

```
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

[CONSTRAINT] common/session-discipline
   # Session Continuity and State Discipline

[CONSTRAINT] python/formatting
   # Python Code Style and Formatting Constraints

[CONSTRAINT] python/type-checking
   # Python Type Hints and Static Type Checking Constraints

======================================================================
Total constraints loaded: 5
======================================================================

NEXT STEPS:
1. Review the loaded constraints above
2. If working on a roadmap, read roadmap files in authority order
3. Proceed with your work following the loaded constraints
```

## Integration with Existing Skills

The `/init` skill complements other skills:

- **`/roadmap`**: If active roadmap detected, `/init` reminds you to load roadmap files
- **`/pre-commit`**: Use before committing to validate against loaded constraints
- **`/dependency`**: Use when adding dependencies (will trigger dependency constraints on next `/init`)

## Benefits

### Reduced Context Usage

Instead of loading 2000+ lines of constraints at session start, `/init` loads only 500-1000 lines of relevant constraints based on your current work.

### Intelligent and Dynamic

The skill analyzes your actual context (modified files, git status, roadmaps) and loads only what you need.

### Prevents Omissions

By making `/init` mandatory at session start, you ensure constraints are never forgotten or omitted.

### Clear Visibility

You see exactly which constraints are active for your current session.

## Constraint File Organization

Constraints are organized in `.claude/constraints/`:

```
.claude/constraints/
|-- python/
|   |-- testing.md
|   |-- formatting.md
|   |-- type-checking.md
|   |-- dependencies.md
|   |-- documentation.md
|   |-- error-handling.md
|   `-- security.md
|-- cpp/
|   |-- testing.md
|   |-- formatting.md
|   |-- cmake.md
|   |-- cuda.md
|   |-- memory-safety.md
|   |-- static-analysis.md
|   `-- documentation.md
`-- common/
    |-- git-workflow.md
    |-- roadmap-awareness.md
    `-- session-discipline.md
```

Each file is self-contained and focused on a single topic, making them easy to reference and understand.

## Relationship to Main Documentation

The constraint files in `.claude/constraints/` are extracted from:
- `CLAUDE.md`
- `CONTRIBUTING.md`

The main documentation files remain as comprehensive references. The `/init` skill provides on-demand, context-aware loading of relevant sections.

## Troubleshooting

### "Could not detect project type"

The skill defaults to Python if it can't detect the project type. You can manually specify constraints by reading the appropriate files from `.claude/constraints/`.

### "Roadmap check script not found"

The `/roadmap` skill is not installed. This is optional - `/init` will continue without roadmap checking.

### "Not a git repository"

The skill works best in git repositories. Some features (branch checking, modified file analysis) will be skipped if not in a git repo.

## Version History

- **1.0.0** (2026-01-28): Initial release
  - Automatic project type detection
  - Smart constraint loading based on context
  - Git status analysis
  - Active roadmap detection
  - Protected branch warnings
  - Verbose mode for debugging
