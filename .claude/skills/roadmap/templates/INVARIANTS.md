# INVARIANTS -- Phase Constitutional Constraints (Template)

> These invariants apply to phase `<PHASE_FOLDER_NAME>` and override lower-priority guidance.

## 1. Authority

- Invariants are non-negotiable unless user explicitly approves a change.
- Conflicts resolve in this order: `INVARIANTS.md` > `ROADMAP.md` > `roadmap.yml` > session notes.

## 2. Dependency Invariants

- Do not execute this phase until all `depends_on_phases` are completed.
- Do not mark a task active if its `depends_on` tasks are incomplete.
- Do not bypass dependency checks by manual status edits without user approval.

## 3. Architecture and Behavior

Define system boundaries and behavior that must not regress in this phase.

## 4. Quality and Safety

- Existing test suite must remain green.
- New changes must include adequate validation.
- No silent behavior changes are allowed.

## 5. Process Invariants

- Progress tracking must happen in `roadmap.yml` and session handoff files only.
- Work must happen on branch `roadmap/<PHASE_FOLDER_NAME>`.
- Blockers must be reported; constraints must not be worked around silently.

## 6. Final Rule

When uncertain, stop and ask the user.
