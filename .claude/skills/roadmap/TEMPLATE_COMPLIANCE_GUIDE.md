# Roadmap Template Compliance Guide

> **Quick reference for AI agents creating roadmaps**
> This guide ensures strict compliance with roadmap.yml template

## Mandatory Checklist

Before finalizing any phase roadmap, verify:

- [ ] Each phase has its own folder: `agent_roadmaps/<project>/<phase-folder-name>/`
- [ ] Each phase folder contains its own `roadmap.yml`
- [ ] All phase IDs follow `phase-N` format (e.g., `phase-0`, `phase-1`)
- [ ] All task IDs follow `task-N-M` format (e.g., `task-0-1`, `task-1-2`)
- [ ] All status values are: `pending`, `active`, `completed`, or `blocked`
- [ ] Exactly ONE task has `status: active`
- [ ] No custom fields added (only use template fields)
- [ ] All tasks are atomic (completable in 1-2 hours)
- [ ] All task titles are 10-80 characters
- [ ] Complex tasks have detailed `notes` field
- [ ] Work is on branch `roadmap/<phase-folder-name>`
- [ ] Validation passes: `python3 .claude/skills/roadmap/scripts/validate_schema.py <phase-folder-name>`

## Schema Reference

### Top-Level Structure

```yaml
roadmap:
  name: <string>           # Required
  description: <string>    # Required

status:
  active: <boolean>        # Required
  blocked: <boolean>       # Required
  completed: <boolean>     # Required

current_focus:
  phase: <phase-id>        # Required, format: phase-N
  task: <task-id>          # Required, format: task-N-M

phases:                    # Required, list of phases
  - ...
```

### Phase Structure

```yaml
- id: phase-0              # Required, format: phase-\d+
  title: <string>          # Required, descriptive name
  status: pending          # Required, one of: pending|active|completed|blocked
  tasks:                   # Required, list of tasks
    - ...
```

**Allowed fields**: `id`, `title`, `status`, `tasks`
**No other fields permitted**

### Task Structure

```yaml
- id: task-0-1             # Required, format: task-\d+-\d+
  title: <string>          # Required, 10-80 chars, specific and actionable
  status: pending          # Required, one of: pending|active|completed|blocked
  notes: <string>          # Optional but recommended, detailed description
```

**Allowed fields**: `id`, `title`, `status`, `notes`
**No other fields permitted**

## Task Atomicity Guidelines

### Good Task Titles (Atomic)

[GOOD] "Create user model with email and password fields"
[GOOD] "Add bcrypt password hashing function"
[GOOD] "Implement POST /api/auth/login endpoint"
[GOOD] "Write unit tests for authentication flow"
[GOOD] "Add JWT token generation utility"

### Bad Task Titles (Non-Atomic)

[BAD] "Implement entire authentication system"
[BAD] "Build and test all API endpoints"
[BAD] "Complete user management features"
[BAD] "Fix all bugs and add tests"
[BAD] "Refactor everything and optimize"

### Red Flags

Avoid these words in task titles (they suggest non-atomic tasks):
- "entire", "all", "complete", "full", "whole", "everything"
- "and", "or", "then", "plus", "also" (conjunctions)
- Titles longer than 80 characters

### Splitting Tasks

If a task contains "and", split it:

**Before**: "Implement login endpoint and add tests"

**After**:
- "Implement POST /api/auth/login endpoint"
- "Write unit tests for login endpoint"

## Task Description Quality

### Good Task Notes

```yaml
notes: >
  Create POST /api/auth/login endpoint.

  Requirements:
  - Accept JSON body with email and password
  - Validate credentials against database
  - Return JWT token on success

  Constraints:
  - Use bcrypt for password verification
  - Token expiry: 15 minutes
  - Return 401 for invalid credentials

  Success criteria:
  - Returns 200 with valid JWT for correct credentials
  - Returns 401 for incorrect password
  - Returns 404 for non-existent user
```

### Bad Task Notes

```yaml
notes: "Implement login"  # Too vague
notes: "Add endpoint"     # No details
notes: ""                 # Empty
```

## Common Violations

### Violation 1: Custom Fields

```yaml
# WRONG
- id: task-1-1
  title: "Implement feature"
  priority: high           # [ERROR] NOT in template
  assignee: "claude"       # [ERROR] NOT in template
  estimated_hours: 4       # [ERROR] NOT in template
```

### Violation 2: Invalid ID Format

```yaml
# WRONG
phases:
  - id: "Phase 1"          # [ERROR] Should be: phase-1
  - id: "setup_phase"      # [ERROR] Should be: phase-0
  - id: "p1"               # [ERROR] Should be: phase-1

tasks:
  - id: "task_1_1"         # [ERROR] Should be: task-1-1
  - id: "Task1"            # [ERROR] Should be: task-1-1
```

### Violation 3: Invalid Status

```yaml
# WRONG
status: in-progress        # [ERROR] Should be: active
status: done               # [ERROR] Should be: completed
status: todo               # [ERROR] Should be: pending
status: waiting            # [ERROR] Should be: blocked
```

### Violation 4: Multiple Active Tasks

```yaml
# WRONG - Only ONE task can be active
tasks:
  - id: task-1-1
    status: active         # [ERROR]
  - id: task-1-2
    status: active         # [ERROR] Only one allowed
```

## Validation Workflow

### Step 1: Create Phase Folders

```bash
python3 .claude/skills/roadmap/scripts/create.py <project-name> --phases <N> --phase-names <name1> <name2> ...
```

This creates `agent_roadmaps/<project-name>/phase-0-<name1>/roadmap.yml`, `agent_roadmaps/<project-name>/phase-1-<name2>/roadmap.yml`, etc.

### Step 2: Edit Files

Edit the generated files in each phase folder:
- `agent_roadmaps/<project-name>/<phase-folder-name>/INVARIANTS.md` - Add constraints
- `agent_roadmaps/<project-name>/<phase-folder-name>/ROADMAP.md` - Add detailed plan
- `agent_roadmaps/<project-name>/<phase-folder-name>/roadmap.yml` - Define phases and tasks

### Step 3: Validate Schema

```bash
python3 .claude/skills/roadmap/scripts/validate_schema.py phase-0-baseline
```

### Step 4: Fix Errors

If validation fails:
1. Read error messages carefully
2. Fix CRITICAL errors (blocking)
3. Address WARNINGS (recommended)
4. Consider INFO suggestions
5. Re-run validation

### Step 5: Activate

Set in the phase's `roadmap.yml`:
```yaml
status:
  active: true
```

## Quick Validation

Run this command before committing:

```bash
python3 .claude/skills/roadmap/scripts/validate_schema.py <phase-folder-name>
```

**Exit codes**:
- `0` = Validation passed (no critical errors)
- `1` = Validation failed (critical errors found)

## Examples

### Minimal Valid Roadmap

```yaml
roadmap:
  name: example-roadmap
  description: Example roadmap demonstrating minimal structure

status:
  active: true
  blocked: false
  completed: false

current_focus:
  phase: phase-0
  task: task-0-1

phases:
  - id: phase-0
    title: Setup Phase
    status: active
    tasks:
      - id: task-0-1
        title: Initialize project structure
        status: active
        notes: Create basic directory structure and configuration files
```

### Complete Valid Roadmap

See: `.claude/skills/roadmap/templates/roadmap.yml`

## Troubleshooting

### "Invalid phase ID format"

**Problem**: Phase ID doesn't match `phase-\d+` pattern

**Solution**: Use format `phase-0`, `phase-1`, `phase-2`, etc.

### "Extra fields in task"

**Problem**: Added custom fields not in template

**Solution**: Remove all fields except: `id`, `title`, `status`, `notes`

### "Multiple active tasks found"

**Problem**: More than one task has `status: active`

**Solution**: Set only ONE task to `active`, others to `pending`

### "Task title too short"

**Problem**: Task title is less than 10 characters

**Solution**: Provide more specific, descriptive title

### "Task may not be atomic"

**Problem**: Task title contains words like "entire", "all", or "and"

**Solution**: Split into multiple smaller, atomic tasks

## Summary

**Remember**:
1. Use ONLY template fields
2. Follow ID format strictly: `phase-N`, `task-N-M`
3. Use ONLY valid status values
4. Keep tasks atomic (1-2 hours)
5. Provide detailed task notes
6. Validate before committing
7. Fix all CRITICAL errors

**When in doubt**: Run validation and read error messages carefully.
