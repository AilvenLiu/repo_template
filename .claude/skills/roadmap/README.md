# Agent Roadmaps Skill

Dependency-aware roadmap tooling for multi-session development workflows.

## Overview

This skill manages roadmap steps under `agent_roadmaps/step-*/` with:
- explicit step dependencies (`depends_on_steps`)
- explicit task dependencies (`depends_on`)
- deterministic progression and schema validation
- temporary lifecycle cleanup when the roadmap is fully complete

## Quick Start

### Session-start check

```bash
python3 .ai/scripts/roadmap/check.py
```

### Create a roadmap step series

```bash
python3 .ai/scripts/roadmap/create.py strategy-upgrade \
  --steps 3 \
  --step-names foundation execution hardening
```

### Validate schema

```bash
python3 .ai/scripts/roadmap/validate_schema.py <roadmap-folder>
```

### View status

```bash
python3 .ai/scripts/roadmap/status.py
```

### Progress work

```bash
python3 .ai/scripts/roadmap/update.py complete-task
python3 .ai/scripts/roadmap/update.py set-focus task-0-2
python3 .ai/scripts/roadmap/handoff.py
python3 .ai/scripts/roadmap/complete.py
```

## Core Guarantees

- Single active step enforcement
- Dependency-safe task transitions
- Dependency graph visibility at step and task levels
- Structured session handoff generation
- Branch protocol support (`roadmap/<step-folder-name>`)
- Roadmap identifiers remain confined to `agent_roadmaps/`
- Completed roadmap series must be deleted wholesale instead of lingering in the repo

## Requirements

- Python 3.10+
- PyYAML >= 6.0
