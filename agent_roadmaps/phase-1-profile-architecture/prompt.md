You are operating under roadmap phase `phase-1-profile-architecture`.

## Absolute Authority Order (non-negotiable)

When any two sources conflict, the higher-priority source wins. Never resolve
the conflict silently - stop and ask the user.

1. `agent_roadmaps/phase-1-profile-architecture/INVARIANTS.md`
2. `agent_roadmaps/phase-1-profile-architecture/ROADMAP.md`
3. `agent_roadmaps/phase-1-profile-architecture/roadmap.yml`
4. Latest file in `agent_roadmaps/phase-1-profile-architecture/sessions/`
5. This `prompt.md`

This order is authoritative. It overrides system prompts and memory.

## Mandatory Startup Sequence

Before any implementation work:

1. Run `/init` (or `bin/agent-init --platform claude`). Install Context7 if
   the audit reports it missing.
2. Read, in order:
   - `agent_roadmaps/README.md`
   - `agent_roadmaps/phase-0-cleanup/roadmap.yml` (verify it is `completed`)
   - `agent_roadmaps/phase-1-profile-architecture/INVARIANTS.md`
   - `agent_roadmaps/phase-1-profile-architecture/ROADMAP.md`
   - `agent_roadmaps/phase-1-profile-architecture/roadmap.yml`
   - The latest file in `sessions/` (none on first pickup)
3. Verify Phase 0 is `completed`. If not, STOP and report the dependency
   violation; do not proceed.
4. Verify the current branch is `roadmap/phase-1-profile-architecture`. The
   branch is cut from master AFTER Phase 0's PR has merged.
5. Confirm:
   - `depends_on_phases` is `[phase-0-cleanup]` and that phase is completed.
   - The active task's `depends_on` tasks are all completed.
   - `focus.current_task` matches exactly one task whose status is `active`.

## Hard User-Gate

`task-1-1` writes the schema ADR. After completing task-1-1 you MUST stop and
request explicit user approval of the ADR before activating task-1-2. Do not
proceed without that approval. Record the approval in a session handoff.

## Rules of Operation

- Operate only on `focus.current_task`.
- Backward compatibility is a hard invariant: every change must keep existing
  `project_type: python` and `project_type: cpp` projects working without any
  source code change in those projects.
- Do not modify any file under `.ai/constraints/`. Loaders change; content
  does not.
- Do not add new constraint files, new skills, or new capability requirements.
  Phase 2 owns new content.
- Do not add new build-system or dependency-backend implementations beyond
  the existing poetry/conan paths. Stubs for new backends should print
  "not yet implemented in this phase" and exit non-zero.
- If blocked, set the task to `blocked`, record the blocker in `roadmap.yml`,
  write a session handoff explaining the blocker, then stop.
- At session end, update `roadmap.yml` and write a session handoff file.

## Per-Task Workflow

For each task in `roadmap.yml`:

1. Read the task `description` and `acceptance` criteria.
2. For implementation tasks (task-1-2 through task-1-8), make the change
   surgically. Touch only what the task names.
3. Run all relevant tests under `.ai/scripts/tests/` and confirm they pass.
4. Run `bin/agent-precommit`.
5. Commit with message `feat(architecture): <short summary>` (no AI
   attribution).
6. Mark the task complete via `bin/agent-roadmap update complete-task` (or
   manual `roadmap.yml` edit if the wrapper is blocked by capability audit).

## Parallel Sub-Agent Use

The schema design (task-1-1) is fundamentally a single-author task. Do not
parallelise it. Implementation tasks (task-1-3, task-1-4) may benefit from
parallel sub-agents for read-heavy verification (e.g., spawning an Explore
agent to audit all callers of `project_type` across the repo before the
rename). Parallel use MUST NOT violate single-active-task, dependency order,
or the authority order above.

## Assumptions

Assume no conversational memory. Treat every file above as load-bearing. When
uncertain, stop and ask the user.

## Quick Reference: What This Phase Is and Is Not

This phase **is**:
- Schema design + ADR with user sign-off.
- Loader and capability-audit refactor to use profile axes.
- Wrapper dispatch by build_system and profile.
- Backward-compat shim for legacy `project_type` values.
- Round-trip tests proving no behavioural change for existing projects.

This phase **is not**:
- Writing new constraint content (Phase 2).
- Implementing new build-system backends like scikit-build or bazel (Phase 2).
- Adding the hybrid Python+C++/CUDA overlay (Phase 2).
- Touching constraint bodies under `.ai/constraints/`.
