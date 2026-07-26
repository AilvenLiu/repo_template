---
name: deploy-service
description: Design, implement, review, or troubleshoot secure host-side deployment of a service using an approved data or www root, immutable release artefacts, restricted SSH or host helpers, atomic activation, runtime services, health gates, rollback, retention, reverse proxy, TLS, DNS, firewall, and production evidence. Use for static sites, Python services, C++/CUDA services, hybrid applications, container stacks, fresh-server bootstrap, service units, host activation, or deployment runbooks. Use service-cicd separately for GitHub Actions CI, auto-deployment, and auto-release.
---

# Deploy Service

Deploy a verified immutable artefact into a deliberately selected host root,
then activate it through a narrow persistent interface. This skill owns the
host. Read `$service-cicd` for GitHub Actions validation, build, publication,
auto-deployment, and auto-release. A self-hosted CI runner provides compute; it
does not replace the separate restricted SSH deployment identity and host
activation boundary.

## Start with the host contract

1. Read `.agents/constraints/common/service-deployment.md`. When GitHub Actions,
   auto-deployment, or auto-release is in scope, also read
   `.agents/constraints/common/github-actions-cicd.md`; skill guidance does not
   replace either mandatory constraint.
2. Read repository entrypoints, `.agents/project.yml`, release metadata, existing
   host helpers, service units, reverse-proxy configuration, mounts, and
   operations documentation.
3. Inventory the host before mutation: identities, mounts, filesystem capacity,
   ownership, existing release layout, persistent data, backups, listeners,
   services, containers, routes, firewall, VPN, DNS, TLS, and recovery access.
4. Record assumptions affecting availability or security: target hosts,
   deployment root, runtime identity, persistent state, compatibility, health
   surfaces, rollback objective, retention, and privilege boundary.
5. Select and document the deployment root using
   [host-layout.md](references/host-layout.md). Unless a durable, reviewed
   project-specific deployment policy says otherwise, use an independently
   mounted `/data/www/<service>`-style root, an approved `~/data/www/<service>`
   root, or another explicitly approved dedicated data volume. Do NOT use
   `/var/`, `/srv/`, `/opt/`, `/usr/`, `/usr/local/`, or another system-owned
   hierarchy as the default deployment root.
6. Select the activation model:
   - Static files: read [static-releases.md](references/static-releases.md).
   - Containers, native binaries, Python runtimes, or long-running services:
     read [service-releases.md](references/service-releases.md).
7. Read [project-profiles.md](references/project-profiles.md) to verify the
   artefact/host compatibility boundary.
8. For fresh host, reverse proxy, TLS, DNS, firewall, VPN, or systemd work, read
   [host-bootstrap.md](references/host-bootstrap.md).

Stop for approval before changing public DNS, firewall policy, credentials,
production data, privileged command boundaries, destructive retention, or an
existing live layout.

## Resolve automatic promotion authority

Before designing or enabling automatic host activation, resolve the release
authorisation. Unless a durable, reviewed project-specific release policy says
otherwise, automation runs only after `master` is updated and deploys the
immutable artefact built from that exact `master` SHA. `develop`, `release/*`,
and `hotfix/*` may validate candidates but MUST NOT automatically activate a
production service or publish a version. Manual deployment and rollback remain
explicit operator actions and promote verified `master` artefacts only.

Unless the project-specific policy grants an explicit reviewed exception, the
automated deploy workflow and host helper MUST use a canonical dedicated data
root and reject `/var/`, `/srv/`, `/opt/`, `/usr/`, `/usr/local/`, and other
system-owned deployment roots. A workflow input or existing host convention is
not an exception.

## Enforce these invariants

- Production receives an immutable CI-built artefact. Do not deploy with
  `git pull`, dependency resolution, package installation, or source compilation
  on the host.
- The deployment root is fixed by trusted host configuration, not selected by a
  branch, release id, workflow input, archive path, or other user-controlled
  value. Canonicalize and enforce path containment at every file boundary.
- Keep transfer/staging outside the live document root. Separate immutable
  releases from uploads, databases, credentials, logs, and all persistent state.
- Give every deployment a validated release id joining source SHA, artefact
  digest, host metadata, activation status, rollback target, and retention.
- Verify digest, provenance when available, archive paths, and host compatibility
  before activation.
- Keep the deploy principal unprivileged. Privileged activation uses a narrow,
  persistent, root-owned helper through an exact forced-command or `sudo -n`
  allow-list. Never run a newly uploaded script as root.
- If self-hosted CI shares the production machine, give its runner and deploy
  path separate principals with no overlapping credentials, privileged groups,
  helpers, control sockets, or writable paths. The runner MUST NOT modify live
  releases or persistent production state.
- Pin SSH host identity and restrict deployment keys: no general shell, PTY,
  forwarding, agent forwarding, X11, or user-selected command.
- Serialize activation and pruning per environment with a host-side lock.
- Make activation atomic where supported. Traffic sees the old complete release
  or the new complete release, never a mixed tree.
- Declare success only after release identity, exact process/container topology,
  loopback health, worker progress where applicable, ingress, and representative
  application behaviour pass.
- Rollback selects a retained verified artefact and uses the same helper family.
  It does not rebuild or repair source manually.
- Cleanup is dry-run capable, cannot escape the approved root, preserves live,
  rollback, activating, pinned, and held releases, and fails closed on malformed
  metadata or unknown state.

## Use an explicit host state machine

```text
received -> verified -> staged -> activating -> healthy -> live
                                   |             |
                                   +-- failed ---+--> rollback -> restored
```

Record at least release id, source SHA, artefact digest, compatibility, created
and activated UTC timestamps, previous live release, status, health results,
and retention reasons. Retrying the same verified release is a safe no-op or
repeats validation without corrupting state.

## Keep the host interface narrow

Prefer one of:

1. A forced-command SSH key invoking one fixed unprivileged publisher.
2. A restricted account invoking a fixed root-owned helper through an exact
   `sudo -n` rule.
3. A pull-based deployment agent with equivalent digest, identity, and
   activation restrictions.

Validate every argument again inside the host helper. Remote automation is not
a host security boundary. Never give CI general sudo, Docker daemon access,
unrestricted `systemctl`, package managers, interpreters, or uploaded scripts.

## Validate adversarially

Challenge at least:

- selected root is missing, full, wrongly owned, symlinked outside its approved
  boundary, or on a different filesystem from atomic staging
- archive traversal, hostile release id, mismatched digest, incompatible ABI,
  or incomplete transfer
- two activations overlap or complete out of order
- a stale duplicate process remains after apparently successful activation
- one process, worker, route, FFI/native path, or ingress check fails
- rollback target is absent, ambiguous, incompatible, or no longer restorable
- cleanup sees malformed metadata, symlink escape, expired hold, or unknown live
  release
- a migration is not backward compatible with automatic rollback
- IPv4 works while IPv6, VPN DNS, forwarding, or an existing listener is broken

Do not weaken a failed gate. Preserve the last known-good release, capture
evidence, and make the failure actionable.

## Handoff

Deliver or update host helpers, service/reverse-proxy configuration, tests, and
operator runbooks actually required. Report the selected deployment root and
why, ownership and privilege boundary, artefact contract, activation, health,
rollback, retention, ingress, bootstrap steps still requiring an operator, and
validation evidence. Use [validation.md](references/validation.md) for closure.
