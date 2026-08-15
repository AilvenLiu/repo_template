# Server-local CI artefact storage and rolling retention

Use this contract for every CI artefact that must survive a job or host boundary,
whether the build runs on a persistent self-hosted runner, another
operator-controlled server, or GitHub-hosted infrastructure. GitHub Actions
artefact storage is default-deny: uploads consume repository quota, are not a
durable rollback store, and can fail before a verified build can be promoted.
A GitHub-hosted build must use a fixed operator-controlled local store, a fixed
direct transfer, or a protected build-and-promote job; if none exists, stop for
provisioning rather than silently using Actions artefact storage.

## Storage boundary

- Put CI artefacts in a fixed, operator-approved data root such as
  `/data/ci-artifacts/<repository>` or `~/data/ci-artifacts/<repository>`.
  Resolve `~` to the runner account's absolute home during provisioning.
- Keep this store separate from the deployment root, immutable production
  releases, databases, uploads, logs, credentials, and the runner workspace.
- A persistent self-hosted runner identity owns the store and may write only
  beneath its repository namespace. The `deploy` identity may read a selected
  immutable record through one fixed host helper, but must not write or prune.
- A GitHub-hosted job MUST NOT receive either the runner or `deploy` identity.
  It reaches only a separate repository- and environment-scoped writer interface
  with a fixed endpoint and namespace; it may create one digest-verified staging
  record but cannot list, prune, delete, or access production state. The host
  interface validates event SHA and digest before atomically committing it.
- The root is trusted host configuration. A branch, workflow input, archive
  name, release id, or event payload MUST NOT select or escape it.
- Record each artefact beside a manifest containing at least the repository,
  branch, immutable source SHA, workflow run id, release id, digest, target
  compatibility, creation time, status, and retention reason.

## Build and promotion contract

1. Validate source and build once on the trusted build host. A GitHub-hosted
   build must commit to the fixed operator-controlled store through a reviewed
   direct interface or complete its protected promotion in the same job.
2. Write the complete bytes and manifest into a run-specific staging directory
   on the same approved filesystem.
3. Verify the digest, manifest, archive paths, and compatibility before an
   atomic commit into the immutable artefact record.
4. Downstream jobs refer to the record id and digest; they do not rebuild and
   do not resolve a branch, tag, or mutable `latest` path.
5. A protected deploy or publish boundary reads that exact record through a
   fixed host interface. It must fail closed when the record is missing,
   malformed, superseded, or has a different digest.

Do not use `actions/upload-artifact`, `actions/download-artifact`, the Actions
artefact API or CLI, or an equivalent GitHub byte-storage path for build, test,
diagnostic, release, deployment, or rollback bytes under this contract. A
different host, multi-job workflow, GitHub-hosted runner, manual dispatch, or
generic operator approval is not an exception.
A temporary GitHub artefact is permitted only when **both** conditions are met:
1. Documented technical necessity shows the fixed local store, fixed direct
   transfer, and approved pull interface demonstrably cannot meet a concrete
   cross-host need.
2. The current user explicitly requests that specific upload. A durable,
   reviewed policy may carry prior explicit user authorisation only when it
   names the exact GitHub surface and exception.

The exception record MUST identify its workflow and surface, producer, consumer,
environment, non-secret contents, positive size limit, source SHA, digest,
technical necessity, and user request. It MUST expire within one day and never
be the release or rollback authority. That record is a durable-policy audit
gate; it never substitutes for the actual explicit user authorisation. Keep the
immutable local record until normal retention can safely prune it.

### Exception record schema

Record a workflow exception in `.agents/github-artifact-exceptions.json`. The
file is an object with `version: 1` and an `exceptions` array. Each entry binds
one exception to exactly one action line, so any edit that moves or renames the
step invalidates the record and forces re-review.

Required non-empty string fields: `workflow` (repository-relative POSIX path
under `.github/workflows/`), `surface` (`actions/upload-artifact` or
`actions/download-artifact`), `technical_necessity`, `user_request`,
`request_reference`, `producer`, `consumer`, `environment`, `contents`,
`artifact_name` (matching the step's single `with.name`), `source_sha`, and
`digest`.

Required non-string fields: `action_line` and `size_limit_bytes` as positive
integers, `retention_days: 1`, `non_secret: true`,
`release_or_rollback_authority: false`, and `reviewed: true`. An
`actions/download-artifact` entry additionally sets `producer_upload_line` to
the positive action line of its approved upload, which MUST be in the same
workflow and carry the same `artifact_name`, `source_sha`, and `digest`.

The workflow step itself MUST pin the action to a full 40-character commit SHA,
declare exactly one `with.name`, and — for an upload — set exactly one
`with.retention-days: 1`. The normal constraint check fails closed when an
Actions artifact route lacks an exact valid record, and an artefact route hidden
in a composite action, local helper script, `gh run download`, or the Actions
artefact API is never exception-eligible at all.

```json
{
  "version": 1,
  "exceptions": [
    {
      "workflow": ".github/workflows/release.yml",
      "surface": "actions/upload-artifact",
      "action_line": 42,
      "artifact_name": "staging-handoff",
      "technical_necessity": "The hosted build cannot reach the local store and no fixed direct transfer or pull interface exists for this environment.",
      "user_request": "The current user explicitly requested this one-day upload on 2026-08-14.",
      "request_reference": "Task request: temporary staging hand-off only.",
      "producer": "build",
      "consumer": "deploy",
      "environment": "staging",
      "contents": "Non-secret signed release archive and manifest.",
      "source_sha": "0000000000000000000000000000000000000000",
      "digest": "sha256:0000000000000000000000000000000000000000000000000000000000000000",
      "size_limit_bytes": 1048576,
      "retention_days": 1,
      "non_secret": true,
      "release_or_rollback_authority": false,
      "reviewed": true
    }
  ]
}
```

## Rolling retention

The default small rolling set is:

- the three newest successful, verified `master` records;
- the two newest successful, verified `develop` records; and
- any record explicitly marked `live`, `rollback`, `pinned`, `held`, or
  `activating`.

Records from pull requests, feature branches, release branches, hotfix
branches, tags, other refs, cancelled runs, and failed builds are not retained
as release artefacts. Preserve failure information in ordinary workflow logs or
a short-lived local diagnostic store when required; do not turn it into an
unbounded artefact history or a GitHub-upload workaround.

Branch classification comes from the immutable workflow event and recorded
source ref, not from a manually supplied name. A successful `develop` record
may be retained for validation and promotion review, but retention does not
grant it production-release or deployment authority.

Pruning MUST:

- acquire a repository-specific host lock;
- run in dry-run mode before the first activation and after policy changes;
- preserve live, rollback, pinned, held, activating, and unknown-state records;
- refuse malformed manifests, symlink escapes, digest mismatches, and paths
  outside the canonical store; and
- delete only explicitly identified expired records beneath the repository
  root, never an entire shared filesystem or runner workspace.

Run the cleanup after a successful commit, on a host timer, and before a
release promotion. Before cleanup or promotion can race, acquire the same
repository lock and mark the selected record `activating` or `held`; cleanup
must preserve that record until promotion or rollback records a terminal state.
Monitor record count, byte usage, failed cleanup attempts, and free space. Host
rollback remains valid only while its retained record and its digest are
present; GitHub Actions artefact expiry must not affect it.
