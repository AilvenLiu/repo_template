# Python Dependency and Environment Policy

> Poetry owns Python environments, dependency resolution, and lock files. Use
> repository wrappers for changes so agent behavior and checked-in state remain
> deterministic.

## Mandatory authority

For every project with a Python component:

- `pyproject.toml` declares Python metadata and dependencies.
- `poetry.lock` is committed and changes with the manifest.
- `poetry.toml` sets `virtualenvs.in-project = true` and disables inherited
  system site packages.
- Poetry creates and operates `.venv/`; do not create or activate a manual venv.
- Application, test, and tool commands run through Poetry or a repository wrapper.
- Python 3.10 or newer is required unless a stricter project requirement applies.

Direct pip/pip3 package installation, requirements-only authority, direct
`poetry add`, and manual dependency-file edits are forbidden. The documented
hybrid editable-install command is only a scikit-build-core packaging bridge
after direct CMake validation; it is not a dependency workflow.

## Session-start checks

Before Python or hybrid work:

```bash
.agents/bin/agent-python-env-setup verify
```

The check must establish:

1. Poetry is available from the approved isolated tool installation (normally
   pipx or a pinned development/CI image).
2. `poetry.toml` configures an in-project environment.
3. Any existing Poetry environment resolves inside the repository.
4. The selected interpreter satisfies `pyproject.toml`.
5. An externally activated `VIRTUAL_ENV` is not shadowing Poetry/pyenv selection.
6. Custom package sources, when declared, use HTTPS, contain no embedded
   credentials, and have an explicit reviewed priority.

A project with no custom source uses Poetry's default PyPI source. Do not force a
regional mirror into a general template or silently rewrite a project's approved
index. Repository or organization policy may declare a mirror or private index;
credentials belong in the approved secret/configuration mechanism, never in
`pyproject.toml`.

If a mandatory check fails, stop mutation, report the exact failure and remediation,
and wait for required operator action. Do not falsify session state or weaken the
check.

## Dependency changes

Use the guarded workflow for add, remove, update, or version changes:

```bash
.agents/bin/agent-dependency add <package> [version] [--dev]
```

The workflow must update `pyproject.toml` and `poetry.lock` together. Review both
files for unexpected transitive changes, source changes, Python-version changes,
and platform-specific markers. Commit the manifest, lock file, code, tests, and
documentation for one dependency change together.

For a hybrid PEP 621 manifest, the wrapper must support both inline and
multi-line dependency arrays, validate the candidate TOML before retaining it,
and refresh `poetry.lock`. If validation or resolution fails, it must restore
both the manifest and lock file to their original bytes; reporting failure
while leaving either file half-updated is forbidden.

For hybrid projects:

- Python packages still use the guarded Poetry workflow.
- C++ source dependencies use the CMake/CPM workflow.
- CUDA, drivers, compilers, and binary/system SDKs are discovered prerequisites,
  not Poetry or CPM packages unless an approved ADR says otherwise.

## Version and source policy

- Pin the Python interpreter/toolchain to the reproducibility level required by
  the project and CI matrix.
- Use dependency ranges only when compatibility is tested and lock-file updates
  are reviewed.
- Pin release-critical build tools and native ABI inputs deliberately.
- Treat a package-index URL or priority change as a supply-chain policy change,
  not a routine package addition.
- Use immutable hashes/signatures/provenance where the packaging ecosystem and
  project risk require them.

Example source declarations are project policy, not universal defaults:

```toml
[[tool.poetry.source]]
name = "approved-internal"
url = "https://packages.example.invalid/simple/"
priority = "supplemental"
```

Never embed a username, password, token, or environment-specific secret in this
block.

## Poetry provisioning

Provision pipx with the operating-system package manager or a pinned tool image,
then install Poetry into its isolated environment. Do not install Poetry into the
project or system interpreter.

```bash
pipx install poetry
poetry --version
```

CI images may pre-provision a reviewed Poetry version. Record and pin that version
in the image or workflow rather than downloading an unreviewed latest release in
every job.

## Validation and closure

Before handoff:

```bash
poetry check
poetry install
.agents/bin/agent-build test
.agents/bin/agent-precommit
.agents/bin/agent-check-constraints
```

Verify that:

- the environment path is inside the project
- manifest and lock state agree
- custom sources are approved and secret-free
- imports and tests use the locked environment
- generated wheels or hybrid bindings were tested through the profile build
  authority
- no dependency or package-source change is hidden in unrelated edits

Missing Poetry, interpreter, lock file, required quality tools, or source access
is a blocking provisioning failure. It is not permission to fall back to direct
pip, system Python, or skipped validation.
