# GitHub Actions CI/CD

This constraint governs GitHub Actions continuous integration, artefact
production, auto-deployment, and auto-release. Host layout and activation are
governed separately by `common/service-deployment.md`.

## CI Build Authority

- Every pull request MUST run the repository's authoritative format, lint,
  static-analysis, build, and test commands for its active project profile.
- Pure Python uses Poetry. Pure C++/CUDA uses direct CMake configure/build/test
  with Ninja and CPM where applicable. Hybrid projects validate direct CMake
  first, then use scikit-build-core only as the packaging bridge; Poetry owns
  the Python environment and dependencies, not the native build graph.
- Build a deployable artefact once after required validation succeeds. Release
  and deployment jobs MUST promote that exact artefact; they MUST NOT rebuild
  from a mutable branch, tag, package index, or production checkout.
- CUDA execution may be separated into labelled GPU runners, but skipping it
  requires an explicit documented compatibility/risk decision. CPU and
  non-CUDA native validation remain mandatory where applicable.
- Every PR/MR targeting `master` MUST also run the read-only
  `master-merge-gate` status. Configure it and the profile-authoritative
  validation status as required hosted branch checks; CI configuration alone is
  not a substitute for branch protection.

## Master PR/MR Gate

- Accept master-bound PRs/MRs only from same-repository `develop`, `release/*`,
  or `hotfix/*` branches.
- Reject every changed or renamed development-stage path listed in
  `common/master-merge-policy.md`; permit only `docs/changelog/` below `docs/`.
- On GitHub, the gate may use `pull_request_target` only to execute trusted
  base-branch policy with read-only permissions. It MUST NOT check out, build,
  or execute PR code, and it MUST NOT receive production secrets.
- Direct `develop` to `master` is allowed but a release branch created from an
  immutable reviewed develop SHA is strongly preferred as the buffer.

## Default Automatic Release Authority

Unless a durable, reviewed project-specific release policy explicitly defines a
different authorisation, automatic publication and production deployment MAY run
only after an update to `master`. On GitHub, use a `push` event restricted to
`master` and promote the exact `github.sha` from that event.

- Do not auto-publish or auto-deploy from pull requests, merge requests, tags,
  scheduled runs, manual dispatches, `develop`, `release/*`, or `hotfix/*`.
- Build and promote an immutable artefact whose manifest records that exact
  `master` SHA. Do not resolve a mutable branch, tag, or workflow input later.
- A `release/*` branch is a validation and review buffer; it has no default
  authority to publish a version or activate a production service.
- For a dedicated server, automatic deployment MUST target a canonical root on
  `/data/`, `~/data/`, or another operator-approved dedicated data volume. It
  MUST NOT use `/var/`, `/srv/`, `/opt/`, `/usr/`, `/usr/local/`, or another
  system-owned hierarchy without a durable, reviewed project-specific exception.
- Manual release, deployment, or rollback is an operator action. It needs
  explicit approval and still promotes a verified artefact from `master`; it
  cannot silently become an automatic alternative channel.
- A project-specific exception MUST be durable, reviewed, and explicit about
  the alternate event/ref, environments, approvals, and artefact provenance.

## Workflow Trust Boundary

- Declare least-privilege `permissions` at workflow or job scope. Grant write
  permissions only to the job that needs them.
- Pin every third-party action to a reviewed full commit SHA. A version comment
  may document the corresponding release; a mutable tag alone is not a pin.
- Untrusted pull-request jobs MUST NOT receive production secrets, deployment
  identities, release credentials, or write-capable tokens. Never execute
  untrusted checkout contents in a privileged `pull_request_target` job.
- Resolve requested refs, tags, channels, and manual inputs to validated,
  immutable values before checkout or interpolation. Treat event fields as
  untrusted input and avoid constructing shell or SSH programs from them.
- Use protected GitHub environments for production secrets, branch/tag rules,
  reviewers, and deployment history. Prefer short-lived identity federation;
  otherwise scope and rotate one credential per repository and environment.

## Artefacts, Releases, and Evidence

- Assign a release identifier that joins source SHA, artefact digest, workflow
  run, environment, activation metadata, rollback, and retention decisions.
- Package deterministic immutable artefacts, calculate and verify digests, and
  produce provenance or attestations when supported. Record target OS,
  architecture, language ABI, compiler/runtime ABI, and GPU compatibility as
  applicable.
- Auto-release MUST publish only after required tests, policy gates, and
  environment protections pass. Published packages, images, release assets,
  and deployment inputs MUST refer to the same verified digests.
- Set explicit workflow and artefact retention. Host rollback safety MUST NOT
  depend solely on an expiring GitHub Actions upload.
- Logs and summaries MUST preserve the source SHA, release id, digests,
  approvals, deployment result, health evidence, and rollback outcome without
  exposing secrets.

## Auto-Deployment and Rollback

- Document which reviewed event authorizes each channel. Manual dispatch is an
  operator action, not evidence that a protected branch was reviewed.
- Serialize deployments with environment-scoped concurrency and define whether
  queued runs may be cancelled. Never let an older run activate after a newer
  release or prune another run's rollback target.
- Transfer to a release-specific temporary location, verify server host
  identity and artefact digest, then invoke one fixed, narrowly authorized host
  interface. CI-side validation is not a host security boundary.
- Mark deployment successful only after host activation and release-specific
  health checks succeed. A failed gate MUST preserve evidence and the last
  known-good release; do not weaken the gate to make the workflow green.
- Rollback SHOULD be a separate protected workflow selecting a retained release
  id or digest and invoking the same host helper family. It MUST NOT rebuild.

Read `.agents/skills/service-cicd/SKILL.md` before implementing or reviewing this
workflow.
