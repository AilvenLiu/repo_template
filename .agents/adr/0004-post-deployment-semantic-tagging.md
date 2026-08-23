# ADR 0004: Post-deployment Semantic Tagging and Operational Identity Separation

**Status**: Active
**Date**: 2026-08-23
**Authors**: Template maintainers
**Amends**: ADR 0002 (tag ordering, identity separation, verification trust
context, and the provenance claim in its final section)

## Summary

ADR 0002 required the `release-v<x.y.z>` tag to be created before any release or
deployment job that consumes it. That ordering is wrong wherever promotion
includes a deployment gate: it produces a semantic tag for a commit whose
deployment then fails, and afterwards nothing distinguishes that tag from one
naming a release that actually shipped.

This ADR moves the tag write after a successful deployment of the exact `master`
SHA, forbids operational deployment identifiers from being published as Git
tags, and requires independent verification to run in a fresh read-only trust
context rather than trusting the publisher.

## Context

The correction was authored and proven in the Consilience repository, whose
v0.2.4 release separated timestamped operational deployment identifiers from
semantic Git tags, moved semantic publication after a successful master
deployment, added create-only oldest-first reconciliation of missing historical
tags, and added an independent read-only verifier. That repository carries the
project-specific record of the same decision, including its own historical
recovery evidence, as its ADR 0004.

The failure ADR 0002's ordering permits is not hypothetical. In the AlphaForge
repository -- the reference implementation ADR 0002 cites -- run 32157164287
created `release-v0.2.1` seven seconds into the workflow and the deployment job
for the same commit failed twenty-three minutes later at host activation. No
successful re-run for that SHA exists. `release-v0.2.1` therefore names a commit
that never reached production, and did so while faithfully implementing the
policy as written.

This also corrects ADR 0002's provenance section, which records that the
reference implementation created `release-v0.2.1` and `release-v0.2.2` "both
cleanly". The tag operations succeeded; the promotion `release-v0.2.1` claims did
not.

## Decision

1. A semantic tag is written only after the merge and every required promotion
   and deployment gate for that exact `master` SHA has succeeded. Where a
   workflow deploys, the tag job declares `needs:` on the deployment job, not the
   reverse.
2. The version contract MAY still be evaluated before the deployment gate so a
   missing bump fails in seconds. Only the tag write waits.
3. Operational deployment identifiers are host, artefact, retention, and rollback
   join keys. Automation does not create them as Git tags and never substitutes
   one for a semantic tag.
4. The tag write uses a create-only operation with no force-update, move, or
   deletion path, in a job holding `contents: write` and nothing else, which is
   the only write-capable job and never receives deployment credentials.
5. Verification runs after every tagging attempt, from a fresh read-only context
   that independently re-derives eligible commits, manifest versions, expected
   tag names, and exact targets. It does not consume publisher outputs and holds
   no production environment, deployment credential, or write token.
6. Reconciliation of missing historical tags is optional. A project that adopts
   it must review the recovery policy into `master` first, fix the repository
   identity and promotion evidence including the exact successful deployment
   workflow and job, record known evidence limitations, accept no user-supplied
   ref, reconcile in ascending numeric order, and revalidate the remote `master`
   and every promotion ref immediately before each write.

## Consequences

A semantic tag can no longer claim a release whose required deployment failed.

Verification necessarily follows the merge and deployment it depends on, so it
cannot be a pre-merge required check for that same promotion. A project must
treat it as a mandatory post-merge result and block or alert on later promotions
until it succeeds. This is a real weakening of the "required check" story in ADR
0002 and is stated rather than hidden: the check still cannot be skipped
silently, but it detects rather than prevents.

Moving the tag write later means a promotion with an unbumped version now fails
after a full build unless the version contract is kept as a separate early step.
Projects are expected to keep that early check for exactly this reason.

Repositories that already tag before deploying carry tags whose deployment
status is unknown. This ADR does not authorise moving or deleting them; a
published tag stays published. The correct remedy is to record which historical
tags lack deployment evidence and let the next release supersede them.

This ADR mandates no workflow shape and ships no workflow template. Per-project
CI/CD remains project-authored against these constraints, so a repository on
another forge is bound by the properties without being bound to the mechanism.
