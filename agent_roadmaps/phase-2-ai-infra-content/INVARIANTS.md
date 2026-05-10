# INVARIANTS - Phase 2 AI-Infra Content

> These invariants apply to phase `phase-2-ai-infra-content` and override
> lower-priority guidance.

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

- This phase has one upstream dependency: `phase-1-profile-architecture` MUST
  be marked `completed` before any task here is activated. The hybrid overlay
  needs the profile composition; new constraint axes need the loader's
  `when:` selector.
- Do not mark a task active if its `depends_on` tasks are incomplete.
- Do not bypass dependency checks by manual status edits without user approval.

## 3. Draft-First Discipline (Hard Invariant)

This is the load-bearing invariant of Phase 2. Every new constraint, skill,
or template overlay MUST land with an explicit `status: draft` marker in
its frontmatter or first paragraph. Drafts have these properties:

- They are loaded as **advisory** by the constraint loader, not required.
- They cannot fail `bin/agent-precommit` or `bin/agent-check-constraints`.
- They are listed under "Drafts under validation" in the relevant
  `templates/<axis>/AGENTS.md` so contributors know they are not yet binding.
- A draft is promoted to `status: stable` (and becomes binding) only after
  the validation gate (`task-2-10`) confirms it works on a real consuming
  project. Promotion is a separate user-approved change, not part of the
  initial drop.

The reason: nothing in Phase 2 has been battle-tested. The Python overlay
earned its rules on real projects. New AI-infra content earns its rules the
same way - by surviving real use - not by being declared mandatory at birth.

## 4. Architecture and Behaviour

- New constraint files live under:
  - `.ai/constraints/cpp/cuda-modern.md`
  - `.ai/constraints/cpp/kernel-correctness.md`
  - `.ai/constraints/hybrid/ffi-boundary.md`
  - `.ai/constraints/hybrid/python-cpp-build.md`
  - `.ai/constraints/hybrid/system-deps.md`
- New skill bodies live under `.ai/skills/<id>/SKILL.md` with a Claude Code
  stub at `.claude/skills/<id>/SKILL.md`.
- New template overlay lives under `templates/hybrid/`.
- The `project_profile` axes added in Phase 1 (`bindings`, `distribution`,
  `external_dependencies`) gain real loader behaviour here: each new
  constraint declares the axis selector it activates on.
- Battle-tested Python constraints under `.ai/constraints/python/` MUST NOT
  be modified.

## 5. Quality and Safety

- Every new constraint MUST declare its enforcement path explicitly: hook,
  wrapper check, CI gate, or `advisory only`. "Advisory only" is the default
  for drafts.
- Every new skill MUST have both `.ai/skills/<id>/SKILL.md` (vendor-neutral
  body) and `.claude/skills/<id>/SKILL.md` (Claude Code stub). The
  capability audit MUST be updated to require both, gated by the appropriate
  axis selector.
- ASCII-only enforcement preserved.
- British English spelling preserved.
- No emojis in committed files.
- The `Co-Authored-By:` policy from root `CLAUDE.md` applies.

## 6. Process Invariants

- Progress tracking happens in `roadmap.yml` and `sessions/*.md` only.
- Work happens on branch `roadmap/phase-2-ai-infra-content` (cut from master
  after Phase 1 has merged).
- Blockers MUST be reported in `roadmap.yml` and a session handoff.
- The validation task (`task-2-10`) is mandatory and cannot be skipped. The
  phase is not complete without it. The user nominates the consuming
  project (TVM fork, FlashInfer fork, MLC-LLM fork, xgrammar fork, or
  similar) at the time `task-2-10` activates.

## 7. Scope Discipline

The scope of this phase is **the AI-infra content layer**: new constraints
for modern CUDA, kernel correctness, FFI boundaries, hybrid builds, system
deps; the Bazel skill; the GPU-CI skill; the hybrid template overlay; and
validation. Out of scope:

- Schema or loader changes (Phase 1 owned that).
- Speculative content that has no consuming project (Phase 3).
- Writing new constraints for HIP/ROCm, WebGPU, SPIR-V, autotuning frameworks
  (Phase 3).

When uncertain whether a change belongs in Phase 2, default to deferring.

## 8. Final Rule

When uncertain, stop and ask the user.
