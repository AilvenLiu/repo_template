# ROADMAP - Phase 1 Profile Architecture

> This document describes the phase `phase-1-profile-architecture`.
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

Replace the binary `project_type: python | cpp` with a composable
`project_profile` that captures the multiple axes a real AI infra project
varies along (language, build system, bindings, distribution, hardware
targets, external dependencies). This is the load-bearing architectural
unlock for Phase 2's hybrid Python+C++/CUDA story.

Why this phase exists:
- The current binary `project_type` cannot express a TVM-like project
  (Python+C++/CUDA, scikit-build-core, nanobind/tvm-ffi, system CUDA libs,
  PyPI wheel).
- Adding more `project_type` enum values (e.g., `python_cpp_cuda`) explodes
  combinatorially.
- A composition-based profile lets Phase 2 add new axes (bindings,
  distribution, hybrid) without touching the loader logic.

## 2. Upstream Dependencies

- `phase-0-cleanup` MUST be marked `completed` before this phase is activated.
- Verification: read
  `agent_roadmaps/phase-0-cleanup/roadmap.yml`; `status.completed_at` must be
  a valid ISO date and every task `status` must be `completed`.

## 3. Scope and Non-Goals

### In Scope
- Design the `project_profile` schema and write it as an ADR.
- Implement the schema in `.ai/scripts/project_profile.py` (renamed from
  `project_type.py`).
- Refactor `.ai/scripts/session_init.py` to load constraints by profile axis,
  not by binary type.
- Refactor `.ai/capabilities.yml` so `required` skills can be declared per
  axis (`when: language=cpp`, `when: build_system=bazel`, etc.) rather than
  per project_type.
- Refactor `bin/agent-build` to dispatch by `build_system`.
- Refactor `bin/agent-dependency` to dispatch by profile.
- Build and ship a backward-compatibility shim: existing
  `project_type: python` resolves to a default profile equivalent to the
  pre-refactor behaviour.
- Add round-trip tests proving that legacy projects load identical constraint
  sets before and after the refactor.

### Out of Scope
- Writing new constraint files (Phase 2).
- Adding the Bazel skill or other new skills (Phase 2).
- Hybrid Python+C++/CUDA overlay content (Phase 2).
- Adding new capability requirements beyond what already exists (Phase 2).
- Touching the constraint bodies under `.ai/constraints/`. Loaders change;
  content does not.

## 4. Task Strategy

Tasks are ordered to minimise risk: spec first, then implementation, then
wrappers, then tests. The user-gate at the end of `task-1-1` is explicit and
hard.

- `task-1-1` (write the schema ADR): produce `.ai/adr/0001-project-profile.md`
  documenting the schema, the migration story, the backward-compat semantics,
  and the trade-offs. STOP and request user review before any implementation.
- `task-1-2` (rename and reshape the type detector): rename
  `.ai/scripts/project_type.py` to `.ai/scripts/project_profile.py`. Keep the
  old import path as a shim that re-exports the new module's API plus a
  `legacy_project_type_to_profile()` helper. Add unit tests for the shim.
- `task-1-3` (refactor the constraint loader): update `session_init.py` so
  it accepts a `project_profile` and loads constraints additively per axis.
  When given a legacy `project_type`, it routes through
  `legacy_project_type_to_profile()` and produces the same loaded set.
- `task-1-4` (refactor capabilities.yml): introduce `when:` selectors on each
  required skill so `python-env-setup` is required only when
  `language=python`, `bazel` (added in Phase 2) only when
  `build_system=bazel`, etc. The schema migration must keep current required
  skills required for current `project_type` values.
- `task-1-5` (refactor `bin/agent-build`): dispatch by `build_system`. New
  build systems land empty (or with a "not yet implemented" stub) and are
  filled in by Phase 2. Existing `poetry` and `cmake` paths keep working.
- `task-1-6` (refactor `bin/agent-dependency`): dispatch by profile. Existing
  Poetry and Conan paths keep working. New axes are stubs.
- `task-1-7` (add the back-compat shim and document the migration): write a
  short migration note in `templates/python/CLAUDE.md` and
  `templates/cpp/CLAUDE.md` saying the new `project_profile` block is
  optional and the old `project_type` value still works.
- `task-1-8` (add tests and verify capability audit): add `pytest` tests for
  the shim and the loader; run the capability audit against a fixture
  project with each legacy `project_type` value and assert the audit result
  is identical to the pre-Phase-1 result.

## 5. Deliverables

- `.ai/adr/0001-project-profile.md` (new file).
- `.ai/scripts/project_profile.py` (renamed; old path retained as shim).
- Updated `.ai/scripts/session_init.py`, `.ai/capabilities.yml`,
  `bin/agent-build`, `bin/agent-dependency`.
- Migration note added to `templates/python/CLAUDE.md` and
  `templates/cpp/CLAUDE.md`.
- New tests under `.ai/scripts/tests/` (or wherever the test root is); CI
  evidence that they pass.
- One PR titled `feat(architecture): introduce project_profile composition`
  with the ADR linked from the description.
- Session handoffs documenting the user-gate sign-off on the ADR.

## 6. Exit Criteria

Phase 1 is complete only when:
- Every task in `roadmap.yml` is `completed`.
- `status.completed_at` is set in `roadmap.yml`.
- The ADR has been approved by the user (recorded in a session handoff).
- The PR from `roadmap/phase-1-profile-architecture` to master is open with
  a passing CI run (or, if CI is not configured, the user has manually
  confirmed `bin/agent-precommit` passes and the back-compat tests pass).
- A real-world Python project consuming this template runs
  `bin/agent-build full` against the post-Phase-1 template successfully.
  This is the "did we actually preserve backward compatibility" gate.
- The user has explicitly approved Phase 2 activation.

## 7. Risks and Rollback

| Risk | Detection | Mitigation |
|---|---|---|
| Schema design has a flaw that only surfaces during Phase 2 | Phase 2 tries to add a new axis and discovers a structural conflict | The user-gate after task-1-1 exists for this; the ADR should walk through at least one Phase 2 axis (e.g., `bindings`) as a worked example to stress-test the schema |
| Backward-compat shim silently changes which constraints load | Round-trip test in task-1-8 fails | The round-trip test is mandatory; it MUST pass before the PR is opened |
| Loader refactor breaks an existing Python project | Real-world project's `bin/agent-build full` fails | Exit Criteria require this exact verification before Phase 2 activates |
| Capabilities.yml rewrite drops a previously-required skill | Capability audit fixture test in task-1-8 fails | The fixture tests assert audit equality, not just success |

Rollback: each task is one commit (or small series). `git revert` of the PR
restores the pre-Phase-1 architecture; constraint bodies were never touched
so no data loss.

## 8. Execution Rule

Follow task and dependency order; do not bypass declared dependencies. The
user-gate after task-1-1 is non-negotiable. Do not expand scope into Phase 2
territory: no new constraints, no new skills, no new content.
