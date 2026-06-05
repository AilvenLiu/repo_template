---
name: navigate
description: "Navigate and analyse code structure. Find definitions, trace dependencies, analyse call graphs."
---

# /navigate

Code navigation and structural analysis for Python and C++/CUDA projects.

## Commands

| Command | What it does |
|---------|--------------|
| `/navigate find <symbol>` | Locate the definition of a symbol |
| `/navigate uses <symbol>` | Find all references to a symbol |
| `/navigate deps <file>` | Show all imports / includes for a file |
| `/navigate arch` | Analyse repository architecture (modules, layers) |
| `/navigate calls <function>` | Show the call graph for a function |

## Behaviour (guaranteed)

- **Python**: AST-based analysis for definitions, imports, and call graphs.
- **C++**: regex + clang-based tools for symbol lookup.
- Returns file path, line number, and surrounding context for each result.

## Behaviour (best-effort)

- Dynamic imports and metaprogramming may not be resolved.
- C++ analysis quality depends on `compile_commands.json` availability.
- Large codebases may take longer to analyse.

## Note on Claude Code

Claude Code ships with native search tools (`Grep`, `Glob`, `Bash(rg:*)`) that
can serve most navigation needs directly. Use `/navigate` when you need
structured analysis (call graphs, dependency trees) beyond simple text search.
