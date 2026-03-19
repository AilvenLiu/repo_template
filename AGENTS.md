# Agent Operating Constraints: Template Repository

## About This File

This is the **template repository**. In real projects created from this template,
this file contains vendor-neutral agent operating constraints that work across
different AI agent platforms (Claude Code, Codex, Cursor, etc.).

The template maintains language-specific variants:
- `AGENTS_PYTHON.md` — becomes `AGENTS.md` in Python projects
- `AGENTS_CPP.md` — becomes `AGENTS.md` in C++/CUDA projects

When you create a project using `/create-project`, the appropriate variant is
copied and renamed to `AGENTS.md`.

## Purpose

`AGENTS.md` serves as the vendor-neutral entrypoint for AI agents that:
1. Don't have platform-specific instruction files (like `CLAUDE.md` / `CODEX.md`)
2. Need a common reference for constraints and workflows
3. Want to understand the project's coding standards and requirements

## Architecture

The constraint system has three layers:

1. **Platform-specific entrypoints** (e.g., `CLAUDE.md`, `CODEX.md`)
   - Self-sufficient with critical rules inline
   - Maps platform-specific skills to generic procedures
   - References this file for full constraint details

2. **This file** (`AGENTS.md`)
   - Vendor-neutral operating constraints
   - Absolute prohibitions and mandatory workflows
   - References detailed constraint files in `.ai/constraints/`

3. **Detailed constraints** (`.ai/constraints/`)
   - Modular, topic-specific constraint files
   - Loaded dynamically by session initialization
   - Common constraints + language-specific constraints

## For Template Users

To create a new project from this template:

```bash
# From a Claude Code session inside this template repo:
/create-project /path/to/new/project

# Or manually:
python3 .claude/skills/create-project/scripts/init.py /path/to/new/project
```

The script will:
1. Prompt for project type (Python or C++/CUDA)
2. Copy the template structure
3. Rename language-specific files to generic names
4. Write `.ai/project.yml` with the correct project type
5. Remove template-only artifacts
6. Create an initial git commit

## For Real Projects

If you're reading this in a real project (not the template), see the sections
below for your project's specific constraints. The content will be either from
`AGENTS_PYTHON.md` or `AGENTS_CPP.md` depending on your project type.

---

**Note**: The sections below this line are template-only documentation. In real
projects, this file contains the actual operating constraints for that project.
