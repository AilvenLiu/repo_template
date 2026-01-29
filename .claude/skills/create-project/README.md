# Create Project Skill

A Claude Code skill for initializing new projects from the repo_template.

## Overview

This skill automates the process of creating a new Python or C++/CUDA project from the template, copying appropriate files and setting up the initial directory structure.

## Installation

This skill is part of the repo_template and should be used from within the template directory.

## Quick Start

### Create a New Project

```bash
python3 .claude/skills/create-project/scripts/init.py /path/to/new/project
```

The script will:
1. Prompt for project type (Python or C++/CUDA)
2. Create the target directory if it doesn't exist
3. Copy appropriate template files
4. Rename language-specific files to generic names
5. Create initial directory structure
6. Initialize git repository

## What Gets Copied

### For Python Projects
- `.claude/` directory (all skills and constraints)
- `agent_roadmaps/` directory
- `requirements.txt` (empty template)

### For C++/CUDA Projects
- `.claude/` directory (all skills and constraints)
- `agent_roadmaps/` directory
- `CMakeLists.txt` (basic template)

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

## Version

1.0.0 (2026-01-29)

## License

This skill is part of the repo_template project and follows the same license (Creative Commons BY-NC-SA 4.0).