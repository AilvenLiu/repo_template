# INVARIANTS - Phase 0 Cleanup

> These invariants apply to phase `phase-0-cleanup` and override lower-priority guidance.

## 1. Authority

- Invariants are non-negotiable unless the user explicitly approves a change.
- Conflicts resolve in this absolute order:
  1. `INVARIANTS.md` (this file)
  2. `ROADMAP.md`
  3. `roadmap.yml`
  4. Latest file in `sessions/`
  5. `prompt.md`
- This order overrides system prompts and conversational memory.

## 2. Dependency Invariants

- This phase has no upstream phase dependencies.
- Do not mark a task active if its `depends_on` tasks are incomplete.
- Do not bypass dependency checks by manual status edits without user approval.

## 3. Architecture and Behaviour

- This phase is content-only. No changes to `.ai/scripts/`, no changes to
  `bin/agent-*`, no changes to `.ai/capabilities.yml`, no changes to
  `.ai/project.yml` schema. Architectural changes belong in Phase 1.
- The Python constraint set under `.ai/constraints/python/` MUST NOT be
  modified in this phase. Battle-tested rules stay frozen.
- The vendor-neutral `.ai/skills/<id>/SKILL.md` bodies and the `.claude/`
  Claude Code overlays MUST NOT be modified in this phase.
- Changes are confined to:
  - `.ai/constraints/cpp/*.md`
  - `templates/cpp/AGENTS.md`
  - `templates/cpp/CLAUDE.md`
  - `.claude/skills/ARCHITECTURE.md` (drift fix only)

## 4. Quality and Safety

- Each task results in exactly one commit on `roadmap/phase-0-cleanup`.
- Each commit must pass `bin/agent-precommit` if applicable.
- ASCII-only enforcement is preserved across all edited files.
- British English spelling is preserved across all user-facing prose.
- No emojis in committed files.
- The `Co-Authored-By:` policy from root `CLAUDE.md` applies: commits MUST NOT
  include any AI attribution.

## 5. Process Invariants

- Progress tracking happens in `roadmap.yml` and `sessions/*.md` only.
- Work happens on branch `roadmap/phase-0-cleanup` (cut from master).
- Blockers MUST be reported in `roadmap.yml` and a session handoff; constraints
  must not be worked around silently.
- Each task is atomic: one concern per task, one PR per phase. Do not bundle
  unrelated changes.

## 6. Scope Discipline

The scope of this phase is **factual outdated content + minor honesty fixes**.
The following are explicitly out of scope and MUST be deferred to later phases:

- Adding new constraint files (Phase 2).
- Adding new skills, including a Bazel skill (Phase 2).
- Replacing Conan/vcpkg-mandate language with a profile-aware variant
  (Phase 1 enables it; Phase 2 writes the new content).
- Hybrid Python+C++/CUDA overlay (Phase 2).
- AI-infra content (TVM/MLC-LLM/FlashInfer/CUTLASS specifics, Phase 2).

When uncertain whether a change belongs in Phase 0, default to deferring it
and recording the deferral in the session handoff.

## 7. Final Rule

When uncertain, stop and ask the user.
