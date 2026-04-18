# Roadmap Awareness Constraints

> Mandatory roadmap constraints for all AI agents.
> Applies to Python and C++/CUDA projects.

## Overview

Roadmaps govern complex, multi-session work. They are dependency-aware and phase-driven.
Each phase lives in `agent_roadmaps/phase-*/` and must declare both:
- phase dependencies (`depends_on_phases`)
- task dependencies (`tasks[].depends_on`)

## 1. Mandatory Startup Check

At the beginning of every session, the agent MUST:
1. Read `agent_roadmaps/README.md`
2. Check whether an active phase exists
3. If active, read:
   - `INVARIANTS.md`
   - `ROADMAP.md`
   - `roadmap.yml`
   - latest handoff in `sessions/`
4. Verify current branch is `roadmap/<active-phase-folder>`
5. Verify active phase dependencies are satisfied

Skipping this check is forbidden.

## 2. Roadmap Creation Trigger

The agent MUST ask whether to create a roadmap before implementation when work:
1. Cannot be completed confidently in 1-2 sessions
2. Requires architectural or invariant-sensitive change
3. Needs constraints to survive context resets
4. Has non-trivial phase or rollback dependencies

If user approves roadmap creation, the agent MUST create roadmap files before production implementation.

## 3. Required Phase Structure

Each phase folder must include:

```text
agent_roadmaps/
  phase-N-name/
    INVARIANTS.md
    ROADMAP.md
    roadmap.yml
    prompt.md
    sessions/
```

## 4. Canonical roadmap.yml Schema

```yaml
phase: <int>
name: <string>

status:
  active: <bool>
  blocked: <bool>
  started_at: <YYYY-MM-DD|null>
  completed_at: <YYYY-MM-DD|null>

depends_on_phases:
  - <phase-folder-name>

tasks:
  - id: task-N-M
    title: <string>
    description: <string>
    status: pending|active|completed|blocked
    effort: low|medium|high
    key_files: [<path>, ...]
    depends_on: [task-id, ...]

focus:
  current_task: <task-id|null>
  notes: <string>
```

Rules:
- At most one phase may be active.
- Active phase must have exactly one active task.
- `focus.current_task` must match the active task.
- Tasks may be activated only when all `depends_on` tasks are completed.
- A phase may be activated only when all `depends_on_phases` are completed.
- `completed_at` may be set only after all tasks are completed.

## 5. Branching Discipline

- Each phase uses `roadmap/<phase-folder-name>` branch.
- Do not commit phase work directly on base branch.
- Phase completion requires PR/MR into base branch.
- Do not activate downstream phases until dependency phases are completed and merged.

## 6. Session-End Discipline

For roadmap sessions, always:
1. Update `roadmap.yml` state
2. Write new handoff: `sessions/session-YYYY-MM-DD-HH-MM.md`
3. Record completed work, decisions, blockers, and next steps

## 7. Blockage Handling

If dependencies prevent forward progress:
- mark blocked state in roadmap
- report exact unmet dependencies
- do not bypass dependency order without explicit user approval

## 8. Enforcement Summary

1. Always perform roadmap startup check
2. Enforce single active phase
3. Enforce phase/task dependency ordering
4. Track state only in roadmap.yml + sessions handoffs
5. Stop and ask when unsure
