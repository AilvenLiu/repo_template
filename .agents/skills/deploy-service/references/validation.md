# Host deployment validation checklist

## Layout and policy

- [ ] The selected deployment root follows the documented mount/ownership
      decision and is absolute in host configuration.
- [ ] Capacity supports staging, live, rollback, evidence, and expected growth.
- [ ] Canonical path checks reject traversal, absolute archive entries, symlink
      escape, device files, and cleanup outside the approved root.
- [ ] Release ids, paths, channels, SHAs, and digests are validated again by the
      host helper.
- [ ] Helpers are persistent, root-owned where privileged, not writable by the
      deploy principal, and narrowly exposed through sudoers or forced command.

## Pre-cutover

- [ ] Backups and restore procedure for persistent state have current evidence.
- [ ] Host prerequisites, capacity, clock, certificates, routes, listeners,
      firewall, VPN, DNS, and recovery access are inventoried.
- [ ] Artefact digest, provenance where available, archive contents, and target
      compatibility are verified before stopping the live release.
- [ ] A known-good rollback artefact exists locally.
- [ ] Dry-run cleanup retains live, activating, rollback, pinned, and held
      releases for explicit reasons.

## Activation

- [ ] A host lock prevents concurrent activation and cleanup.
- [ ] Activation exposes only a complete old or complete new release.
- [ ] Exactly the intended release and service topology are live.
- [ ] Loopback, worker, reverse-proxy, public-ingress, and representative
      application checks pass and identify the release.
- [ ] Logs and status evidence do not leak secrets.

## Failure and rollback drills

- [ ] Failed health does not mark the release live.
- [ ] Interrupted activation leaves the old release live or an actionable
      recoverable state.
- [ ] Rollback uses a retained verified artefact and repeats health checks.
- [ ] Migration compatibility or a manual recovery boundary is documented.
- [ ] Malformed metadata or symlink escape makes cleanup stop without deletion.
- [ ] Concurrent/out-of-order requests cannot replace a newer live release.

## Closure evidence

- [ ] Record root decision, ownership, release id, source SHA, digest, host
      status, health results, cleanup output, disk usage, and rollback evidence.
- [ ] State every check not run and the resulting production risk.
