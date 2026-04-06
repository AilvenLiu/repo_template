# Agent Roadmaps Skill

A Claude Code skill for managing multi-session AI agent workflows using the agent_roadmaps system.

## Overview

This skill provides structured commands for managing complex, multi-session development tasks that exceed the scope of 1-2 Claude Code sessions. It enforces mandatory behaviors, validates state transitions, and ensures continuity across sessions. Each phase of a project lives in its own folder under `agent_roadmaps/`, and work for each phase is tracked on a dedicated branch.

## Installation

1. Copy this directory to your Claude Code skills directory:
   ```bash
   cp -r .claude/skills/roadmap ~/.claude/skills/
   ```

2. Install dependencies:
   ```bash
   pip3 install -r ~/.claude/skills/roadmap/requirements.txt
   ```

## Quick Start

### Check for Active Phases (Mandatory at Session Start)

```bash
python3 .claude/skills/roadmap/scripts/check.py
```

### Create Phase Folders for a Project

```bash
python3 .claude/skills/roadmap/scripts/create.py my-project --phases 3 --phase-names baseline core-impl cleanup
```

This creates `agent_roadmaps/my-project/phase-0-baseline/`, `agent_roadmaps/my-project/phase-1-core-impl/`, and `agent_roadmaps/my-project/phase-2-cleanup/`, each with its own `roadmap.yml`.

### Validate a Phase Schema

```bash
python3 .claude/skills/roadmap/scripts/validate_schema.py phase-0-baseline
```

### View Cross-Phase Status

```bash
python3 .claude/skills/roadmap/scripts/status.py
```

### Complete Current Task

```bash
python3 .claude/skills/roadmap/scripts/update.py complete-task
```

### Generate Session Handoff

```bash
python3 .claude/skills/roadmap/scripts/handoff.py
```

### Complete Active Phase

```bash
python3 .claude/skills/roadmap/scripts/complete.py
```

## Features

- **Automatic Session-Start Checks**: Ensures agents check for active phases at every session start
- **Per-Phase Folder Structure**: Each phase has its own folder and `roadmap.yml` under `agent_roadmaps/`
- **Branch Management**: Enforces work on `roadmap/<phase-folder-name>` branches
- **Single Active Phase Rule**: Enforces at most one active phase at a time
- **Cross-Phase Overview**: `status` command shows progress across all phases
- **State Machine Validation**: Validates all state transitions to prevent invalid operations
- **Session Handoff Generation**: Creates structured handoff files for continuity
- **YAML-Based State Management**: Uses per-phase `roadmap.yml` as single source of truth
- **Authority Hierarchy**: Enforces INVARIANTS.md > ROADMAP.md > roadmap.yml precedence

## Commands

| Command | Description |
|---------|-------------|
| `check` | Check for active phases (mandatory at session start) |
| `create <name> --phases <N> --phase-names <names...>` | Create per-phase folder structure |
| `status` | Display cross-phase overview of all phases and progress |
| `update <action>` | Update phase state (complete-task, block-task, etc.) |
| `handoff` | Generate session handoff file |
| `complete` | Mark active phase as completed and deactivate |

## Documentation

See [SKILL.md](SKILL.md) for comprehensive documentation including:
- Detailed command usage
- Authority hierarchy
- Critical rules and enforcement
- Examples and troubleshooting
- Integration with existing agent_roadmaps system

## Requirements

- Python 3.10+
- PyYAML >= 6.0

## Version

1.0.0 (2026-01-25)

## License

This skill is part of the repo_template project and follows the same licence (Creative Commons BY-NC-SA 4.0).
