---
name: roadmap
description: "Manage multi-session agent workflows via agent_roadmaps/. Checks for active roadmaps at session start."
---

# /roadmap

Structured commands for multi-session AI agent workflows using the
`agent_roadmaps/` system.

## Commands

- `/roadmap check` — check for active roadmaps (run at session start)
- `/roadmap create <name> [description]` — create new roadmap
- `/roadmap status` — show detailed progress
- `/roadmap update complete-task` — mark current task done, advance
- `/roadmap update block-task <reason>` — mark current task blocked
- `/roadmap update unblock-task` — clear blocked status
- `/roadmap update set-focus <phase> <task>` — change focus manually
- `/roadmap handoff` — generate session handoff file
- `/roadmap complete` — mark roadmap done and deactivate

## Behaviour (guaranteed)

1. Enforces single-active-roadmap rule.
2. Validates state transitions (no skipping tasks/phases).
3. Validates roadmap schema (phase/task ID formats, allowed statuses).
4. Generates session handoff files in `sessions/`.

## Critical rules

- At most ONE active roadmap at a time.
- Work ONLY on the current focus task.
- Generate a handoff at the end of every session.
- Authority hierarchy: INVARIANTS.md > ROADMAP.md > roadmap.yml > sessions/ > prompt.md.
