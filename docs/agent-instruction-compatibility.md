# Agent Instruction Compatibility

## Purpose

This template supports Claude Code, Codex, and agents that read `AGENTS.md`.
Repository policy must remain strong without claiming authority that a local
file cannot have. This document records the compatibility model, validation
procedure, and migration path for projects generated before this hardening.

## Failure Mode and Root Cause

Some generated projects caused normal Claude Code sessions to refuse even a
minimal first request with a message beginning “I can't share or summarize
instructions before your message.” Safe mode did not exhibit the failure.

The strongest repository evidence was a set of local instruction surfaces that
claimed priority over platform controls, asked an agent to disregard those
controls, and ranked platform guidance below local files. The normal `/init`
path also emitted every selected constraint body into the live conversation.
Those properties made the project customisation resemble an instruction
conflict rather than an ordinary repository policy.

The remediation removes that wording, keeps initialisation bounded, and
preserves policy strength through scoped repository-local precedence.

## Loading-Surface Map

| Surface | Loading time | Role |
|---|---|---|
| Root `CLAUDE.md` | Claude Code session start | Claude-specific entrypoint |
| Root `AGENTS.md` | `AGENTS.md`-aware agent session start | Vendor-neutral entrypoint |
| `templates/*/CLAUDE.md` and `AGENTS.md` | Generated-project session start | Profile-specific entrypoints |
| `.claude/settings.json` and hooks | Tool lifecycle | Permission and session gates, not policy text |
| `.agents/bin/agent-init` | Explicit `/init` or wrapper invocation | Profile detection, capability audit, bounded constraint manifest |
| `.agents/constraints/` | Read from the init manifest before relevant work | Canonical shared and profile policy |
| `.agents/skills/` | Codex session discovery and relevant procedure invocation | Canonical skill bodies; native Codex repository skills |
| `.claude/skills/` | Claude Code skill discovery | Thin delegates to canonical skill bodies |
| `.codex/hooks.json` and `.claude/settings.json` | Platform startup/tool lifecycle | Native hook registration; adapters delegate to `.agents/hooks/` |
| `agent_roadmaps/` | Only when a roadmap is active | Temporary phase scope and execution state |
| `.agents/skills/create-project/scripts/init.py` | Project generation | Copies canonical shared assets and applies one profile overlay |

The generator is the source of generated output. Do not edit a disposable
generated project to change template policy; update its canonical source and
regenerate it instead.

## Hierarchy Model

Higher-priority platform safety, developer, managed organisational, and
tool-enforced requirements always apply. Repository files cannot grant
additional permissions or relax those requirements.

Only within repository-controlled guidance, use this order:

1. Active phase `INVARIANTS.md`
2. Active phase `roadmap.yml` for current executable state and dependencies
3. Active phase `ROADMAP.md` for scope and execution intent
4. Applicable shared and profile-specific constraints
5. The platform entrypoint
6. Durable contribution documentation
7. Session handoffs, `prompt.md`, and other temporary notes

If a higher-priority requirement makes local compliance impossible, follow it,
minimise the deviation, and report the conflict before an unsafe or
unauthorised mutation. Session records and conversational assumptions cannot
change current repository state.

## Safe Authoring Rules

When adding a constraint, skill, roadmap template, hook message, or entrypoint:

- State the operational rule directly (`MUST`, `MUST NOT`, required command,
  quality gate, or stop condition).
- Scope precedence explicitly: “Within repository-controlled guidance ...”.
- Acknowledge higher-priority platform and tool requirements once at the policy
  boundary; do not speculate about non-repository context.
- Keep platform adapters short and refer to vendor-neutral canonical policy.
- Put durable state in machine-readable project files and treat session records
  as context, not authority.
- Never place credentials, access tokens, machine-specific paths, or user names
  in generated instructions. Use a descriptive placeholder for setup examples.

The instruction-safety scanner checks canonical instruction files and the same
surfaces in generated projects. It reports the file, line, rule, reason, and
preferred remediation. Tests and fixtures may contain deliberate unsafe strings,
but they are excluded from the scanner's production-source scope.

## Validation

Run the static checks from the template root:

```bash
.agents/bin/agent-check-constraints
python3 -m pytest tests/test_instruction_safety.py tests/test_e2e_project_generation.py
```

The constraint wrapper intentionally reports a protected-branch violation when
run on `master`, `main`, or `develop`; instruction safety must still be absent
from that report.

The generation tests create Python, C++/CUDA, and hybrid projects with the
actual creation function, then scan their copied instruction surfaces and
verify the profile-specific entrypoints.

For a manual normal-mode Claude Code check in each fresh generated project:

```bash
claude -p --no-session-persistence --permission-mode plan \
  'Reply with exactly: OK'
claude -p --no-session-persistence --permission-mode plan \
  'Identify the project profile and the required initialisation command. Do not modify files.'
.agents/bin/agent-init --platform claude
```

Do not add `--safe-mode` to the normal-mode check. Use safe mode only as a
diagnostic comparison if a normal session fails. For Codex, use the same fresh
project and run `.agents/bin/agent-init --platform codex`; then perform a read-only
profile and workflow check through the available Codex surface.

## Downstream Migration

For a repository generated from an older template, first preserve local policy
customisations in a separate review diff. Then update these generated sources:

1. Root `AGENTS.md` and `CLAUDE.md`
2. `.agents/constraints/common/instruction-hierarchy.md` and
   `.agents/constraints/common/git-workflow.md`
3. `.agents/skills/init/SKILL.md`, `.agents/skills/roadmap/SKILL.md`, and their
   `.claude/skills/` adapters
4. `.agents/scripts/session_init.py`, the roadmap templates, and
   `.agents/scripts/instruction_safety.py`
5. Tests and the `.agents/bin/agent-check-constraints` validation path
6. Any copied setup examples that contain real credential material

Regenerate a throwaway project from the updated template and compare these
files with the downstream repository. Reapply only project-specific additions
that follow the safe authoring rules above. Finish by running the static checks,
a fresh normal-mode Claude Code probe, and the Codex initialisation check.
