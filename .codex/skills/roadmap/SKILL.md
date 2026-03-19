---
name: roadmap
description: Manage roadmap-aware workflows using the existing roadmap files under agent_roadmaps/.
---

# Codex Roadmap

## Startup Protocol

1. Read `agent_roadmaps/README.md`
2. If an active roadmap exists, read in order:
- `INVARIANTS.md`
- `prompt.md`
- `roadmap.yml`
- latest `sessions/session-*.md`

## Session Handoff Requirements

At end of each roadmap session:

1. Create `agent_roadmaps/<active>/sessions/session-YYYY-MM-DD-HH-MM.md`
2. Include sections:
- Work Completed
- Current State
- Next Steps
- Notes
3. Update `agent_roadmaps/<active>/roadmap.yml`
