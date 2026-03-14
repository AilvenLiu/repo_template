---
name: init
description: "Session initialization — run at the start of EVERY session before any other action."
---

# /init

Detects project type, loads constraint bodies into the conversation,
writes `.claude/session_state.json`, and warns about protected branches
and active roadmaps.

## Behaviour (guaranteed)

1. Reads `.ai/project.yml` for project type; falls back to heuristic scan.
2. Prints the full text of every loaded constraint so the agent ingests it.
3. Creates `.claude/session_state.json` — hooks use this to gate mutations.

## Usage

```
/init
```
