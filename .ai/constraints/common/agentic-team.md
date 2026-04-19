# Agentic Team Launch Constraints

> Mandatory guidance for parallel sub-agent / agentic-team execution.
> Applies to Python and C++/CUDA projects across Claude Code and Codex.

## Overview

Modern AI coding platforms (Claude Code, Codex, etc.) expose primitives for
launching independent sub-agents to process work in parallel. Using these
primitives well reduces latency, protects the main context window from
noise, and lets specialised agents drive their own search depth. Using them
poorly burns tokens, produces conflicting edits, and obscures authority.

This document defines when the agent MUST explicitly propose or launch an
agentic team, and when it MUST NOT.

## 1. When to Launch an Agentic Team (MUST consider)

The agent MUST explicitly declare its intent to launch parallel sub-agents
when ALL of the following hold:

1. The work decomposes into two or more independent sub-tasks.
2. Sub-tasks have NO write-write conflicts (they touch disjoint files, or
   only one performs writes).
3. At least one of:
   - Sub-tasks are read-heavy (broad codebase exploration, doc lookup,
     constraint audits, parity analysis, security review).
   - Sub-tasks each exceed ~3 tool calls.
   - Running sub-tasks sequentially in the main context would exceed
     ~50% of remaining context budget.
4. The active roadmap phase (if any) permits it — the single-active-task
   rule is never violated by parallel sub-agents; only one authoritative
   task is still `focus.current_task`.

Typical triggers:
- "Audit all constraints for parity with X."
- "Find every call site of Y and classify them."
- "Review the repository for security/forbidden-practice violations."
- "Research how libraries A, B, C each handle Z."

## 2. When NOT to Launch an Agentic Team

The agent MUST NOT launch an agentic team when:

- Sub-tasks share write targets (risk of conflicting edits).
- The decision depends on synchronous user confirmation.
- The remaining work fits in one or two direct tool calls.
- The active roadmap phase has only a single atomic task in progress.
- Sub-agents would need the user to arbitrate between conflicting outputs
  (prefer a sequential plan and single decision point instead).

## 3. Required Declaration

Before launching parallel sub-agents, the agent MUST:

1. State, in one short sentence, WHY parallelism is being used.
2. List the sub-agents it intends to launch with their exact, self-contained
   prompts (each prompt must stand on its own without conversation context).
3. State the expected artefact from each sub-agent (e.g., "short report",
   "file list", "yes/no verdict").
4. Confirm no write-write conflicts are possible.

If the user is present and the operation is non-trivial, the agent SHOULD
ask for confirmation unless previously authorised for this scope.

## 4. Coordination and Merging

After sub-agents return:

1. The main agent is responsible for synthesis; never delegate final
   synthesis or user-facing summary to a sub-agent.
2. Treat each sub-agent report as evidence, not ground truth — verify
   before acting on any claim that names a specific file, symbol, or flag.
3. Resolve conflicts between sub-agent reports explicitly, citing the
   source files rather than the sub-agent output.

## 5. Authority Interaction

Agentic-team use is subordinate to:

- Roadmap authority order:
  `INVARIANTS.md` > `ROADMAP.md` > `roadmap.yml` > `sessions/` > `prompt.md`
- `.ai/constraints/common/*.md`
- Platform-specific entrypoint (`CLAUDE.md`, `CODEX.md`)

Parallel execution MUST NOT be used to bypass capability-audit failures,
protected-branch rules, dependency order, or pre-commit validation.

## 6. Platform Mapping

- **Claude Code**: Use the `Agent` tool with an appropriate `subagent_type`
  (e.g., `Explore` for read-heavy research, `Plan` for design, `general-purpose`
  for multi-step tasks). Launch independent calls in a single assistant turn.
- **Codex**: Use the platform's native parallel sub-agent or tool-call
  primitive. If unavailable, fall back to sequential execution and record
  the decision in the session handoff.

## 7. Enforcement Summary

1. Declare intent, prompts, and expected outputs BEFORE launching.
2. Ensure disjoint writes and no dependency violations.
3. Always synthesise in the main agent; never in a sub-agent.
4. Verify file/symbol claims from sub-agents before acting.
5. When uncertain, run sequentially and ask the user.
