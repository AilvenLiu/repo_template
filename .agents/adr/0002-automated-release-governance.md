# ADR 0002: Automated Release Projection and Tagging

**Status**: Active
**Date**: 2026-08-19
**Authors**: Template maintainers
**Amended by**: ADR 0003 (adds an opt-in direct automation projection route and
validation provenance for release-bound PRs)

## Summary

The release projection onto `release/v<x.y.z>` and the `release-v<x.y.z>` tag on
the resulting `master` merge are both mandated to be performed by the repository's
coding agent or other automation, never by hand. Tag presence is separately
verified by a read-only check, so that a skipped or broken creation step fails
loudly instead of passing unnoticed.

## Decision

Three rules, in `common/master-merge-policy.md` and `common/github-actions-cicd.md`:

1. The deletion-only projection MUST be produced by the coding agent or other
   automation. A hand-built projection is a violation even when its tree is
   correct.
2. The `release-v<x.y.z>` tag MUST be created by automation, deriving the version
   from the authoritative manifest at the recorded source commit, rejecting
   non-monotonic versions, and remaining idempotent on re-run.
3. Tag presence MUST be verified independently of tag creation. A promoted
   `master` head with no matching tag MUST fail a check.

The mandate to automate lives in the vendor-neutral policy. The concrete GitHub
Actions shape -- a dedicated job holding `contents: write` and nothing else, with
release and deployment jobs declaring `needs:` on it -- lives in the
vendor-specific constraint, so a repository on another forge is bound by the
property without being bound to the mechanism.

## Rationale

Neither step involves judgement. The deletion set follows entirely from the
forbidden-path list and the authoritative manifest; the tag name follows entirely
from that manifest and the merge commit. There is nothing for a person to decide,
and therefore nothing a person contributes except the opportunity to make a
mistake.

Both failure modes are observed rather than hypothetical, in the repository that
prompted this ADR:

- A `master` PR merged without its tag. The merge succeeded, every check passed,
  and the omission surfaced only when someone noticed later and created the tag by
  hand. Tagging is a separate action taken after the step everyone is watching has
  already reported success, which is precisely the shape of action that gets
  forgotten.
- A release projection was committed directly onto the protected release branch,
  skipping the `chore/release-v<x.y.z>` staging branch and its reviewed PR. The
  master merge gate passed, because it compares the resulting tree against the
  recorded source SHA and does not examine the route taken to build it. The
  deletion-only invariant held while the review the protected branch exists to
  carry was bypassed.

The second case is the more instructive. A correct outcome reached by the wrong
route still passed every gate, which means prose describing the route was not
enforcing it. Automation that always takes the same route, plus verification that
asserts the route was taken, closes that gap in a way more prose cannot.

## Consequences

Verification is mandatory; creation automation is mandatory only where CI exists.
A repository with no CI can still satisfy the read-only check, so the constraint
set stays uniformly satisfiable rather than inviting selective bypass.

Mandating automatic creation puts a `contents: write` credential into the release
workflow of every repository that has one. This is a real expansion of what a
compromised workflow can do, since a token that can create refs can generally
force-update them unless tag protection rules are configured. It is bounded by
confining the credential to a single dedicated job, forbidding force-update, and
keeping every other job read-only. Repositories handling this credential SHOULD
also configure forge-side tag protection, which this ADR does not itself require.

## Provenance and limitations

The reference implementation is the `tag` job in the AlphaForge repository. At the
time of writing it has run twice, creating `release-v0.2.1` and `release-v0.2.2`,
both cleanly and including the monotonicity comparison. Two runs is a thin
evidence base for a fleet-wide mandate, and this ADR should be revisited if the
pattern proves awkward in a repository with a different release model.

That implementation ends its highest-existing-tag lookup with a trailing
`|| true`, which is load-bearing for the bootstrap case where no release tags
exist yet, but which also swallows a genuine failure of the lookup and would
report a passing comparison that never ran. The constraint text calls this out
explicitly so the wart is not propagated by repositories copying the pattern.
