# navigate — code navigation and structural analysis

> Vendor-neutral procedure description. Claude Code dispatches `/navigate`
> to this body via the stub at `.claude/skills/navigate/SKILL.md`. Codex /
> Cursor / Cline read this file directly via the AGENTS.md procedures table
> or use their own native navigation tools (ripgrep, ctags, LSP, etc.).

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
is informational; the actual navigation has no `.ai/bin/agent-*` wrapper because
all sane agent platforms ship with their own search/grep capabilities.
