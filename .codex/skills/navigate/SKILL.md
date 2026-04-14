---
name: navigate
description: Navigate and analyse repository structure in Codex sessions. Use when locating symbols, tracing references, or summarising architecture before editing.
---

# Codex Navigate

Use fast repo-native search first.

## Workflow

1. List candidate files with `rg --files`.
2. Locate definitions and usages with `rg -n "<pattern>"`.
3. Follow imports or includes outward from the entrypoint you found.
4. Summarise the relevant slice of architecture before making non-trivial edits.

## Notes

- Prefer `rg` over slower grep-style scans.
- For large changes, pair this with `karpathy-guidelines` so exploration stays targeted.
