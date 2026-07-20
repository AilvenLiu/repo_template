---
name: init
description: Initialize an agent session, resolve the project profile, audit required capabilities, and emit the deterministic constraint manifest. Use at the start of repository work or whenever profile, branch, roadmap, or capability state changes.
---

# init — session initialization

> Canonical repository skill. Codex discovers it natively from `.agents/skills/`;
> Claude Code reaches it through the matching `.claude/skills/` delegate.

Detects project type, produces a bounded manifest of applicable constraint
paths, writes `.agents/session_state.json` (and `.claude/session_state.json` for
compatibility), and warns about protected branches and active roadmaps.

## Execution

```bash
# Claude Code
.agents/bin/agent-init --platform claude

# Codex / Cursor / Cline / generic agents
.agents/bin/agent-init --platform codex
```

## Behaviour (guaranteed)

1. Reads `.agents/project.yml` for project type; falls back to heuristic scan.
2. Runs the capability audit defined by `.agents/capabilities.yml`.
3. Prints a deterministic, profile-aware manifest of selected constraints.
   Read the listed files before work to which they apply; this keeps initial
   context bounded and makes the source of each rule inspectable.
4. Creates `.agents/session_state.json` (+ `.claude/session_state.json` mirror) —
   hooks and wrappers use this file to gate mutations.

## Failure mode

If the capability audit fails, the wrapper exits non-zero. The session is
considered blocked for mutating operations until the failure is resolved
and `.agents/bin/agent-init` is re-run.

## Detailed reference

Read [references/guide.md](references/guide.md) when troubleshooting session
initialization or constraint selection.
