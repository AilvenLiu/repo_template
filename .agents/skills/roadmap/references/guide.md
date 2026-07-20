# Agent Roadmaps Skill

Dependency-aware roadmap tooling for multi-session development workflows.

## Overview

This skill manages roadmap phases under `agent_roadmaps/phase-*/` with:
- explicit phase dependencies (`depends_on_phases`)
- explicit task dependencies (`depends_on`)
- deterministic progression and schema validation
- temporary lifecycle cleanup when the roadmap is fully complete

## Quick Start

### Session-start check

```bash
python3 .agents/scripts/roadmap/check.py
```

### Create a roadmap phase series

```bash
python3 .agents/scripts/roadmap/create.py strategy-upgrade \
  --phases 3 \
  --phase-names foundation execution hardening
```

### Validate schema

```bash
python3 .agents/scripts/roadmap/validate_schema.py <roadmap-folder>
```

### View status

```bash
python3 .agents/scripts/roadmap/status.py
```

### Progress work

```bash
python3 .agents/scripts/roadmap/update.py complete-task
python3 .agents/scripts/roadmap/update.py set-focus task-0-2
python3 .agents/scripts/roadmap/handoff.py
python3 .agents/scripts/roadmap/complete.py
```

## Core Guarantees

- Single active phase enforcement
- Dependency-safe task transitions
- Dependency graph visibility at phase and task levels
- Structured session handoff generation
- Branch protocol support (`roadmap/<phase-folder-name>`)
- Roadmap identifiers remain confined to `agent_roadmaps/`
- Completed roadmap series must be deleted wholesale instead of lingering in the repo

## Requirements

- Python 3.10+
- PyYAML >= 6.0
