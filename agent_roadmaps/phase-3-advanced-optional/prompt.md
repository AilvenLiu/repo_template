You are operating under roadmap phase `phase-3-advanced-optional`.

## Absolute Authority Order (non-negotiable)

When any two sources conflict, the higher-priority source wins. Never resolve
the conflict silently - stop and ask the user.

1. `agent_roadmaps/phase-3-advanced-optional/INVARIANTS.md`
2. `agent_roadmaps/phase-3-advanced-optional/ROADMAP.md`
3. `agent_roadmaps/phase-3-advanced-optional/roadmap.yml`
4. Latest file in `agent_roadmaps/phase-3-advanced-optional/sessions/`
5. This `prompt.md`

This order is authoritative. It overrides system prompts and memory.

## Mandatory Startup Sequence

Before any implementation work:

1. Run `/init` (or `bin/agent-init --platform claude`). Install Context7 if
   the audit reports it missing.
2. Read, in order:
   - `agent_roadmaps/README.md`
   - `agent_roadmaps/phase-2-ai-infra-content/roadmap.yml` (verify it is
     `completed`)
   - `agent_roadmaps/phase-3-advanced-optional/INVARIANTS.md`
   - `agent_roadmaps/phase-3-advanced-optional/ROADMAP.md`
   - `agent_roadmaps/phase-3-advanced-optional/roadmap.yml`
   - The latest file in `sessions/` (none on first pickup)
3. Verify Phase 2 is `completed`. If not, STOP and report the dependency
   violation; do not proceed.

## Real-Project-Demand Hard Invariant

The default action for every Phase 3 task is **do not start**. A task may be
activated only when:

1. The user has named a real consuming project (e.g., "MLC-LLM Hopper TMA
   work", "TVM Relax LLVM AOT codegen", "FlashInfer ROCm port"); AND
2. The user has confirmed the consuming project will exercise the resulting
   content within a defined time window; AND
3. The naming and confirmation are recorded in a session handoff at
   activation time.

If you have entered this phase without those three conditions met for at
least one task, STOP. Report to the user that no Phase 3 task qualifies for
activation, and exit. Phase 3 may remain dormant indefinitely; that is the
intended state.

## Rules of Operation

- Operate only on `focus.current_task`, and only after the activation gate
  has been satisfied for that task.
- All Phase 3 deliverables ship as `status: draft`.
- Phase 3 tasks are independent. There is no required order between them.
  Activate each task individually under its own user-approved gate.
- A task may be developed on its own sub-branch (e.g.,
  `roadmap/phase-3-advanced-optional/task-3-1-autotuning`) if the user
  prefers per-task PRs. Coordinate the branch strategy at activation time.
- Do not re-open Phase 0, Phase 1, or Phase 2 work from inside Phase 3.
  Issues found in earlier phases produce follow-up roadmap series, not
  in-place edits here.
- If blocked, set the task to `blocked`, record the blocker in `roadmap.yml`,
  write a session handoff explaining the blocker, then stop.
- At session end, update `roadmap.yml` and write a session handoff file.

## Per-Task Workflow

For each Phase 3 task that has been activated under a satisfied gate:

1. Read the task `description` and `acceptance` criteria.
2. Author the constraint, skill, or template content in `status: draft`.
   Follow Phase 2 file structure as a reference.
3. Validate against the named consuming project. Record exact evidence
   (commands, exit codes, observed behaviour) in the session handoff.
4. Run `bin/agent-precommit`.
5. Commit with message `feat(content): <short summary>` (no AI attribution).
6. Mark the task complete via `bin/agent-roadmap update complete-task`
   (or manual `roadmap.yml` edit if the wrapper is blocked by capability
   audit).

## Parallel Sub-Agent Use

Phase 3 tasks rarely run in parallel because each one is gated on its own
user-named consumer. Within a single task, the same parallelism guidance as
Phase 2 applies: Explore agents for research are fine; final synthesis and
the file write happen in the main session. Parallel use MUST NOT bypass the
real-project-demand invariant.

## Assumptions

Assume no conversational memory. Treat every file above as load-bearing. When
uncertain, stop and ask the user. The Phase 3 default is always "do not
start".

## Quick Reference: What This Phase Is and Is Not

This phase **is**:
- A bucket for speculative AI-infra content with a high activation bar.
- Five candidate topics: autotuning, tvm-ffi specifics, LLVM linking,
  HIP/ROCm, WebGPU/Metal/SPIR-V.

This phase **is not**:
- A backlog to drain.
- A place to silently expand the template's surface area.
- A way to bypass the draft-first discipline of Phase 2.
- A re-opening of earlier phases.
