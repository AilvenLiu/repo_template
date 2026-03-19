---
name: context7
description: Retrieve up-to-date library docs through Context7 tools during Codex sessions.
---

# Codex Context7

Use Context7 before coding with external libraries.

## Invocation Steps

1. Resolve the library ID with `mcp__context7__resolve_library_id`.
   Example payload: `{"libraryName":"numpy","query":"array broadcasting rules"}`
2. Query docs with `mcp__context7__query_docs` using the returned library ID.
   Example payload: `{"libraryId":"/numpy/numpy","query":"broadcasting examples"}`
3. Use returned signatures/examples to drive implementation and cite the API source.

## Fallback

If Context7 is unavailable, report it and stop external-library-dependent work.
Do not silently guess API signatures.
