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

## Artefact and release review

- [ ] Validation precedes build; deploy and publish consume the same immutable
      build artefact without rebuilding.
- [ ] Source SHA, release id, digests, compatibility, provenance, workflow run,
      and target surface are joined in durable evidence.
- [ ] GitHub Release, package, container, and deployment identifiers agree.
- [ ] Retries reject an existing release identifier with different bytes.
- [ ] Retention does not make host rollback depend on an expired CI artefact.

## Deployment and rollback review

- [ ] The protected deploy job verifies server identity, artefact digest, and
      provenance before invoking one fixed narrow host interface.
- [ ] Environment concurrency prevents overlap and out-of-order activation.
- [ ] Release-specific health failure fails the job and preserves the last
      known-good release and diagnostic evidence.
- [ ] Rollback selects a retained verified release and never rebuilds.

## Behavioural and adversarial tests

- [ ] Exercise forked PRs, hostile dispatch inputs, mismatched refs/digests,
      missing secrets, cancelled and overlapping jobs, truncated transfer,
      failed health, partial publication, and missing rollback artefacts.
- [ ] Confirm logs redact secrets and still identify the exact source, artefact,
      environment, approval, and result.
- [ ] Record each check not run and the resulting operational or supply-chain
      risk.
