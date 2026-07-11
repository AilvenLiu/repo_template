# Repository Template

A repository template for Python, C++/CUDA, and hybrid AI-infra projects with
vendor-neutral AI agent constraints and development standards. Copy it, pick a
project profile, and get a working repo with `CLAUDE.md`, `AGENTS.md`, and full
skill support across Claude Code and Codex-style `agents.md` consumers.

## Overview

See [Agent instruction compatibility](docs/agent-instruction-compatibility.md)
for the cross-platform hierarchy model, validation procedure, and migration
guidance for previously generated repositories.

Language-specific source files live under `templates/<language>/` with their
generic names (`CLAUDE.md`, `AGENTS.md`, `CONTRIBUTING.md`, `.gitignore`,
`project.yml`). The `/create-project` skill copies the shared template tree
(`.ai/`, `.claude/`, `agent_roadmaps/`) and overlays the chosen
language's directory onto the target. The copied `agent_roadmaps/` directory is
an empty placeholder for temporary roadmap state only; generated projects must
not inherit historical roadmap files.

The recommended way to create a project is `/create-project` (see below).

## Quick Start

```bash
# From a Claude Code session inside this template repo:
/create-project /path/to/new/project

# Or manually:
python3 .claude/skills/create-project/scripts/init.py /path/to/new/project
```

The script prompts for project type (Python, C++/CUDA, or hybrid
Python/C++/CUDA), copies the template, overlays the correct
`templates/<language>/` files, removes template-only artifacts, and creates an
initial git commit.

## Contents

### Template-Level Files (this repo only, not copied to generated projects)

- `AGENTS.md` -- describes the architecture for humans browsing the template
- `CLAUDE.md` -- explains the template structure and points at `templates/`
- `README.md` -- this file

### Language-Specific Overlays

```
templates/
  python/
    AGENTS.md         -> AGENTS.md in generated Python projects
    CLAUDE.md         -> CLAUDE.md
    CONTRIBUTING.md   -> CONTRIBUTING.md
    .gitignore        -> .gitignore
    project.yml       -> .ai/project.yml
    poetry.toml       -> poetry.toml (in-project venv config)
    POETRY_README.md  -> (template-level note about poetry.toml; not copied)
  cpp/
    AGENTS.md         -> AGENTS.md in generated C++ projects
    CLAUDE.md         -> CLAUDE.md
    CONTRIBUTING.md   -> CONTRIBUTING.md
    .gitignore        -> .gitignore
    project.yml       -> .ai/project.yml
  hybrid/
    AGENTS.md         -> AGENTS.md in generated hybrid projects
    CLAUDE.md         -> CLAUDE.md
    CONTRIBUTING.md   -> CONTRIBUTING.md
    .gitignore        -> .gitignore
    project.yml       -> .ai/project.yml
```

### Shared Infrastructure (copied verbatim into generated projects)

- `.ai/project.yml` -- machine-readable project type (source of truth, set
  by `/create-project` from `templates/<language>/project.yml`)
- `.ai/constraints/` -- vendor-neutral constraint files (common, python, cpp, hybrid)
- `.ai/skills/` -- vendor-neutral skill procedure manifests (`<name>/SKILL.md`)
- `.ai/scripts/` -- shared runtime tools used by `.ai/bin/agent-*` wrappers
- `.ai/bin/` -- platform-neutral guarded workflow commands (`agent-*`)
- `.claude/` -- Claude Code skill stubs, hooks, and settings (native loader)
- `agent_roadmaps/` -- temporary multi-session workflow workspace

### Claude Code Skills

| Skill | Purpose |
|-------|---------|
| `/karpathy-guidelines` | Behavioural guardrails for non-trivial coding, review, debugging, and refactors |
| `/init` | Session initialisation (mandatory at session start) |
| `/create-project` | Bootstrap a new project from this template |
| `/pre-commit` | Code quality validation before commits |
| `/dependency` | Add dependencies (Poetry for Python, CPM through CMake for C++) |
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
- `.ai/skills/` -- vendor-neutral skill procedure manifests
- `.ai/scripts/` -- shared init/audit/policy enforcement core used by adapters

`CLAUDE.md` and `AGENTS.md` are the only first-class entrypoints; everything
else routes through them.

## Vendor-Neutral Support

This template is designed to work with multiple AI agent platforms:

- **Claude Code**: Reads `CLAUDE.md` natively. Slash commands (`/init`, etc.)
  are auto-discovered from `.claude/skills/<name>/SKILL.md` (each is a
  frontmatter+pointer stub) and dispatch to `.ai/bin/agent-*` wrappers.
- **Codex / Cursor / Cline / generic agents.md consumers**: Read `AGENTS.md`
  natively. The `Procedures and Wrappers` table in `AGENTS.md` lists every
  `.ai/bin/agent-*` wrapper, with the canonical procedure descriptions in
  `.ai/skills/<name>/SKILL.md`.

Both platforms inherit the bundled `karpathy-guidelines` behaviour and shared
closure discipline:
- via the matching skill manifest under `.ai/skills/karpathy-guidelines/`
  (with a Claude stub at `.claude/skills/karpathy-guidelines/`)
- via `.ai/constraints/common/karpathy-guidelines.md`, which `init` loads
  automatically into the active session
- via `.ai/constraints/common/closure-discipline.md`, which requires rigorous
  review, strongest relevant validation, and explicit residual-risk reporting
  before session, task, commit, or roadmap phase closure

Capability audit requirements are filtered by the generated project's
language, so copied C++ repos do not require Python-only support skills
such as `python-env-setup`, while hybrid repos correctly require both the
Python and C++/CUDA skill surface plus the hybrid constraint layer.

## License

Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International
(CC BY-NC-SA 4.0). See LICENSE for details.
