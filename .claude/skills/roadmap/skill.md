---
name: roadmap
description: Manage multi-session AI agent workflows using the agent_roadmaps system. Automatically checks for active roadmaps at session start. Use when starting a new session, creating roadmaps, or managing complex multi-phase tasks.
version: 1.0.0
---

# Agent Roadmaps Skill

This skill provides structured commands for managing multi-session AI agent workflows using the agent_roadmaps system. It enforces mandatory behaviors, validates state transitions, and ensures continuity across sessions.

## Requirements

This skill requires Python 3.9+ and the following dependencies:

```bash
pip3 install -r .claude/skills/roadmap/requirements.txt
```

Dependencies:
- PyYAML >= 6.0

## CRITICAL: Automatic Session-Start Check

**THIS IS NON-NEGOTIABLE:**

At the start of EVERY Claude Code session, before any other action, this skill MUST check for active roadmaps.

Run immediately:
```bash
python3 .claude/skills/roadmap/scripts/check.py
```

If an active roadmap is found (exit code 0):
1. Read all roadmap files in authority order (see below)
2. Load the current task context
3. Operate ONLY on the current focus task
4. Never skip or ignore the roadmap

If no active roadmap is found (exit code 1):
- Proceed normally, OR
- Ask user if task requires roadmap (see creation criteria below)

**Skipping this check is a critical agent failure.**

---

## Available Commands

### `/roadmap check`

Check for active roadmaps and display status.

**Usage:**
```bash
python3 .claude/skills/roadmap/scripts/check.py
```

**Output:**
- Active roadmap details (name, path, current phase/task)
- Or "No active roadmap" message

**When to use:**
- At session start (MANDATORY)
- Before creating a new roadmap
- To verify current roadmap status

---

### `/roadmap create <name> [description]`

Create a new roadmap directory structure.

**Usage:**
```bash
python3 .claude/skills/roadmap/scripts/create.py <roadmap-name> [description]
```

**Arguments:**
- `<roadmap-name>`: Required. Lowercase with hyphens (e.g., `api-v2-migration`)
- `[description]`: Optional. Brief description of roadmap purpose

**Behaviour:**
1. Verifies no active roadmap exists (enforces single-active rule)
2. Validates roadmap name format
3. Creates directory: `agent_roadmaps/<name>/`
4. Copies template files (INVARIANTS.md, ROADMAP.md, roadmap.yml, prompt.md)
5. Creates empty `sessions/` directory
6. Initialises roadmap.yml with provided name/description

**When to use:**
Create a roadmap when a task meets ANY of these criteria:
- Cannot be completed within 1-2 Claude Code sessions
- Involves system-wide refactor or architectural change
- Requires long-lived constraints that must survive context resets
- Has multiple dependent phases or non-trivial rollback risk

**Example:**
```bash
python3 .claude/skills/roadmap/scripts/create.py api-v2-migration "Migrate from API v1 to v2"
```

---

### `/roadmap status`

Display detailed status of active roadmap.

**Usage:**
```bash
python3 .claude/skills/roadmap/scripts/status.py
```

**Output:**
- Roadmap name and description
- Current status (active/blocked/completed)
- Hierarchical view of phases and tasks
- Current focus highlighted
- Completion statistics

**When to use:**
- To understand roadmap progress
- Before starting work on a task
- To identify what needs to be done next

---

### `/roadmap update <action> [args]`

Update roadmap state (task completion, phase transitions).

**Usage:**
```bash
python3 .claude/skills/roadmap/scripts/update.py <action> [args]
```

**Actions:**

1. **complete-task** - Mark current task as completed, advance to next
   ```bash
   python3 .claude/skills/roadmap/scripts/update.py complete-task
   ```
   - Marks current task as completed
   - Advances to next task in phase
   - If phase complete, advances to next phase
   - If all complete, marks roadmap as completed

2. **block-task <reason>** - Mark current task as blocked
   ```bash
   python3 .claude/skills/roadmap/scripts/update.py block-task "Waiting for API access"
   ```
   - Marks current task as blocked
   - Sets roadmap status to blocked
   - Records reason in task notes

3. **unblock-task** - Remove blocked status
   ```bash
   python3 .claude/skills/roadmap/scripts/update.py unblock-task
   ```
   - Removes blocked status from current task
   - Clears roadmap blocked flag

4. **set-focus <phase> <task>** - Manually change focus
   ```bash
   python3 .claude/skills/roadmap/scripts/update.py set-focus phase-1 task-1-2
   ```
   - Changes current focus to specified phase/task
   - Use when you need to work out of order

**When to use:**
- After completing a task
- When encountering a blocker
- When resolving a blocker
- When you need to change focus manually

---

### `/roadmap handoff`

Generate session handoff file.

**Usage:**
```bash
python3 .claude/skills/roadmap/scripts/handoff.py
```

**Behaviour:**
- Prompts for session information:
  - Work completed
  - Decisions made
  - Open issues/blockers
  - Next session guidance
- Generates filename: `YYYY-MM-DD-claude-<index>.md`
- Writes structured handoff to `sessions/` directory

**When to use:**
- At the end of every session working on a roadmap
- Before context reset or long break
- To ensure continuity for next session

---

### `/roadmap complete`

Mark roadmap as completed and deactivate.

**Usage:**
```bash
python3 .claude/skills/roadmap/scripts/complete.py
```

**Behaviour:**
1. Verifies all phases and tasks are completed
2. Updates roadmap.yml: `status.completed: true`, `status.active: false`
3. Clears current_focus
4. Generates completion summary

**When to use:**
- When all phases and tasks are completed
- To deactivate a roadmap and allow creating a new one

---

## Authority Hierarchy (ABSOLUTE)

When operating under an active roadmap, instructions conflict resolution:

1. **INVARIANTS.md** - Constitutional constraints (HIGHEST AUTHORITY)
2. **ROADMAP.md** - Long-form execution manual
3. **roadmap.yml** - Canonical state machine
4. **sessions/** - Session handoff notes
5. **prompt.md** - Session initialisation prompt (LOWEST)

If any instruction conflicts with a higher authority, the higher authority wins.

**Example:** If prompt.md says "optimise aggressively" but INVARIANTS.md says "no performance changes without approval", INVARIANTS.md wins.

---

## Critical Rules

### 1. Single Active Roadmap Rule

**At most ONE roadmap may be active at any time.**

Before creating a new roadmap, you MUST:
- Check if one is active: `/roadmap check`
- If active, either:
  - Complete it: `/roadmap complete`
  - Or ask user to explicitly deactivate it

**NEVER create a second active roadmap.**

### 2. Current Focus Discipline

When a roadmap is active:
- Work ONLY on the current focus task
- Never skip ahead to future tasks
- Never work on multiple tasks simultaneously
- Complete current task before advancing

### 3. Session Handoff Requirement

At the end of EVERY session working on a roadmap:
- Generate a session handoff file
- Document work completed, decisions, blockers, next steps
- Ensure next session can continue seamlessly

### 4. State Validation

All state transitions must be valid:
- Can't skip tasks in a phase
- Can't advance phase until all tasks complete
- Can't complete roadmap with incomplete items
- Scripts enforce these rules automatically

### 5. When in Doubt, STOP

If you're unsure about:
- Whether to create a roadmap
- Which task to work on
- How to resolve a conflict
- Any roadmap operation

**STOP and ask the user.**

---

## Roadmap File Structure

When a roadmap is created, the following structure is generated:

```
agent_roadmaps/<roadmap-name>/
|-- INVARIANTS.md       # Constitutional constraints (highest authority)
|-- ROADMAP.md          # Long-form execution manual
|-- roadmap.yml         # Machine-readable state (canonical)
|-- prompt.md           # Session initialisation prompt
`-- sessions/           # Session handoff records
    `-- YYYY-MM-DD-claude-N.md
```

### File Purposes

- **INVARIANTS.md**: Non-negotiable constraints that override all other instructions. Defines what must never change, what must always hold true, and what requires explicit human approval.

- **ROADMAP.md**: Detailed, verbose, step-by-step operational guide. Explains the "why" and "how" of the roadmap.

- **roadmap.yml**: Canonical execution state. Tracks phases, tasks, current focus, and status. Single source of truth for state.

- **prompt.md**: Copy-paste only prompt for session initialisation. No commentary, just instructions.

- **sessions/**: Append-only session handoff records. One file per session, ensures continuity.

---

## Examples

### Example 1: Starting a Session

```bash
# MANDATORY: Check for active roadmap
python3 .claude/skills/roadmap/scripts/check.py

# If active roadmap found:
# 1. Read INVARIANTS.md
# 2. Read ROADMAP.md
# 3. Read roadmap.yml
# 4. Read latest session handoff
# 5. Continue work on current task
```

### Example 2: Creating a Roadmap

```bash
# Check no active roadmap exists
python3 .claude/skills/roadmap/scripts/check.py

# Create new roadmap
python3 .claude/skills/roadmap/scripts/create.py database-migration "Migrate from PostgreSQL to MongoDB"

# Edit the generated files:
# - agent_roadmaps/database-migration/INVARIANTS.md
# - agent_roadmaps/database-migration/ROADMAP.md
# - agent_roadmaps/database-migration/roadmap.yml

# Activate by setting status.active: true in roadmap.yml
```

### Example 3: Working on a Task

```bash
# Check status
python3 .claude/skills/roadmap/scripts/status.py

# Work on current task...
# (implement, test, commit)

# Mark task complete
python3 .claude/skills/roadmap/scripts/update.py complete-task

# Generate handoff
python3 .claude/skills/roadmap/scripts/handoff.py
```

### Example 4: Handling a Blocker

```bash
# Encountered a blocker
python3 .claude/skills/roadmap/scripts/update.py block-task "Waiting for API credentials from ops team"

# Later, when unblocked
python3 .claude/skills/roadmap/scripts/update.py unblock-task

# Continue work...
```

---

## Troubleshooting

### "ERROR: Roadmap 'X' is already active"

You tried to create a new roadmap while one is active. Complete or deactivate the current roadmap first.

```bash
python3 .claude/skills/roadmap/scripts/complete.py
```

### "ERROR: No current task set in roadmap.yml"

The roadmap.yml file is missing current_focus. Edit roadmap.yml and set:

```yaml
current_focus:
  phase: phase-0
  task: task-0-1
```

### "ERROR: Cannot complete roadmap - incomplete items found"

Some phases or tasks are not completed. Use `/roadmap status` to see what's incomplete, then complete them:

```bash
python3 .claude/skills/roadmap/scripts/update.py complete-task
```

### "Invalid YAML in roadmap.yml"

The roadmap.yml file has syntax errors. Validate YAML syntax and fix errors.

---

## Integration with Existing System

This skill **complements** the existing agent_roadmaps system:

- **agent_roadmaps/README.md** remains authoritative documentation
- **agent_roadmaps/template/** remains reference templates
- Skill embeds copy of templates for portability
- Skill enforces rules defined in README.md
- Skill automates manual processes
- Works with existing manually-created roadmaps

---

## Version History

- **1.0.0** (2026-01-25): Initial release
  - Core commands: check, create, status, update, handoff, complete
  - Python scripts for deterministic operations
  - YAML parsing and validation
  - State machine enforcement
  - Session handoff generation
