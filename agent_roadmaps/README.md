# Agent Roadmaps - Authoritative Guide

This document is authoritative for all AI agents operating in this repository.
Violating these roadmap rules is a critical failure.

## 1. Purpose

`agent_roadmaps/` is the single source of truth for long-running, multi-session
work that requires durable constraints and explicit dependency management.

## 2. Global Rules

- At most one phase may be active at any time.
- Every phase must live in `agent_roadmaps/phase-N-name/`.
- Phase and task dependencies must be declared explicitly in `roadmap.yml`.
- Work must happen on branch `roadmap/<phase-folder-name>`.

## 3. Active Phase Status (Update Every Session)

- **Active phase**: None
- **Path**: N/A
- **Current task**: N/A
- **Status**: inactive

When a phase becomes active, update this section immediately.

## 4. Required Phase Structure

```text
agent_roadmaps/
  phase-N-name/
    INVARIANTS.md
    ROADMAP.md
    roadmap.yml
    prompt.md
    sessions/
```

## 5. Canonical State Fields

Each phase `roadmap.yml` must define:
- `phase`
- `name`
- `status` (`active`, `blocked`, `started_at`, `completed_at`)
- `depends_on_phases`
- `tasks` (with task-level `depends_on`)
- `focus` (`current_task`, `notes`)

## 6. Startup Checklist

At every session start:
1. Read this file.
2. Detect active phase.
3. If active, read its `INVARIANTS.md`, `ROADMAP.md`, `roadmap.yml`, and latest handoff.
4. Verify branch is `roadmap/<active-phase-folder>`.
5. Verify dependencies are satisfied before implementing.

## 7. Session-End Checklist

For roadmap sessions:
1. Update `roadmap.yml` task/phase state.
2. Create `sessions/session-YYYY-MM-DD-HH-MM.md`.
3. Record work completed, decisions, blockers, and next steps.

## 8. Enforcement

If unsure whether an action is allowed, stop and ask the user.
