# GitHub Actions trust and deployment boundary

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

## Artefact transfer and host invocation

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
