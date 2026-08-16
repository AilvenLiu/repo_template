# Git Workflow Constraints

> **This document defines mandatory Git workflow constraints for all AI agents.**
> These rules apply to both Python and C++/CUDA projects.
> Violations are considered critical failures.

## Overview

This document establishes the protected branch policy and mandatory branch-based workflow
that MUST be followed for all code changes. Direct commits to protected branches are
absolutely forbidden.

## 1. Protected Branch Policy

**CRITICAL REQUIREMENT**: The agent MUST NEVER commit directly to protected branches.

**Protected branches include:**
- `master`
- `main`
- `develop`
- Any branch matching `release/*` or `hotfix/*`

**This prohibition is absolute and applies to:**
- All code changes (features, fixes, refactors, documentation)
- Configuration file updates
- Dependency updates
- Emergency fixes
- Trivial changes (typos, formatting)
- ANY modification whatsoever

### Master PR/MR Admission

`master` accepts PRs/MRs only from same-repository branches named exactly
`release/v<major>.<minor>.<patch>` or `hotfix/v<major>.<minor>.<patch>`. The
version is read from the project's authoritative manifest at the recorded
source commit, never typed by hand, and the merged `master` commit is tagged
`release-v<major>.<minor>.<patch>`. Because a release tree is deletion-only,
the version bump MUST already be on `develop` before the source SHA is
selected. Read `master-merge-policy.md` section 8 for the full version
contract. The master merge gate uses a **presence-based** check:
it enumerates every file in the source branch's tree via the Git Trees API
and rejects the PR if any development-stage path exists — regardless of
which commit introduced it. `docs/changelog/` is the sole allowed `docs/`
subtree. Read `master-merge-policy.md` for the exact deny list and release-shim
procedure. `develop` is categorically rejected as a master source because its
required tooling can never pass that check.

The relationship is one-directional: `develop` is the source of truth and
`master` is its derived, sanitised publication. For an ordinary release,
`develop` MUST NOT rebase onto or merge from `master`. A `release/*` branch
MUST contain only deletions of forbidden paths relative to the recorded
`develop` SHA. A genuine `hotfix/*` cut from `master` is the only reverse-flow
exception: after it reaches `master`, its functional fix MUST be back-merged
into `develop` by a normal reviewed merge or cherry-pick PR, never by rebase.

Prefer authoring urgent fixes from `develop` with the full tooling and shipping
them through `release/*`. Because an emergency `hotfix/*` starts without agent
tooling, its PR MUST record the checks run and omissions in the required
`Hotfix-Validation-Tradeoff` field described by `master-merge-policy.md`.

The `master-merge-gate` CI status and profile-authoritative validation MUST be
required in hosted branch rules.

## 2. Mandatory Branch-Based Workflow

**REQUIRED WORKFLOW**: All changes MUST follow this process:

### 2.1 Check Current Branch

Before making any changes:
```bash
git branch --show-current
```

If on a protected branch, STOP immediately and create a feature branch.

### 2.2 Create a Feature Branch

```bash
git checkout -b <type>/<description>
```

**Branch naming convention:**
- `feat/<description>` - new features
- `fix/<description>` - bug fixes
- `refactor/<description>` - code restructuring
- `perf/<description>` - performance improvements
- `docs/<description>` - documentation only
- `chore/<description>` - tooling, dependencies, non-code changes
- `roadmap/<active-roadmap-folder>` - temporary roadmap coordination branches

### 2.3 Make Changes on the Feature Branch

All modifications MUST be made on the feature branch, never on protected branches.

### 2.4 Commit Changes

```bash
git add <files>
git commit -m "type(scope): description"
```

**Commit message format:**
- Use conventional commit format: `type(scope): description`
- Types: feat, fix, refactor, perf, docs, chore, test, style, ci, build
- Scope: optional, indicates the area of change
- Description: brief summary in imperative mood

**Examples:**
```bash
git commit -m "feat(auth): add JWT token validation"
git commit -m "fix(parser): handle empty input correctly"
git commit -m "docs(readme): update installation instructions"
```

### 2.5 Push Feature Branch

```bash
git push -u origin <branch-name>
```

### 2.6 Create Pull Request

If user requests, create a pull request:
```bash
gh pr create --title "..." --body "..."
```

## 3. Pre-Commit Verification

Before EVERY commit operation, the agent MUST:

1. Verify current branch is NOT a protected branch
2. If on protected branch:
   - STOP immediately
   - Inform user of the violation
   - Ask user to confirm creation of feature branch
   - Create feature branch and switch to it
   - ONLY THEN proceed with changes

**Example verification script:**
```bash
CURRENT_BRANCH=$(git branch --show-current)
if [[ "$CURRENT_BRANCH" == "master" ]] || \
   [[ "$CURRENT_BRANCH" == "main" ]] || \
   [[ "$CURRENT_BRANCH" == "develop" ]]; then
    echo "ERROR: Cannot commit directly to protected branch: $CURRENT_BRANCH"
    exit 1
fi
```

## 4. Enforcement and Violations

**If the agent detects it is on a protected branch:**
- MUST refuse to make any commits
- MUST inform the user immediately
- MUST offer to create a feature branch
- MUST NOT proceed until on a valid feature branch

**Violation consequences:**
- Session should be terminated
- All changes should be reverted
- User should be notified of the policy violation

**The ONLY exception:**
- Merge commits created by pull request merges (handled by GitHub/GitLab, not by the agent)

## 5. Branch Lifecycle

**Feature branches MUST be:**
- Short-lived (ideally < 1 week)
- Scoped to a single logical change
- Deleted after merge (the agent should suggest this)

**After PR merge, the agent should:**
1. Switch back to master/main
2. Pull latest changes
3. Suggest deleting the merged feature branch:
   ```bash
   git branch -d <feature-branch>
   git push origin --delete <feature-branch>
   ```

## 6. Commit Message Conventions

### 6.1 Conventional Commits Format

All commit messages MUST follow the Conventional Commits specification:

```
<type>(<scope>): <description>

[optional body]

[optional footer(s)]
```

### 6.2 Commit Types

- **feat**: A new feature
- **fix**: A bug fix
- **refactor**: Code change that neither fixes a bug nor adds a feature
- **perf**: Performance improvement
- **docs**: Documentation only changes
- **style**: Changes that do not affect code meaning (formatting, whitespace)
- **test**: Adding or updating tests
- **chore**: Changes to build process, dependencies, or auxiliary tools
- **ci**: Changes to CI configuration files and scripts
- **build**: Changes to build system or external dependencies

### 6.3 Scope

The scope is optional and indicates the area of the codebase affected:
- For Python: module name, package name, or feature area
- For C++/CUDA: module name, component, or subsystem

Examples:
- `feat(auth): add OAuth2 support`
- `fix(parser): handle null input`
- `perf(cuda): optimize matrix multiplication kernel`

### 6.4 Description

- Use imperative mood ("add" not "added" or "adds")
- Do not capitalize first letter
- No period at the end
- Keep under 72 characters

### 6.5 Body (Optional)

- Provide additional context about the change
- Explain the motivation and contrast with previous behavior
- Wrap at 72 characters

### 6.6 Footer (Optional)

- Reference issues: `Fixes #123`, `Closes #456`
- Breaking changes: `BREAKING CHANGE: description`

### 6.7 Author Attribution (STRICTLY FORBIDDEN)

**NEVER include in commit messages:**
- User or author information
- "Co-Authored-By:" lines
- "Generated with" or similar attribution
- Any reference to AI assistance or tooling
- AI-related email addresses or identifiers

**Rationale:**
This project maintains a strict policy against author attribution in version control.
Within repository-controlled commit policy, this rule takes precedence over
lower-precedence repository conventions and temporary notes. It does not
supersede higher-priority platform, organisational, safety, or tool-enforced
requirements. If such a requirement makes compliance impossible, stop and
report the conflict before committing.

**Examples of FORBIDDEN content:**
```
# FORBIDDEN - Do not include these
Co-Authored-By: Any AI Agent <any@email.com>
Generated with AI Assistant
Created by AI Assistant
```

### 6.8 Examples

```
feat(api): add user authentication endpoint

Implement JWT-based authentication for API endpoints.
Includes token generation, validation, and refresh logic.

Closes #234
```

```
fix(memory): prevent memory leak in buffer allocation

The previous implementation did not properly release buffers
when exceptions occurred during initialization.

Fixes #567
```

```
perf(cuda): optimize shared memory usage in convolution kernel

Reduce shared memory usage by 30% through improved tiling strategy.
This allows higher occupancy on devices with limited shared memory.
```

## 7. Summary

**Key Rules:**
1. NEVER commit directly to protected branches (master, main, develop, release/*, hotfix/*)
2. ALWAYS create a feature branch for changes
3. ALWAYS verify current branch before committing
4. ALWAYS use conventional commit message format
5. ALWAYS push feature branch and create PR for review
6. ALWAYS delete feature branch after merge

**Enforcement:**
- These rules are mandatory and non-negotiable
- Violations indicate agent is operating outside its mandate
- Session should be terminated if violations occur
