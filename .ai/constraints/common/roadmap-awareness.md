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
3. Determine whether there is an **active, unfinished roadmap**

This check is MANDATORY and MUST NOT be skipped.

### 1.2 Behavior When Active Roadmap Exists

If an active roadmap exists, the agent MUST NOT:
- Start unrelated work
- Propose parallel large tasks
- Redefine scope or architecture outside the roadmap

If an active roadmap exists, the agent MUST:
- Follow the active roadmap's `prompt.md`
- Operate strictly within its defined current phase/task
- Update execution state via `roadmap.yml` and session handoff files

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

1. Create a new subdirectory under `agent_roadmaps/`
   - Use descriptive name: `agent_roadmaps/<project-name>/`
   - Follow naming convention: lowercase with hyphens

2. Populate it with all **required files and structure** as defined in `agent_roadmaps/README.md`:
   - `prompt.md` - Main roadmap prompt and objectives
   - `INVARIANTS.md` - Immutable constraints and rules
   - `roadmap.yml` - Structured roadmap definition
   - `sessions/` - Directory for session handoff files

3. STOP and wait for confirmation **before implementing production code**

### 2.3 When NOT to Create a Roadmap

Do NOT create a roadmap for:
- Simple, single-session tasks
- Trivial changes (typos, formatting)
- Well-understood, routine operations

## 3. Roadmap Execution Discipline

### 3.1 Treating Roadmaps as Frozen Contracts

When operating under an active roadmap, the agent MUST:

- Treat roadmap documents as **frozen contracts**
  - Do not reinterpret objectives
  - Do not redesign architecture
  - Do not change scope
  - Follow the plan as written

- NOT reinterpret or redesign objectives unless explicitly instructed
- NOT advance phases or tasks implicitly

- Update execution state only via:
  - `roadmap.yml` - Update phase status, progress
  - A new session handoff file in `sessions/`

### 3.2 Handling Blockages

If blocked, the agent MUST:
- Report the blockage immediately
- Explain the constraint preventing progress
- Propose solutions within roadmap constraints
- NOT work around constraints without approval

### 3.3 Session Handoff Requirements

At the end of EVERY session working on a roadmap, the agent MUST:

1. Create a new handoff file in `agent_roadmaps/<active>/sessions/`
   - Filename: `session-YYYY-MM-DD-HH-MM.md`
   - Include: work completed, decisions made, next steps, blockers

2. Update `roadmap.yml` with current state

3. Commit both files together
   - Use commit message: `chore(roadmap): session handoff YYYY-MM-DD`

### 3.4 Roadmap Completion

When a roadmap is complete, the agent MUST:
1. Mark roadmap as complete in `roadmap.yml`
2. Create final session handoff documenting completion
3. Ask user if roadmap directory should be archived
4. Update `agent_roadmaps/README.md` to reflect completion

## 4. Roadmap Template Compliance (MANDATORY)

### 4.1 Template Structure Requirements

When creating or modifying roadmap.yml, the agent MUST:

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

1. **ALWAYS check for active roadmaps at session start**
2. **NEVER skip roadmap awareness check**
3. **ASK before creating roadmap for complex tasks**
4. **FOLLOW roadmap as frozen contract**
5. **VALIDATE roadmap.yml before finalizing**
6. **USE ONLY template fields, no custom additions**
7. **ENSURE tasks are atomic (1-2 hours max)**
8. **UPDATE roadmap state via roadmap.yml and session handoffs**
9. **REPORT blockages, do not work around constraints**
