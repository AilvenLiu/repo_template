---
name: roadmap
description: Manage roadmap-aware workflows using the existing roadmap files under agent_roadmaps/.
---

# Codex Roadmap

## Startup Protocol

1. Read `agent_roadmaps/README.md`
2. If an active phase exists (scan `phase-*/roadmap.yml` for `status.active: true`), read in order:
   - `agent_roadmaps/<active-phase>/INVARIANTS.md`
   - `agent_roadmaps/<active-phase>/prompt.md`
   - `agent_roadmaps/<active-phase>/roadmap.yml`
   - Latest `agent_roadmaps/<active-phase>/sessions/session-*.md`
3. Verify current branch matches `roadmap/<active-phase-folder>`

## Session Handoff Requirements

At end of each roadmap session:

1. Create `agent_roadmaps/<active-phase>/sessions/session-YYYY-MM-DD-HH-MM.md`
2. Include sections:
   - Work Completed
   - Current State
   - Next Steps
   - Notes
3. Update `agent_roadmaps/<active-phase>/roadmap.yml`

## Phase Branching

- Work on branch `roadmap/<phase-folder-name>`
- On phase completion: open a PR/MR targeting the base branch
- Do not activate the next phase until the previous phase PR is merged
