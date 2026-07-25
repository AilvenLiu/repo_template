# Immutable release promotion

## Build once

Create the deployable or publishable bytes in one build stage after validation.
Emit a manifest containing source SHA, release id, digest, target compatibility,
toolchain, dependency-lock identity, and build run. Downstream jobs verify and
promote that manifest; they do not rebuild.

## Default source authority

Unless a durable, reviewed project-specific release policy explicitly defines a
different channel, automatic publication and production deployment are
authorised only by an update to `master`. The release manifest MUST record the
exact updated `master` SHA, and every published or deployed artefact MUST match
that SHA. A `release/*` branch is for validation and review; it does not
independently authorise automatic release or deployment.

## Publication surfaces

- GitHub Releases: attach the verified assets and checksums to an immutable tag
  that resolves to the recorded source SHA.
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
