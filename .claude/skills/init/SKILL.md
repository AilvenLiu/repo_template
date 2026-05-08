---
name: init
description: "Session initialization — run at the start of EVERY session before any other action."
---

# /init

Session initialization. The canonical, vendor-neutral procedure body lives at
[`.ai/skills/init/SKILL.md`](../../../.ai/skills/init/SKILL.md).

## Execution

```bash
bin/agent-init --platform claude
```

## Behaviour (guaranteed)

1. Reads `.ai/project.yml` for project type; falls back to heuristic scan.
2. Runs the capability audit defined by `.ai/capabilities.yml`.
3. Prints the full text of every selected constraint so the agent ingests it.
4. Creates `.ai/session_state.json` (+ `.claude/session_state.json` mirror).

When the agent invokes this slash command, it should also open
[`.ai/skills/init/SKILL.md`](../../../.ai/skills/init/SKILL.md) for the full
guaranteed-behaviour spec and failure-mode handling.
