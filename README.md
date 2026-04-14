# Repository Template

A dual-language (Python / C++/CUDA) repository template with vendor-neutral
AI agent constraints and development standards. Copy it, pick a language,
and get a working repo with `CLAUDE.md`, `CODEX.md`, `AGENTS.md`, and full skill support.

## Overview

This template maintains paired, language-specific files with suffixes
(`CLAUDE_PYTHON.md` / `CLAUDE_CPP.md`, `CODEX_PYTHON.md` / `CODEX_CPP.md`,
`AGENTS_PYTHON.md` / `AGENTS_CPP.md`,
etc.). On copy, one variant is renamed to the generic name (`CLAUDE.md`,
`CODEX.md`, `AGENTS.md`, `CONTRIBUTING.md`, `.gitignore`) and the other is removed.

The recommended way to create a project is `/create-project` (see below).

## Quick Start

```bash
# From a Claude Code session inside this template repo:
/create-project /path/to/new/project

# Or manually:
python3 .claude/skills/create-project/scripts/init.py /path/to/new/project
```

The script prompts for project type (Python or C++), copies the template,
renames the correct variant files, writes `.ai/project.yml`, removes
template-only artifacts, and creates an initial git commit.

Existing repos can be upgraded with `scripts/migrate_codex_parity.py`, which now
also carries the shared constraints, Claude hook/settings files, and the local
`karpathy-guidelines` assets into older projects.

## Contents

### Documentation Files (Template Pairs)

#### Template-Only Files
- `AGENTS.md` -- template documentation (explains the architecture)
- `CLAUDE.md` -- template documentation (references language-specific variants)
- `CODEX.md` -- template documentation (references language-specific variants)

#### C++/CUDA Variant
- `AGENTS_CPP.md` -- vendor-neutral agent constraints (becomes `AGENTS.md`)
- `CLAUDE_CPP.md` -- self-sufficient Claude Code entrypoint (becomes `CLAUDE.md`)
- `CODEX_CPP.md` -- self-sufficient Codex entrypoint (becomes `CODEX.md`)
- `CONTRIBUTING_CPP.md` -- contribution guidelines (becomes `CONTRIBUTING.md`)
- `.gitignore_cpp` -- gitignore (becomes `.gitignore`)
- `.ai/project_cpp.yml` -- project type config (becomes `.ai/project.yml`)

#### Python Variant
- `AGENTS_PYTHON.md` -- vendor-neutral agent constraints (becomes `AGENTS.md`)
- `CLAUDE_PYTHON.md` -- self-sufficient Claude Code entrypoint (becomes `CLAUDE.md`)
- `CODEX_PYTHON.md` -- self-sufficient Codex entrypoint (becomes `CODEX.md`)
- `CONTRIBUTING_PYTHON.md` -- contribution guidelines (becomes `CONTRIBUTING.md`)
- `.gitignore_python` -- gitignore (becomes `.gitignore`)
- `.ai/project_python.yml` -- project type config (becomes `.ai/project.yml`)

### Configuration

- `.ai/project.yml` -- machine-readable project type (source of truth)
- `.ai/constraints/` -- vendor-neutral constraint files (common, python, cpp)
- `.ai/tools/` -- shared runtime enforcement tools for all agent platforms
- `.claude/` -- Claude Code skills, hooks, and settings
- `.codex/` -- Codex skill bundle
- `bin/` -- platform-neutral guarded workflow commands (`agent-*`)
- `agent_roadmaps/` -- multi-session workflow system

### Claude Code Skills

| Skill | Purpose |
|-------|---------|
| `/karpathy-guidelines` | Behavioural guardrails for non-trivial coding, review, debugging, and refactors |
| `/init` | Session initialisation (mandatory at session start) |
| `/create-project` | Bootstrap a new project from this template |
| `/pre-commit` | Code quality validation before commits |
| `/dependency` | Add dependencies (Poetry for Python, Conan for C++) |
| `/build` | Build orchestration (setup, compile, test) |
| `/roadmap` | Multi-session workflow management |
| `/navigate` | Code navigation and structural analysis |
| `/check-constraints` | Lightweight constraint compliance check |
| `/context7` | Library documentation via Context7 MCP |
| `/python-env-setup` | Diagnose/fix pyenv+Poetry environment issues |

## Architecture

In a real (non-template) repo, the key entrypoints are:

- `CLAUDE.md` -- self-sufficient Claude Code entrypoint with critical rules inline
- `CODEX.md` -- self-sufficient Codex entrypoint with critical rules inline
- `AGENTS.md` -- vendor-neutral agent constraints (works with Codex, etc.)
- `.ai/project.yml` -- deterministic project type detection
- `.ai/constraints/` -- modular constraint files loaded by init workflows
- `.ai/tools/` -- shared init/audit/policy enforcement core used by adapters

`CLAUDE.md`, `CODEX.md`, and `AGENTS.md` are all first-class entrypoints.

## Vendor-Neutral Support

This template is designed to work with multiple AI agent platforms:

- **Claude Code**: Uses `CLAUDE.md` + `/init` (delegates to `.ai/tools/session_init.py`) and discovers local skills from `.claude/skills/`
- **Codex**: Uses `CODEX.md` + `bin/agent-init --platform codex` and local skills from `.codex/skills/`
- **Other agents**: Can use either pattern depending on file discovery mechanism

Both platforms now inherit the bundled `karpathy-guidelines` behaviour in two ways:
- via local platform skills for direct or autonomous skill selection
- via `.ai/constraints/common/karpathy-guidelines.md`, which `init` loads automatically in real projects

Capability audit requirements are also filtered by the generated project's
language where appropriate, so copied C++ repos do not require Python-only
support skills such as `python-env-setup`.

Codex is now intentionally stronger in generated repos than before:
- local Codex skills include `build`, `navigate`, and `python-env-setup` for Python projects
- `bin/agent-build` provides a shared build entrypoint for both platforms
- `bin/agent-python-env-setup` exposes the environment recovery tooling through a platform-neutral wrapper

## License

Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International
(CC BY-NC-SA 4.0). See LICENSE for details.
