# Container, native-binary, and long-running service releases

Use this model when activation changes processes rather than only a document
root.

## Artefact contract

Deploy a CI-built container image by immutable digest or a CI-built native
release archive with a recorded checksum. Do not deploy a floating image tag as
the only identity. Store release metadata separately from writable runtime
state.

For containers, give the application stack a stable project name and stable
labels for service, release, channel, source SHA, and image digest. For native
services, install immutable versioned paths and make systemd reference a stable
activation pointer or validated environment file.

## Automatic promotion source

Unless a durable, reviewed project-specific release policy states otherwise,
automatic activation accepts only release metadata for the exact SHA produced by
a `master` update. Record that `master` SHA with the digest before activation.
A release candidate from `develop`, `release/*`, or `hotfix/*` may be tested,
but it has no default authority to activate production. Manual recovery remains
an approved operator action using a verified `master` artefact. Unless a durable,
reviewed project-specific policy says otherwise, activation metadata must name a
canonical dedicated data root beneath `/data/`, `~/data/`, or another approved
data volume; it must reject system-owned roots such as `/var/`, `/srv/`, or
`/opt/`.

## Privileged activation

Keep activation logic in reviewed, persistent, root-owned helpers. The helper
must:

1. Validate release id, channel, source SHA, paths, and digest against strict
   allow-lists.
2. Acquire an exclusive deployment lock.
3. Refuse unknown parallel or legacy application instances.
4. Verify host compatibility and persistent-state prerequisites.
5. Stage the new release without stopping the current one where possible.
6. Activate exactly the intended services and record the previous release.
7. Run status and smoke gates before marking the release live.
8. Restore the previous release automatically when activation fails safely.

Do not give CI sudo permission to general shells, package managers, Docker as a
whole, systemctl as a whole, wildcard interpreters, or uploaded temporary
scripts.

## Topology and health

Define the expected application topology exactly. Detect both missing services
and stale duplicate stacks. Supporting infrastructure such as the reverse
proxy or monitoring system does not count as a second application stack.

Health checks should cover:

- intended release identity and digest
- exact process or container set
- loopback health for every service role
- worker progress or heartbeat, not only an open port
- reverse-proxy routing with the production host name
- representative authenticated and unauthenticated routes
- native library, FFI, database, and GPU checks where applicable

## Rollback and migrations

Rollback selects an existing verified artefact; it never rebuilds source. If a
release changes persistent data or schema, define compatibility with both the
new and previous application versions before automatic rollback. Otherwise
make rollback a deliberate operator-gated recovery procedure.
