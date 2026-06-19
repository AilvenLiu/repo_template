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
   - References detailed constraint files in `.ai/constraints/`

3. **Detailed constraints** (`.ai/constraints/`)
   - Modular, topic-specific constraint files
   - Loaded dynamically by session initialization
   - Common constraints + language-specific constraints

## C++/CUDA and Hybrid Build Policy Summary

Pure Python templates remain Poetry first.

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
python3 .claude/skills/create-project/scripts/init.py /path/to/new/project
```

The script will:
1. Prompt for project type (Python, C++/CUDA, or hybrid Python/C++/CUDA)
2. Copy the template structure
3. Rename language-specific files to generic names
4. Write `.ai/project.yml` with the correct project type
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
