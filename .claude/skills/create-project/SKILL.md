---
name: create-project
description: Initialize new projects from the repo_template. Use when creating a new Python or C++/CUDA project. This skill is only available in the template repository itself, not in projects created from it.
version: 1.0.0
---

# Create Project Skill

This skill automates the process of creating a new Python or C++/CUDA project from the repo_template.

## When to Use

Use this skill when:
- Creating a new project from the template
- Setting up a fresh Python or C++/CUDA repository
- Bootstrapping development environment

**Note**: This skill is only available in the template repository. It will not be copied to new projects.

## What It Does

1. Prompts for project type (Python or C++/CUDA)
2. Creates target directory
3. Copies appropriate template files
4. Renames language-specific files
5. Creates initial directory structure
6. Initializes git repository

## Usage

```bash
/create-project /path/to/new/project
```

Or directly:

```bash
python3 .claude/skills/create-project/scripts/init.py /path/to/new/project
```

## What Gets Copied

### For Python Projects
- `.claude/` directory (all skills and constraints)
- `agent_roadmaps/` directory
- `CLAUDE_PYTHON.md` -> `CLAUDE.md`
- `CONTRIBUTING_PYTHON.md` -> `CONTRIBUTING.md`
- `.gitignore_python` -> `.gitignore`
- `LICENSE`

### For C++/CUDA Projects
- `.claude/` directory (all skills and constraints)
- `agent_roadmaps/` directory
- `CLAUDE_CPP.md` -> `CLAUDE.md`
- `CONTRIBUTING_CPP.md` -> `CONTRIBUTING.md`
- `.gitignore_cpp` -> `.gitignore`
- `LICENSE`

## Directory Structure Created

### Python Projects
```
project/
|-- .claude/
|-- agent_roadmaps/
|-- src/
|-- tests/
|-- CLAUDE.md
|-- CONTRIBUTING.md
|-- .gitignore
|-- requirements.txt
`-- README.md
```

### C++/CUDA Projects
```
project/
|-- .claude/
|-- agent_roadmaps/
|-- src/
|-- include/
|-- tests/
|-- CLAUDE.md
|-- CONTRIBUTING.md
|-- .gitignore
|-- CMakeLists.txt
`-- README.md
```

## After Creation

Once the project is created, navigate to it and run:

```bash
cd /path/to/new/project
/init
```

This will:
- Detect project type
- Load relevant constraints
- Set up development environment

## Version History

- **1.0.0** (2026-01-29): Initial release
  - Python project creation
  - C++/CUDA project creation
  - Automatic file renaming
  - Git initialization
