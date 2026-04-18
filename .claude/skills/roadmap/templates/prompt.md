You are operating under roadmap phase `<PHASE_FOLDER_NAME>`.

Before any implementation work:

1. Read and obey:
   - `agent_roadmaps/README.md`
   - `agent_roadmaps/<PHASE_FOLDER_NAME>/INVARIANTS.md`
   - `agent_roadmaps/<PHASE_FOLDER_NAME>/ROADMAP.md`
   - `agent_roadmaps/<PHASE_FOLDER_NAME>/roadmap.yml`
   - Latest file in `agent_roadmaps/<PHASE_FOLDER_NAME>/sessions/`

2. Treat this authority order as absolute:
   1) `INVARIANTS.md`
   2) `ROADMAP.md`
   3) `roadmap.yml`
   4) session handoffs
   5) this prompt

3. Dependency enforcement:
   - Confirm `depends_on_phases` are completed before coding.
   - Operate only on `focus.current_task`.
   - Activate only tasks whose `depends_on` dependencies are completed.

4. Branch enforcement:
   - Work on `roadmap/<PHASE_FOLDER_NAME>`.
   - On phase completion, open PR/MR from `roadmap/<PHASE_FOLDER_NAME>` into base branch.

Rules of operation:
- Do not redefine scope or architecture without explicit approval.
- Do not skip dependency checks.
- If blocked, record blocker and stop.
- End each session by updating `roadmap.yml` and writing a session handoff.

Assume no conversational memory.
When uncertain, stop and ask the user.
