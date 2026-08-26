# ADR 0005: Single-PR Deterministic Release Promotion

**Status**: Active
**Date**: 2026-08-26
**Authors**: Template maintainers
**Amends**: ADR 0002 (projection route) and ADR 0003 (direct projection default
and version-bump efficiency)
**Unaffected**: ADR 0004 (post-deployment semantic tagging and operational
identity separation)

## Context

The original release shim protected both the release ref and `master` with
separate reviewed transitions. In real AlphaForge and Consilience promotions,
that produced a dedicated version PR, a staging branch and PR, a release branch,
and finally the master PR. The repeated branch preparation and heavy CI cost
was disproportionate to a projection whose content is mechanically determined.

ADR 0003 proved that the master gate's leaf-object comparison can transfer
validation evidence across a deletion-only projection and allowed direct
projection as an opt-in exception. In practice its dedicated-identity and route
attestation requirements made the exception harder to operate than the staging
PR it replaced. Downstream CI also exposed a second mismatch: a late version-only
commit changes the exact develop SHA, while validation provenance was bound only
to full push validation at that new SHA.

The master PR already reviews the exact candidate that can enter production.
A second review of a mechanical cleanup adds no independent content assurance
when the master gate re-derives every permitted tree difference. The useful
security boundary is therefore a create-once candidate plus a head-bound master
review, not two pull requests carrying the same proof.

## Decision

### One ordinary release PR

The default ordinary promotion has one pull request:

`release/v<major>.<minor>.<patch>` to `master`.

The generic workflow no longer creates or accepts
`chore/release-v<major>.<minor>.<patch>` staging branches. A project may retain
that older route only through a durable project-specific strict profile that
ships and tests its own route enforcement.

### Deterministic create-once projection

The repository-owned `.agents/bin/agent-release prepare` command:

1. resolves an immutable `develop` source SHA and derives the version and ref
   name from its authoritative manifest;
2. rehearses format, mirror agreement, and monotonicity before mutation;
3. copies the source tree into an isolated temporary Git index and deletes only
   master-forbidden paths;
4. independently checks the resulting tree with the same deletion-only
   invariant as the hosted master gate;
5. creates one projection commit whose only parent is the develop source;
6. creates `release/v<version>` only when the ref is absent; and
7. verifies and reuses an existing candidate only when its parent and tree are
   identical, otherwise failing without moving or deleting it.

A person or interactive coding agent may invoke the command. Neither may
hand-build the projection, commit while checked out on the release branch,
force-update the ref, or substitute an arbitrary cleanup procedure. The command
does not push automatically, switch branches, stash, deploy, publish, tag, or
merge.

### Bounded version-only develop exception

Bumping the version in the functional PR remains preferred. When an
already-reviewed release train needs only the final semantic version, the
repository-owned `.agents/bin/agent-release bump <version>` command is the sole
direct-commit exception on protected `develop`.

It requires a clean, current develop branch; changes exactly the authoritative
version field and required hybrid mirror; proves that normalising those fields
makes parent and child manifests byte-identical; requires a strict, increasing
semantic version; and commits only those manifests. It runs no full build or
test. It does not authorise dependency, changelog, source, workflow, mode, or
other metadata changes, and it never force-pushes.

### Parent-bound validation provenance

A release PR sourced from that bounded child records both:

`Develop-Source-SHA: <version-only-child>`

`Release-Metadata-Parent-SHA: <fully-validated-parent>`

Before accepting validation evidence at the parent SHA, the master gate
independently proves that the child has exactly that one parent, complete trees
differ only in the required manifests, only the canonical version tokens differ
inside those manifests, hybrid mirrors agree, and the version increases. A path
allow-list, commit message, Git author, or PR-body assertion is insufficient.

If any proof fails, parent validation is rejected. The source must then carry
its own full evidence or the master PR must run the full profile validation.
Hotfixes never use parent provenance.

### Publication remains master-bound

Release refs remain non-deploying candidate buffers. Automatic deployment and
publication continue to require the exact resulting `master` SHA. ADR 0004
continues to require semantic tagging only after every required deployment gate,
using a create-only write followed by fresh read-only verification.

## Rationale

The deletion-only gate already detects every addition, modification, rename,
mode change, type change, and non-policy deletion. The extra staging PR reviewed
no information the master PR and gate did not review again. Removing it reduces
coordination without weakening candidate identity.

Creating the release ref once at its final commit is safer than first pointing a
protected ref at the unsanitised source and then granting an identity permission
to update it. No update route exists to abuse. Binding hosted checks and approval
to the current master-PR head detects attempted candidate replacement.

The version-only exception is narrower than a general direct-push permission.
Its safety rests on independently normalised content and parent identity, not on
trusting the command invocation. This permits heavy validation to remain attached
to the fully reviewed parent while the release version itself receives a cheap,
structural check.

## Consequences

- A normal promotion has one PR and no staging branch.
- Release preparation needs no checkout, stash, working-tree deletion, dedicated
  bot, signing key, or external projection controller.
- Hosted rules must prevent force updates and deletion of release refs, bind
  checks and approvals to the current master-PR head, and grant release refs no
  deployment or publication authority.
- Projects must teach develop push CI to recognise the bounded version-only
  shape if they want to avoid heavy jobs there. A skipped heavy workflow must
  not masquerade as full validation at the child SHA; the gate deliberately
  uses the validated parent.
- The release command creates local commits and refs but does not push them.
  Operators retain explicit control over remote writes.
- The strict staging profile remains available but is no longer implemented by
  the generic gate.

## Rejected alternatives

- **Keep staging as the default.** Real use showed that its second PR was
  routinely mechanical and encouraged bypass rather than useful review.
- **Permit arbitrary direct commits to develop or release refs.** This would
  discard the structural boundary rather than narrow it.
- **Trust changed paths only for version bumps.** Manifests contain build and
  dependency configuration; the gate must compare their normalised complete
  contents.
- **Require a dedicated signing controller for every projection.** This protects
  route identity but adds more operational machinery than the byte-for-byte
  candidate needs. Projects with stronger organisational separation may still
  adopt it in their strict profile.
- **Move version selection onto the release branch.** That violates the
  deletion-only relationship and breaks source-tree identity.
