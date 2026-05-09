# ROADMAP - Phase 0 Cleanup

> This document describes the phase `phase-0-cleanup`.
> It is explicit enough for a fresh session with zero prior context.

## 0. Authority Order

1. `INVARIANTS.md` (overrides this file)
2. `ROADMAP.md` (this file)
3. `roadmap.yml`
4. Latest file in `sessions/`
5. `prompt.md`

If this file conflicts with `INVARIANTS.md`, follow `INVARIANTS.md` and ask
the user.

## 1. Goal

Remove factually outdated, broken, or unenforceable content from the C++/CUDA
constraint set so it stops blocking AI infra contributors on day one. No
architectural change; no new content. One PR's worth of work.

Why this phase exists:
- The Conan/vcpkg-only mandate blocks every AI infra project (TVM, MLC-LLM,
  FlashInfer, xgrammar all use submodules + system NVIDIA libs).
- `nvprof` and `cuda-memcheck` are deprecated in CUDA 11.6+; recommending them
  as primary tools tells contributors the template is stale.
- The hardcoded SM_70-87 list excludes Ada (89), Hopper (90), and Blackwell
  (100), which is most modern GPUs.
- The stream code example at `cuda.md` section 7.4 has a non-portable VLA and
  allocates inside the per-stream loop. It will be copy-pasted by the next
  reader if not fixed.
- `-Werror` blanket on all targets fights template-heavy headers (CUTLASS,
  Thrust). It needs scoping to first-party translation units.
- `ARCHITECTURE.md` references `verify_skills.py`, which does not exist in
  `.ai/scripts/common/`. Drift undermines trust in the architecture doc.

## 2. Upstream Dependencies

None. This phase begins immediately.

## 3. Scope and Non-Goals

### In Scope
- Replace deprecated CUDA tooling references with modern equivalents
  (`nvprof` -> `nsys` + `ncu`; `cuda-memcheck` -> `compute-sanitizer`).
- Update CUDA architecture lists to include SM_89, SM_90, SM_100 and present
  CMake auto-detection as the default.
- Scope `-Werror` to first-party targets; document `SYSTEM` includes for
  third-party headers.
- Fix the broken stream example in `cuda.md`.
- Soften the absolute Conan/vcpkg mandate into a "documented-mechanism"
  rule that lists Conan, vcpkg, CPM, FetchContent, git submodules, and
  system NVIDIA packages with selection criteria.
- Reconcile `ARCHITECTURE.md` drift (the `verify_skills.py` reference) and
  prune obviously unenforceable rules (no enforcement script, no CI gate).

### Out of Scope
- Adding new constraint files or skills.
- Replacing `project_type` with `project_profile` (Phase 1).
- Writing AI-infra-specific content (Phase 2).
- Touching the Python constraint set.
- Touching `bin/agent-*` wrappers, `.ai/scripts/`, or `.ai/capabilities.yml`.

## 4. Task Strategy

Tasks are intentionally small so each one is a one-commit, one-concern change.
They are independent except where `roadmap.yml` declares `depends_on`. The
recommended execution order matches the task numbering, but the only hard
constraint is that `task-0-6` runs last (it touches multiple files and benefits
from the others being in).

- `task-0-1` (modernise CUDA tooling references): purely text replacement
  across cuda.md, memory-safety.md, testing.md, static-analysis.md. Lowest
  risk, do first.
- `task-0-2` (add modern SM architectures): updates the architecture list and
  switches the default to discovery via `CMAKE_CUDA_ARCHITECTURES native` or
  an explicit list including SM_89, SM_90, SM_100. Lowest risk after task-0-1.
- `task-0-3` (scope -Werror to first-party targets): rewrite the relevant
  cmake.md and forbidden-practices.md sections; show `target_compile_options`
  with `PRIVATE`, and a `SYSTEM` include pattern for third-party headers.
- `task-0-4` (fix broken stream example): replace the buggy example with a
  correct version using a `std::vector<cudaStream_t>` and pre-allocated
  per-stream buffers. Single-file change.
- `task-0-5` (soften dependency mandate): rewrite the dependency rule. Cover
  Conan, vcpkg, CPM, FetchContent, git submodules, and system NVIDIA
  packages, with explicit selection criteria. Move "FORBIDDEN: apt install"
  to "FORBIDDEN: apt install for runtime libraries that ship as part of an
  official NVIDIA distribution channel" - i.e., the rule against polluting
  the system with arbitrary package-manager installs stays, but
  NVIDIA-supplied system libraries are allowed.
- `task-0-6` (drift and unenforceable rules): fix the `verify_skills.py`
  reference in `ARCHITECTURE.md` (either remove the reference or rebuild
  the script as a thin wrapper around `validate_schema.py`); prune any
  `MUST` or `FORBIDDEN` clause that has no enforcement path. Each pruned
  rule must be listed in the session handoff with its rationale.

## 5. Deliverables

- Edited files under `.ai/constraints/cpp/` (cuda.md, dependencies.md,
  cmake.md, memory-safety.md, static-analysis.md, testing.md,
  forbidden-practices.md as needed).
- Edited `templates/cpp/AGENTS.md` and `templates/cpp/CLAUDE.md` if their
  Quick Reference table mentions deprecated tools or the SM list.
- Edited `.claude/skills/ARCHITECTURE.md` to reconcile the `verify_skills.py`
  drift.
- One PR titled `chore(constraints): cleanup C++/CUDA outdated content`.
- A session handoff under `sessions/` summarising every pruned rule with
  rationale.

## 6. Exit Criteria

Phase 0 is complete only when:
- Every task in `roadmap.yml` is `completed`.
- `status.completed_at` is set in `roadmap.yml`.
- A final handoff exists in `sessions/`.
- A PR from `roadmap/phase-0-cleanup` to master is open and has at least one
  passing CI run (or, if no CI runs on the template repo today, the user has
  manually confirmed `bin/agent-precommit` passes).
- The user has explicitly approved Phase 1 activation (single-active-phase
  invariant means Phase 0 must be marked `completed` before Phase 1 starts).

## 7. Risks and Rollback

| Risk | Detection | Mitigation |
|---|---|---|
| Edits accidentally remove load-bearing rules | Schema check via `bin/agent-roadmap validate phase-0-cleanup`; `bin/agent-check-constraints` shows fewer rules than expected | Each pruned rule is listed in the session handoff with rationale; reverting is `git revert <commit>` |
| Modernised tooling references break the Python pre-commit hook | `bin/agent-precommit` fails on a Python project after Phase 0 lands | Phase 0 only edits `.ai/constraints/cpp/*` and `templates/cpp/*`; the Python pre-commit path should not invoke any of these. If it does, that is a Phase-1 architectural concern, not a Phase-0 fix |
| Softening the Conan mandate is interpreted as "no dependency manager required" | A real C++/CUDA project lands without any manifest | Phase 0 keeps the rule "every dependency MUST be declared in a documented mechanism"; the change is *which mechanism is allowed*, not *whether one is required* |

## 8. Execution Rule

Follow task and dependency order; do not bypass declared dependencies. Do not
expand scope into Phase 1 or Phase 2 territory. If a task feels like it wants
to grow beyond a single concern, stop and split it.
