# Repository Template

A dual-language (Python / C++/CUDA) repository template with vendor-neutral
AI agent constraints and development standards. Copy it, pick a language,
and get a working repo with `CLAUDE.md`, `AGENTS.md`, and full skill support.

## Overview

This template maintains paired, language-specific files with suffixes
(`CLAUDE_PYTHON.md` / `CLAUDE_CPP.md`, `AGENTS_PYTHON.md` / `AGENTS_CPP.md`,
`CONTRIBUTING_PYTHON.md` / `CONTRIBUTING_CPP.md`, etc.). On copy, one variant
is renamed to the generic name (`CLAUDE.md`, `AGENTS.md`, `CONTRIBUTING.md`,
`.gitignore`) and the other is removed.

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

## Contents

### Documentation Files (Template Pairs)

#### Template-Only Files
- `AGENTS.md` -- template documentation (explains the architecture)
- `CLAUDE.md` -- template documentation (references language-specific variants)

#### C++/CUDA Variant
- `AGENTS_CPP.md` -- vendor-neutral agent constraints (becomes `AGENTS.md`)
- `CLAUDE_CPP.md` -- self-sufficient Claude Code entrypoint (becomes `CLAUDE.md`)
- `CONTRIBUTING_CPP.md` -- contribution guidelines (becomes `CONTRIBUTING.md`)
- `.gitignore_cpp` -- gitignore (becomes `.gitignore`)
- `.ai/project_cpp.yml` -- project type config (becomes `.ai/project.yml`)

#### Python Variant
- `AGENTS_PYTHON.md` -- vendor-neutral agent constraints (becomes `AGENTS.md`)
- `CLAUDE_PYTHON.md` -- self-sufficient Claude Code entrypoint (becomes `CLAUDE.md`)
- `CONTRIBUTING_PYTHON.md` -- contribution guidelines (becomes `CONTRIBUTING.md`)
- `.gitignore_python` -- gitignore (becomes `.gitignore`)
- `.ai/project_python.yml` -- project type config (becomes `.ai/project.yml`)

### Configuration

- `.ai/project.yml` -- machine-readable project type (source of truth)
- `.ai/constraints/` -- vendor-neutral constraint files (common, python, cpp)
- `.ai/tools/` -- shared runtime enforcement tools for all agent platforms
- `.claude/` -- Claude Code skills, hooks, and settings (native loader)
- `.codex/` -- Codex skill manifests (read on demand from `AGENTS.md`)
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
| `/roadmap` | Dependency-aware multi-session workflow management |
| `/navigate` | Code navigation and structural analysis |
| `/check-constraints` | Lightweight constraint compliance check |
| `/context7` | Library documentation via Context7 MCP |
| `/python-env-setup` | Diagnose/fix pyenv+Poetry environment issues |

## Architecture

In a real (non-template) repo, the key entrypoints are:

- `CLAUDE.md` -- self-sufficient Claude Code entrypoint with critical rules inline
- `AGENTS.md` -- vendor-neutral agent operating constraints, loaded automatically
  by Codex CLI / Cursor / Cline / other [agents.md](https://agents.md)-aware tools
- `.ai/project.yml` -- deterministic project type detection
- `.ai/constraints/` -- modular constraint files loaded by init workflows
- `.ai/tools/` -- shared init/audit/policy enforcement core used by adapters

`CLAUDE.md` and `AGENTS.md` are the only first-class entrypoints; everything
else routes through them.

## Vendor-Neutral Support

This template is designed to work with multiple AI agent platforms:

- **Claude Code**: Reads `CLAUDE.md` natively. Slash commands (`/init`, etc.)
  are auto-discovered from `.claude/skills/<name>/SKILL.md` and dispatch to
  `bin/agent-*` wrappers under the hood.
- **Codex / Cursor / Cline / generic agents.md consumers**: Read `AGENTS.md`
  natively. The `Procedures and Wrappers` table in `AGENTS.md` lists every
  `bin/agent-*` wrapper. Codex-side procedure manifests live under
  `.codex/skills/<name>/SKILL.md` and are read on demand.

Both platforms inherit the bundled `karpathy-guidelines` behaviour:
- via the matching skill manifest under `.claude/skills/` and `.codex/skills/`
- via `.ai/constraints/common/karpathy-guidelines.md`, which `init` loads
  automatically into the active session

Capability audit requirements are filtered by the generated project's
language, so copied C++ repos do not require Python-only support skills
such as `python-env-setup`.

## License

Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International
(CC BY-NC-SA 4.0). See LICENSE for details.
