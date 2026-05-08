---
name: roadmap
description: "Manage dependency-aware multi-session workflows in agent_roadmaps/."
---

# /roadmap

Dependency-aware multi-session workflow management. The canonical,
vendor-neutral procedure body lives at
[`.ai/skills/roadmap/SKILL.md`](../../../.ai/skills/roadmap/SKILL.md).

## Execution

```bash
bin/agent-roadmap <subcommand> [args...]
```

## Critical rules

- At most one phase may be active.
- Work must be on branch `roadmap/<phase-folder-name>`.
- Do not start a phase before `depends_on_phases` are completed.
- Operate only on `focus.current_task`.
- End each roadmap session with roadmap state + handoff update.
- Authority order:
  `INVARIANTS.md` > `ROADMAP.md` > `roadmap.yml` > `sessions/` > `prompt.md`.

When this slash command is invoked, also read
[`.ai/skills/roadmap/SKILL.md`](../../../.ai/skills/roadmap/SKILL.md) for the
full subcommand list and behavioural spec.
