---
name: create-project
description: "Create a new project from the repo_template. Supports Python, C++/CUDA, and Hybrid projects. Template-only skill."
---

# /create-project

Copies the template, renames language-specific files to their generic
names (`CLAUDE.md`, `AGENTS.md`, `CONTRIBUTING.md`, `.gitignore`),
writes `.agents/project.yml`, removes template-only artifacts, and creates
an initial git commit.

## Usage

```
/create-project /path/to/new/project
```

The script will prompt for project type:
1. Python (Poetry-based)
2. C++/CUDA (CMake-based)
3. Hybrid (Python/C++/CUDA with scikit-build-core)

## What it produces

```
project/
  .agents/
    project.yml          # source of truth for project profile
    constraints/         # vendor-neutral constraint files
    scripts/             # shared runtime enforcement tools
    bin/                 # guarded workflow command wrappers
  .claude/               # Claude Code skills and hooks
  agent_roadmaps/
  AGENTS.md              # vendor-neutral agent constraints (Codex / agents.md spec)
  CLAUDE.md              # Claude Code entrypoint (self-sufficient)
  CONTRIBUTING.md
  .gitignore
  README.md
  src/  tests/           # Python projects
  cmake/  3rdparty/      # C++/CUDA and hybrid projects
  cpp/  cuda/            # C++/CUDA and hybrid projects
```

## Execution

```bash
python3 .agents/skills/create-project/scripts/init.py <target-directory>
```

Read [references/guide.md](references/guide.md) when you need the generated
layout details or post-generation checklist.
