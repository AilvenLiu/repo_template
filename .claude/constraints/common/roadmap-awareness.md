# Roadmap Awareness Constraints

> **This document defines mandatory roadmap awareness and management constraints for all AI agents.**
> These rules apply to both Python and C++/CUDA projects.
> Violations are considered critical failures.

## Overview

This document establishes the requirements for roadmap awareness at session start,
roadmap creation triggers, execution discipline, and authority hierarchy. Roadmaps
are used to manage complex, multi-session tasks with long-lived constraints.

## 1. Authority Hierarchy

Claude Code MUST obey the following authority order:

1. `agent_roadmaps/<active>/INVARIANTS.md` (if an active roadmap exists)
2. `agent_roadmaps/README.md`
3. `CLAUDE.md`
4. `CONTRIBUTING.md`
6. Session-level prompts or instructions

**If any conflict exists, higher authority always wins.**

This hierarchy ensures that:
- Active roadmap constraints override all other instructions
- Roadmap system rules are consistently applied
- Language-specific constraints are respected
- Project conventions are followed
- Code-level decisions are honored
- Session instructions are lowest priority

## 2. Mandatory Roadmap Awareness (Startup Requirement)

### 2.1 Always Check for Active Roadmaps

**At the beginning of EVERY session**, Claude Code MUST:

1. Inspect the `agent_roadmaps/` directory
2. Read `agent_roadmaps/README.md`
3. Determine whether there is an **active, unfinished roadmap**

This check is MANDATORY and MUST NOT be skipped.

### 2.2 Behavior When Active Roadmap Exists

If an active roadmap exists, Claude Code MUST NOT:
- Start unrelated work
- Propose parallel large tasks
- Redefine scope or architecture outside the roadmap

If an active roadmap exists, Claude Code MUST:
- Follow the active roadmap's `prompt.md`
- Operate strictly within its defined current phase/task
- Update execution state via `roadmap.yml` and session handoff files

**Skipping this check is forbidden.**

### 2.3 Why This Matters

Roadmap awareness ensures:
- Continuity across sessions (agents have no memory between sessions)
- Adherence to long-lived constraints and invariants
- Prevention of scope creep and conflicting work
- Proper tracking of multi-phase projects
- Clear handoff between sessions

## 3. Mandatory Roadmap Creation Trigger

Claude Code MUST proactively ask the user whether to create a new roadmap **before proceeding**
if a requested task meets **any** of the following criteria:

### 3.1 Roadmap Creation Criteria

Create a roadmap when the task:

1. **Cannot be confidently completed within 1-2 Claude Code sessions**
   - Requires multiple work sessions
   - Has uncertain completion time
   - Involves exploratory work

2. **Involves system-wide refactor, architectural change, or invariant-sensitive logic**
   - Changes core architecture
   - Modifies fundamental assumptions
   - Affects multiple subsystems
   - Requires careful coordination

3. **Requires long-lived constraints across sessions**
   - Has rules that must persist
   - Needs consistent behavior over time
   - Involves decisions that affect future work

4. **Contains multiple dependent phases, steps, or rollback risks**
   - Has sequential dependencies
   - Requires checkpoints
   - Needs rollback capability
   - Has high risk of failure

### 3.2 Roadmap Creation Protocol

If the user agrees to start a roadmap, Claude Code MUST:

1. Create a new subdirectory under `agent_roadmaps/`
   - Use descriptive name: `agent_roadmaps/<project-name>/`
   - Follow naming convention: lowercase with hyphens

2. Populate it with all **required files and structure** as defined in `agent_roadmaps/README.md`:
   - `prompt.md` - Main roadmap prompt and objectives
   - `INVARIANTS.md` - Immutable constraints and rules
   - `roadmap.yml` - Structured roadmap definition
   - `sessions/` - Directory for session handoff files
   - Other files as specified in roadmap template

3. STOP and wait for confirmation **before implementing production code**
   - Review roadmap structure with user
   - Confirm objectives and phases
   - Get explicit approval to proceed

**Partial or informal roadmap creation is not allowed.**

### 3.3 When NOT to Create a Roadmap

Do NOT create a roadmap for:
- Simple, single-session tasks
- Trivial changes (typos, formatting)
- Well-understood, routine operations
- Tasks with clear, immediate completion

## 4. Roadmap Execution Discipline

### 4.1 Treating Roadmaps as Frozen Contracts

When operating under an active roadmap, Claude Code MUST:

- Treat roadmap documents as **frozen contracts**
  - Do not reinterpret objectives
  - Do not redesign architecture
  - Do not change scope
  - Follow the plan as written

- NOT reinterpret or redesign objectives unless explicitly instructed
  - User must explicitly request changes
  - Changes must be documented
  - Updated roadmap must be committed

- NOT advance phases or tasks implicitly
  - Complete current phase fully
  - Get user confirmation before advancing
  - Update roadmap state explicitly

- Update execution state only via:
  - `roadmap.yml` - Update phase status, progress
  - A new session handoff file in `sessions/` - Document session work

### 4.2 Handling Blockages

If blocked, Claude Code MUST:
- Report the blockage immediately
- Explain the constraint preventing progress
- Propose solutions within roadmap constraints
- NOT work around constraints without approval

**Working around roadmap constraints is forbidden.**

### 4.3 Session Handoff Requirements

At the end of EVERY session working on a roadmap, Claude Code MUST:

1. Create a new handoff file in `agent_roadmaps/<active>/sessions/`
   - Filename: `session-YYYY-MM-DD-HH-MM.md`
   - Include: work completed, decisions made, next steps, blockers

2. Update `roadmap.yml` with current state
   - Mark completed tasks
   - Update phase status
   - Note any changes to timeline

3. Commit both files together
   - Use commit message: `chore(roadmap): session handoff YYYY-MM-DD`

### 4.4 Roadmap Completion

When a roadmap is complete, Claude Code MUST:

1. Mark roadmap as complete in `roadmap.yml`
2. Create final session handoff documenting completion
3. Ask user if roadmap directory should be archived
4. Update `agent_roadmaps/README.md` to reflect completion

## 5. Roadmap File Structure

### 5.1 Required Files

Every roadmap MUST contain:

- **prompt.md**: Main roadmap prompt
  - Objectives and goals
  - Success criteria
  - Phases and tasks
  - Timeline estimates

- **INVARIANTS.md**: Immutable constraints
  - Rules that cannot be violated
  - Architectural decisions
  - Non-negotiable requirements
  - Highest authority in the system

- **roadmap.yml**: Structured roadmap data
  - Machine-readable format
  - Phase definitions
  - Task tracking
  - Status and progress

- **sessions/**: Session handoff directory
  - One file per session
  - Chronological record
  - Enables continuity

### 5.2 Optional Files

Roadmaps MAY contain:

- **ARCHITECTURE.md**: Architectural decisions and diagrams
- **TESTING.md**: Testing strategy and requirements
- **DEPLOYMENT.md**: Deployment procedures
- **ROLLBACK.md**: Rollback procedures
- **NOTES.md**: Additional notes and context

## 6. Examples

### 6.1 Example: Starting a Session with Active Roadmap

```
Session Start:
1. Check agent_roadmaps/ directory
2. Find active roadmap: agent_roadmaps/api-refactor/
3. Read agent_roadmaps/README.md
4. Read agent_roadmaps/api-refactor/prompt.md
5. Read agent_roadmaps/api-refactor/INVARIANTS.md
6. Read agent_roadmaps/api-refactor/roadmap.yml
7. Read latest session handoff
8. Inform user: "Active roadmap detected: api-refactor, Phase 2/4"
9. Continue work within roadmap constraints
```

### 6.2 Example: Deciding to Create a Roadmap

```
User: "I want to refactor the entire authentication system to use OAuth2"

Agent Analysis:
- Multi-session task: YES (complex refactor)
- Architectural change: YES (fundamental auth change)
- Long-lived constraints: YES (security requirements)
- Multiple phases: YES (planning, implementation, testing, migration)

Agent Response:
"This task meets the criteria for roadmap creation:
- It's a system-wide architectural change
- It will require multiple sessions
- It has security-sensitive constraints
- It involves multiple phases (planning, implementation, testing, migration)

Would you like me to create a roadmap for this refactor?"
```

### 6.3 Example: Roadmap Execution

```
Current State:
- Active roadmap: agent_roadmaps/oauth2-refactor/
- Current phase: Phase 2 - Implementation
- Current task: Implement token validation

Agent Behavior:
- Follow INVARIANTS.md constraints (e.g., "All tokens must be validated server-side")
- Work only on current task
- Do not advance to Phase 3 without user approval
- Update roadmap.yml when task is complete
- Create session handoff at end of session
```

## 7. Summary

**Key Rules:**

1. **ALWAYS check for active roadmaps at session start**
2. **NEVER skip roadmap awareness check**
3. **ASK before creating roadmap for complex tasks**
4. **FOLLOW roadmap as frozen contract**
5. **UPDATE roadmap state via roadmap.yml and session handoffs**
6. **REPORT blockages, do not work around constraints**
7. **RESPECT authority hierarchy (INVARIANTS.md is highest)**

**Enforcement:**
- These rules are mandatory and non-negotiable
- Violations indicate agent is operating outside its mandate
- Session should be terminated if violations occur
