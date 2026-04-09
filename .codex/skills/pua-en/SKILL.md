---
name: pua-en
description: Performance Improvement Plan enforcement for English sessions. Triggers on repeated failures, passive behavior, or user frustration. Uses Western tech company performance culture rhetoric. Do NOT use for Chinese sessions - use pua instead.
---

# PUA-EN (Performance Improvement Plan - English Edition)

This skill is a wrapper that loads the full PUA-EN methodology from the installed skill.

## Installation

For Codex, install the pua-en skill from the tanweai/pua repository:

```bash
mkdir -p .agents/skills/pua-en
curl -o .agents/skills/pua-en/SKILL.md \
  https://raw.githubusercontent.com/tanweai/pua/main/codex/pua-en/SKILL.md
```

## Trigger Conditions

This skill triggers when:
- Task has failed 2+ times with same approach
- Agent exhibits passive behavior (waiting for instructions, not investigating)
- User expresses frustration ("try harder", "figure it out", "stop failing")
- Agent suggests manual user intervention without exhausting options
- Agent claims "I can't" without completing systematic methodology

## Usage

Once installed, the skill activates automatically based on trigger conditions, or can be invoked manually:

```
$pua-en
```

or

```
/prompts:pua-en
```

## Language Requirement

This repository requires British English for all user-facing output. The `pua-en` variant uses Western tech company performance culture rhetoric (Amazon, Google, Meta, Netflix, etc.) in English.

Do NOT use the default `pua` skill (Chinese variant) for English sessions.

## Full Documentation

For complete methodology, trigger conditions, and corporate flavors, see the installed skill at `.agents/skills/pua-en/SKILL.md` or the upstream repository at https://github.com/tanweai/pua
