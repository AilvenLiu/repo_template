# Session Discipline Constraints

> **This document defines mandatory session continuity and decision hygiene constraints for all AI agents.**
> These rules apply to both Python and C++/CUDA projects.
> Violations are considered critical failures.

## Overview

This document establishes requirements for maintaining continuity across sessions,
managing decisions properly, and knowing when to stop and ask for guidance.
AI agents have no memory between sessions, so all important information must be
externalized to files.

## 1. Session Continuity and State Discipline

### 1.1 The Fundamental Problem

**AI agents have no memory across sessions.**

This means:
- Conversational context is lost between sessions
- Decisions made in previous sessions are forgotten
- Constraints agreed upon are not remembered
- Progress and state are not retained

### 1.2 The Solution: Externalize Everything

Claude Code MUST:

- **Assume no memory across sessions**
  - Never rely on previous conversations
  - Always read state from files
  - Treat each session as a fresh start

- **Externalize all long-lived decisions, constraints, and progress into files**
  - Write decisions to appropriate files
  - Document constraints in code or roadmaps
  - Track progress in roadmap.yml or session handoffs

- **Never rely on conversational memory for:**
  - Architecture decisions
  - Constraints and invariants
  - Roadmap state
  - Dependency versions
  - Configuration choices
  - Build settings
  - Testing requirements
  - Performance targets
  - Security requirements

### 1.3 Where to Externalize Information

**For roadmap work:**
- `agent_roadmaps/<active>/INVARIANTS.md` - Immutable constraints
- `agent_roadmaps/<active>/prompt.md` - Objectives and plan
- `agent_roadmaps/<active>/roadmap.yml` - Current state and progress
- `agent_roadmaps/<active>/sessions/` - Session handoff files

**For architecture decisions:**
- Architecture Decision Records (ADRs) if project uses them
- `docs/architecture/` directory
- Code comments for local decisions
- `ARCHITECTURE.md` in roadmap directory

**For configuration and dependencies:**
- `README.md` - Installation and setup instructions
- `requirements.txt` / `pyproject.toml` (Python) - Dependency versions
- `conanfile.txt` / `conanfile.py` / `vcpkg.json` (C++/CUDA) - Dependency versions
- `CMakeLists.txt` (C++/CUDA) - Build configuration
- `.python-version` (Python) - Python version
- Configuration files (`.toml`, `.yaml`, `.json`)

**For constraints and rules:**
- `CLAUDE.md` - Language-specific constraints
- `CONTRIBUTING.md` - Contribution guidelines
- Code comments - Local constraints
- Test files - Expected behavior

### 1.4 Session Handoff Protocol

**For roadmap work, every session MUST end with:**

1. Create a new handoff record under `agent_roadmaps/<active>/sessions/`
   - Filename: `session-YYYY-MM-DD-HH-MM.md`
   - Template structure:
     ```markdown
     # Session Handoff: YYYY-MM-DD HH:MM

     ## Work Completed
     - List of completed tasks
     - Files modified
     - Decisions made

     ## Current State
     - Current phase/task
     - Progress percentage
     - Blockers or issues

     ## Next Steps
     - What should be done next
     - Dependencies or prerequisites
     - Estimated effort

     ## Notes
     - Important context
     - Warnings or cautions
     - References
     ```

2. Update `roadmap.yml` with current state
   - Mark completed tasks
   - Update phase status
   - Note any timeline changes

3. Commit both files together

### 1.5 Starting a New Session

**At the beginning of EVERY session, Claude Code MUST:**

1. Check for active roadmaps (see roadmap-awareness.md)
2. If active roadmap exists:
   - Read `INVARIANTS.md`
   - Read `prompt.md`
   - Read `roadmap.yml`
   - Read latest session handoff
3. Read relevant constraint files:
   - `CLAUDE.md`
   - `CONTRIBUTING.md`
   - `.claude/constraints/common/*.md`
4. Read relevant configuration files
5. Understand current state before proceeding

## 2. Decision Hygiene

### 2.1 The Problem of Re-Discussion

Without proper decision hygiene:
- Same decisions are debated repeatedly
- Settled issues are reopened
- Time is wasted on redundant discussions
- Inconsistencies emerge across sessions

### 2.2 Avoiding Re-Discussion

Claude Code MUST:

- **Avoid re-discussing previously settled decisions**
  - Check for existing decisions before proposing changes
  - Respect documented choices
  - Only revisit if explicitly requested by user

- **Record irreversible or high-impact decisions explicitly in:**
  - Architecture Decision Records (ADRs) if project uses them
  - Roadmap `INVARIANTS.md`
  - Code comments for local decisions
  - `ARCHITECTURE.md` or similar documentation

### 2.3 Decision Documentation Format

When documenting decisions, include:

1. **Context**: What is the situation?
2. **Decision**: What was decided?
3. **Rationale**: Why was this decided?
4. **Consequences**: What are the implications?
5. **Alternatives**: What other options were considered?

**Example ADR format:**
```markdown
# ADR-001: Use PostgreSQL for Primary Database

## Status
Accepted

## Context
We need a relational database for storing user data, transactions,
and application state. Requirements include ACID compliance, JSON
support, and strong community support.

## Decision
We will use PostgreSQL 14+ as our primary database.

## Rationale
- Strong ACID compliance
- Excellent JSON/JSONB support
- Mature ecosystem and tooling
- Strong community and documentation
- Good performance characteristics

## Consequences
- Team needs PostgreSQL expertise
- Deployment requires PostgreSQL infrastructure
- Migration from other databases would be complex

## Alternatives Considered
- MySQL: Less robust JSON support
- MongoDB: Not ACID compliant for our use case
- SQLite: Not suitable for production scale
```

### 2.4 When to Ask Before Changing

Claude Code MUST ask before changing:

**For Python projects:**
- Public API interfaces
- Architectural boundaries
- Dependency versions (major updates)
- Python version requirements
- Testing framework
- Build/packaging system
- Security-related code

**For C++/CUDA projects:**
- Public API interfaces
- Architectural boundaries
- Build system structure
- Dependency versions (major updates)
- CUDA compute capability requirements
- Memory management strategy
- Threading model
- Performance-critical code

**For all projects:**
- Database schema
- File formats
- Network protocols
- Configuration file structure
- Authentication/authorization logic
- Data validation rules
- Error handling strategy

### 2.5 Silent Reinterpretation is Forbidden

Claude Code MUST NOT:
- Reinterpret requirements without asking
- Change scope without approval
- Redesign architecture without discussion
- Modify constraints without permission
- Override documented decisions

**If uncertain about a decision, STOP and ASK.**

## 3. When to Stop and Ask

### 3.1 The Safety Rule

> **If Claude Code is unsure whether an action is allowed,**
> **it MUST stop and ask the user.**

Guessing, inferring intent, or "doing what seems reasonable" is not acceptable.

### 3.2 Situations Requiring User Confirmation

Claude Code MUST stop and ask when:

**Uncertainty about requirements:**
- Ambiguous specifications
- Conflicting constraints
- Unclear priorities
- Missing information

**High-risk operations:**
- Dependency updates (especially major versions)
- API changes (breaking changes)
- Database migrations
- Configuration changes
- Security-related code
- Performance-critical code
- Memory management decisions (C++/CUDA)
- CUDA kernel launch configurations (C++/CUDA)

**Scope changes:**
- Work outside current roadmap phase
- Additional features not in requirements
- Architectural changes
- New dependencies

**Constraint violations:**
- Action might violate documented constraints
- Conflict between different constraint sources
- Unclear authority hierarchy

**Technical decisions:**
- Multiple valid approaches exist
- Trade-offs between different solutions
- Long-term implications
- Irreversible changes

### 3.3 How to Ask

When stopping to ask, Claude Code SHOULD:

1. **Explain the situation clearly**
   - What is being attempted
   - Why it requires confirmation
   - What the options are

2. **Present options with trade-offs**
   - List possible approaches
   - Explain pros and cons
   - Recommend a preferred option (if appropriate)

3. **Wait for explicit user response**
   - Do not proceed without confirmation
   - Do not assume user intent
   - Do not make the decision unilaterally

**Example:**
```
I need your guidance on a dependency update:

Situation:
- Current: numpy 1.24.3
- Available: numpy 2.0.0 (major version update)
- Our code uses numpy.float (deprecated in 2.0)

Options:
1. Stay on numpy 1.24.3 (safe, but missing new features)
2. Update to numpy 2.0.0 and fix deprecations (requires code changes)
3. Update to numpy 1.26.4 (latest 1.x, includes backported fixes)

Recommendation:
Option 3 provides bug fixes without breaking changes.

How would you like to proceed?
```

### 3.4 Applies Especially To

This safety rule applies especially to:

**For Python projects:**
- Dependency updates
- API changes
- Database migrations
- Configuration changes
- Security-related code
- Testing framework changes
- Package structure changes

**For C++/CUDA projects:**
- Memory management decisions
- CUDA kernel launch configurations
- Build system changes
- Dependency updates
- API changes
- Compiler flag changes
- Threading model changes

**For all projects:**
- Architectural decisions
- Breaking changes
- Data format changes
- Protocol changes
- Security implementations
- Performance optimizations with trade-offs

## 4. Examples

### 4.1 Example: Good Session Continuity

**Session 1:**
```
User: "Add JWT authentication to the API"
Agent: "I'll add JWT authentication. Let me document the approach..."
[Creates ADR-005-jwt-authentication.md]
[Implements JWT authentication]
[Commits with documentation]
```

**Session 2 (different day):**
```
Agent: [Reads ADR-005-jwt-authentication.md]
Agent: "I see JWT authentication was implemented in the previous session
       using the PyJWT library with RS256 algorithm. How can I help today?"
```

### 4.2 Example: Bad Session Continuity

**Session 1:**
```
User: "Add JWT authentication to the API"
Agent: "I'll use PyJWT with RS256 algorithm"
[Implements JWT authentication]
[No documentation created]
```

**Session 2 (different day):**
```
Agent: "I don't see any authentication. Would you like me to add it?"
[Agent has no memory of previous session]
[User must explain again]
```

### 4.3 Example: Good Decision Hygiene

```
User: "Should we use PostgreSQL or MongoDB?"
Agent: [Checks for existing ADRs]
Agent: "I found ADR-001 which documents the decision to use PostgreSQL.
       The decision was made based on ACID compliance requirements and
       JSON support needs. Is there a reason to reconsider this decision?"
```

### 4.4 Example: Bad Decision Hygiene

```
User: "Should we use PostgreSQL or MongoDB?"
Agent: "Let's discuss the options..."
[Agent doesn't check for existing decisions]
[Wastes time re-discussing settled issue]
```

### 4.5 Example: Good Safety Rule Application

```
User: "Update all dependencies to latest versions"
Agent: "I found several dependencies with major version updates:
       - numpy: 1.24.3 -> 2.0.0 (breaking changes in API)
       - pandas: 1.5.3 -> 2.1.0 (deprecations removed)
       - requests: 2.31.0 -> 3.0.0 (not released yet, you may mean 2.32.0)

       Major version updates can break existing code. Would you like me to:
       1. Update only patch/minor versions (safe)
       2. Update all to latest (requires testing and potential fixes)
       3. Review each major update individually

       I recommend option 3 for safety."
```

### 4.6 Example: Bad Safety Rule Application

```
User: "Update all dependencies to latest versions"
Agent: [Updates all dependencies without checking]
Agent: [Breaks code due to API changes]
Agent: "I updated all dependencies but some tests are failing..."
```

## 5. Summary

**Key Rules:**

1. **ASSUME no memory across sessions**
2. **EXTERNALIZE all decisions, constraints, and progress to files**
3. **CREATE session handoffs for roadmap work**
4. **READ state files at session start**
5. **AVOID re-discussing settled decisions**
6. **DOCUMENT high-impact decisions explicitly**
7. **ASK before changing documented decisions**
8. **STOP and ASK when uncertain**
9. **NEVER guess or infer intent for high-risk operations**

**Enforcement:**
- These rules are mandatory and non-negotiable
- Violations indicate agent is operating outside its mandate
- Session should be terminated if violations occur

**Benefits:**
- Continuity across sessions
- Consistent decision-making
- Reduced redundant work
- Clear audit trail
- Better collaboration
- Fewer mistakes
