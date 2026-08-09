# Server-local CI artefact storage and rolling retention

Use this contract when CI runs on a persistent self-hosted runner or another
operator-controlled server that triggers the workflow. GitHub Actions artefact
uploads are not the primary release transport: they consume repository quota,
are not a durable rollback store, and can fail before the host is able to
promote a verified build.

## Storage boundary

- Put CI artefacts in a fixed, operator-approved data root such as
  `/data/ci-artifacts/<repository>` or `~/data/ci-artifacts/<repository>`.
  Resolve `~` to the runner account's absolute home during provisioning.
- Keep this store separate from the deployment root, immutable production
  releases, databases, uploads, logs, credentials, and the runner workspace.
- The self-hosted runner identity owns the store and may write only beneath its
  repository namespace. The `deploy` identity may read a selected immutable
  record through one fixed host helper, but must not write or prune the store.
- The root is trusted host configuration. A branch, workflow input, archive
  name, release id, or event payload MUST NOT select or escape it.
- Record each artefact beside a manifest containing at least the repository,
  branch, immutable source SHA, workflow run id, release id, digest, target
  compatibility, creation time, status, and retention reason.

## Build and promotion contract

1. Validate source and build once on the triggering self-hosted server.
2. Write the complete bytes and manifest into a run-specific staging directory
   on the same approved filesystem.
3. Verify the digest, manifest, archive paths, and compatibility before an
   atomic commit into the immutable artefact record.
4. Downstream jobs refer to the record id and digest; they do not rebuild and
   do not resolve a branch, tag, or mutable `latest` path.
5. A protected deploy or publish boundary reads that exact record through a
   fixed host interface. It must fail closed when the record is missing,
   malformed, superseded, or has a different digest.

Do not use `actions/upload-artifact` or `actions/download-artifact` for the
primary build, release, or deployment bytes under this contract. If a job must
cross to a different host and no approved server-side interface exists, obtain
operator approval for a temporary GitHub artefact with a retention of no more
than one day; it is a transport convenience, never the rollback authority.

## Rolling retention

The default small rolling set is:

- the three newest successful, verified `master` records;
- the two newest successful, verified `develop` records; and
- any record explicitly marked `live`, `rollback`, `pinned`, or `held`.

Records from pull requests, feature branches, release branches, hotfix
branches, tags, other refs, cancelled runs, and failed builds are not retained
as release artefacts. Preserve failure information in ordinary workflow logs or
a short-lived, separately governed diagnostic store when required; do not turn
it into an unbounded artefact history.

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
