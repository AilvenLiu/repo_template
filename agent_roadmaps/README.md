# Agent Roadmaps

This directory is a temporary workspace for multi-session roadmaps.

## Current State

No roadmap is active in the Agent Foundry source repository.

## Rules

- Roadmap files under `agent_roadmaps/` are operational state, not durable project documentation.
- Durable files outside `agent_roadmaps/` MUST NOT include legacy numbered roadmap labels or roadmap-phase identifiers.
- A roadmap may keep completed phases while later phases are still in flight.
- Once every phase in the active roadmap is completed, delete the entire temporary roadmap workspace and return this directory to its empty placeholder state.
- If no roadmap is active, agents must proceed without roadmap-specific authority files.

## Placeholder Structure

```text
agent_roadmaps/
  README.md
```
