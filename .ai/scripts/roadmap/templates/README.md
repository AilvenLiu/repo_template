# Agent Roadmaps - Dependency-Aware Phase Series

**This document is authoritative for all AI agents operating in this repository.**
Any violation of the rules defined here is a critical failure.

Read this file at the start of every session.

## 1. Roadmap Overview

- **Roadmap name**: `<ROADMAP_TITLE>`
- **Roadmap slug**: `<ROADMAP_SLUG>`
- **Description**:
  <ROADMAP_DESCRIPTION>

## 2. Phase Series Status

At most one phase may be active at any time.

| Phase | Folder | Status | Depends On |
|-------|--------|--------|------------|
<PHASE_TABLE_ROWS>

**Active phase**: `<ACTIVE_PHASE_FOLDER>`

## 3. Dependency Graph

```text
<PHASE_DEP_GRAPH>
```

Rules:
- A phase may be activated only when every `depends_on_phases` entry is completed.
- The phase branch MUST be `roadmap/<phase-folder-name>`.
- Next phase activation is blocked until previous phase PR/MR is merged.

## 4. Branching Protocol

Each phase has a dedicated git branch:
- Branch name: `roadmap/<phase-folder-name>`
- Created from: base branch (`main`, `master`, or project default)
- Merged via: PR/MR after phase completion

## 5. Per-Phase Folder Structure

```text
agent_roadmaps/
  <phase-folder-name>/
    INVARIANTS.md
    ROADMAP.md
    roadmap.yml
    prompt.md
    sessions/
```

## 6. Startup Checklist (Mandatory)

At every session start:
1. Read this file.
2. Identify the active phase.
3. Read active phase `INVARIANTS.md`, `ROADMAP.md`, `roadmap.yml`, and latest session handoff.
4. Confirm branch is `roadmap/<active-phase-folder-name>`.
5. Confirm active phase dependencies are satisfied before implementation.

## 7. Session Handoff Rules

For roadmap sessions:
1. Create `sessions/session-YYYY-MM-DD-HH-MM.md`
2. Include work completed, decisions, blockers, next steps
3. Update `roadmap.yml`
4. Commit handoff and roadmap state together

## 8. Final Enforcement Rule

If uncertain whether an action is allowed, stop and ask the user.
