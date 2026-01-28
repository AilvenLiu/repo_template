# ROADMAP -- Long-Form Execution Guide (Template)

> This document describes a **large, multi-session roadmap task**.
> It is written to be read by an AI agent with no prior context.
> Verbosity is intentional to prevent ambiguity.

---

## 1. Background and Motivation

(Explain why this roadmap exists.)

- What problem is being solved?
- Why incremental or ad-hoc changes are insufficient
- What risks exist if this work is done incorrectly

---

## 2. Overall Objective

By the end of this roadmap, the following MUST be true:

- [Objective 1]
- [Objective 2]
- [Objective 3]

These objectives are **contractual**.

---

## 3. Explicit Non-Goals

The following are **explicitly excluded** from this roadmap:

- [Non-goal 1]
- [Non-goal 2]

If something is not listed as a goal, assume it is out of scope.

---

## 4. High-Level Strategy

(Describe the approach, not the steps.)

- Why this strategy was chosen
- What alternatives were considered and rejected
- Key trade-offs

Detailed decision rationale belongs in ADRs if needed.

---

## 5. Phase Overview

This roadmap is divided into **ordered phases**.
Phases MUST be completed sequentially.

Example:

- Phase 0 -- Baseline & Freeze
- Phase 1 -- Structural Change
- Phase 2 -- Behavioral Change
- Phase 3 -- Optimization & Hardening

---

## 6. Phase Details

### Phase X -- <Phase Name>

#### Objective

After this phase:

- [Concrete truth that must hold]

#### Inputs / Preconditions

- [What must already exist]

#### Constraints (Re-affirmed)

- Refer to INVARIANTS.md
- Phase-specific constraints (if any)

#### Execution Guidance

(How to think while executing this phase.)

- What to focus on
- What to avoid
- Typical failure modes

#### Deliverables

- [Concrete artifacts]

#### Exit Criteria

This phase is complete when:

- [Measurable condition 1]
- [Measurable condition 2]

Do NOT advance to the next phase unless all exit criteria are met.

---

## 7. Risk and Rollback Considerations

- Known risks
- How to detect failure early
- Rollback or mitigation strategy

---

## 8. Completion Definition

The roadmap is considered complete when:

- All phases are completed
- roadmap.yml reflects completion
- No open blockers remain

---

## 9. Final Execution Rule

> Follow this document literally.  
> Do not infer intent beyond what is written.
