# Immutable release promotion

## Build once

Create the deployable or publishable bytes in one build stage after validation.
Emit a manifest containing source SHA, release id, digest, target compatibility,
toolchain, dependency-lock identity, and build run. Downstream jobs verify and
promote that manifest; they do not rebuild.

For a governed release-shim promotion, the one build stage MAY run at the
recorded develop source SHA: the master merge gate proves that the promoted
`master` tree differs from that SHA only by deletions of build-irrelevant
paths, so the artefact of the source SHA is the artefact of the `master` SHA
(`master-merge-policy.md` section 9.1). A release manifest that reuses such an
artefact MUST record both SHAs and the gate evidence binding them, and
deployment still promotes only after `master` is updated.

Commit the bytes and manifest to the fixed operator-controlled local artefact
store described in [artifact-storage.md](artifact-storage.md), whether the
build runs on a self-hosted server or GitHub-hosted infrastructure. A hosted
build must use a fixed direct transfer or protected build-and-promote job; do
not use a GitHub Actions artefact upload as the hand-off or rollback store
unless the documented technical-necessity and explicit-user-request exception applies.

## Default source authority

Unless a durable, reviewed project-specific release policy explicitly defines a
different channel, automatic publication and production deployment are
authorised only by an update to `master`. The release manifest MUST record the
exact updated `master` SHA, and every published or deployed artefact MUST match
that SHA. A `release/*` branch is for validation and review; it does not
independently authorise automatic release or deployment.

## Publication surfaces

GitHub Release assets are a public publication surface, not CI transport,
retention, or rollback storage. Do not attach them by default: they require a
current user who explicitly requests that publication, or a durable reviewed
policy recording prior explicit user authorisation for that exact surface.
GitHub attestations and provenance are metadata, not permission to upload
artefact bytes. GitHub Packages and GHCR are GitHub byte-publication surfaces:
never use them as CI transport, retention, or rollback storage, and publish
only when a current user explicitly requests that named surface or a durable
reviewed policy records prior explicit user authorisation. Other package and
container registries still require an explicit release contract and must never
become the rollback source.
- Release tag: tag the merged `master` commit `release-v<major>.<minor>.<patch>`,
  using the version read from the project's authoritative manifest at the
  recorded source commit. Tag after the merge, never before. The tag names one
  immutable commit and MUST NOT be moved, deleted, or re-pointed; a corrected
  release takes the next version instead. See
  `.agents/constraints/common/master-merge-policy.md` section 8.
- GitHub Releases: when explicitly authorised, attach the verified assets and
  checksums to an immutable tag that resolves to the recorded source SHA.
- Package registries: use trusted publishing or short-lived identity where
  supported and verify the uploaded version and digest after publication.
- Container registries: push by digest, apply human-readable tags only as
  aliases, and deploy the digest.
- Server deployment: transfer the matching asset and digest, then use the host
  contract in `$deploy-service`.

If multiple surfaces are updated, record each resulting immutable identifier in
one release manifest. Do not silently accept diverging digests.

## Idempotency and partial failure

Release identifiers and versions are immutable. A retry may verify an existing
matching object or finish missing surfaces, but must reject an existing object
with different bytes. Document compensation for partial publication; avoid
deleting an already-consumed public release automatically.

Generate provenance or attestations where supported and sign artefacts when the
distribution ecosystem requires it. Consumers must be able to trace a published
or deployed object back to the reviewed source and workflow run.
