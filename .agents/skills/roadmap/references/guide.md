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
.agents/bin/agent-roadmap check
```

### Create a roadmap phase series

```bash
.agents/bin/agent-roadmap create strategy-upgrade \
  --phases 3 \
  --phase-names foundation execution hardening
```

### Validate schema

```bash
.agents/bin/agent-roadmap validate <roadmap-folder>
```

### View status

```bash
.agents/bin/agent-roadmap status
```

### Progress work

```bash
.agents/bin/agent-roadmap update complete-task
.agents/bin/agent-roadmap update set-focus task-0-2
.agents/bin/agent-roadmap handoff
.agents/bin/agent-roadmap complete
```

## Core Guarantees

- Single active phase enforcement
- Dependency-safe task transitions
- Dependency graph visibility at phase and task levels
- Structured session handoff generation
- Every command uses the repository's Poetry-aware Python dispatcher
- Branch protocol support (`roadmap/<phase-folder-name>`)
- Roadmap identifiers remain confined to `agent_roadmaps/`
- Completed roadmap series must be deleted wholesale instead of lingering in the repo

## Requirements

- Python 3.10+
- PyYAML >= 6.0
