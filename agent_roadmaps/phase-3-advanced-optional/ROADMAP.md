# ROADMAP - Phase 3 Advanced / Optional

> This document describes the phase `phase-3-advanced-optional`.
> It is explicit enough for a fresh session with zero prior context.

## 0. Authority Order

1. `INVARIANTS.md` (overrides this file)
2. `ROADMAP.md` (this file)
3. `roadmap.yml`
4. Latest file in `sessions/`
5. `prompt.md`

If this file conflicts with `INVARIANTS.md`, follow `INVARIANTS.md` and ask
the user.

## 1. Goal

Provide a structured place for speculative AI-infra content that is plausibly
needed by some consuming project, but for which no consumer currently exists.
This phase intentionally has a high activation bar: each task only starts
when the user names a real project that needs it (see `INVARIANTS.md` section
3).

The phase exists so that future requests like "we're now working on TVM
Relax with LLVM AOT, can you add LLVM-linking guidance?" have a defined
landing pad rather than an ad-hoc add to the constraint set.

Why this phase exists rather than not existing at all:
- The Phase 2 review surfaces a long list of "we could also cover X" topics.
  Without a Phase 3 bucket, those topics either land in Phase 2 (bloating it
  and breaking the draft-first discipline because each Phase 2 draft is
  expected to validate within the phase) or they get lost.
- Listing them here as `pending` tasks documents the design space without
  inflating the active surface area.

## 2. Upstream Dependencies

- `phase-2-ai-infra-content` MUST be marked `completed` before this phase
  is activated.
- Verification: read `agent_roadmaps/phase-2-ai-infra-content/roadmap.yml`;
  `status.completed_at` must be a valid ISO date and every task `status`
  must be `completed`.

## 3. Scope and Non-Goals

### In Scope (each task gated on user-named consuming project)
- `task-3-1`: Autotuning frameworks guidance (AutoTVM, Ansor, MetaSchedule,
  Triton autotuner, FlashInfer JIT compile).
- `task-3-2`: TVM-FFI packed-function calling convention specifics
  (separate from the generic FFI guidance in Phase 2's `ffi-boundary.md`).
- `task-3-3`: LLVM-as-a-library linking pattern (TVM, MLC for AOT codegen).
- `task-3-4`: HIP/ROCm parallel-stack rules.
- `task-3-5`: WebGPU, Metal, SPIR-V codegen guidance.

### Out of Scope
- Anything not listed above. Adding a new Phase 3 task requires a
  user-approved roadmap edit.
- Promoting any draft to `status: stable`.
- Re-opening Phase 0, Phase 1, or Phase 2 work.

## 4. Task Strategy

Phase 3 tasks are independent and individually gated. There is no required
order. The default state for every task is `pending`.

When the user names a consuming project for a task:
1. Record the named project and the target time window in a session handoff.
2. Activate the task in `roadmap.yml`.
3. Coordinate the branch strategy with the user (sub-branch per task vs
   single phase branch).
4. Author the constraint, skill, or template content in `status: draft`.
5. Validate against the named consuming project (same shape as Phase 2's
   `task-2-10`: real-project dry-run, recorded evidence).
6. Mark the task complete only after validation evidence is recorded.

## 5. Deliverables

Per task, when activated:
- A new constraint file or skill body, marked `status: draft`.
- Validation evidence in a session handoff against the named consuming
  project.
- A focused PR.

## 6. Exit Criteria

The phase as a whole is unusual: it may never reach an "all tasks completed"
state. That is acceptable.

The phase is considered:
- **Complete** when every task is `completed` (every speculative axis has
  found a consumer and shipped).
- **Indefinitely-dormant** when no task is active and no user request has
  named a consumer for any task. This is a valid steady state.
- **Partially-complete** when some tasks are `completed` and others are
  still `pending` because no consumer has emerged.

The phase MUST NOT be marked `completed` while any task is `pending`. The
phase is `completed` only when all tasks are completed.

## 7. Risks and Rollback

| Risk | Detection | Mitigation |
|---|---|---|
| A Phase 3 task is silently activated without a named consumer | The task moves to `active` without a corresponding session handoff naming the project | The hard invariant in `INVARIANTS.md` section 3 forbids this; reviewers MUST reject any PR whose handoff does not record the named consumer |
| A Phase 3 task ships content that diverges from the consuming project's actual needs | Validation step surfaces drift | Validation is mandatory per task, same shape as `task-2-10` |
| The Phase 3 task list is treated as a feature backlog rather than a design-space catalogue | Pressure to "tick off" tasks even without consumers | Treat the dormant state as a success, not a failure; the catalogue exists to prevent ad-hoc additions, not to be drained |

Rollback: each completed task is a focused PR; `git revert` of that PR
removes the task's content without affecting other Phase 3 tasks or earlier
phases.

## 8. Execution Rule

The default action for every Phase 3 task is "do not start". Only activate
under the conditions described in `INVARIANTS.md` section 3.
