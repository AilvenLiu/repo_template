# Agent Roadmaps Skill

Dependency-aware roadmap tooling for multi-session development workflows.

## Overview

This skill manages roadmap phases under `agent_roadmaps/phase-*/` with:
- explicit phase dependencies (`depends_on_phases`)
- explicit task dependencies (`depends_on`)
- deterministic progression and schema validation

## Quick Start

### Session-start check

```bash
python3 .claude/skills/roadmap/scripts/check.py
```

### Create a roadmap phase series

```bash
python3 .claude/skills/roadmap/scripts/create.py strategy-upgrade \
  --phases 3 \
  --phase-names foundation execution hardening
```

### Validate schema

```bash
python3 .claude/skills/roadmap/scripts/validate_schema.py phase-0-foundation
```

### View status

```bash
python3 .claude/skills/roadmap/scripts/status.py
```

### Progress work

```bash
python3 .claude/skills/roadmap/scripts/update.py complete-task
python3 .claude/skills/roadmap/scripts/update.py set-focus task-0-2
python3 .claude/skills/roadmap/scripts/handoff.py
python3 .claude/skills/roadmap/scripts/complete.py
```

## Core Guarantees

- Single active phase enforcement
- Dependency-safe task transitions
- Dependency graph visibility at phase and task levels
- Structured session handoff generation
- Branch protocol support (`roadmap/<phase-folder-name>`)

## Requirements

- Python 3.10+
- PyYAML >= 6.0
