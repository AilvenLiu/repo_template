# GitHub Actions trust and deployment boundary

## Select compute and deployment independently

Self-hosted CI compute (Pattern A) and restricted SSH deployment (Pattern B)
solve different problems and may be used together. Read
[self-hosted-runners.md](self-hosted-runners.md) for Pattern A. Pattern B below
remains the deployment boundary whether the immutable artefact was built on a
GitHub-hosted runner or a self-hosted runner.
When Pattern A is the triggering server, also read
[artifact-storage.md](artifact-storage.md): the primary bytes remain in its
fixed server-local store and are not uploaded to GitHub Actions.

When both patterns involve the same machine, the self-hosted CI identity and
the deployment identity MUST be separate principals with no overlapping
credentials, privilege, helpers, production groups, or writable paths.
Unless durable reviewed project policy says otherwise, the deployment identity
is the canonical unprivileged host account named `deploy`; it owns the approved
service root while privileged helpers remain root-owned.

## Events and workflow structure

- Give `GITHUB_TOKEN` explicit least-privilege `permissions` and isolate jobs
  that need `contents: write`, package writes, attestations, or deployments.
- Pin every third-party action to a reviewed full commit SHA. Add a release
  comment for maintainability; a mutable tag alone is not a security pin.
- Use protected GitHub environments for production secrets, branch/tag rules,
  reviewers, and deployment history.
- Use an environment-scoped `concurrency` group. Decide whether pending runs may
  be cancelled; do not blindly cancel an in-progress activation.
- Keep untrusted pull-request validation separate from jobs with secrets or
  write permissions. Never check out untrusted contents in a privileged
  `pull_request_target` job.
- Resolve deployable refs to immutable full commit SHAs before build. Validate
  dispatch inputs before checkout and keep protected channels behind review and
  environment approval.

## Default automatic promotion

Unless a durable, reviewed project-specific release policy defines another
channel, automatic publication and production deployment use only `push` events
for `master`. Gate privileged jobs on `github.ref == 'refs/heads/master'` and
promote the immutable artefact for the event `github.sha`; do not resolve a
branch, tag, or workflow input later. `release/*` is a review buffer, not a
default deployment or publication trigger. Manual dispatch is an operator action
and needs explicit authorisation for a verified `master` artefact. For a dedicated
server, privileged deployment must use a canonical root under `/data/`, `~/data/`,
or another approved dedicated data volume; it must reject `/var/`, `/srv/`,
`/opt/`, `/usr/`, `/usr/local/`, and other system-owned roots unless a durable,
reviewed project-specific deployment policy grants that exception. GitHub
Actions is the recommended automatic-deployment orchestrator. Its protected job
authenticates as `deploy` with a repository- and environment-scoped credential,
and `deploy` owns the approved service root. When the service needs a local
database, use a separate deploy-managed root such as
`/data/database/<service-or-engine>` or
`~/data/database/<service-or-engine>` and keep it outside release pruning.

## Artefact transfer and host invocation

Pattern B uses an isolated GitHub-hosted deploy job with a repository- and
environment-scoped SSH credential for `deploy`. Do not run this job as the
Pattern A self-hosted CI principal, including when CI and production share a
machine.

1. Resolve the exact server-local record id and digest without rebuilding it.
2. Ask the fixed host interface to read that record; do not accept a mutable
   branch, tag, `latest` path, or arbitrary archive path.
3. Verify its digest, provenance, and compatibility in the protected boundary.
4. Transfer it to a release-specific temporary location beneath the host's
   approved staging boundary, or let the fixed host helper perform that copy.
5. Verify the server host key and transferred digest.
6. Pass only validated scalar arguments to one fixed host command.
7. Wait for activation and release-specific health evidence.

Do not embed secrets or unchecked event data into a remote shell program.
Prefer short-lived identity federation when available. For SSH-only hosts, use
one restricted, rotated key per repository and environment.

GitHub Actions artefact storage is default-deny. Do not use
`actions/upload-artifact`, `actions/download-artifact`, the Actions artefact
API or CLI, or an equivalent GitHub byte-storage path for build, test,
diagnostic, release, deployment, or rollback bytes. Permit a temporary
cross-host exception only when the local store, fixed direct transfer, and
approved pull interface demonstrably cannot work and the current user explicitly
requests that specific upload. Record the producer, consumer, SHA, digest,
environment, non-secret contents, size, and reason; expire it within one day,
and never make it the release or rollback source. A durable reviewed policy may
stand for a prior explicit user request only when it names this exact exception.

Every workflow exception must satisfy the exact record schema in
`artifact-storage.md`; an upload step sets `retention-days: 1` and the normal
constraint check fails closed without it.

## Secrets and evidence

- Store private keys, tokens, sensitive host data, and environment configuration
  in environment secrets or an approved secret manager.
- Do not print secrets, private keys, complete environment files, or
  credential-bearing command lines.
- Record workflow run, release id, source SHA, digest, approvals, activation and
  smoke results, rollback result, and cleanup plan.
- Set explicit server-local rolling retention as described in
  [artifact-storage.md](artifact-storage.md). Host rollback must not rely on
  an expired Actions upload.

## Rollback

Rollback is a separate protected operation selecting a retained release id or
digest. It invokes the same persistent host helper family and repeats the same
health checks. Manual dispatch is an operator action, not proof that a protected
branch or tag was reviewed.
