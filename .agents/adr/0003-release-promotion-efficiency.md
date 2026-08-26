# ADR 0003: Release Promotion Efficiency

**Status**: Active
**Date**: 2026-08-20
**Authors**: Template maintainers
**Amends**: ADR 0002 (route verification gains one sanctioned alternative)
**Amended by**: ADR 0005 (makes deterministic direct projection the default,
removes the generic staging route, and adds bounded version-parent provenance)

## Summary

The release-shim workflow validated the same functional content up to three
times per promotion: on the develop PR, on the staging PR, and on the master
PR, with a fourth dedicated CI round when the version bump travelled in its own
PR. In practice this made every promotion, including a one-line fix, cost
several full build-and-test cycles, and a failure discovered late forced the
whole sequence to repeat. This ADR removes the redundant validation and the
avoidable rounds without weakening any invariant, as
`common/master-merge-policy.md` section 9.

## Decision

1. **Validation provenance (9.1).** The master merge gate already proves, by
   leaf-level object-SHA comparison, that a release tree equals the recorded
   develop source SHA tree minus deletions of build-irrelevant paths. That
   proof makes a rebuild of the release PR logically redundant: the content
   under validation is byte-identical to content the authoritative validation
   already passed. A release-bound PR may therefore satisfy the validation
   requirement with machine-verified evidence of the successful validation at
   the source SHA. The gate enforces this through `REQUIRED_SOURCE_CHECKS`:
   each named Actions workflow must have a successful, completed `push` run of
   the `develop` branch at exactly the recorded SHA, read from the read-only
   workflow-runs API, failing closed on malformed or partial listings. The
   Checks API was deliberately rejected as the evidence source: check runs
   match by bare name and can be minted at an arbitrary SHA by any
   same-repository branch workflow holding `checks: write`, whereas a workflow
   run's event, head branch, and head SHA are forge-recorded. The hosted
   validation status stays required for every master-bound PR; provenance
   changes how an identity-proved release PR satisfies it, never whether it is
   required, which is also what keeps the hotfix requirement intact. Hotfix
   PRs are excluded from substitution: their trees are not identity-proved
   against any validated SHA.

2. **Per-step required checks (9.2).** The single paid validation of any
   functional content is the one where it is authored: the develop PR. The
   staging PR needs only the deletion-only projection check, which the gate
   itself now runs for PRs targeting `release/*` branches (accepting only the
   matching `chore/release-v<x.y.z>` source and a deletion-only tree); the
   master PR needs the gate plus provenance or a rebuild.

3. **Combined bump default (sections 4 and 8.4).** Bumping the
   version in the same PR as the change it describes was already permitted;
   it is now the recommended default, eliminating one full CI round. The
   dedicated bump PR remains the fallback for release trains whose merged
   changes did not set the version.

4. **Release cadence (9.3).** The pipeline is priced per release, so its cost
   amortises. Release trains are the assumed default; promoting every merge is
   a per-project choice.

5. **Pre-flight rehearsal (9.4).** The gate ships a `--rehearse` mode: a
   read-only, network-free local pre-flight that derives names from the
   manifest, runs the same pure validation, and simulates the projection.
   Failures move from the end of the promotion cycle to before it starts.

6. **Direct automation projection (9.5).** The staging branch and its reviewed
   PR remain the default route mandated by ADR 0002. A project may opt in to
   letting the mandated automation commit the deletion-only projection
   directly to the protected release branch, collapsing one PR round, only
   under a durable reviewed project policy, a dedicated non-merging identity,
   unchanged gate verification, and route verification updated to assert the
   forge-authenticated pusher (or a verified signature) instead of the staging
   merge -- never the self-asserted git author fields, and never an
   interactive coding-agent session standing in for the automation.

## Rationale

The deletion-only invariant was designed as an integrity guarantee, but an
integrity guarantee strong enough to prove tree identity is also strong enough
to carry validation evidence across the promotion. Re-running identical
validation on identical bytes is not defence in depth; it is the same defence
repeated, and its cost was pushing real projects toward resenting or bypassing
the governance. Removing redundancy that the invariants themselves prove
redundant preserves the design's credibility.

The staging-PR amendment is the one deliberate trade-off. ADR 0002 mandated
route verification because a projection once bypassed review by landing
directly on the release branch. That failure was a hand-driven shortcut. When
the projection is produced only by mandated automation and its content is
re-derived byte-for-byte by the gate, a staged review of the automation's own
commit verifies nothing the gate does not already verify; the residual risk is
compromised automation, which rubber-stamp review of an automation-authored PR
does not meaningfully mitigate. The exception is opt-in, durable, and
reviewable precisely so the default remains the stricter route.

## Consequences

- A normal promotion costs one authoritative validation (on develop) plus gate
  checks, instead of three or four full validation rounds.
- A failed promotion retries from the develop fix onward; the rehearsal makes
  most gate-shaped failures visible before any ref is cut.
- `REQUIRED_SOURCE_CHECKS` introduces a configuration surface: naming a
  workflow that does not exist, or one that runs only on pull requests rather
  than on pushes to `develop`, blocks every release PR until corrected, which
  is the fail-closed direction and surfaces misconfiguration immediately.
  Workflow names containing commas cannot be expressed and must be renamed.
- Projects adopting 9.5 concentrate more trust in the automation identity;
  the conditions in 9.5 bound that trust and keep it inspectable.

## Provenance and limitations

The redundancy analysis assumes forbidden paths are build-irrelevant, which
section 9.1 now states as an explicit obligation rather than an assumption. The
provenance check trusts the forge to record workflow-run metadata (event, head
branch, head SHA, conclusion) faithfully; a forge that cannot offer an
equivalent unforgeable binding leaves the rebuild fallback in force.
Real-world evidence for the pain this ADR addresses comes from downstream
projects running the full workflow per minor fix; evidence for the remedy is
so far limited to this repository's own test suite and dummy-project
end-to-end validation, and this ADR should be revisited if provenance-based
promotion misbehaves in a production repository.
