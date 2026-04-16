---
name: init
description: "Session initialization — run at the start of EVERY session before any other action."
---

# /init

Detects project type, loads constraint bodies into the conversation,
writes `.ai/session_state.json` (and `.claude/session_state.json` for compatibility),
and warns about protected branches
and active roadmaps.

## Execution

Run:

```bash
bin/agent-init --platform claude
```

## Behaviour (guaranteed)

1. Reads `.ai/project.yml` for project type; falls back to heuristic scan.
2. Prints the full text of every selected constraint so the agent ingests it.
3. Creates `.ai/session_state.json` + `.claude/session_state.json` — hooks and wrappers use this to gate mutations.
