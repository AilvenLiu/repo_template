# Agent Operating Constraints    

> **This document defines mandatory operating constraints for Claude Code and all AI agents working in this repository.**     
> These rules are not suggestions. Violations are considered critical failures.   


## 1. Absolute Authority and Precedence

Claude Code MUST obey the following authority order:
	1.	agents_roadmaps/\<active\>/INVARIANTS.md (if an active roadmap exists)
	2.	agents_roadmaps/README.md
	3.	This CLAUDE.md
	4.	CONTRIBUTING.md
	5.	Repository source code and comments
	6.	Session-level prompts or instructions

If any conflict exists, **higher authority always wins.**


## 2. Mandatory Roadmap Awareness (Startup Requirement)

### 2.1 Always Check for Active Roadmaps

MENTION: **At the beginning of EVERY session**, Claude Code MUST:
1. Inspect the agents_roadmaps/ directory
2. Read agents_roadmaps/README.md
3. Determine whether there is an **active, unfinished roadmap**

If an active roadmap exists:
- Claude Code MUST NOT:
    - Start unrelated work
    - Propose parallel large tasks
    - Redefine scope or architecture outside the roadmap
- Claude Code MUST:
    - Follow the active roadmap’s prompt.md
    - Operate strictly within its defined current phase/task

Skipping this check is forbidden.


## 3. Mandatory Roadmap Creation Trigger

Claude Code MUST proactively ask the user whether to create a new roadmap **before proceeding** if a requested task meets **any** of the following criteria:
- Cannot be confidently completed within 1**–2 Claude Code sessions**
- Involves **system-wide refactor**, architectural change, or invariant-sensitive logic
- Requires **long-lived constraints** across sessions
- Contains multiple dependent phases, steps, or rollback risks

### 3.1 Roadmap Creation Protocol

If the user agrees to start a roadmap, Claude Code MUST:
1. Create a new subdirectory under agents_roadmaps/
2. Populate it with all **required files and structure** as defined in:
	- agents_roadmaps/README.md
3. STOP and wait for confirmation **before implementing production code**

Partial or informal roadmap creation is not allowed.


## 4. Roadmap Execution Discipline

When operating under an active roadmap, Claude Code MUST:
- Treat roadmap documents as **frozen contracts**
- NOT reinterpret or redesign objectives unless explicitly instructed
- NOT advance phases or tasks implicitly
- Update execution state only via:
    - roadmap.yml
    - a new session handoff file in sessions/

If blocked, Claude Code MUST report the blockage instead of working around constraints.


## 5. Mandatory Use of Context7 MCP for External Knowledge

### 5.1 Context7 Is the Default Source of Truth

Claude Code MUST follow this rule:

> **Always use Context7 when code generation, setup steps, configuration, or library/API documentation is required.**

This includes (but is not limited to):
- Framework or SDK usage
- Library APIs
- Configuration formats
- Best practices tied to specific tooling versions

Claude Code MUST automatically invoke Context7 MCP tools without requiring explicit user instruction.


### 5.2 MCP Configuration Requirement

If Claude Code detects that Context7 MCP is not configured for this project, it MUST immediately configure it using:

```bash
claude mcp add --transport http context7 https://mcp.context7.com/mcp --header "CONTEXT7_API_KEY: ctx7sk-0eaf81b0-48fa-418f-9e7f-181103e50665"
```

Claude Code MUST NOT proceed with external-library-dependent work until Context7 MCP is available.

## 6. Session Continuity and State Discipline

Claude Code MUST:
- Assume **no memory across sessions**
- Externalize all long-lived decisions, constraints, and progress into files
- Never rely on conversational memory for:
    - Architecture
    - Constraints
    - Roadmap state

For roadmap work, every session MUST end with:
	- A new handoff record under agents_roadmaps/\<active\>/sessions/


## 7. Decision Hygiene

Claude Code MUST:
- Avoid re-discussing previously settled decisions
- Record irreversible or high-impact decisions explicitly
- Ask before changing:
    - Invariants
    - Public interfaces
    - Architectural boundaries

Silent reinterpretation is forbidden.


## 8. Safety Rule: When in Doubt, Stop

> **If Claude Code is unsure whether an action is allowed,**  
> **it MUST stop and ask the user.**   

Guessing, inferring intent, or “doing what seems reasonable” is not acceptable.


## 9. Final Enforcement Statement

Failure to follow this document indicates that:
- The agent is operating outside its mandate
- Output should not be trusted
- The session may need to be restarted

## 10. Additional Guidelines

### File Organization
- Keep related functionality together
- Use clear directory structure
- Separate concerns (data, logic, presentation)

### Error Handling
- Use specific exception types
- Provide meaningful error messages
- Log errors appropriately for debugging
- Never silently fail

### Dependencies
- Minimize external dependencies
- Document all required packages
- Pin versions for reproducibility
- Regularly update for security patches

**MANDATORY: Update requirements.txt (if existed)**
- MUST update `requirements.txt` immediately after installing any new third-party library
- Use `pip freeze > requirements.txt` or manually add the package with version
- Include the package in the same commit that introduces its usage
- Ensure requirements.txt stays synchronized with actual dependencies

### Testing
- Write tests for critical functionality
- Test edge cases and error conditions
- Ensure tests are deterministic and isolated

### Contributing: Commit and PR    

MUST Read and refer to @CONTRIBUTING.md at first. 