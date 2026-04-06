# Agent Roadmaps - Phase Series Overview

**This document is authoritative for all AI agents (including Claude Code) operating in this repository.**
Any violation of the rules defined here is considered a critical agent failure.

Read this file at the start of every session, without exception.


## 1. Purpose of agent_roadmaps/

The `agent_roadmaps/` directory is the **single source of truth** for:
- Whether the repository is currently executing a **large, system-level, multi-session task series**
- Which phase (if any) is **currently active**
- How AI agents must **initialize, constrain, execute, and hand off** work across sessions

This mechanism exists to **prevent context loss, decision drift, and architectural regression** when tasks exceed one or two sessions.


## 2. Phase Series

Each phase is a self-contained folder. Phases MUST be completed sequentially.

1. `phase-0-<name>/` -- <brief description> -- status: pending | active | completed
2. `phase-1-<name>/` -- <brief description> -- status: pending | active | completed
3. `phase-2-<name>/` -- <brief description> -- status: pending | active | completed

**Active phase**: `<PHASE_FOLDER_NAME>` (update this when the active phase changes)


## 3. Branching Protocol

Each phase has a dedicated git branch:

- Branch name: `roadmap/<phase-folder-name>`
- Created from: the project's base branch (e.g., `main` or `master`)
- Merged via: PR/MR into the base branch when the phase is complete

Rules:
- Work for phase N MUST only happen on `roadmap/phase-N-<name>`.
- Do NOT commit phase work directly to the base branch.
- The next phase MUST NOT be activated until the previous phase's PR/MR is merged.


## 4. Operating Rules

- Read this file at the start of every session.
- Work ONLY inside the currently active phase folder.
- Do NOT start, create, or propose work on a non-active phase.
- Do NOT activate the next phase until the current phase's PR/MR is merged into the base branch.
- At most ONE phase may be active at any time.


## 5. Per-Phase Folder Structure

Each phase folder contains:

```
agent_roadmaps/
-- <phase-folder-name>/
    |-- INVARIANTS.md   # Non-negotiable constraints for this phase
    |-- ROADMAP.md      # Long-form execution guide for this phase
    |-- roadmap.yml     # Machine-readable execution state for this phase
    |-- prompt.md       # Session initialization prompt (copy-paste only)
    -- sessions/        # Session handoff records
```


## 6. Agent Startup Checklist (MANDATORY)

Every session MUST:

1. Read this `agent_roadmaps/README.md`.
2. Identify which phase is currently active (see Section 2).
3. If a phase is active:
   - Enter that phase's folder.
   - Read its `INVARIANTS.md`, `ROADMAP.md`, `roadmap.yml`, and the latest file in `sessions/`.
   - Follow `prompt.md` to initialize the session.
   - Confirm you are on the correct branch (`roadmap/<phase-folder-name>`).
4. If no phase is active:
   - Proceed normally, or
   - Ask the user whether to activate the next phase if prior phase's PR/MR has been merged.


## 7. Final Enforcement Rule

> **If an agent is unsure whether an action is allowed,**
> it MUST stop and ask the user.

Silent assumption is forbidden.
