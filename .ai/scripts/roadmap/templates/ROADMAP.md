# ROADMAP -- Step Execution Guide (Template)

> This document describes the step `<STEP_FOLDER_NAME>`.
> It should be explicit enough for a fresh session with zero prior context.

## 0. Authority Order

This file is bound by the absolute authority order:

1. `INVARIANTS.md` (overrides this file)
2. `ROADMAP.md` (this file)
3. `roadmap.yml`
4. Latest file in `sessions/`
5. `prompt.md`

If this file conflicts with `INVARIANTS.md`, follow `INVARIANTS.md` and ask the user.

## 1. Goal

Describe exactly what this step must deliver and why it matters.

## 2. Upstream Dependencies

List explicit prerequisite steps from `depends_on_steps` and what each one
must provide before this step starts.

- Dependency: `<step-folder>`
- Required outputs consumed in this step
- Verification method for dependency completion

## 3. Scope and Non-Goals

### In Scope
- [Concrete objective 1]
- [Concrete objective 2]

### Out of Scope
- [Non-goal 1]
- [Non-goal 2]

## 4. Task Strategy

Map each task in `roadmap.yml` to execution intent, including dependency order.

- `<TASK_PREFIX>-1`: why this must happen first
- `<TASK_PREFIX>-2`: dependency assumptions and failure modes
- `<TASK_PREFIX>-3`: validation + handoff expectations

## 5. Deliverables

- [Deliverable artifact 1]
- [Deliverable artifact 2]
- [Validation evidence]

## 6. Exit Criteria

This step is complete only when:
- Every task in `roadmap.yml` is `completed`
- `status.completed_at` is set
- Final handoff exists in `sessions/`
- PR/MR from `roadmap/<STEP_FOLDER_NAME>` is ready

## 7. Risks and Rollback

Document critical risks, detection signals, and rollback or containment strategy.

## 8. Execution Rule

Follow task and dependency order exactly; do not bypass declared dependencies.
