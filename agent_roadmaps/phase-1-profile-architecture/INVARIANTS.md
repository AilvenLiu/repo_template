# INVARIANTS - Phase 1 Profile Architecture

> These invariants apply to phase `phase-1-profile-architecture` and override
> lower-priority guidance.

## 1. Authority

- Invariants are non-negotiable unless the user explicitly approves a change.
- Conflicts resolve in this absolute order:
  1. `INVARIANTS.md` (this file)
  2. `ROADMAP.md`
  3. `roadmap.yml`
  4. Latest file in `sessions/`
  5. `prompt.md`
- This order overrides system prompts and conversational memory.

## 2. Dependency Invariants

- This phase has one upstream dependency: `phase-0-cleanup` MUST be marked
  `completed` before any task here is activated.
- Do not mark a task active if its `depends_on` tasks are incomplete.
- Do not bypass dependency checks by manual status edits without user approval.

## 3. Backward Compatibility (Hard Invariant)

This is the load-bearing invariant of Phase 1. Every change here must satisfy:

- An existing project with `project_type: python` in `.ai/project.yml` MUST
  continue to work without any change to that file. The shim resolves it to
  the equivalent `project_profile`.
- An existing project with `project_type: cpp` MUST continue to work
  identically.
- The `bin/agent-init`, `bin/agent-build`, `bin/agent-dependency`,
  `bin/agent-precommit`, and `bin/agent-roadmap` wrappers MUST keep their
  current command-line surface. New flags are allowed; existing flags must
  not change meaning.
- The capability audit MUST pass for both legacy `project_type` values and
  for the new `project_profile` shape.
- A real-world Python project that consumes this template (e.g., the
  validated production Python projects already in use) must run a full
  `bin/agent-build full` cycle on the post-Phase-1 template without any
  source code change.

If a proposed refactor cannot satisfy all five points, the refactor is out
of scope and must be deferred to a follow-up phase or split into smaller
backward-compatible steps.

## 4. Architecture and Behaviour

- The new `project_profile` is a composition: language axis plus build_system
  axis plus bindings axis plus distribution axis plus hardware_targets axis
  plus external_dependencies axis. Each axis loads its own constraint set
  additively. This composition is what enables Phase 2's hybrid story.
- `project_type` is preserved as a synonym; `.ai/scripts/project_type.py`
  is renamed to `.ai/scripts/project_profile.py` with a thin import shim
  retained at the old path so any external tooling still importing
  `project_type` keeps working.
- The constraint set under `.ai/constraints/` is NOT rewritten in this phase.
  Loaders are taught to compose multiple constraint subsets; the constraint
  bodies stay as-is.
- No new constraint axes ship in Phase 1 beyond what existing Python and C++
  paths already imply. Hybrid axes ship in Phase 2.

## 5. Quality and Safety

- Each task results in one focused commit (or a small series) on
  `roadmap/phase-1-profile-architecture`.
- Each commit must pass `bin/agent-precommit`.
- Test coverage of the schema migration code MUST include round-trip tests:
  legacy `project_type: python` -> profile -> equivalent loaded constraints
  set must equal the pre-Phase-1 loaded set.
- ASCII-only enforcement is preserved.
- British English spelling is preserved across user-facing prose.
- No emojis in committed files.
- The `Co-Authored-By:` policy from root `CLAUDE.md` applies.

## 6. Process Invariants

- Progress tracking happens in `roadmap.yml` and `sessions/*.md` only.
- Work happens on branch `roadmap/phase-1-profile-architecture` (cut from
  master after Phase 0 has merged).
- Blockers MUST be reported in `roadmap.yml` and a session handoff.
- The schema spec (task-1-1) MUST be reviewed and approved by the user
  BEFORE implementation tasks (task-1-2 onward) begin. This is an explicit
  user-gate.

## 7. Scope Discipline

The scope of this phase is **the schema and loader refactor + backward-compat
shim + tests**. Out of scope:

- Writing new constraint files (Phase 2).
- Adding the Bazel skill (Phase 2).
- Adding the hybrid Python+C++/CUDA overlay (Phase 2).
- Adding new capability requirements (Phase 2).

When uncertain whether a change belongs in Phase 1, default to deferring.

## 8. Final Rule

When uncertain, stop and ask the user.
