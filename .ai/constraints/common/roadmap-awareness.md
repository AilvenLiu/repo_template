# Roadmap Awareness Constraints

> Mandatory roadmap constraints for all AI agents.
> Applies to Python and C++/CUDA projects.

## Overview

Roadmaps govern complex, multi-session work. They are dependency-aware and step-driven.
Roadmap files are temporary operational artefacts that live only under
`agent_roadmaps/`.
Each step lives in `agent_roadmaps/step-*/` and must declare both:
- step dependencies (`depends_on_steps`)
- task dependencies (`tasks[].depends_on`)

## 1. Mandatory Startup Check

At the beginning of every session, the agent MUST:
1. Read `agent_roadmaps/README.md`
2. Check whether an active step exists
3. If active, read:
   - `INVARIANTS.md`
   - `ROADMAP.md`
   - `roadmap.yml`
   - latest handoff in `sessions/`
4. Verify current branch is `roadmap/<active-step-folder>`
5. Verify active step dependencies are satisfied

Skipping this check is forbidden.

If no active roadmap exists, the agent MUST treat `agent_roadmaps/` as an
empty placeholder and MUST NOT resurrect closed roadmap state from memory.

## 2. Roadmap Creation Trigger

The agent MUST ask whether to create a roadmap before implementation when work:
1. Cannot be completed confidently in 1-2 sessions
2. Requires architectural or invariant-sensitive change
3. Needs constraints to survive context resets
4. Has non-trivial step or rollback dependencies

If user approves roadmap creation, the agent MUST create roadmap files before production implementation.
Roadmap identifiers must stay inside `agent_roadmaps/`; code, configuration,
durable documentation, and user-facing strings outside that directory MUST NOT
contain roadmap-stage labels such as `step-*-*`, `roadmap/step-*`, or "Step N".

## 3. Required Step Structure

Each step folder must include:

```text
agent_roadmaps/
  step-N-name/
    INVARIANTS.md
    ROADMAP.md
    roadmap.yml
    prompt.md
    sessions/
```

## 4. Canonical roadmap.yml Schema

```yaml
step: <int>
name: <string>

status:
  active: <bool>
  blocked: <bool>
  started_at: <YYYY-MM-DD|null>
  completed_at: <YYYY-MM-DD|null>

depends_on_steps:
  - <step-folder-name>

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
- At most one step may be active.
- Active step must have exactly one active task.
- `focus.current_task` must match the active task.
- Tasks may be activated only when all `depends_on` tasks are completed.
- A step may be activated only when all `depends_on_steps` are completed.
- `completed_at` may be set only after all tasks are completed.

## 5. Branching Discipline

- Each step uses `roadmap/<step-folder-name>` branch.
- Do not commit step work directly on base branch.
- Step completion requires PR/MR into base branch.
- Do not activate downstream steps until dependency steps are completed and merged.
- A roadmap branch name is temporary coordination state and MUST NOT be copied
  into durable repository files.

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
2. Enforce single active step
3. Enforce step/task dependency ordering
4. Track state only in roadmap.yml + sessions handoffs
5. Delete the whole roadmap workspace once every step in that roadmap is completed
6. Keep roadmap identifiers out of durable files outside `agent_roadmaps/`
7. Stop and ask when unsure
