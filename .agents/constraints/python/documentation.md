# Python Documentation

> Documentation is part of the product surface. It must describe the same
> Poetry-owned environment, repository wrappers, supported Python version, and
> behavior that the code and CI actually implement.

## Required documentation surfaces

Maintain the smallest relevant set:

- `README.md`: purpose, prerequisites, Poetry setup, common commands, and links
- public API docstrings: contract, parameters, return value, raised exceptions,
  side effects, and short examples where behavior is not obvious
- operator or deployment runbooks for stateful or production procedures
- architecture decisions for exceptional build or dependency choices
- changelog or release notes when the project publishes versions

Do not copy the same detailed procedure into several files. Keep one canonical
procedure and link to it from entrypoints.

## README contract

A Python-project README should use the repository's actual profile and wrappers:

````markdown
# Project Name

One paragraph describing the user problem and the project's boundary.

## Requirements

- The Python version declared in `pyproject.toml`
- pyenv and Poetry as required by this repository

## Setup

```bash
.agents/bin/agent-python-env-setup verify
poetry install
```

## Validate

```bash
.agents/bin/agent-build full
.agents/bin/agent-precommit
```
````

Never document direct pip installation, manual virtual-environment creation,
`requirements.txt` as an alternative authority, or `setup.py` as the project
build interface. Add dependencies through `.agents/bin/agent-dependency`.

Commands shown to users must be runnable from the documented directory. Include
required environment variables by name but never include real credentials.

## Docstrings

Document public modules, classes, functions, methods, and exceptions. Prefer a
consistent Google-style layout:

```python
from pathlib import Path


def load_records(path: Path, *, strict: bool = True) -> list[str]:
    """Load normalized records from a UTF-8 text file.

    Args:
        path: File containing one record per line.
        strict: Reject blank records when true.

    Returns:
        Normalized records in source order.

    Raises:
        FileNotFoundError: If ``path`` does not exist.
        ValueError: If strict mode encounters a blank record.
    """
```

Do not restate type annotations mechanically. Explain semantic constraints,
units, ownership, mutation, ordering, retries, security properties, and failure
modes. Keep examples deterministic and free of network or production side
effects.

## Comments and generated API documentation

Comments explain why an implementation is constrained, not what each line does.
Remove stale commented-out code. Link issue or ADR identifiers only when those
references are durable.

If the project uses Sphinx or another generator, add it through the guarded
dependency workflow and execute it inside Poetry:

```bash
.agents/bin/agent-dependency add sphinx --dev
poetry run sphinx-build -W -b html docs docs/_build/html
```

Do not modify `sys.path` in documentation configuration to compensate for a
broken package layout. Install the project through Poetry and import the same
package users import.

## Runbooks

A runbook must state:

- scope, owner, prerequisites, and authorization boundary
- exact inputs and commands, with placeholders clearly marked
- expected evidence and success conditions
- failure modes, rollback, safe retry behavior, and escalation path
- persistent-data boundaries and destructive steps
- last validation date when environment assumptions can expire

Host deployment runbooks must use `deploy-service`; GitHub Actions CI, auto-deployment, and auto-release runbooks must use `service-cicd`. Link to checked-in workflow and helper files rather than pasting divergent copies.

## Examples and security

- Use synthetic hostnames, identities, tokens, and data.
- Mark placeholders so they cannot be mistaken for working secrets.
- Do not recommend disabled certificate or SSH host verification.
- Do not show `shell=True`, unsafe deserialization, dynamic evaluation, insecure
  temporary files, or string-prefix path-containment checks as valid examples.
- Pin third-party CI actions to reviewed full commit SHAs in runnable snippets.
- State whether a command is read-only, mutating, privileged, or destructive.

## Keep documentation true

For every behavior-changing edit:

1. Find affected README, API, runbook, architecture, and configuration examples.
2. Update the canonical source rather than adding a second explanation.
3. Run documented commands where safe and record checks that could not run.
4. Check links, code examples, versions, paths, and CLI flags.
5. Run `.agents/bin/agent-precommit` and `.agents/bin/agent-check-constraints`.

Documentation that promises an untested command, unsupported version, missing
rollback, or different dependency/build authority is a correctness defect.
