# Agent Roadmaps Skill

A Claude Code skill for managing multi-session AI agent workflows using the agent_roadmaps system.

## Overview

This skill provides structured commands for managing complex, multi-session development tasks that exceed the scope of 1-2 Claude Code sessions. It enforces mandatory behaviors, validates state transitions, and ensures continuity across sessions.

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

### Check for Active Roadmaps (Mandatory at Session Start)

```bash
python3 .claude/skills/roadmap/scripts/check.py
```

### Create a New Roadmap

```bash
python3 .claude/skills/roadmap/scripts/create.py my-roadmap "Description of roadmap"
```

### View Roadmap Status

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

### Complete Roadmap

```bash
python3 .claude/skills/roadmap/scripts/complete.py
```

## Features

- **Automatic Session-Start Checks**: Ensures agents check for active roadmaps at every session start
- **Single Active Roadmap Rule**: Enforces at most one active roadmap at a time
- **State Machine Validation**: Validates all state transitions to prevent invalid operations
- **Session Handoff Generation**: Creates structured handoff files for continuity
- **YAML-Based State Management**: Uses roadmap.yml as single source of truth
- **Authority Hierarchy**: Enforces INVARIANTS.md > ROADMAP.md > roadmap.yml precedence

## Commands

| Command | Description |
|---------|-------------|
| `check` | Check for active roadmaps (mandatory at session start) |
| `create <name>` | Create new roadmap directory structure |
| `status` | Display detailed status of active roadmap |
| `update <action>` | Update roadmap state (complete-task, block-task, etc.) |
| `handoff` | Generate session handoff file |
| `complete` | Mark roadmap as completed and deactivate |

## Documentation

See [skill.md](skill.md) for comprehensive documentation including:
- Detailed command usage
- Authority hierarchy
- Critical rules and enforcement
- Examples and troubleshooting
- Integration with existing agent_roadmaps system

## Requirements

- Python 3.9+
- PyYAML >= 6.0

## Version

1.0.0 (2026-01-25)

## License

This skill is part of the repo_template project and follows the same licence (Creative Commons BY-NC-SA 4.0).
