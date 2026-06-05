# .claude/constraints/

These subdirectories (`common/`, `cpp/`, `python/`) are intentionally empty.

## Where constraints actually live

All constraint bodies live in `.ai/constraints/` (vendor-neutral, platform-agnostic):

```
.ai/constraints/
  common/   — git-workflow, session-discipline, karpathy-guidelines, mcp-integration, …
  python/   — dependencies (Poetry enforcement), forbidden-practices, security, …
  cpp/      — cmake, cuda, memory-safety, static-analysis, …
  hybrid/   — ffi-boundary, python-cpp-build, system-deps
```

`session_init.py` reads those files during `/init` (or `bin/agent-init --platform codex`)
and prints their full text into the session context.  No Claude-specific constraint
variant is needed; the same constraint bodies govern both Claude Code and Codex agents.

## Why these subdirectories exist

They mirror the `.ai/constraints/` structure as a visual placeholder, making it obvious
that the parallel directory tree exists.  No code reads from `.claude/constraints/`.

## Adding Claude-specific constraint overrides (future)

If a constraint ever needs a Claude-only variant, add it here and update
`session_init.py → load_constraint()` to check `.claude/constraints/<key>.md`
before falling back to `.ai/constraints/<key>.md`.
