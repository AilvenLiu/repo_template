---
name: roadmap
description: "Manage dependency-aware multi-session workflows in agent_roadmaps/."
---

# /roadmap

Structured commands for dependency-aware phase workflows.

## Commands

- `/roadmap check` — detect active phase and dependency readiness (run at session start)
- `/roadmap create <name> --phases <N> --phase-names <names...>` — create phase series with explicit dependencies
- `/roadmap status` — show cross-phase and task dependency status
- `/roadmap update complete-task` — complete current task and advance to next dependency-ready task
- `/roadmap update block-task <reason>` — mark current task blocked
- `/roadmap update unblock-task` — unblock first dependency-ready blocked task
- `/roadmap update set-focus <task-id>` — set focus to a dependency-ready task
- `/roadmap handoff` — generate session handoff file
- `/roadmap complete` — mark active phase completed

## Behaviour (guaranteed)

1. Enforces single-active-phase rule.
2. Enforces dependency-safe task progression (`depends_on`).
3. Validates dependency-aware roadmap schema.
4. Generates session handoff files under `sessions/`.

## Critical rules

- At most one phase may be active.
- Work must be on branch `roadmap/<phase-folder-name>`.
- Do not start a phase before `depends_on_phases` are completed.
- Operate only on `focus.current_task`.
- End each roadmap session with roadmap state + handoff update.
- Authority order: `INVARIANTS.md` > `ROADMAP.md` > `roadmap.yml` > `sessions/` > `prompt.md`.
