# Agent Operating Constraints: Template Repository

## About This File

This is the **template repository**. In real projects created from this template,
this file contains vendor-neutral agent operating constraints that work across
different AI agent platforms (Claude Code, Codex, Cursor, etc.).

The template maintains language-specific overlays under `templates/`:
- `templates/python/AGENTS.md` — becomes `AGENTS.md` in Python projects
- `templates/cpp/AGENTS.md` — becomes `AGENTS.md` in C++/CUDA projects
- `templates/hybrid/AGENTS.md` — becomes `AGENTS.md` in hybrid Python/C++/CUDA projects

When you create a project using `/create-project`, the appropriate overlay
is copied to the project root with the generic name `AGENTS.md`.

## Purpose

`AGENTS.md` is the canonical entrypoint defined by the
[agents.md spec](https://agents.md). It is loaded automatically by Codex CLI,
Cursor, Cline, and other agents.md-aware tools. Claude Code reads `CLAUDE.md`
natively and falls back to `AGENTS.md` for vendor-neutral content.

## Architecture

The constraint system has three layers:

1. **Platform-specific entrypoints**
   - `CLAUDE.md` — Claude Code (native loader)
   - `AGENTS.md` — Codex / Cursor / Cline / generic agents.md consumers (native loader)
   - Self-sufficient with critical rules inline
   - References this file for full constraint details

2. **This file** (`AGENTS.md`)
   - Vendor-neutral operating constraints
   - Absolute prohibitions and mandatory workflows
   - References detailed constraint files in `.agents/constraints/`

3. **Detailed constraints** (`.agents/constraints/`)
   - Modular, topic-specific constraint files
   - Loaded dynamically by session initialization
   - Common constraints + language-specific constraints

## Mandatory Cross-Agent Contract

Agents must treat repository constraints as mandatory, not advisory. Before any
edit, every agent must:

1. Read the native entrypoint for its platform (`AGENTS.md`, and `CLAUDE.md`
   for Claude Code).
2. Read `.agents/project.yml` and determine the active project type/profile.
3. Read `.agents/capabilities.yml` and verify required skills/wrappers exist.
4. Run the platform's session initialisation procedure to obtain its
   deterministic constraint manifest.
5. Read the listed common constraints and the constraints applicable to the
   intended files from the project-type family below.
6. Read the relevant skill body under `.agents/skills/<skill>/SKILL.md` before
   following that workflow. Platform-specific skill files are wrappers.

## Platform and Tool Requirements

Repository guidance applies subject to higher-priority platform safety,
developer, managed organisational, and tool-enforced requirements. It cannot
grant permissions outside the active sandbox or user authorisation. If such a
requirement conflicts with repository policy, follow it, minimise the
deviation, and report the conflict rather than silently bypassing policy.

## Repository-Local Precedence

Within repository-controlled guidance, precedence is:

1. Active roadmap `INVARIANTS.md`, if present
2. Active roadmap `roadmap.yml` for current execution state
3. Active roadmap `ROADMAP.md` for phase scope and intent
4. Applicable `.agents/constraints/` files
5. The relevant platform entrypoint (`AGENTS.md` or `CLAUDE.md`)
6. `CONTRIBUTING.md` and other durable documentation
7. Session handoffs, `prompt.md`, and temporary notes

This local order does not supersede platform or tool requirements. Session
records and conversational assumptions cannot alter current repository state.
When two repository rules at the same level conflict, prefer the stricter rule;
if that does not resolve the issue, stop, explain the conflict, and ask for an
approved exception or ADR path.

### Project Type to Constraint Family

Prefer `project_profile` in `.agents/project.yml`; use legacy `project_type` only
when `project_profile` is absent.

| Project metadata | Required constraint families | Primary build authority |
|------------------|------------------------------|-------------------------|
| `project_type: python` or `language: [python]` | `.agents/constraints/common/`, `.agents/constraints/python/` | Poetry for Python environment and dependencies |
| `project_type: cpp` or `language: [cpp]` | `.agents/constraints/common/`, `.agents/constraints/cpp/` | CMake for native build graph; CPM for lightweight C++ deps |
| `language` includes both `python` and `cpp` | `.agents/constraints/common/`, `.agents/constraints/python/`, `.agents/constraints/cpp/`, `.agents/constraints/hybrid/` | CMake for native build graph; scikit-build-core only bridges packaging |

Before final response after edits, run the relevant validation command, or state
why it could not be run:

```bash
.agents/bin/agent-check-constraints
```

## C++/CUDA and Hybrid Build Policy Summary

Pure Python templates remain Poetry first.

For C++/CUDA and hybrid templates, the project is C++ First:
- C++/CUDA owns core libraries, runtime kernels, native executables, C++ tests,
  CUDA tests, benchmarks, compile options, link options, third-party C++
  dependencies, ABI-sensitive configuration, and installation/export targets.
- Python owns only thin bindings, wrapper APIs, Python packaging metadata,
  Python-side tests, wheel exposure, and developer environment management.
- Python packaging must not define or replace the native build graph, compiler
  configuration, CUDA architecture policy, ABI policy, dependency discovery,
  benchmark topology, native test topology, or installation/export semantics.

Pure C++/CUDA templates are CMake first and CPM first:
- CMake owns the native build graph.
- CPM owns lightweight C++ dependency acquisition.
- Direct native validation is `cmake -S . -B build -G Ninja -DCMAKE_BUILD_TYPE=RelWithDebInfo`, `cmake --build build -j`, then `ctest --test-dir build --output-on-failure`.

C++/Python hybrid templates are CMake first, CPM first, scikit-build-core bridge:
- CMake owns native targets, compile/link options, tests, benchmarks, install/export targets, and ABI-sensitive configuration.
- scikit-build-core bridges CMake into Python packaging only.
- Poetry owns Python virtualenv and Python dependencies only.
- `pip install -e .` is not the authoritative C++ build command; use `poetry run pip install -e . --no-build-isolation` only after direct CMake validation passes.

Conan, vcpkg, Bazel, and git submodules are exceptional choices for these templates and require an ADR.

## For Template Users

To create a new project from this template:

```bash
# From a Claude Code session inside this template repo:
/create-project /path/to/new/project

# Or manually:
python3 .agents/skills/create-project/scripts/init.py /path/to/new/project
```

The script will:
1. Prompt for project type (Python, C++/CUDA, or hybrid Python/C++/CUDA)
2. Copy the template structure
3. Rename language-specific files to generic names
4. Write `.agents/project.yml` with the correct project type
5. Remove template-only artifacts
6. Create an initial git commit

## For Real Projects

If you're reading this in a real project (not the template), see the sections
below for your project's specific constraints. The content will have been
copied from `templates/python/AGENTS.md`, `templates/cpp/AGENTS.md`, or
`templates/hybrid/AGENTS.md` depending on your project type.

---

**Note**: The sections below this line are template-only documentation. In real
projects, this file contains the actual operating constraints for that project.
