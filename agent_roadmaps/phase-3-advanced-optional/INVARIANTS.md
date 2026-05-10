# INVARIANTS - Phase 3 Advanced / Optional

> These invariants apply to phase `phase-3-advanced-optional` and override
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

- This phase has one upstream dependency: `phase-2-ai-infra-content` MUST be
  marked `completed` before any task here is activated.
- Do not mark a task active if its `depends_on` tasks are incomplete.
- Do not bypass dependency checks by manual status edits without user approval.

## 3. Real-Project-Demand Hard Invariant

This is the load-bearing invariant of Phase 3, and the reason the phase
exists as its own bucket rather than being folded into Phase 2.

**No task in this phase may be activated without explicit user approval
citing a real consuming project that requires it.**

The user must:
1. Name the project (e.g., "MLC-LLM Hopper TMA work", "Triton-derived
   internal kernel library", "TVM Relax LLVM AOT codegen").
2. Confirm the project will consume the resulting content within a defined
   time window (so validation evidence can be gathered).
3. Record the approval in a session handoff at the time of activation.

Without this approval, the task stays `pending`. Phase 3 may remain
indefinitely dormant; that is the intended state.

The reason: every speculative skill or constraint that ships unused becomes
debt the next maintainer must reason about. The Python overlay earned its
rules on real projects. Phase 2 follows the same pattern via its draft
discipline. Phase 3 raises the bar further: not just draft-first, but
"do not write at all without a named consumer".

## 4. Architecture and Behaviour

- All Phase 3 deliverables ship as `status: draft` (same discipline as
  Phase 2).
- The Phase 3 deliverables are independent of each other. There is no
  required ordering between them. Each task has its own activation gate.
- A task that is activated produces a focused PR; the phase as a whole is
  not a single PR.

## 5. Quality and Safety

- Every new constraint or skill MUST declare its enforcement path explicitly.
- ASCII-only enforcement preserved.
- British English spelling preserved.
- No emojis in committed files.
- The `Co-Authored-By:` policy from root `CLAUDE.md` applies.

## 6. Process Invariants

- Progress tracking happens in `roadmap.yml` and `sessions/*.md` only.
- Work happens on branch `roadmap/phase-3-advanced-optional` (cut from
  master after Phase 2 has merged), but each Phase 3 task may instead be
  developed on its own sub-branch (e.g.,
  `roadmap/phase-3-advanced-optional/task-3-1-autotuning`) when the user
  wants to ship that task as a standalone PR. Coordinate the branch
  strategy with the user at activation time.
- Blockers MUST be reported in `roadmap.yml` and a session handoff.

## 7. Scope Discipline

The scope of this phase is **speculative content for AI infra patterns that
the template may eventually need but does not yet have a consumer for**.
Out of scope:

- Anything outside the listed task topics. New speculative axes need a new
  Phase 3 task added via user-approved roadmap edit, not a silent expansion.
- Promoting any draft to `status: stable`. Promotion is a separate
  user-approved follow-up.
- Re-opening Phase 0, Phase 1, or Phase 2 work. Issues found in earlier
  phases produce follow-up roadmap series, not in-place edits here.

## 8. Final Rule

When uncertain, stop and ask the user. The default disposition for any
Phase 3 task is "do not start".
