# Roadmap Template Compliance Guide

Quick checklist for dependency-aware roadmap files.

## Mandatory Checklist

- [ ] Step folder is `agent_roadmaps/step-N-name/`
- [ ] `roadmap.yml` has keys: `step`, `name`, `status`, `depends_on_steps`, `tasks`, `focus`
- [ ] `status` includes: `active`, `blocked`, `started_at`, `completed_at`
- [ ] `depends_on_steps` explicitly lists upstream step folder names (or `[]`)
- [ ] Every task includes: `id`, `title`, `description`, `status`, `effort`, `key_files`, `depends_on`
- [ ] Task IDs use `task-N-M` format
- [ ] Task dependencies reference valid task IDs
- [ ] Dependency graph has no cycles
- [ ] Active step has exactly one active task and matching `focus.current_task`
- [ ] Validation passes: `python3 .ai/scripts/roadmap/validate_schema.py <step-folder>`
- [ ] Durable files outside `agent_roadmaps/` do not mention roadmap-stage identifiers
- [ ] Full roadmap series is deleted once every step is completed

## Minimal Schema

```yaml
step: 7
name: Close the Operational Loop

status:
  active: true
  blocked: false
  started_at: "2026-04-17"
  completed_at: null

depends_on_steps:
  - upstream-roadmap-step

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

- Missing or empty `depends_on_steps`
- Missing `depends_on` on tasks
- Unknown task IDs in `depends_on`
- Multiple active tasks
- `focus.current_task` not matching the active task
- Non-atomic task definitions

## Validation Workflow

1. Create step folders with `create.py`
2. Fill `INVARIANTS.md`, `ROADMAP.md`, `roadmap.yml`, `prompt.md`
3. Validate with `validate_schema.py`
4. Fix critical errors and re-run validation
5. Activate only dependency-ready step/task work
