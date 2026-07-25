---
name: service-cicd
description: Design, implement, review, or troubleshoot GitHub Actions CI/CD for service validation, immutable artefact builds, auto-deployment, auto-release, provenance, protected environments, concurrency, rollback, and release evidence. Use for workflow YAML, CI matrices, deployment or publishing jobs, release channels, GitHub environments, Actions secrets, artefact promotion, or release automation for Python, C++/CUDA, and hybrid Python/C++ projects.
---

# Service CI/CD

Use GitHub Actions to validate source, build one immutable artefact, and promote
that exact artefact through protected release and deployment boundaries. This
skill owns automation; read the separate `$deploy-service` skill for host paths,
activation helpers, runtime services, ingress, and rollback storage.

## Establish the release contract

1. Read `.agents/constraints/common/github-actions-cicd.md`. For auto-deployment or
   host rollback, also read `.agents/constraints/common/service-deployment.md`;
   skill guidance does not replace either mandatory constraint.
   For a master-bound PR/MR, also read
   `.agents/constraints/common/master-merge-policy.md` and apply the
   `branch-governance` skill.
2. Read the repository entrypoints, `.agents/project.yml`, build and test commands,
   existing workflows, package metadata, host interface, and release policy.
3. Record the events and approvals for each channel: pull request, merge,
   version tag, manual dispatch, scheduled build, deployment, and rollback.
4. Identify trust boundaries: untrusted source, `GITHUB_TOKEN`, environment
   secrets, package or registry identity, SSH or cloud identity, host helper,
   and public release surface.
5. Read [project-profiles.md](references/project-profiles.md) and preserve the
   profile's build authority. Do not invent a parallel build graph in Actions.
6. Read [github-actions.md](references/github-actions.md) before writing or
   reviewing workflow YAML.
7. For packages, images, GitHub Releases, provenance, or cross-platform
   promotion, read [release-promotion.md](references/release-promotion.md).
8. For an auto-deployment job, also read
   `.agents/skills/deploy-service/SKILL.md` and its applicable host references.

Stop for operator direction before changing release-channel semantics,
production approvals, credentials, public package ownership, destructive
retention, or which refs may deploy.

## Resolve automatic promotion authority

Before creating a release or deployment workflow, find any durable,
project-specific release policy. If none exists, automatic publication and
production deployment run only on an update to `master`; on GitHub this is a
`push` restricted to `master`, using the exact event `github.sha`. The workflow
builds or promotes only the immutable artefact for that SHA. Do not give a pull
request, tag, scheduled run, manual dispatch, `develop`, `release/*`, or
`hotfix/*` default automatic release/deployment authority. A release branch is
a validation buffer, not a production trigger. For a dedicated server, the
default deploy job targets a canonical root beneath `/data/`, `~/data/`, or
another operator-approved dedicated data volume. It MUST NOT target `/var/`,
`/srv/`, `/opt/`, `/usr/`, `/usr/local/`, or another system-owned hierarchy
unless the durable project-specific deployment policy explicitly permits it.

## Preserve these invariants

- Pull-request CI runs without production secrets or write permissions and
  cannot execute untrusted code in a privileged `pull_request_target` context.
- A master-bound PR/MR validates the allowed same-repository source branch and
  development-stage path deny list before release, build, or deployment work.
- Every third-party action is pinned to a reviewed full commit SHA. Mutable tags
  and branches may appear only as explanatory comments, never as the pin.
- Workflow and job permissions are explicit and least-privilege. Production
  credentials are scoped to protected GitHub environments.
- The deployable artefact is built and tested once. Publishing and deployment
  promote the same verified bytes; neither job rebuilds from source.
- A validated release id joins source SHA, artefact digest, workflow run,
  target compatibility, approvals, host metadata, and rollback evidence.
- Deployments are serialized per environment. An older or cancelled run cannot
  activate after a newer release or prune its rollback target.
- CI transfers only to a release-specific temporary path and invokes one fixed,
  narrowly authorized host interface. Never upload and run a fresh root script.
- Auto-release occurs only after the required CI, policy, provenance, and
  channel gates pass. Published assets and deployed assets share verified
  digests.
- A failed deployment or release gate remains failed. Preserve the last
  known-good release and actionable evidence instead of weakening the gate.
- Rollback selects a retained verified release through a protected workflow; it
  does not rebuild or repair a production checkout.

## Model the pipeline explicitly

Use distinct jobs or reusable workflows when permissions differ:

```text
source -> validate -> build -> attest -> approve -> publish/deploy -> verify
                    |                  |                    |
                    +-- immutable -----+--------------------+
                                                        failure
                                                           |
                                                protected rollback
```

Recommended ownership:

- `validate`: formatting, lint, static analysis, unit/integration tests; no
  production secrets.
- `build`: profile-authoritative build and packaging; uploads immutable
  artefacts, digests, compatibility metadata, and test evidence.
- `attest`: provenance or GitHub artefact attestation with minimal write scope.
- `publish`: signs or publishes the already-built package, image, or release
  asset after channel checks.
- `deploy`: protected environment, environment concurrency, scoped identity,
  transfer, fixed host command, and release-specific health verification.
- `rollback`: protected operator-selected retained release, same host interface,
  same health gates.

Keep deployment and publication independently selectable when a project needs
one without the other, while preserving artefact identity across both.

## Validate adversarially

Challenge at least these cases:

- a forked pull request edits workflow code and attempts to read secrets
- an action pin is replaced by a tag or an unexpected workflow gains write scope
- manual input contains shell syntax, traversal, a pull ref, hostile slug, or an
  unreviewed protected channel
- tag, branch, and artefact source SHA do not agree
- build and release jobs produce different bytes or compatibility metadata
- two deploys overlap, finish out of order, or one is cancelled mid-activation
- transfer is truncated, substituted, or sent to the wrong environment
- activation succeeds but release identity, a worker, ingress, FFI, or package
  verification fails
- attestations, signatures, retained artefacts, or rollback targets are absent
- auto-release partially publishes and a retry would duplicate or mutate it

Use [validation.md](references/validation.md) for the final static, behavioural,
and failure-injection review. Report checks that could not run and the remaining
risk rather than claiming unverified coverage.

## Handoff

Deliver the workflow files, reusable workflow contracts, release metadata,
tests, policy configuration, and operator documentation actually required.
Report the event/channel model, build matrix, permission and secret boundaries,
artefact/provenance identity, deployment interface, release and rollback flow,
concurrency policy, and validation evidence.
