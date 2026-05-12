# Create Project Skill

A Claude Code skill for initializing new projects from the repo_template.

## Overview

This skill automates the process of creating a new Python, C++/CUDA, or Hybrid (Python/C++/CUDA) project from the template, copying appropriate files and setting up the initial directory structure.

## Installation

This skill is part of the repo_template and should be used from within the template directory.

## Quick Start

### Create a New Project

```bash
python3 .claude/skills/create-project/scripts/init.py /path/to/new/project
```

The script will:
1. Prompt for project type (Python, C++/CUDA, or Hybrid)
2. Create the target directory if it doesn't exist
3. Copy appropriate template files
4. Rename language-specific files to generic names
5. Create initial directory structure
6. Initialize git repository

## What Gets Copied

### For Python Projects
- `.ai/` directory (constraints and tools)
- `.claude/` directory (all skills)
- `agent_roadmaps/` directory
- `bin/` directory (workflow wrappers)
- `poetry.toml` (Poetry configuration)
- Python-specific template overlay from `templates/python/`

### For C++/CUDA Projects
- `.ai/` directory (constraints and tools)
- `.claude/` directory (C++-relevant skills only, python-env-setup removed)
- `agent_roadmaps/` directory
- `bin/` directory (workflow wrappers, agent-python-env-setup removed)
- `CMakeLists.txt` (basic template)
- `conanfile.txt` (Conan configuration)
- C++-specific template overlay from `templates/cpp/`

### For Hybrid Projects (Phase 2)
- `.ai/` directory (constraints and tools)
- `.claude/` directory (all skills, both Python and C++ needed)
- `agent_roadmaps/` directory
- `bin/` directory (all workflow wrappers)
- `pyproject.toml` (scikit-build-core configuration)
- `CMakeLists.txt` (hybrid build template with CUDA support)
- Hybrid-specific template overlay from `templates/hybrid/`

## Directory Structure Created

### Python Projects
```
project/
|-- .ai/
|-- .claude/
|-- agent_roadmaps/
|-- bin/
|-- src/
|-- tests/
|-- CLAUDE.md
|-- AGENTS.md
|-- CONTRIBUTING.md
|-- .gitignore
|-- poetry.toml
`-- README.md
```

### C++/CUDA Projects
```
project/
|-- .ai/
|-- .claude/
|-- agent_roadmaps/
|-- bin/
|-- src/
|-- include/
|-- tests/
|-- CLAUDE.md
|-- AGENTS.md
|-- CONTRIBUTING.md
|-- .gitignore
|-- CMakeLists.txt
|-- conanfile.txt
`-- README.md
```

### Hybrid Projects
```
project/
|-- .ai/
|-- .claude/
|-- agent_roadmaps/
|-- bin/
|-- src/
|-- include/
|-- tests/
|-- CLAUDE.md
|-- AGENTS.md
|-- CONTRIBUTING.md
|-- .gitignore
|-- pyproject.toml
|-- CMakeLists.txt
`-- README.md
```

## Version

1.1.0 (2026-05-12) - Added hybrid project support

## License

This skill is part of the repo_template project and follows the same license (Creative Commons BY-NC-SA 4.0).