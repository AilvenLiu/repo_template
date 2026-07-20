# Roadmap Template Compliance Guide

Quick checklist for dependency-aware roadmap files.

## Mandatory Checklist

- [ ] Phase folder is `agent_roadmaps/phase-N-name/`
- [ ] `roadmap.yml` has keys: `phase`, `name`, `status`, `depends_on_phases`, `tasks`, `focus`
- [ ] `status` includes: `active`, `blocked`, `started_at`, `completed_at`
- [ ] `depends_on_phases` explicitly lists upstream phase folder names (or `[]`)
- [ ] Every task includes: `id`, `title`, `description`, `status`, `effort`, `key_files`, `depends_on`
- [ ] Task IDs use `task-N-M` format
- [ ] Task dependencies reference valid task IDs
- [ ] Dependency graph has no cycles
- [ ] Active phase has exactly one active task and matching `focus.current_task`
- [ ] Validation passes: `python3 .agents/scripts/roadmap/validate_schema.py <phase-folder>`
- [ ] Durable files outside `agent_roadmaps/` do not mention roadmap-phase identifiers
- [ ] Full roadmap series is deleted once every phase is completed

## Minimal Schema

```yaml
phase: 7
name: Close the Operational Loop

status:
  active: true
  blocked: false
  started_at: "2026-04-17"
  completed_at: null

depends_on_phases:
  - phase-6-upstream

tasks:
  - id: task-7-1
    title: Add pre-market position inquiry email
    description: Add a 09:00 ET inquiry email trigger in worker daemon mode.
    status: active
    effort: medium
    key_files:
      - src/worker_shell.py
    depends_on: []

focus:
  current_task: task-7-1
  notes: Start with the trigger because downstream tasks depend on it.
```

## Common Violations

- Missing or malformed `depends_on_phases`
- Missing `depends_on` on tasks
- Unknown task IDs in `depends_on`
- Multiple active tasks
- `focus.current_task` not matching the active task
- Non-atomic task definitions

## Validation Workflow

1. Create phase folders with `create.py --phases <N> --phase-names <names...>`
2. Fill `INVARIANTS.md`, `ROADMAP.md`, `roadmap.yml`, `prompt.md`
3. Validate with `validate_schema.py`
4. Fix critical errors and re-run validation
5. Activate only dependency-ready phase/task work
