# Agent Roadmaps - Dependency-Aware Step Series

**This document is authoritative for all AI agents operating in this repository.**
Any violation of the rules defined here is a critical failure.

Read this file at the start of every session.

## 1. Roadmap Overview

- **Roadmap name**: `<ROADMAP_TITLE>`
- **Roadmap slug**: `<ROADMAP_SLUG>`
- **Description**:
  <ROADMAP_DESCRIPTION>

## 2. Step Series Status

At most one step may be active at any time.

| Step | Folder | Status | Depends On |
|-------|--------|--------|------------|
<STEP_TABLE_ROWS>

**Active step**: `<ACTIVE_STEP_FOLDER>`

## 3. Dependency Graph

```text
<STEP_DEP_GRAPH>
```

Rules:
- A step may be activated only when every `depends_on_steps` entry is completed.
- The step branch MUST be `roadmap/<step-folder-name>`.
- Next step activation is blocked until previous step PR/MR is merged.

## 4. Branching Protocol

Each step has a dedicated git branch:
- Branch name: `roadmap/<step-folder-name>`
- Created from: base branch (`main`, `master`, or project default)
- Merged via: PR/MR after step completion

## 5. Per-Step Folder Structure

```text
agent_roadmaps/
  <step-folder-name>/
    INVARIANTS.md
    ROADMAP.md
    roadmap.yml
    prompt.md
    sessions/
```

## 6. Startup Checklist (Mandatory)

At every session start:
1. Read this file.
2. Identify the active step.
3. Read active step `INVARIANTS.md`, `ROADMAP.md`, `roadmap.yml`, and latest session handoff.
4. Confirm branch is `roadmap/<active-step-folder-name>`.
5. Confirm active step dependencies are satisfied before implementation.

## 7. Session Handoff Rules

For roadmap sessions:
1. Create `sessions/session-YYYY-MM-DD-HH-MM.md`
2. Include work completed, decisions, blockers, next steps
3. Update `roadmap.yml`
4. Commit handoff and roadmap state together

## 8. Final Enforcement Rule

If uncertain whether an action is allowed, stop and ask the user.
