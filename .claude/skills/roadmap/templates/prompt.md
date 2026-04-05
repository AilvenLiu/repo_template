You are operating under the roadmap phase `<PHASE_FOLDER_NAME>`.

Before doing anything else, you MUST:

1. Read and obey:
   - agent_roadmaps/README.md
   - agent_roadmaps/<PHASE_FOLDER_NAME>/INVARIANTS.md
   - agent_roadmaps/<PHASE_FOLDER_NAME>/ROADMAP.md
   - agent_roadmaps/<PHASE_FOLDER_NAME>/roadmap.yml
   - The latest file in agent_roadmaps/<PHASE_FOLDER_NAME>/sessions/

2. Treat the following authority order as absolute:
   1) INVARIANTS.md
   2) ROADMAP.md
   3) roadmap.yml
   4) session handoff notes
   5) this prompt

3. Identify the current active task from roadmap.yml.
   You MUST operate ONLY on that task.

4. Branch enforcement:
   - You MUST work on the branch `roadmap/<PHASE_FOLDER_NAME>`.
   - If you are not on that branch, create it from the base branch
     and switch to it before making any changes.
   - When this phase is complete, open a PR/MR from
     `roadmap/<PHASE_FOLDER_NAME>` into the base branch.

Rules of operation:

- Do NOT redefine objectives, scope, or architecture.
- Do NOT advance tasks implicitly.
- If blocked, report the blocker instead of working around it.
- Record all progress by:
  - Updating roadmap.yml appropriately
  - Writing a session handoff file at the end of this session

Assume no prior memory.
Assume no implicit permissions.

When in doubt, STOP and ask the user.
