# Roadmap Awareness Constraints

> **This document defines mandatory roadmap awareness and management constraints for all AI agents.**
> These rules apply to both Python and C++/CUDA projects.
> Violations are considered critical failures.

## Overview

This document establishes the requirements for roadmap awareness at session start,
roadmap creation triggers, execution discipline, and authority hierarchy. Roadmaps
are used to manage complex, multi-session tasks with long-lived constraints.

## 1. Mandatory Roadmap Awareness (Startup Requirement)

### 1.1 Always Check for Active Roadmaps

**At the beginning of EVERY session**, the agent MUST:

1. Inspect the `agent_roadmaps/` directory
2. Read `agent_roadmaps/README.md`
3. Scan for `phase-*/roadmap.yml` files under each project directory in `agent_roadmaps/`
4. Determine whether there is an **active, unfinished phase**

This check is MANDATORY and MUST NOT be skipped.

### 1.2 Behavior When Active Phase Exists

If an active phase exists, the agent MUST NOT:
- Start unrelated work
- Propose parallel large tasks
- Redefine scope or architecture outside the roadmap

If an active phase exists, the agent MUST:
- Follow the active phase's `prompt.md`
- Operate strictly within its defined current phase/task
- Update execution state via the active phase's `roadmap.yml` and session handoff files
- Verify that the current git branch matches the active phase branch (`roadmap/<phase-folder-name>`)

## 2. Mandatory Roadmap Creation Trigger

The agent MUST proactively ask the user whether to create a new roadmap **before proceeding**
if a requested task meets **any** of the following criteria:

### 2.1 Roadmap Creation Criteria

Create a roadmap when the task:

1. **Cannot be confidently completed within 1-2 sessions**
2. **Involves system-wide refactor, architectural change, or invariant-sensitive logic**
3. **Requires long-lived constraints across sessions**
4. **Contains multiple dependent phases, steps, or rollback risks**

### 2.2 Roadmap Creation Protocol

If the user agrees to start a roadmap, the agent MUST:

1. Create a new project subdirectory under `agent_roadmaps/`
   - Use descriptive name: `agent_roadmaps/<project-name>/`
   - Follow naming convention: lowercase with hyphens

2. Within the project directory, create **phase folders** for each phase:
   - Phase folder naming: `phase-0-<short-description>/`, `phase-1-<short-description>/`, etc.
   - Each phase folder MUST contain:
     - `prompt.md` - Phase-specific prompt and objectives
     - `INVARIANTS.md` - Immutable constraints and rules for this phase
     - `ROADMAP.md` - Human-readable roadmap description for this phase
     - `roadmap.yml` - Structured phase definition
     - `sessions/` - Directory for session handoff files

3. STOP and wait for confirmation **before implementing production code**

### 2.3 When NOT to Create a Roadmap

Do NOT create a roadmap for:
- Simple, single-session tasks
- Trivial changes (typos, formatting)
- Well-understood, routine operations

### 2.4 Phase Branching Strategy

Each roadmap phase MUST be worked on a dedicated git branch. The following rules apply:

1. **Branch per phase**: Each phase MUST have its own branch named `roadmap/<phase-folder-name>`
   - Example: `roadmap/phase-0-baseline`, `roadmap/phase-1-refactor`

2. **Branch verification**: Before making any code changes, the agent MUST verify that the current git branch matches the active phase's branch (`roadmap/<phase-folder-name>`). If it does not match, the agent MUST stop and correct the branch before proceeding.

3. **Phase completion**: When a phase is complete, the agent MUST open a PR/MR to merge the phase branch into the base branch. The phase branch MUST NOT be merged by the agent directly.

4. **Next phase activation**: The next phase may only be activated after:
   - The previous phase's PR is merged into the base branch
   - The agent switches back to the base branch
   - A new branch `roadmap/<next-phase-folder>` is created from the base branch

5. **No direct base-branch commits**: The agent MUST NOT commit phase work directly to the base branch (`master`, `main`, or `develop`).

## 3. Roadmap Execution Discipline

### 3.1 Treating Phase Documents as Frozen Contracts

When operating under an active phase, the agent MUST:

- Treat the active phase's documents (`prompt.md`, `INVARIANTS.md`, `ROADMAP.md`) as **frozen contracts** for that phase
  - Do not reinterpret objectives
  - Do not redesign architecture
  - Do not change scope
  - Follow the plan as written

- NOT reinterpret or redesign objectives unless explicitly instructed
- NOT advance phases or tasks implicitly

- Update execution state only via:
  - The active phase's `roadmap.yml` - Update phase status, progress
  - A new session handoff file in the active phase's `sessions/`

### 3.2 Handling Blockages

If blocked, the agent MUST:
- Report the blockage immediately
- Explain the constraint preventing progress
- Propose solutions within roadmap constraints
- NOT work around constraints without approval

### 3.3 Session Handoff Requirements

At the end of EVERY session working on a roadmap phase, the agent MUST:

1. Create a new handoff file in the active phase's `sessions/` directory
   (`agent_roadmaps/<project-name>/<phase-folder>/sessions/`)
   - Filename: `session-YYYY-MM-DD-HH-MM.md`
   - Include: work completed, decisions made, next steps, blockers

2. Update the active phase's `roadmap.yml` with current state

3. Commit both files together
   - Use commit message: `chore(roadmap): session handoff YYYY-MM-DD`

### 3.4 Phase Completion

When a phase is complete, the agent MUST:
1. Mark the phase as complete in its `roadmap.yml`
2. Create a final session handoff documenting completion in the phase's `sessions/` directory
3. Open a PR/MR to merge the phase branch (`roadmap/<phase-folder-name>`) into the base branch
4. Wait for the PR to be merged before activating the next phase
5. After merge: switch to base branch, pull latest, then create `roadmap/<next-phase-folder>` branch
6. Update `agent_roadmaps/README.md` to reflect phase completion and next active phase

## 4. Roadmap Template Compliance (MANDATORY)

### 4.1 Template Structure Requirements

When creating or modifying a phase's `roadmap.yml`, the agent MUST:

1. **Follow exact schema**:
   - Phase IDs: `phase-0`, `phase-1`, etc. (format: `phase-\d+`)
   - Task IDs: `task-0-1`, `task-1-1`, etc. (format: `task-\d+-\d+`)
   - Status values: ONLY `pending`, `active`, `completed`, `blocked`

2. **Use only template fields**:
   - Allowed fields per task: `id`, `title`, `status`, `notes` (optional)
   - Allowed fields per phase: `id`, `title`, `status`, `tasks`

3. **Ensure task atomicity**:
   - Each task must be completable in 1-2 hours maximum
   - Tasks should have single, clear objective

4. **Provide detailed descriptions**:
   - Task titles: 10-80 characters, specific and actionable
   - Avoid vague descriptions like "Fix bugs", "Update code"

## 5. Summary

**Key Rules:**

1. **ALWAYS check for active phases at session start** (scan `phase-*/roadmap.yml` under each project in `agent_roadmaps/`)
2. **NEVER skip roadmap awareness check**
3. **ASK before creating roadmap for complex tasks**
4. **FOLLOW the active phase as a frozen contract**
5. **VALIDATE each phase's `roadmap.yml` before finalizing**
6. **USE ONLY template fields, no custom additions**
7. **ENSURE tasks are atomic (1-2 hours max)**
8. **UPDATE phase state via its `roadmap.yml` and `sessions/` handoffs**
9. **REPORT blockages, do not work around constraints**
10. **WORK on a dedicated `roadmap/<phase-folder-name>` branch per phase**
11. **NEVER commit phase work directly to the base branch**
