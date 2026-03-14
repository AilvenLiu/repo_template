---
name: navigate
description: "Navigate and analyse code structure. Find definitions, trace dependencies, analyse call graphs."
---

# /navigate

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
- C++ analysis quality depends on compile_commands.json availability.
- Large codebases may take longer to analyse.
