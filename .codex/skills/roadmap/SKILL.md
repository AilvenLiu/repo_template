---
name: roadmap
description: Manage dependency-aware roadmap workflows in agent_roadmaps/.
---

# Codex Roadmap

Use the shared roadmap command wrapper so Codex and Claude follow the same logic.

## Commands

- `bin/agent-roadmap check`
- `bin/agent-roadmap create <name> --phases <N> --phase-names <names...>`
- `bin/agent-roadmap status`
- `bin/agent-roadmap update complete-task`
- `bin/agent-roadmap update block-task <reason>`
- `bin/agent-roadmap update unblock-task`
- `bin/agent-roadmap update set-focus <task-id>`
- `bin/agent-roadmap handoff`
- `bin/agent-roadmap complete`
- `bin/agent-roadmap validate <phase-folder>`

## Startup Protocol

1. Read `agent_roadmaps/README.md`.
2. Run `bin/agent-roadmap check`.
3. If a phase is active, read:
   - `agent_roadmaps/<active-phase>/INVARIANTS.md`
   - `agent_roadmaps/<active-phase>/ROADMAP.md`
   - `agent_roadmaps/<active-phase>/roadmap.yml`
   - latest `agent_roadmaps/<active-phase>/sessions/session-*.md`
4. Verify branch is `roadmap/<active-phase-folder>`.

## Dependency Rules

- Do not activate a phase before all `depends_on_phases` are completed.
- Do not activate a task before all `depends_on` tasks are completed.
- Keep exactly one active task for an active phase.
