# Closure Discipline Constraints

> Mandatory completion and review discipline for all AI agents.
> Applies to every session, task, commit, and roadmap phase across platforms.

## Overview

Correctness, completeness, and evidence take priority over fast closure.
Agents MUST NOT rush to mark a task, session, or roadmap phase complete merely
because an initial implementation exists.

## 1. Best-Effort Completion Standard

Before claiming any work is complete, the agent MUST make its strongest
reasonable effort to deliver a complete, production-quality result:

- Re-read the user request and active constraints.
- Compare the implementation against the requested scope and acceptance
  criteria.
- Review its own changes critically for edge cases, regressions, incomplete
  paths, unsafe assumptions, and missing tests.
- Fix issues found during review instead of deferring them when they are within
  scope.
- Run the strongest relevant validation available for the change.
- State any unrun checks, known limitations, blockers, or residual risk.

## 2. Repeated Review Before Closure

For non-trivial work, the agent MUST perform at least one explicit review pass
after implementation and before final response or task advancement.

For high-risk work, including roadmap phase completion, security-sensitive
changes, data migrations, dependency changes, public API changes, build-system
changes, CUDA/native changes, or production-facing behaviour, the review pass
MUST be rigorous and adversarial:

- Search for implicit failure modes, not only obvious syntax errors.
- Inspect changed files directly rather than relying only on memory.
- Check that tests or validation cover the most important behaviour.
- Re-run focused checks after fixes made during review.

## 3. Evidence-Based Closure

The agent MUST NOT claim success without evidence. Acceptable evidence includes
passing tests, builds, linters, type checks, schema validation, targeted manual
inspection, generated artefact inspection, or another concrete verification
appropriate to the task.

If validation cannot be run, the agent MUST say why and describe the remaining
risk clearly.

## 4. Roadmap Phase Closure

A roadmap phase is eligible to close only when:

- Every task in `roadmap.yml` is complete or the user explicitly accepts a
  documented blocked/partial outcome.
- Phase invariants and acceptance criteria have been re-read.
- The phase branch has relevant validation evidence.
- A session handoff records completed work, decisions, blockers, validation,
  residual risk, and next action.

Do not advance to another phase to create a sense of progress when the current
phase still has unresolved in-scope issues.

## 5. Final Response Discipline

Final responses MUST distinguish verified facts from assumptions. They MUST
summarise what changed, what was validated, and any residual risk. They MUST NOT
overstate certainty or imply an impeccable result when validation evidence is
incomplete.
