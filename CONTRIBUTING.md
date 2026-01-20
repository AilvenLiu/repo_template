

# Development & Collaboration Guidelines

> This document defines **mandatory contribution standards** for this repository.
> All contributors (human or AI) must follow these rules.


## 1. General Principles
- Prefer **clarity over cleverness**
- Prefer **explicit decisions over implicit assumptions**
- Prefer **small, reviewable changes over large, opaque ones**
- Never trade correctness or safety for speed

If unsure, ask before acting.


## 2. Branching Model

### 2.1 Main Branches

The repository follows a **trunk-based development model** with the following conventions:
- master
- Always stable
- Always releasable
- Protected branch (no direct commits)

Optional long-lived branches (if applicable):
- release/* — release stabilization
- hotfix/* — urgent fixes on released versions


### 2.2 Feature / Work Branches

All work MUST be done on a dedicated branch.

Naming convention:
```
<type>/<short-description>
```

Allowed types:
- feat/ — new features
- fix/ — bug fixes
- refactor/ — structural changes without behavior change
- chore/ — tooling, infra, non-code changes
- docs/ — documentation only

Examples:
```
feat/add-cache-layer
refactor/decouple-parser
fix/null-pointer-on-startup
```

Branches MUST be:
- Short-lived
- Scoped to a single logical change
- Deleted after merge


## 3. Commit Message Convention

### 3.1 Format

All commits MUST follow this format:
```
<type>(optional-scope): <short summary>

[optional body]
```

Types:
- feat
- fix
- refactor
- docs
- test
- chore

Examples:
```
feat(api): add pagination support
fix: handle empty config file
refactor(core): split validation logic
```


### 3.2 Rules
- Summary line:
- less than 72 characters
- Imperative mood (“add”, not “added”)
- Body (if present):
- Explains **why**, not just what
- One logical change per commit

**FORBIDDEN** Avoid messages like:
- “update”
- “fix stuff”
- “wip”


## 4. Pull Request (PR) Guidelines

### 4.1 When to Open a PR

Open a PR when:
- A logical unit of work is complete
- Tests are passing
- The change is ready for review

Draft PRs are encouraged for early feedback.


### 4.2 PR Title

PR titles MUST follow the same convention as commit messages:
```
<type>: <short description>
```

Example:
```
refactor: decouple auth from request parsing
```


### 4.3 PR Description (Required Sections)

Each PR MUST include:
```
## Summary
What does this PR do?

## Motivation
Why is this change necessary?

## Changes
- Bullet list of key changes

## Testing
How was this change tested?

## Related
- Related issues, ADRs, or roadmaps (if any)
```


### 4.4 Scope Control
- A PR SHOULD address one concern
- Avoid mixing:
- Refactors + new features
- Behavior changes + formatting
- Large changes should be split into multiple PRs when possible

## 5. Recommand Practices 
- Write clear, concise commit messages
- Keep commits atomic and focused
- Don't commit generated files or secrets

**STRICTLY FORBIDDEN: User or Author Attribution**
- **NEVER** include user or author information in commit messages
- **NEVER** include "Generated with", "Co-Authored-By", or any attribution lines
- **NEVER** include tool names, AI assistant names, or generation metadata
- Commit messages and PR descriptions must contain ONLY technical content
- This is a STRICT requirement with NO exceptions

**MANDATORY: Pull Request Requirements**
- MUST include a formal, comprehensive PR description when submitting pull requests
- PR description MUST include:
  - Summary: Brief overview of changes
  - Components Implemented: Detailed list of what was added/modified
  - Test Coverage: Number of tests and coverage percentage
  - Performance Impact: Expected improvements or considerations
  - Files Changed: List of added/modified/deleted files
  - Testing: How to verify the changes
  - Compliance: Confirmation of adherence to project standards
- Use markdown formatting for readability
- Include relevant context for reviewers
- Reference related issues or documentation


## 6. Code Review Expectations

### 6.1 For Authors
- Keep PRs small and focused
- Respond to feedback constructively
- Update PRs instead of opening new ones


### 6.2 For Reviewers
- Review for:
    - Correctness
    - Clarity
    - Maintainability
- Avoid nitpicking style unless it affects readability or consistency
- Approve only when confident the change is safe


## 7 Testing and Quality
- All new features MUST include tests
- Bug fixes MUST include regression tests when feasible
- Existing tests MUST continue to pass

Do not merge code that breaks the build.


## 8. Tags and Releases

### 8.1 Tagging Convention

If the project uses version tags, follow Semantic Versioning:
```
v<MAJOR>.<MINOR>.<PATCH>
```

Examples:
```
v1.0.0
v2.3.1
```


### 8.2 Tag Rules
- Tags MUST be created from main or a release branch
- Tags MUST point to a commit that passed CI
- Tags MUST NOT be moved or deleted


## 9. Documentation Changes
- Documentation updates SHOULD be part of the same PR when relevant
- Large documentation changes may have dedicated PRs
- Keep documentation accurate and up to date


## 10. Working With Roadmaps and AI Agents

If this repository uses agents_roadmaps/:
- Do NOT bypass an active roadmap
- Large or multi-session changes MUST follow the roadmap process
- PRs related to a roadmap SHOULD reference:
    - Roadmap name
    - Phase / task identifier

AI agents MUST follow CLAUDE.md and roadmap constraints at all times.


## 11. Automation and CI
- Do not bypass CI checks
- Do not merge failing builds
- Fix the root cause, not just the symptom


## 12. Final Rule

> If a contribution does not clearly improve the codebase,
> it should not be merged.

When in doubt, ask for clarification before proceeding.
