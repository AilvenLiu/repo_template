---
name: python-env-setup
description: Diagnose and recover pyenv or Poetry environment issues in Codex sessions. Use when Python version selection, virtualenv location, or Poetry environment detection is wrong.
---

# Codex Python Env Setup

Run:

```bash
bin/agent-python-env-setup <diagnose|fix|verify>
```

## Notes

- `diagnose` is the safe first step.
- `fix` may propose or perform shell-config changes; review output carefully.
- This skill is relevant only for Python projects.
