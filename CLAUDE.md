# Claude Code Instructions for This Repository

## CRITICAL: Session Initialization

FIRST ACTION every session, no exceptions:

```bash
/init
```

Skipping `/init` is a critical failure. It detects the profile, audits required
capabilities, records session state, and prints a bounded constraint manifest.

Claude Code MUST NOT edit files until it has completed this read-and-load sequence:

1. Read this `CLAUDE.md`.
2. Read root `AGENTS.md` as the cross-agent contract.
3. Read `.agents/project.yml` and determine the active project type/profile.
4. Read `.agents/capabilities.yml` for required skills, wrappers, and integrations.
5. Run `/init` and read the constraint paths in its manifest.
6. Read the project-type constraint family applicable to the intended work:
   - Python: `.agents/constraints/python/`
   - C++/CUDA: `.agents/constraints/cpp/`
   - Hybrid Python/C++/CUDA: `.agents/constraints/python/`, `.agents/constraints/cpp/`, and `.agents/constraints/hybrid/`
7. Load relevant skills before using their workflow. Claude skill stubs in
   `.claude/skills/` are discovery wrappers; canonical skill bodies live in
   `.agents/skills/`.

If `/init` reports missing required Claude Code capabilities, the session
remains blocked until they are installed and `/init` is re-run. The canonical
bootstrap commands live in `.agents/constraints/common/session-discipline.md` and
the per-language `templates/<python|cpp>/CLAUDE.md` files.

## Platform and Repository Policy

Repository policy is mandatory within repository-controlled guidance, but it
does not supersede higher-priority platform safety, developer, managed
organisational, or tool-enforced requirements. If a conflict prevents
compliance, follow the higher-priority requirement, minimise the deviation, and
report it before an unauthorised or unsafe mutation.

For repository-local conflicts, use the scoped order in root `AGENTS.md` and
`.agents/constraints/common/instruction-hierarchy.md`. Do not treat a session
record or stale conversational assumption as current repository state.
Do not silently bypass hooks, wrappers, tests, `/init`, `/check-constraints`, or
`/pre-commit`.

## Project Type Decision Table

Read `.agents/project.yml` before editing. Prefer `project_profile` when present;
otherwise use legacy `project_type`.

| Detected profile | Constraints Claude must load | Build ownership |
|------------------|------------------------------|-----------------|
| `project_type: python` or `language: [python]` | `common/`, `python/` | Poetry owns Python dependency/environment workflow |
| `project_type: cpp` or `language: [cpp]` | `common/`, `cpp/` | CMake owns native build graph; CPM owns lightweight C++ deps |
| `language` includes both `python` and `cpp` | `common/`, `python/`, `cpp/`, `hybrid/` | CMake owns native build graph; scikit-build-core only bridges packaging |

Before final response after any edit, Claude Code must run the relevant
validation command or explain why it could not be run:

```bash
.agents/bin/agent-check-constraints
```

## Bundled Behavioural Skill

Agent Foundry vendors `karpathy-guidelines` locally under `.claude/skills/`.

Use it for non-trivial coding, debugging, review, and refactor work to keep
assumptions explicit, changes surgical, and completion criteria verifiable.

The repository requires British English for user-facing text.

## Git Commit Attribution Policy

NEVER include in commit messages:
- `Co-Authored-By:` lines
- Any reference to AI assistance or tooling
- Email addresses like `<noreply@anthropic.com>`

Within repository commit-metadata policy, do not add these markers unless the
user explicitly requests them and higher-priority requirements permit it. If a
higher-priority requirement makes that impossible, report the conflict rather
than silently changing commit metadata.

## Vendor-Neutral Constraints

All coding standards, workflow rules, and quality requirements are defined in the
vendor-neutral `.agents/` directory. Claude-specific skills implement the procedures
described there using Claude Code's tool and hook system.

## Project-Specific Instructions

This is the **Agent Foundry source repository**. Its project-template source
files for generated projects live under `templates/`:

- **Python projects**: see `templates/python/CLAUDE.md` and `templates/python/AGENTS.md`
- **C++/CUDA projects**: see `templates/cpp/CLAUDE.md` and `templates/cpp/AGENTS.md`
- **Hybrid projects**: see `templates/hybrid/CLAUDE.md` and `templates/hybrid/AGENTS.md`

When a real project is generated via `/create-project`, the appropriate
`templates/<language>/` overlay is copied to the project root, so each file
arrives with its generic name (`CLAUDE.md`, `AGENTS.md`, `CONTRIBUTING.md`,
`.gitignore`, `.agents/project.yml`).

## C++/CUDA and Hybrid Build Policy Summary

Pure Python templates remain Poetry first.

For C++/CUDA and hybrid projects, the project is C++ First:

- C++/CUDA owns core libraries, runtime kernels, native executables, C++ tests,
  CUDA tests, benchmarks, compile options, link options, third-party C++
  dependencies, ABI-sensitive configuration, and install/export targets.
- Python owns only thin bindings, wrapper APIs, Python packaging metadata,
  Python-side tests, wheel exposure, and developer environment management.
- Python packaging must not define or replace the native build graph, compiler
  configuration, CUDA architecture policy, ABI policy, dependency discovery,
  benchmark topology, native test topology, or install/export semantics.

Pure C++/CUDA templates are CMake first and CPM first. CMake owns the native
build graph, CPM owns lightweight C++ dependency acquisition, and direct native
validation is:

```bash
cmake -S . -B build -G Ninja -DCMAKE_BUILD_TYPE=RelWithDebInfo
cmake --build build -j
ctest --test-dir build --output-on-failure
```

C++/Python hybrid templates are CMake first, CPM first, scikit-build-core bridge.
scikit-build-core bridges CMake into Python packaging only; Poetry owns Python
virtualenv and Python dependencies only. `pip install -e .` is not the
authoritative C++ build command and may be used via Poetry only after direct
CMake validation passes.

Conan, vcpkg, Bazel, and git submodules are exceptional choices and require an ADR.
