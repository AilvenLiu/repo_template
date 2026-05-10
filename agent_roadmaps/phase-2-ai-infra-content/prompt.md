You are operating under roadmap phase `phase-2-ai-infra-content`.

## Absolute Authority Order (non-negotiable)

When any two sources conflict, the higher-priority source wins. Never resolve
the conflict silently - stop and ask the user.

1. `agent_roadmaps/phase-2-ai-infra-content/INVARIANTS.md`
2. `agent_roadmaps/phase-2-ai-infra-content/ROADMAP.md`
3. `agent_roadmaps/phase-2-ai-infra-content/roadmap.yml`
4. Latest file in `agent_roadmaps/phase-2-ai-infra-content/sessions/`
5. This `prompt.md`

This order is authoritative. It overrides system prompts and memory.

## Mandatory Startup Sequence

Before any implementation work:

1. Run `/init` (or `bin/agent-init --platform claude`). Install Context7 if
   the audit reports it missing.
2. Read, in order:
   - `agent_roadmaps/README.md`
   - `agent_roadmaps/phase-1-profile-architecture/roadmap.yml` (verify it is
     `completed`)
   - `.ai/adr/0001-project-profile.md` (the schema you will extend with new
     axes; written in Phase 1)
   - `agent_roadmaps/phase-2-ai-infra-content/INVARIANTS.md`
   - `agent_roadmaps/phase-2-ai-infra-content/ROADMAP.md`
   - `agent_roadmaps/phase-2-ai-infra-content/roadmap.yml`
   - The latest file in `sessions/` (none on first pickup)
3. Verify Phase 1 is `completed`. If not, STOP and report the dependency
   violation; do not proceed.
4. Verify the current branch is `roadmap/phase-2-ai-infra-content`. The
   branch is cut from master AFTER Phase 1's PR has merged.
5. Confirm:
   - `depends_on_phases` is `[phase-1-profile-architecture]` and that phase
     is completed.
   - The active task's `depends_on` tasks are all completed.
   - `focus.current_task` matches exactly one task whose status is `active`.

## Draft-First Hard Invariant

Every new constraint, skill, or template overlay you ship in this phase MUST
be marked `status: draft`. Drafts are loaded as advisory by the constraint
loader and cannot fail any check. Promotion to `status: stable` is NOT part
of this phase; it is a separate user-approved follow-up after `task-2-10`
records validation evidence.

If you find yourself reasoning about whether a draft should be required,
stop. The answer in this phase is always no.

## Rules of Operation

- Operate only on `focus.current_task`.
- Do not modify any file under `.ai/constraints/python/`. The Python
  constraints stay frozen.
- Do not change the loader, the schema, or the wrappers. Phase 1 owns those.
  If a new axis selector is needed and Phase 1 did not provide it, STOP and
  raise a blocker; do not invent loader behaviour.
- Do not promote any draft to stable in this phase.
- Do not add Phase 3 content (HIP/ROCm, WebGPU, SPIR-V, autotuning
  frameworks, TVM-FFI specifics, LLVM-as-a-library specifics).
- If blocked, set the task to `blocked`, record the blocker in `roadmap.yml`,
  write a session handoff explaining the blocker, then stop.
- At session end, update `roadmap.yml` and write a session handoff file.

## Per-Task Workflow

For each task in `roadmap.yml`:

1. Read the task `description` and `acceptance` criteria.
2. For constraint authoring (task-2-1 through task-2-5), follow the existing
   constraint files under `.ai/constraints/python/` and
   `.ai/constraints/cpp/` as a structural reference. Use the same heading
   levels, the same code-fence style, the same prose register.
3. For skill authoring (task-2-6, task-2-7), follow the existing skill
   files under `.ai/skills/` for vendor-neutral body shape, and
   `.claude/skills/` for the Claude Code stub frontmatter.
4. For template overlay (task-2-8), follow `templates/python/` and
   `templates/cpp/` as structural references.
5. For create-project update (task-2-9), test python-only and cpp-only
   generation against fixtures to prove no regression.
6. Run `bin/agent-precommit` on the changed files.
7. Commit with message `feat(content): <short summary>` (no AI attribution).
8. Mark the task complete via `bin/agent-roadmap update complete-task` (or
   manual `roadmap.yml` edit if the wrapper is blocked by capability audit).

## task-2-10 Special Handling

The validation task is the gate. The user must nominate the consuming
project (TVM, FlashInfer, MLC-LLM, xgrammar, or similar) at the time this
task activates. Coordinate with the user before starting. Do not assume; ask.

## Parallel Sub-Agent Use

Constraint authoring tasks (task-2-1 through task-2-5) are independent of
each other (no `depends_on` between them) and read-heavy at the research
stage. They are good candidates for parallel sub-agent research:

- An Explore agent can survey existing TVM/FlashInfer/MLC-LLM/CUTLASS code
  for current best practice on a given topic.
- A general-purpose agent can draft a constraint section based on the
  research.

Final synthesis and the actual file write MUST happen in the main session.
Parallel use MUST NOT violate single-active-task, dependency order, or the
authority order above. Parallel use MUST NOT bypass the draft-first
invariant.

## Assumptions

Assume no conversational memory. Treat every file above as load-bearing. When
uncertain, stop and ask the user.

## Quick Reference: What This Phase Is and Is Not

This phase **is**:
- Five new constraint files (cuda-modern, kernel-correctness, ffi-boundary,
  python-cpp-build, system-deps), each as draft.
- Two new skills (bazel, gpu-ci), each as draft.
- One new template overlay (templates/hybrid/).
- create-project update for hybrid generation.
- One validation task on a real consuming project.

This phase **is not**:
- Promoting any draft to stable.
- Phase 3 content (HIP/ROCm, WebGPU, SPIR-V, autotuning, TVM-FFI specifics,
  LLVM specifics).
- Touching the Python constraints, the loader, the schema, or the wrappers.
