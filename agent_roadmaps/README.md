# Agents Roadmaps - Authoritative Guide

**This document is authoritative for all AI agents (including Claude Code) operating in this repository.**   
Any violation of the rules defined here is considered a critical agent failure.


## 1. Purpose of agent_roadmaps/

The agent_roadmaps/ directory is the **single source of truth** for:
- Whether the repository is currently executing a **large, system-level, multi-session task**
- Which roadmap (if any) is **currently active**
- How AI agents must **initialize, constrain, execute, and hand off** such tasks across sessions

This mechanism exists to **prevent context loss, decision drift, and architectural regression** when tasks exceed one or two Claude Code sessions.


## 2. Global Rule: At Most One Active Roadmap

**MENTION: At most ONE roadmap may be active at any time.** 
- AI agents **MUST NOT** start, create, or propose a second roadmap while one is active
    - All work must either:
    - Continue the active roadmap, or
- Explicitly conclude it before starting a new one

Violation of this rule is forbidden.


## 3. Active Roadmap Status (MANDATORY CHECKPOINT)

Every agent session **MUST begin** by checking the following section.

### 3.1 Current Status

> **Active Roadmap**:    
> [] None   
> [x] Exists (see below)     

**If active, fill exactly one entry below**:   
- **Name** : <roadmap-name>
- **Path** : agent_roadmaps/\<roadmap-name\>/
- **Current Phase / Task** : \<as defined in roadmap.yml\>
- **Status** : active | blocked | completing

If **no roadmap is active**, this section MUST explicitly say:

> Active Roadmap: None    


## 4. When a New Roadmap MUST Be Created

An AI agent **MUST ask the user to create a new roadmap** if a task meets **any** of the following conditions:
- Cannot be confidently completed within **1-2 Claude Code sessions**
- Involves **system-wide refactor**, architectural change, or invariant-sensitive work
- Requires **long-lived constraints** that must survive context resets
- Has multiple dependent phases or non-trivial rollback risk

If the user agrees, the agent MUST create a new roadmap following Section 5 **before writing any implementation code**.


## 5. Mandatory Structure of a Roadmap Directory

When a roadmap is activated, a **dedicated subdirectory** MUST be created under agent_roadmaps/ with @agent_roadmaps/template/ as example.

```
agent_roadmaps/
`-- <roadmap-name>/
    |-- INVARIANTS.md
    |-- ROADMAP.md
    |-- roadmap.yml
    |-- prompt.md
    `-- sessions/
```

Each file has **strict semantics** defined below.


## 6. Required Files (Authoritative Definitions)

**Template:**    
Use @agent_roadmaps/template/ as example. 

### 6.1 INVARIANTS.md -- Constitutional Constraints

**Template:**     
Use @agent_roadmaps/template/INVARIANTS.md as example.

**Purpose:**     
Defines **non-negotiable, constitutional-level constraints** that override all other instructions.

Requirements:    
- Must be compatible with:
    - CLAUDE.md
    - CONTRIBUTING.md
    - The project's existing architectural and policy constraints
- Must clearly state:
    - What **must never change**
    - What **must always hold true**
    - What **requires explicit human approval to modify**

**Authority Order (highest):**    
1. INVARIANTS.md
2. ROADMAP.md
3. roadmap.yml
4. Session handoff notes
5. prompt.md


### 6.2 ROADMAP.md -- Long-Form Execution Manual

**Template:**    
Use @agent_roadmaps/template/ROADMAP.md as example.

**Purpose:**     
A **detailed, instructional, long-form document** describing the roadmap task in its entirety.

**Mandatory Characteristics:**     
- Written as a **step-by-step operational manual**  
- Explicitly defines:
- Overall objective
- Phases and their intent
- Non-goals
- Dependencies
- Risks and forbidden shortcuts
- May be long and verbose
**(verbosity is preferred over ambiguity)**

**FORBIDDEN:** ROADMAP.md must **NOT** be a TODO list or a timeline-only document.


### 6.3 roadmap.yml -- Canonical Execution State (Machine-Readable)

**Template:**     
Use @agent_roadmaps/template/roadmap.yml as example.

**Purpose:**     
Provides a **normalized, authoritative state machine** for the roadmap.

This file is the **only place** where execution progress is tracked.

#### 6.3.1 Required Top-Level Schema

```yaml
roadmap:
  name: <string>
  description: <string>

status:
  active: true | false
  blocked: true | false
  completed: true | false

current_focus:
  phase: <phase_id>
  task: <task_id>

phases:
  - id: <phase_id>
    title: <string>
    status: pending | active | completed | blocked
    tasks:
      - id: <task_id>
        title: <string>
        status: pending | active | completed | blocked
        notes: <optional string>
```

#### 6.3.2 Rules   

- Exactly **one** task may be active at any time
- current_focus MUST always point to that task
- Agents MUST NOT advance phases or tasks implicitly
- State changes must reflect **already completed work**, not intentions


### 6.4 prompt.md -- Session Initialization Prompt (Copy-Paste Only)

**Purpose:**     
Contains the **entire initialization prompt** for starting a new Claude Code session for this roadmap.

**STRICT RULES:**     
- Must contain **only** text intended to be copied verbatim into Claude Code
- Must NOT contain:
    - Commentary
    - Instructions to humans
    - Explanatory metadata
- Must explicitly instruct the agent to:
    - Read all roadmap files
    - Respect authority order
    - Operate only on current_focus

If content should **not** be copied into Claude Code, it **must not** be in this file.


### 6.5 sessions/ -- Session-to-Session Handoff Records

**Purpose:**     
Ensures **continuity across sessions and agent restarts.** 

**Rules:**    
- Each session MUST generate exactly one new file here
- Files are **append-only**
- No retroactive edits

**Recommended naming:**     

```
YYYY-MM-DD-<agent>-<index>.md
```

**Required structure per file:**    

```markdown
## Focus
- Phase: <phase_id>
- Task: <task_id>

## Work Completed
- ...

## Decisions Made
- ...

## Open Issues / Blockers
- ...

## Next Session Handoff
- ...
```


## 7. Agent Startup Checklist (MANDATORY)

Every Claude Code session MUST:
1. Read this agent_roadmaps/README.md
2. Determine whether a roadmap is active
3. If active:
    - Enter the roadmap directory
    - Follow prompt.md
4. If inactive:
    - Proceed normally, or
    - Ask the user whether to start a new roadmap if criteria in Section 4 are met


## 8. Final Enforcement Rule

> **If an agent is unsure whether an action is allowed,**    
> it MUST stop and ask the user.**    

Silent assumption is forbidden.
