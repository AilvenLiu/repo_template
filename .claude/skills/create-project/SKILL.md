---
name: create-project
description: "Create a new project from the repo_template. Template-only skill."
---

# /create-project

Copies the template, renames language-specific files to their generic
names (`CLAUDE.md`, `CODEX.md`, `AGENTS.md`, `CONTRIBUTING.md`, `.gitignore`),
writes `.ai/project.yml`, removes template-only artifacts, and creates
an initial git commit.

## Usage

```
/create-project /path/to/new/project
```

## What it produces

```
project/
  .ai/
    project.yml          # source of truth for project type
    constraints/         # vendor-neutral constraint files
    tools/               # shared runtime enforcement tools
  .claude/               # Claude Code skills and hooks
  .codex/                # Codex skills
  bin/                   # guarded workflow command wrappers
  agent_roadmaps/
  AGENTS.md              # vendor-neutral agent constraints
  CLAUDE.md              # Claude Code entrypoint (self-sufficient)
  CODEX.md               # Codex entrypoint (self-sufficient)
  CONTRIBUTING.md
  .gitignore
  README.md
  src/  tests/           # (+ include/ for C++)
```
