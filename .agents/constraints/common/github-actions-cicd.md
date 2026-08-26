# GitHub Actions CI/CD

This constraint governs GitHub Actions continuous integration, artefact
production, auto-deployment, and auto-release. Host layout and activation are
governed separately by `common/service-deployment.md`.

## CI Build Authority

- Every pull request MUST run the repository's authoritative format, lint,
  static-analysis, build, and test commands for its active project profile,
  with the release exception defined by `common/master-merge-policy.md`
  section 9: a master-bound `release/*` PR MAY satisfy this through validation
  provenance for the structurally proved source SHA instead of a rebuild. A
  bounded version-only push to `develop` runs focused manifest proof rather
  than a full build; provenance remains bound to its validated parent. A
  `hotfix/*` PR never substitutes provenance for validation.
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
  `master-merge-gate` status and carry the applicable approval evidence from
  `common/master-merge-policy.md`. Independent human approval is the default; a
  durable single-maintainer policy may substitute only its exact owner
  attestation. Configure it and the profile-authoritative validation status as
  required hosted branch checks; CI configuration alone is not a substitute
  for branch protection. Both statuses stay required for every master-bound
  PR: validation provenance changes how the validation status is satisfied on
  an identity-proved release PR, never whether it is required, so the
  `hotfix/*` validation requirement is untouched.

## CI Compute and Deployment Boundaries

Self-hosted CI compute and SSH deployment solve separate concerns and MAY be
used independently or together:

- Pattern A moves build, test, lint, package, or hardware-specific compute to a
  persistent self-hosted Actions runner. That runner MUST use a dedicated
  unprivileged identity, narrow labels and repository scope, and no deployment
  key, production secret, sudo rule, or production activation authority.
- Pattern B promotes an immutable verified artefact from an isolated
  GitHub-hosted deploy job through a repository- and environment-scoped SSH
  credential to the canonical unprivileged host account named `deploy` and one
  narrow host interface. The `deploy` account owns the approved dedicated
  service root; privileged helpers remain root-owned. Pattern B remains the
  deployment mechanism even when Pattern A built the artefact.

When both patterns involve the same machine, their operating-system principals,
credentials, privileged groups, helpers, control sockets, and writable paths
MUST NOT overlap. Treat self-hosted workflow execution as arbitrary repository
code, not as a trusted host operator. Container-daemon membership is
root-equivalent and therefore does not provide process-only separation from
co-located production.

A persistent runner MUST be installed and maintained by a committed, idempotent
host bootstrap that pins and verifies the runner release, provisions privileged
dependencies outside workflow steps, sets explicit service restart, PATH, and
ownership policy, and refuses to restart during an active job. Workflow jobs
MUST NOT use sudo or create accumulating host resources such as per-run swap
devices. Read
`.agents/skills/service-cicd/references/self-hosted-runners.md` for the
procedural and validation contract.

## Master PR/MR Gate

- Accept master-bound PRs/MRs only from same-repository branches named exactly
  `release/v<major>.<minor>.<patch>` or `hotfix/v<major>.<minor>.<patch>`.
  Reject `develop` categorically because its required tooling cannot pass the
  presence-based tree check.
- Verify that the version in the source branch name equals the authoritative
  manifest version at the recorded source commit, that a hybrid project's
  `pyproject.toml` mirrors its `CMakeLists.txt` version, and that the candidate
  version is strictly greater than the version currently on `master`.
- Reject any source tree containing a development-stage path listed in
  `common/master-merge-policy.md`; permit only `docs/changelog/` below `docs/`.
- For `release/*`, require the PR body to record `Develop-Source-SHA` and fail
  unless the source SHA is reachable from `develop`, the release descends from
  it, and the release tree differs only by forbidden-path deletions. When the
  source is the bounded version-only commit, also require
  `Release-Metadata-Parent-SHA`; prove one-parent ancestry, complete-tree
  equality outside the authoritative manifests, exact version-field-only
  manifest changes, manifest agreement, and a strict semantic increase before
  accepting validation provenance from that parent.
- For `hotfix/*`, require the PR body to record the reduced local validation in
  `Hotfix-Validation-Tradeoff`; a missing record is a hard failure.
- For `release/*`, the gate MAY additionally verify validation provenance:
  set the repository variable `REQUIRED_SOURCE_CHECKS` to a comma-separated
  list of Actions workflow names (names must not contain commas), and the gate
  requires each named workflow to have a successful, completed `push` run of
  the `develop` branch at exactly the recorded develop source SHA, or at its
  independently proved `Release-Metadata-Parent-SHA`, read
  through the read-only Actions workflow-runs API. Workflow-run bindings are
  forge-recorded and cannot be minted through the check-runs API, which is why
  the gate does not accept bare check-run names. The validation workflow must
  therefore run on `push` to `develop`, not only on pull requests. When this
  is configured, the required validation status on a release PR MAY be
  reported by a provenance-aware job that verifies the same evidence and
  succeeds without rebuilding; that job MUST still run the full rebuild for
  `hotfix/*` PRs and for any PR whose provenance cannot be verified, and the
  status itself is never removed from the branch rules. Leaving the variable
  empty keeps the rebuild requirement unchanged.
- Configure `master-merge-gate` as a required check for `master`. The generic
  promotion route opens no PR targeting `release/*`: `agent-release prepare`
  creates the release ref once at its fully projected final commit, and the
  gate independently proves that projection on the sole master-bound PR.
- On GitHub, the gate may use `pull_request_target` only to execute trusted
  base-branch policy with read-only permissions. It MUST NOT check out, build,
  or execute PR code, and it MUST NOT receive production secrets.
- `develop` MUST NOT merge or rebase from `master` for ordinary releases. The
  functional change from a master-origin hotfix MUST return to `develop`
  through a reviewed merge or cherry-pick PR, never through rebase.

## Default Automatic Release Authority

Unless a durable, reviewed project-specific release policy explicitly defines a
different authorisation, automatic publication and production deployment MAY run
only after an update to `master`. On GitHub, use a `push` event restricted to
`master` and promote the exact `github.sha` from that event.

- GitHub Actions is the recommended automatic-deployment orchestrator for this
  policy. The protected deploy job MUST authenticate as `deploy` by default,
  use a repository- and environment-scoped credential, and invoke only the
  fixed host interface.
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
  The root MUST be owned by `deploy`; for `~/data/`, `~` is the `deploy`
  account's home and MUST be resolved before use.
- When the service needs a local database, the host contract MUST reserve a
  separate deploy-managed root such as `/data/database/<service-or-engine>` or
  `~/data/database/<service-or-engine>`. Database state MUST remain outside
  release artefacts and deployment pruning; engine-specific ownership is
  delegated only as documented by `common/service-deployment.md`.
- Manual release, deployment, or rollback is an operator action. It needs
  explicit approval and still promotes a verified artefact from `master`; it
  cannot silently become an automatic alternative channel.
- A project-specific exception MUST be durable, reviewed, and explicit about
  the alternate event/ref, environments, approvals, and artefact provenance.

### Release Tagging

`common/master-merge-policy.md` section 8.6 requires that the `release-v<x.y.z>`
tag be created by automation and verified independently. On GitHub Actions:

- Only a trusted `push` event restricted to `master` may create a semantic tag,
  in a job dedicated to that single purpose.
- That job MUST declare `permissions: contents: write` and nothing further, and
  it MUST be the only job in the workflow holding a write credential. The
  deployment job and every other job stay read-only.
- Where the workflow deploys, the tag job MUST declare `needs:` on the deployment
  job and MUST NOT run unless that deployment succeeded for the same
  `github.sha`. Inverting this -- deployment declaring `needs:` on the tag job --
  produces a tag for a commit whose deployment then fails, which is
  indistinguishable afterwards from a release that shipped.
- Operational deployment identifiers such as `master-<timestamp>-<short-sha>`
  MUST remain host and artefact join keys. They MUST NOT be created as Git tags
  or substituted for semantic tags.
- The version MUST be read from the authoritative manifest at the exact promoted
  `master` SHA. A branch name, a PR title, or a workflow input is not
  authoritative; a release branch may be misnamed, and the gate that checks the
  name runs on a different event. This check MAY run before the deployment job so
  that a missing version bump fails fast; only the tag write waits.
- A version that is not strictly greater than the preceding eligible `master`
  release MUST fail the job. Compare numerically per component, not lexically: a
  string sort places `0.10.0` below `0.9.0`.
- Re-running the workflow on an already-tagged commit MUST succeed without
  re-pointing the tag. Deployments are re-run for reasons unrelated to tagging,
  and a tag job that fails on its second run makes recovery harder than the
  problem it was invoked for. A stale event whose `master` tip has since advanced
  MUST fail instead; idempotency never authorises replay of an obsolete
  deployment.
- The job MUST NOT force-update, move, or delete a tag under any condition. Use a
  create-only ref operation.
- Error handling in the version comparison MUST distinguish "no release tags
  exist yet", which is the legitimate bootstrap case, from "the lookup failed".
  A trailing `|| true` on the lookup pipeline covers the first and silently
  swallows the second, which converts a broken comparison into an apparently
  passing one.
- A separate read-only verification job MUST run after every tagging attempt on a
  promoted `master` commit. It MUST independently re-derive the eligible commits,
  manifest versions, expected tag names, and exact targets rather than trusting
  the tag job's outputs, and MUST fail when any governed tag is absent, moved, or
  mismatched. It MUST receive no production environment, deployment credential,
  or write permission. This is what detects a tag job that was skipped,
  cancelled, or never wired up, and it holds for repositories that do no
  automatic tagging at all.
- Workflow concurrency MUST serialise deployment and tagging for an environment,
  with `cancel-in-progress: false`. Concurrency alone does not prove freshness:
  the activation boundary MUST also re-read the protected-channel branch tip and
  reject an old rerun after that ref advances.

## Workflow Trust Boundary

- Declare least-privilege `permissions` at workflow or job scope. Grant write
  permissions only to the job that needs them.
- Pin every third-party action to a reviewed full commit SHA. A version comment
  may document the corresponding release; a mutable tag alone is not a pin.
- Untrusted pull-request jobs MUST NOT receive production secrets, deployment
  identities, release credentials, or write-capable tokens. Never execute
  untrusted checkout contents in a privileged `pull_request_target` job.
- A persistent self-hosted runner SHOULD be private-repository scoped. A public
  repository MUST NOT route arbitrary fork code to persistent owned
  infrastructure without a reviewed approval and disposable-isolation model
  that prevents access to secrets and host state.
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
- Every build, release, deployment, diagnostic, or test byte that must survive
  a job or host boundary MUST use the fixed operator-controlled local artefact
  store described by `service-cicd/references/artifact-storage.md`. A
  GitHub-hosted runner without such a store must use a fixed direct transfer or
  protected build-and-promote job, or stop for provisioning; it MUST NOT make
  GitHub Actions artefact storage the default workaround.
- GitHub Actions artefact storage is default-deny. Do not add or use
  `actions/upload-artifact`, `actions/download-artifact`, the Actions artefact
  API or CLI, or an equivalent GitHub byte-storage path for build, test,
  diagnostics, release transport, deployment, or rollback merely for
  convenience.
- An exception requires both documented technical necessity (the exact
  producer/consumer and why the local store, fixed direct transfer, or pull
  interface cannot work) and a current user who explicitly requests that
  specific GitHub upload. A workflow shape, GitHub-hosted runner, manual
  dispatch, generic operator approval, or existing upload is not consent. A
  durable reviewed project policy may carry prior explicit user authorisation
  only when it names the exact GitHub surface and exception.
- An approved exception contains only the necessary non-secret bytes, records
  source SHA and digest, producer, consumer, environment, size, and reason,
  expires within one day, and is never the release or rollback authority. Keep
  the authoritative immutable local record until normal retention can safely
  prune it.
- A workflow exception MUST satisfy the exact durable record schema in
  `artifact-storage.md`; an upload step sets `retention-days: 1` and the normal
  constraint check fails closed without it.
- Apply a small rolling policy to that store: retain the three newest verified
  `master` records and two newest verified `develop` records by default, plus
  live, rollback, pinned, held, or activating records. Do not retain release
  artefacts from pull requests, tags, or arbitrary refs by default.
- Cleanup must be locked, dry-run capable, fail closed on malformed or unknown
  metadata, and unable to escape the canonical store. Mark a selected record
  `activating` or `held` under the same lock before cleanup or promotion. It
  must never remove a record needed by a live service or a verified rollback.
- Auto-release MUST publish only after required tests, policy gates, and
  environment protections pass. Published packages, images, release assets,
  and deployment inputs MUST refer to the same verified digests.
- Set explicit server-local retention and monitor capacity. Host rollback
  safety MUST NOT depend on an expiring GitHub Actions upload. GitHub
  attestations and provenance are metadata, not permission to upload artefact
  bytes. A GitHub Release asset is a public publication surface, not CI
  transport, retention, or rollback storage. Attach it only when a current
  user explicitly requests that publication or a durable reviewed policy
  records prior explicit authorisation for that exact public surface.
- Logs and summaries MUST preserve the source SHA, release id, digests,
  approvals, deployment result, health evidence, and rollback outcome without
  exposing secrets. Prefer ordinary workflow logs and job summaries for
  diagnostics; they MUST NOT become an artefact-upload workaround.

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
