# Claude Code Skills Architecture

This document describes the architecture and design principles for Claude Code skills in this repository template.

## Overview

Skills are modular, discoverable capabilities that extend Claude Code's functionality. They provide structured workflows for common development tasks and help Claude Code make better execution decisions.

## Skill Discovery Mechanism

Claude Code discovers skills by scanning for `SKILL.md` files (case-sensitive, uppercase) in the `.claude/skills/` directory.

### Required Structure

```
.claude/skills/<skill-name>/
|-- SKILL.md              # Skill definition with YAML frontmatter
|-- README.md             # Optional: Detailed documentation
`-- scripts/              # Optional: Python scripts for automation
    |-- script1.py
    `-- script2.py
```

### SKILL.md Format

Every skill must have a `SKILL.md` file with YAML frontmatter:

```markdown
---
name: skill-name
description: Brief description that helps Claude Code decide when to use this skill
version: 1.0.0
---

# Skill Name

Detailed documentation...
```

**Required fields:**
- `name`: Skill invocation name (must match directory name)
- `description`: Trigger conditions and use cases

**Optional fields:**
- `version`: Semantic version
- `author`: Skill author
- `requires`: Dependencies

## Design Principles

### 1. Self-Locating

Skills must not rely on hardcoded paths. Use the `SkillBase` class for path resolution:

```python
from pathlib import Path
import sys

# Add common utilities to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "common"))
from skill_base import SkillBase

# Initialize with self-location
skill = SkillBase(__file__)
repo_root = skill.repo_root
```

This ensures skills work regardless of:
- Where they're invoked from
- Where the template was copied to
- Repository structure variations

### 2. Discoverable

Skills should have clear, specific descriptions that help Claude Code decide when to use them:

**Good:**
```yaml
description: Retrieve documentation from Context7 MCP server. Use when you need official library documentation or API references.
```

**Bad:**
```yaml
description: Documentation tool
```

### 3. Composable

Skills should integrate with other skills:

```markdown
## Integration with Other Skills

### With /init
When /init detects unfamiliar imports, suggests using this skill.

### With /dependency
After adding dependencies, suggests documentation lookup.
```

### 4. Actionable

Skills should provide clear, actionable outputs:

- Exit codes for success/failure
- Structured error messages
- Next steps and suggestions
- Links to relevant documentation

### 5. Robust

Skills must handle edge cases gracefully:

- Missing dependencies
- Invalid project structure
- Network failures
- Permission issues

## Skill Categories

### Core Workflow Skills

Essential skills for development workflow:

- **init**: Session initialization and constraint loading
- **pre-commit**: Code quality validation before commits
- **dependency**: Dependency management
- **build**: Build orchestration

### Knowledge Retrieval Skills

Skills that fetch external information:

- **context7**: Documentation from Context7 MCP
- **navigate**: Code structure analysis

### Behavioural Skills

Skills that steer execution quality across other workflows:

- **karpathy-guidelines**: Non-trivial coding guidance focused on explicit assumptions, simple solutions, surgical diffs, and verification-first execution

### Project Management Skills

Skills for managing complex tasks:

- **roadmap**: Multi-session workflow management
- **check-constraints**: Constraint compliance validation

### Environment Skills

Skills for environment setup and diagnostics:

- **python-env-setup**: Python environment diagnostics

## Creating New Skills

### Step 1: Create Directory Structure

```bash
mkdir -p .claude/skills/my-skill/scripts
```

### Step 2: Create SKILL.md

```markdown
---
name: my-skill
description: What this skill does and when to use it
version: 1.0.0
---

# My Skill

## When to Use

Automatically triggered when:
- Condition 1
- Condition 2

## What It Does

1. Step 1
2. Step 2

## Usage

```bash
/my-skill <args>
```

## Examples

...
```

### Step 3: Create Scripts (Optional)

```python
#!/usr/bin/env python3
"""My skill implementation."""

import sys
from pathlib import Path

# Add common utilities
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "common"))
from skill_base import SkillBase

def main():
    skill = SkillBase(__file__)
    # Implementation...

if __name__ == "__main__":
    main()
```

### Step 4: Verify Discoverability

```bash
python3 .claude/skills/common/verify_skills.py
```

## Common Utilities

The `common/` directory provides shared utilities:

### skill_base.py

Base class for path resolution:

```python
from skill_base import SkillBase

skill = SkillBase(__file__)
repo_root = skill.repo_root
claude_dir = skill.claude_dir
```

### verify_skills.py

Verification tool for skill installation:

```bash
python3 .claude/skills/common/verify_skills.py
```

Checks:
- SKILL.md exists and is properly formatted
- YAML frontmatter is valid
- Required fields are present
- Directory name matches skill name

## Skill Selection Strategy

Claude Code selects skills based on:

1. **Explicit invocation**: User types `/skill-name`
2. **Description matching**: Skill description matches user query
3. **Context triggers**: Current state matches skill triggers
4. **Integration hints**: Other skills suggest this skill

### Improving Selection

Make your skill more discoverable:

1. **Specific descriptions**: Include trigger keywords
2. **Clear use cases**: List concrete scenarios
3. **Integration points**: Reference other skills
4. **Examples**: Show typical usage patterns

## Testing Skills

### Manual Testing

```bash
# Test skill invocation
/my-skill test-args

# Test script directly
python3 .claude/skills/my-skill/scripts/main.py test-args
```

### Verification

```bash
# Verify skill is discoverable
python3 .claude/skills/common/verify_skills.py

# Check for errors
echo $?  # Should be 0
```

## Troubleshooting

### Skill Not Discovered

1. Check SKILL.md exists (uppercase)
2. Verify YAML frontmatter format
3. Ensure name matches directory
4. Run verification tool

### Path Resolution Fails

1. Use SkillBase for path resolution
2. Don't hardcode paths
3. Test from different working directories

### Script Import Errors

1. Add common/ to Python path
2. Use relative imports within skill
3. Check Python version compatibility

## Best Practices

1. **Use SkillBase**: Always use for path resolution
2. **Verify after creation**: Run verify_skills.py
3. **Document integrations**: Show how skills work together
4. **Provide examples**: Include real usage examples
5. **Handle errors gracefully**: Clear error messages
6. **Test portability**: Test after copying template
7. **Keep descriptions specific**: Help Claude Code choose correctly
8. **Version your skills**: Use semantic versioning

## Migration Guide

### Updating Existing Skills

To make existing skills more robust:

1. Add SkillBase for path resolution
2. Update SKILL.md with better descriptions
3. Add integration documentation
4. Test with verify_skills.py

### Template Copying

When copying template to new project:

1. Copy entire `.claude/` directory
2. Run verify_skills.py
3. Update project-specific paths in CLAUDE.md
4. Test skill invocation

## Future Enhancements

Planned improvements:

1. **Skill dependencies**: Declare skill dependencies
2. **Skill composition**: Chain skills together
3. **Skill marketplace**: Share skills across projects
4. **Auto-update**: Update skills from template
5. **Skill analytics**: Track skill usage and effectiveness

## Version History

- **1.0.0** (2026-03-06): Initial architecture
  - Self-locating skills with SkillBase
  - Verification tool
  - Core workflow skills
  - Knowledge retrieval skills
  - Build orchestration
  - Code navigation
