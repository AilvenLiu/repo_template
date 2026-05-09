# ROADMAP - Phase 2 AI-Infra Content

> This document describes the phase `phase-2-ai-infra-content`.
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

Make the template genuinely usable on AI infra projects (Apache TVM family,
MLC-LLM, FlashInfer, xgrammar, CUTLASS-derived work, Google LiteRT-LM)
without contributors having to override or delete its constraints on day one.
Add the new constraints, skills, and template overlay that the Phase 1
profile architecture made possible. Validate the result on a real consuming
project before promoting any draft to required.

Why this phase exists:
- Phase 0 made the existing C++/CUDA constraints accurate; Phase 1 made the
  schema composable. Neither added the AI-infra-specific content the
  template still lacks.
- TVM, MLC-LLM, FlashInfer, xgrammar are all hybrid Python+C++/CUDA wheels
  with system-installed CUDA, scikit-build-core driving CMake, nanobind
  or pybind11 or tvm-ffi bindings. None of that is captured anywhere.
- LiteRT-LM uses Bazel. The template currently has no Bazel skill.

## 2. Upstream Dependencies

- `phase-1-profile-architecture` MUST be marked `completed` before this
  phase is activated.
- Verification: read
  `agent_roadmaps/phase-1-profile-architecture/roadmap.yml`;
  `status.completed_at` must be a valid ISO date and every task `status`
  must be `completed`. The ADR at `.ai/adr/0001-project-profile.md` must
  exist and have been user-approved.

## 3. Scope and Non-Goals

### In Scope

New constraints (each landed as draft):
- `.ai/constraints/cpp/cuda-modern.md`: Tensor Cores, TMA, cudaGraph,
  `cudaMallocAsync` and stream-ordered allocator, CUTLASS/CuTe idioms,
  FP8/BF16/FP16 precision discipline, modern SM dispatch.
- `.ai/constraints/cpp/kernel-correctness.md`: reference-correctness against
  PyTorch eager, numerical tolerance bands per dtype, perf-regression
  gates, SM-version coverage matrix, shape-bucket coverage. Replaces
  line-coverage as the rubric for kernel work.
- `.ai/constraints/hybrid/ffi-boundary.md`: pybind11 vs nanobind vs ctypes
  vs tvm-ffi selection, GIL release rules, DLPack as canonical tensor
  exchange, capsule lifetimes, error propagation, async semantics.
- `.ai/constraints/hybrid/python-cpp-build.md`: scikit-build-core, PyTorch
  CXX11 ABI, `TORCH_CUDA_ARCH_LIST`, manylinux2014 / manylinux_2_28,
  auditwheel, multi-CUDA wheel matrix.
- `.ai/constraints/hybrid/system-deps.md`: discovering and asserting on
  system-installed CUDA, cuDNN, NCCL, TensorRT; fail-fast at configure.

New skills:
- `bazel`: `bin/agent-bazel build|test|run`, `.ai/skills/bazel/SKILL.md`,
  `.claude/skills/bazel/SKILL.md`. Required when `build_system=bazel`.
- `gpu-ci`: `sccache` for CUDA, `auditwheel` flow, multi-arch wheel build,
  H100/A100/L40 gating patterns. Required when
  `distribution=pypi-wheel` or `hardware_targets.cuda_arch` is non-empty.

New template overlay:
- `templates/hybrid/` containing `CLAUDE.md`, `AGENTS.md`, `CONTRIBUTING.md`,
  `.gitignore`, `project.yml`. The `project.yml` is a worked
  `project_profile` example for a hybrid project.
- Update `.claude/skills/create-project/` to support hybrid profile
  selection at project-generation time.

Validation:
- `task-2-10`: dry-run the new content on a real consuming project, fix any
  drift, record evidence.

### Out of Scope
- Phase 1 schema or loader changes.
- HIP/ROCm, WebGPU, SPIR-V, autotuning framework content (Phase 3).
- Promoting drafts to `status: stable`. That is a separate user-approved
  change after `task-2-10` lands.
- Touching battle-tested Python constraints under `.ai/constraints/python/`.

## 4. Task Strategy

Tasks are ordered to land related content together and end with the
validation gate.

- `task-2-1` (cuda-modern.md): the most substantial constraint write. Cover
  Tensor Cores, TMA, cudaGraph, stream-ordered allocator, CUTLASS/CuTe
  idioms, FP8/BF16/FP16 precision, modern SM dispatch. Draft.
- `task-2-2` (kernel-correctness.md): replace line-coverage with the
  reference-correctness rubric. Numerical tolerance bands per dtype,
  perf-regression gates, SM coverage matrix, shape-bucket coverage. Draft.
- `task-2-3` (ffi-boundary.md): the binding-layer constraint. Selection
  between pybind11, nanobind, ctypes, tvm-ffi; GIL release rules; DLPack
  canonical; capsule lifetimes; error propagation; async semantics. Draft.
- `task-2-4` (python-cpp-build.md): the hybrid build constraint.
  scikit-build-core; PyTorch CXX11 ABI; `TORCH_CUDA_ARCH_LIST`;
  manylinux; auditwheel; multi-CUDA wheel matrix. Draft.
- `task-2-5` (system-deps.md): system-installed NVIDIA libraries discovery,
  version assertion, fail-fast. Draft.
- `task-2-6` (bazel skill): `.ai/skills/bazel/SKILL.md` body and the
  `.claude/skills/bazel/SKILL.md` Claude Code stub. `bin/agent-bazel`
  wrapper with `build`, `test`, `run` subcommands. Hooks into
  `build_system=bazel` axis selector. Draft skill (capability audit
  requires it but `bin/agent-bazel` itself only stubs the most common
  subcommand surface; full implementation is incremental).
- `task-2-7` (gpu-ci skill): same shape - body + stub + wrapper if needed.
  Documents `sccache`, `auditwheel`, multi-arch wheel build, H100/A100/L40
  gating patterns. Draft.
- `task-2-8` (hybrid template overlay): write `templates/hybrid/CLAUDE.md`,
  `AGENTS.md`, `CONTRIBUTING.md`, `.gitignore`, `project.yml`. The
  `project.yml` is a worked profile example.
- `task-2-9` (create-project hybrid support): update
  `.claude/skills/create-project/` so it can generate a hybrid project.
  The generator copies `templates/hybrid/` instead of (or in addition to)
  the language-specific overlays.
- `task-2-10` (validation gate): nominate one real consuming project (TVM
  fork, FlashInfer fork, MLC-LLM fork, xgrammar fork, or similar). Drop
  the new template into it. Run the standard workflow: `bin/agent-init`,
  `bin/agent-build full`, `bin/agent-dependency add <something>`,
  `bin/agent-precommit`. Record evidence in the session handoff. Any drift
  must be fixed before this task can be marked complete. **No draft is
  promoted to `stable` in this phase**; promotion is a follow-up.

## 5. Deliverables

- Five new constraint files (each marked draft).
- Two new skills with both vendor-neutral and Claude Code overlays.
- One new template overlay (`templates/hybrid/`).
- Updated `create-project` skill supporting hybrid generation.
- Validation evidence in a session handoff.
- One PR titled `feat(content): AI-infra constraints, skills, hybrid overlay`
  with the validation evidence linked in the description.

## 6. Exit Criteria

Phase 2 is complete only when:
- Every task in `roadmap.yml` is `completed`.
- `status.completed_at` is set in `roadmap.yml`.
- Validation evidence (`task-2-10`) is recorded in a session handoff and
  shows the new content working on a real consuming project.
- The PR from `roadmap/phase-2-ai-infra-content` to master is open with a
  passing CI run (or, if CI is not configured, manual verification by the
  user).
- The user has explicitly approved either Phase 3 activation or end-of-roadmap
  (Phase 3 is intentionally optional and may stay dormant indefinitely).

## 7. Risks and Rollback

| Risk | Detection | Mitigation |
|---|---|---|
| New constraints encode opinions that disagree with the consuming project's house style | `task-2-10` validation surfaces conflicts | Drafts are advisory; the validation step exists exactly to catch this; conflicts trigger draft revision, not template adoption |
| Bazel skill ships as a stub and gives a false sense of coverage | A LiteRT-LM contributor tries to use it and finds it incomplete | The skill stub MUST clearly state which subcommands are stubbed; the AGENTS.md MUST list it under "Drafts under validation" |
| Hybrid template overlay diverges from Python and C++ overlays | A regression is found in one of the three after a shared piece of content moves | All three overlays should reference shared content via `.ai/constraints/` paths, not duplicate it; review each PR for accidental duplication |
| Validation project's owner does not approve the dry-run | task-2-10 cannot start | Either coordinate access in advance with the user or use a personal fork; document the choice in the session handoff |

Rollback: each task is one focused commit (or a small series). `git revert`
of the PR removes the new content; constraint loader changes from Phase 1
are unaffected. The hybrid overlay is purely additive; removing it does not
break any Python-only or C++-only project.

## 8. Execution Rule

Follow task and dependency order; do not bypass declared dependencies.
Drafts ship as drafts; promoting them is a follow-up under explicit user
approval. Do not expand scope into Phase 3: HIP/ROCm, WebGPU, SPIR-V,
autotuning content all belong there.
