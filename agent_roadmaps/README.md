# Agent Roadmaps - AI Infra Optimisation Series

**This document is authoritative for all AI agents operating in this repository.**
Any violation of the rules defined here is a critical failure.

Read this file at the start of every session.

## 1. Roadmap Overview

- **Roadmap name**: `AI Infra Optimisation`
- **Roadmap slug**: `ai-infra-optimisation`
- **Description**:
  Re-shape this template so it is genuinely usable on AI infra projects
  (Apache TVM family, MLC-LLM, FlashInfer, xgrammar, CUTLASS-derived work,
  Google LiteRT-LM) without contributors having to override or delete its
  constraints on day one. The Python overlay is battle-tested and stays
  largely untouched; the C++/CUDA overlay and the missing hybrid
  Python+C++/CUDA story are the targets.

## 2. Phase Series Status

At most one phase may be active at any time.

| Phase | Folder | Status | Depends On |
|-------|--------|--------|------------|
| 0 | `phase-0-cleanup` | completed | none |
| 1 | `phase-1-profile-architecture` | completed | `phase-0-cleanup` |
| 2 | `phase-2-ai-infra-content` | completed | `phase-1-profile-architecture` |
| 3 | `phase-3-advanced-optional` | dormant (optional) | `phase-2-ai-infra-content` |

**Active phase**: none
**Roadmap state**: closed after Phase 2; Phase 3 remains intentionally dormant

## 3. Dependency Graph

```text
phase-0-cleanup -> phase-1-profile-architecture -> phase-2-ai-infra-content -> phase-3-advanced-optional
```

Rules:
- A phase may be activated only when every `depends_on_phases` entry is completed.
- The phase branch MUST be `roadmap/<phase-folder-name>`.
- Next phase activation is blocked until previous phase PR/MR is merged.
- It is valid for **no phase** to be active after roadmap closure.
- Phase 3 may remain dormant indefinitely unless the user explicitly chooses to
  activate it for a real consuming project.

## 4. Branching Protocol

Each phase has a dedicated git branch:
- Branch name: `roadmap/<phase-folder-name>`
- Created from: `master` (this repository's default branch)
- Merged via: PR to `master` after phase completion and review

The roadmap files themselves were created on
`chore/create-ai-infra-optimisation-roadmap`. After that branch lands on
master, each phase branch is cut from master.

## 5. Per-Phase Folder Structure

```text
agent_roadmaps/
  phase-0-cleanup/
    INVARIANTS.md
    ROADMAP.md
    roadmap.yml
    prompt.md
    sessions/
  phase-1-profile-architecture/
    ...
  phase-2-ai-infra-content/
    ...
  phase-3-advanced-optional/
    ...
```

## 6. Startup Checklist (Mandatory)

At every session start:
1. Run `/init` (or `bin/agent-init --platform claude`). The capability audit
   may report Context7 missing; install Context7 before mutation work, see
   `templates/python/CLAUDE.md` or `templates/cpp/CLAUDE.md` for the install
   commands.
2. Read this file.
3. Identify the active phase from the table above, or confirm that the roadmap
   is currently closed with no active phase.
4. If a phase is active, read that phase's `INVARIANTS.md`, `ROADMAP.md`,
   `roadmap.yml`, and the latest file in its `sessions/`.
5. If no phase is active, read the latest closure / handoff note from the most
   recently completed phase before proposing reactivation or Phase 3 work.
6. If a phase is active, confirm the current branch is
   `roadmap/<active-phase-folder-name>`. If the chore branch has not yet merged
   to master, the next session must coordinate with the user before cutting
   phase branches.
7. If a phase is active, confirm the active phase's `depends_on_phases` are all
   completed.

## 7. Session Handoff Rules

For every roadmap session:
1. Create `sessions/session-YYYY-MM-DD-HH-MM.md` with work completed,
   decisions taken, blockers, and next steps.
2. Update `roadmap.yml` (task statuses, `focus.current_task`, `focus.notes`).
3. Commit handoff and roadmap state together; do not split.

## 8. Out-of-Scope for This Roadmap Series

- Any rewrite of the battle-tested Python constraints. Phase 1 must compose
  with them, not replace them.
- New LLM product surface (chat, RAG, agent loops). This roadmap is about
  infrastructure scaffolding, not application templates.
- Speculative skills (autotuning, HIP/ROCm, WebGPU, SPIR-V) without a real
  consuming project. These belong in Phase 3 and remain dormant unless
  the user explicitly invokes them with a project name.

## 9. Reading Order on First Pickup

A fresh session with no prior context should read in this order:
1. Repository `CLAUDE.md` and `MEMORY.md` (auto-loaded).
2. This file.
3. `agent_roadmaps/phase-0-cleanup/INVARIANTS.md`.
4. `agent_roadmaps/phase-0-cleanup/ROADMAP.md`.
5. `agent_roadmaps/phase-0-cleanup/roadmap.yml`.
6. Latest file in `agent_roadmaps/phase-0-cleanup/sessions/` (none on first
   pickup).
7. `agent_roadmaps/phase-0-cleanup/prompt.md`.

## 10. Final Enforcement Rule

If uncertain whether an action is allowed, stop and ask the user.
