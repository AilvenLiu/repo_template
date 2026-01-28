# INVARIANTS -- Constitutional Constraints (Template)

> This document defines **non-negotiable invariants** for a roadmap task.
> These constraints override ROADMAP.md, roadmap.yml, session instructions, and prompts.

---

## 1. Authority and Scope

- These invariants apply to **all phases, tasks, and sessions** of this roadmap.
- No phase completion, optimization, or workaround may violate these constraints.
- Modifying this file requires **explicit human approval**.

---

## 2. Architectural Invariants

(Examples -- must be customized per roadmap)

- Public APIs MUST remain backward compatible unless explicitly approved.
- Core module boundaries MUST NOT be collapsed or bypassed.
- New abstractions MUST have a single clear responsibility.

---

## 3. Behavioral Invariants

- Existing externally observable behavior MUST remain unchanged unless explicitly stated.
- Feature flags MUST guard any new behavior.
- No silent behavior changes are allowed.

---

## 4. Quality and Safety Invariants

- All existing tests MUST continue to pass.
- New code MUST include adequate test coverage.
- No degradation in stability, safety, or compliance is permitted.

---

## 5. Performance and Resource Invariants

- Performance regressions beyond agreed thresholds are forbidden.
- Resource usage MUST NOT exceed defined limits without approval.

---

## 6. Process Invariants

- All progress MUST be tracked via roadmap.yml.
- Each session MUST produce a handoff record.
- Blockers MUST be reported, not worked around.

---

## 7. Interpretation Rule

> If any instruction conflicts with these invariants,  
> **these invariants always win**.

---

## 8. Final Clause

When in doubt, STOP and ask the user.  
Assumptions are not allowed.
