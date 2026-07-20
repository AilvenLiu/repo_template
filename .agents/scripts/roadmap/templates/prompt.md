You are operating under roadmap phase `<PHASE_FOLDER_NAME>`.

## Repository-Local Precedence

When any two sources conflict, higher-priority source wins. Never resolve the
conflict silently — stop and ask the user.

1. `agent_roadmaps/<PHASE_FOLDER_NAME>/INVARIANTS.md`
2. `agent_roadmaps/<PHASE_FOLDER_NAME>/roadmap.yml` for current execution state
3. `agent_roadmaps/<PHASE_FOLDER_NAME>/ROADMAP.md`
4. Latest file in `agent_roadmaps/<PHASE_FOLDER_NAME>/sessions/`
5. This `prompt.md`

This order resolves only repository-controlled guidance. It does not supersede
higher-priority platform or tool requirements. Current repository state takes
precedence over stale conversational assumptions.

## Mandatory Startup Sequence

Before any implementation work:

1. Read, in order:
   - `agent_roadmaps/README.md`
   - `agent_roadmaps/<PHASE_FOLDER_NAME>/INVARIANTS.md`
   - `agent_roadmaps/<PHASE_FOLDER_NAME>/ROADMAP.md`
   - `agent_roadmaps/<PHASE_FOLDER_NAME>/roadmap.yml`
   - Latest file in `agent_roadmaps/<PHASE_FOLDER_NAME>/sessions/`

2. Verify branch is `roadmap/<PHASE_FOLDER_NAME>`.

3. Confirm:
   - `depends_on_phases` are all completed
   - The active task's `depends_on` tasks are all completed
   - `focus.current_task` matches exactly one active task

## Rules of Operation

- Operate only on `focus.current_task`. Do not prefetch or speculate on later tasks.
- Do not redefine scope or architecture without explicit user approval.
- Do not skip or reorder dependencies.
- If blocked, set the task to `blocked`, record the blocker in `roadmap.yml`, and stop.
- At session end, update `roadmap.yml` and write a session handoff file.

## Parallel Sub-Agent Use (when applicable)

If the active task decomposes into independent, read-heavy or research-heavy
sub-tasks, you SHOULD explicitly launch an agentic team in parallel rather than
executing sequentially. See `.agents/constraints/common/agentic-team.md` for the
full policy.

Parallelisation MUST NOT violate:
- single-active-task rule (one task active per phase)
- dependency order (`depends_on`)
- the authority order above

## Assumptions

Assume no conversational memory. Treat every file above as load-bearing.
When uncertain, stop and ask the user.
