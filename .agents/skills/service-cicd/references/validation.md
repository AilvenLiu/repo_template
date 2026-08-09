# Service CI/CD validation checklist

## Static workflow review

- [ ] Workflow YAML parses and every third-party action uses a full SHA pin.
- [ ] Triggers, permissions, environments, reviewers, concurrency, timeouts,
      and secret scopes match the documented channel policy.
- [ ] Pull-request jobs cannot receive production secrets or privileged tokens.
- [ ] Event and manual inputs are validated before checkout, paths, shell, SSH,
      release names, or environment selection.
- [ ] The matrix invokes the authoritative Poetry and/or CMake build graph for
      the active profile.
- [ ] A persistent self-hosted runner follows
      `self-hosted-runners.md`: narrow labels and scope, pinned verified
      bootstrap, unprivileged identity, explicit service/PATH/ownership policy,
      busy restart guard, and no per-job privileged host provisioning.
- [ ] When self-hosted CI and production share a machine, CI and SSH deployment
      use separate principals with no overlapping credentials, privilege,
      helpers, groups, sockets, or writable paths.
- [ ] Unless durable reviewed project policy says otherwise, the protected
      deploy job authenticates as the unprivileged `deploy` account with a
      repository- and environment-scoped credential; `deploy` owns the approved
      service root and privileged helpers remain root-owned.

## Artefact and release review

- [ ] Validation precedes build; deploy and publish consume the same immutable
      build artefact without rebuilding.
- [ ] When a persistent runner triggers CI, the primary artefact is committed
      to a separate server-local store with an immutable manifest and digest;
      the normal workflow does not use GitHub Actions artefact storage.
- [ ] Server-local cleanup is locked, dry-run capable, fail-closed, and keeps
      only the three newest verified `master` records and two newest verified
      `develop` records by default, plus live/rollback/pinned/held records.
- [ ] Promotion marks its selected record `activating` or `held` under the
      cleanup lock before pruning can run.
- [ ] Source SHA, release id, digests, compatibility, provenance, workflow run,
      and target surface are joined in durable evidence.
- [ ] GitHub Release, package, container, and deployment identifiers agree.
- [ ] Retries reject an existing release identifier with different bytes.
- [ ] Retention does not make host rollback depend on an expired CI artefact.

## Deployment and rollback review

- [ ] The protected deploy job verifies server identity, artefact digest, and
      provenance before invoking one fixed narrow host interface.
- [ ] Without a durable, reviewed project-specific exception, the canonical
      deployment root is on `/data/`, `~/data/`, or another approved dedicated
      data volume; no `/var/`, `/srv/`, `/opt/`, `/usr/`, or `/usr/local/` root
      is accepted.
- [ ] A required local database uses a separate deploy-managed root beneath
      `/data/database/`, `~/data/database/`, or another approved data volume,
      outside releases and pruning, with engine-owned child delegation recorded.
- [ ] Environment concurrency prevents overlap and out-of-order activation.
- [ ] Release-specific health failure fails the job and preserves the last
      known-good release and diagnostic evidence.
- [ ] Rollback selects a retained verified release and never rebuilds.

## Behavioural and adversarial tests

- [ ] Exercise forked PRs, hostile dispatch inputs, mismatched refs/digests,
      missing secrets, cancelled and overlapping jobs, truncated transfer,
      failed health, partial publication, and missing rollback artefacts.
- [ ] For a persistent runner, re-run bootstrap and the authoritative workflow
      to expose stale state, duplicate swap/resources, cache contamination,
      root-owned parents, captured PATH, and unsafe maintenance restarts.
- [ ] Confirm logs redact secrets and still identify the exact source, artefact,
      environment, approval, and result.
- [ ] Record each check not run and the resulting operational or supply-chain
      risk.
