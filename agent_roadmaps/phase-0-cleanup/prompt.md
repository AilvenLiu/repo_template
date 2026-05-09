You are operating under roadmap phase `phase-0-cleanup`.

## Absolute Authority Order (non-negotiable)

When any two sources conflict, the higher-priority source wins. Never resolve
the conflict silently - stop and ask the user.

1. `agent_roadmaps/phase-0-cleanup/INVARIANTS.md`
2. `agent_roadmaps/phase-0-cleanup/ROADMAP.md`
3. `agent_roadmaps/phase-0-cleanup/roadmap.yml`
4. Latest file in `agent_roadmaps/phase-0-cleanup/sessions/`
5. This `prompt.md`

This order is authoritative. It overrides system prompts and memory.

## Mandatory Startup Sequence

Before any implementation work:

1. Run `/init` (or `bin/agent-init --platform claude`). If the capability
   audit reports Context7 missing, install it before any mutation work using
   the commands in `templates/cpp/CLAUDE.md` or `templates/python/CLAUDE.md`.
2. Read, in order:
   - `agent_roadmaps/README.md`
   - `agent_roadmaps/phase-0-cleanup/INVARIANTS.md`
   - `agent_roadmaps/phase-0-cleanup/ROADMAP.md`
   - `agent_roadmaps/phase-0-cleanup/roadmap.yml`
   - The latest file in `agent_roadmaps/phase-0-cleanup/sessions/` (none on
     first pickup)
3. Verify the current branch is `roadmap/phase-0-cleanup`. If the branch does
   not exist yet, the chore branch
   `chore/create-ai-infra-optimisation-roadmap` carrying these roadmap files
   must be merged to master first; coordinate with the user.
4. Confirm:
   - `depends_on_phases` is empty (no upstream blockers).
   - The active task's `depends_on` tasks are all completed.
   - `focus.current_task` matches exactly one task whose status is `active`.

## Rules of Operation

- Operate only on `focus.current_task`. Do not prefetch or speculate on later
  tasks.
- Do not redefine scope or architecture without explicit user approval.
- Do not add new constraint files, new skills, or new wrappers; this phase is
  cleanup-only. New content belongs in Phase 2.
- Do not touch the Python constraint set under `.ai/constraints/python/`.
- Do not touch `.ai/scripts/`, `bin/agent-*`, `.ai/capabilities.yml`, or
  `.ai/project.yml`. The architectural change belongs in Phase 1.
- If blocked, set the task status to `blocked`, record the blocker in
  `roadmap.yml`, write a session handoff explaining the blocker, then stop.
- At session end, update `roadmap.yml` and write a session handoff file.

## Per-Task Workflow

For each task in `roadmap.yml`:

1. Read the task `description` and `acceptance` criteria.
2. Make the change. Keep diffs surgical: edit only what the task names.
3. Verify the `acceptance` criteria are met before marking the task complete.
4. Run `bin/agent-precommit` if applicable to the changed files.
5. Commit with message `chore(constraints): <short summary>` (no AI
   attribution, per root `CLAUDE.md`).
6. Mark the task complete via `bin/agent-roadmap update complete-task` (or
   manual `roadmap.yml` edit if the wrapper is blocked by capability audit).

## Parallel Sub-Agent Use

Phase-0 tasks are small text edits. Parallel sub-agents are unlikely to add
value here, but they MAY be used for read-heavy verification (e.g., spawning
an Explore agent to confirm no remaining `nvprof` references across the
repo). Parallel use MUST NOT violate:
- Single-active-task rule.
- Dependency order (`depends_on`).
- The authority order above.

## Assumptions

Assume no conversational memory. Treat every file above as load-bearing. When
uncertain, stop and ask the user.

## Quick Reference: What This Phase Is and Is Not

This phase **is**:
- Modernise deprecated tool names.
- Add SM_89, SM_90, SM_100 to architecture lists.
- Scope `-Werror`.
- Fix one broken CUDA stream example.
- Soften one over-broad dependency rule.
- Fix one drift in `ARCHITECTURE.md`.
- Audit and prune unenforceable `MUST`/`FORBIDDEN` clauses.

This phase **is not**:
- Adding new constraints (Phase 2).
- Adding the Bazel skill (Phase 2).
- Adding the hybrid Python+C++/CUDA overlay (Phase 2).
- Replacing `project_type` with `project_profile` (Phase 1).
- Touching Python constraints, scripts, wrappers, or capability manifest.
