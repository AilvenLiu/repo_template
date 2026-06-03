# Agent Roadmaps

This directory is a temporary workspace for multi-session roadmaps.

## Current State

No roadmap is active in the template repository.

## Rules

- Roadmap files under `agent_roadmaps/` are operational state, not durable project documentation.
- Durable files outside `agent_roadmaps/` MUST NOT include legacy numbered roadmap labels or roadmap-step identifiers.
- A roadmap may keep completed steps while later steps are still in flight.
- Once every step in the active roadmap is completed, delete the entire temporary roadmap workspace and return this directory to its empty placeholder state.
- If no roadmap is active, agents must proceed without roadmap-specific authority files.

## Placeholder Structure

```text
agent_roadmaps/
  README.md
```
