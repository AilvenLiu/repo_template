# ROADMAP -- Phase Execution Guide (Template)

> This document describes the phase `<PHASE_FOLDER_NAME>`.
> It should be explicit enough for a fresh session with zero prior context.

## 1. Goal

Describe exactly what this phase must deliver and why it matters.

## 2. Upstream Dependencies

List explicit prerequisite phases from `depends_on_phases` and what each one
must provide before this phase starts.

- Dependency: `<phase-folder>`
- Required outputs consumed in this phase
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

This phase is complete only when:
- Every task in `roadmap.yml` is `completed`
- `status.completed_at` is set
- Final handoff exists in `sessions/`
- PR/MR from `roadmap/<PHASE_FOLDER_NAME>` is ready

## 7. Risks and Rollback

Document critical risks, detection signals, and rollback or containment strategy.

## 8. Execution Rule

Follow task and dependency order exactly; do not bypass declared dependencies.
