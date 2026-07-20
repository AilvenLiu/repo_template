---
name: navigate
description: Locate symbols, references, dependencies, inheritance, and call relationships in Python or C++ repositories. Use for codebase orientation, impact analysis, dependency tracing, or finding the smallest safe edit surface.
---

# navigate — code navigation and structural analysis

> Canonical repository skill. Codex discovers it natively from `.agents/skills/`;
> Claude Code reaches it through the matching `.claude/skills/` delegate.

Code navigation and structural analysis for Python and C++ projects.

## Commands

- `/navigate find <symbol>` — locate definition
- `/navigate uses <symbol>` — find all references
- `/navigate deps <file>` — show file dependencies
- `/navigate arch` — analyse repository architecture
- `/navigate calls <function>` — show call graph

## Behaviour (guaranteed)

- Python: AST-based analysis for definitions, imports, and call graphs.
- C++: regex + clang-based tools for symbol lookup.
- Returns file path, line number, and context for each result.

## Behaviour (best-effort)

- Dynamic imports and metaprogramming may be missed.
- C++ analysis quality depends on `compile_commands.json` availability.
- Large codebases may take longer to analyse.

## For agents without a native navigate skill

Use `rg` (ripgrep) and your platform's native code-search tools. The procedure
is informational; the actual navigation has no `.agents/bin/agent-*` wrapper because
all sane agent platforms ship with their own search/grep capabilities.
