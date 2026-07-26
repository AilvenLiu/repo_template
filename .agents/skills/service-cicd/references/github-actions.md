# GitHub Actions trust and deployment boundary

## Select compute and deployment independently

Self-hosted CI compute (Pattern A) and restricted SSH deployment (Pattern B)
solve different problems and may be used together. Read
[self-hosted-runners.md](self-hosted-runners.md) for Pattern A. Pattern B below
remains the deployment boundary whether the immutable artefact was built on a
GitHub-hosted runner or a self-hosted runner.

When both patterns involve the same machine, the self-hosted CI identity and
the deployment identity MUST be separate principals with no overlapping
credentials, privilege, helpers, production groups, or writable paths.

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
reviewed project-specific deployment policy grants that exception.

## Artefact transfer and host invocation

Pattern B uses an isolated GitHub-hosted deploy job with a repository- and
environment-scoped SSH identity. Do not run this job as the Pattern A
self-hosted CI principal, including when CI and production share a machine.

1. Download the exact build-job artefact without rebuilding it.
2. Verify its digest and provenance in the privileged job.
3. Transfer it to a release-specific temporary location beneath the host's
   approved staging boundary.
4. Verify the server host key and transferred digest.
5. Pass only validated scalar arguments to one fixed host command.
6. Wait for activation and release-specific health evidence.

Do not embed secrets or unchecked event data into a remote shell program.
Prefer short-lived identity federation when available. For SSH-only hosts, use
one restricted, rotated key per repository and environment.

## Secrets and evidence

- Store private keys, tokens, sensitive host data, and environment configuration
  in environment secrets or an approved secret manager.
- Do not print secrets, private keys, complete environment files, or
  credential-bearing command lines.
- Record workflow run, release id, source SHA, digest, approvals, activation and
  smoke results, rollback result, and cleanup plan.
- Set explicit workflow and artefact retention. Host rollback must not rely on
  an expired Actions upload.

## Rollback

Rollback is a separate protected operation selecting a retained release id or
digest. It invokes the same persistent host helper family and repeats the same
health checks. Manual dispatch is an operator action, not proof that a protected
branch or tag was reviewed.
