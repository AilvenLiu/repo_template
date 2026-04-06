# ROADMAP -- Phase Execution Guide (Template)

> This document describes the **single phase** `<PHASE_FOLDER_NAME>`.
> It is written to be read by an AI agent with no prior context.
> Verbosity is intentional to prevent ambiguity.

---

## 1. Background and Motivation

(Explain why this phase exists.)

- What problem is being solved in this phase?
- Why is this work necessary at this stage of the project?
- What risks exist if this phase is done incorrectly?

---

## 2. Overall Objective (for THIS phase)

By the end of this phase, the following MUST be true:

- [Objective 1]
- [Objective 2]
- [Objective 3]

These objectives are **contractual**.

---

## 3. Explicit Non-Goals

The following are **explicitly excluded** from this phase:

- [Non-goal 1]
- [Non-goal 2]

If something is not listed as a goal, assume it is out of scope.

---

## 4. High-Level Strategy

(Describe the approach, not the steps.)

- Why this strategy was chosen for this phase
- What alternatives were considered and rejected
- Key trade-offs

Detailed decision rationale belongs in ADRs if needed.

---

## 5. Deliverables

Concrete artifacts this phase must produce:

- [Deliverable 1]
- [Deliverable 2]

---

## 6. Exit Criteria

This phase is complete when:

- [Measurable condition 1]
- [Measurable condition 2]
- roadmap.yml reflects `completed: true` for this phase
- All tasks in roadmap.yml are marked `completed`
- A final session handoff file has been written in sessions/

Do NOT mark this phase complete unless all exit criteria are met.

---

## 7. Risk and Rollback Considerations

- Known risks for this phase
- How to detect failure early
- Rollback or mitigation strategy

---

## 8. Completion Definition

This phase is considered complete when:

- All exit criteria in section 6 are met
- roadmap.yml reflects completion
- No open blockers remain
- A PR/MR from `roadmap/<PHASE_FOLDER_NAME>` into the base branch has been opened

---

## 9. Final Execution Rule

> Follow this document literally.  
> Do not infer intent beyond what is written.
