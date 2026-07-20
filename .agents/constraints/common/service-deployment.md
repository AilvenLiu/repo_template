# Service Deployment

This constraint governs host-side deployment and operation. GitHub Actions
workflow design, CI, auto-deployment, and auto-release are governed separately
by `common/github-actions-cicd.md`.

## Deployment Root Selection

Before changing the host, inventory mounts, ownership, free space, backups,
existing service layout, and operator conventions. Select the deployment root
deliberately, preserving a sound existing layout instead of moving a live
service merely to match a template.

For a new service, prefer these locations in order:

1. An independently mounted, operator-approved data filesystem, normally
   `/data/www/<service>` or another `www/` directory beneath the mounted data
   root. A stable path may point to that filesystem when the mount is elsewhere.
2. A user-owned data filesystem for a rootless or single-user service, normally
   `~/data/www/<service>` or the equivalent approved `~/data/` path.
3. An operator-owned local `www/<service>` path when the service and its
   lifecycle are intentionally local to that project or account.
4. `/var/www/<service>` as a compatibility alternative when the host already
   uses that system convention or the preceding options are unsuitable. Do not
   introduce system-wide layout changes solely to force `/var/www`.

The chosen root MUST be absolute in host configuration, resolve beneath the
approved root after symlink resolution, have explicit ownership and modes, and
have enough capacity for staging plus rollback. User-controlled release input
MUST NOT select or interpolate the root.

## Release and State Boundaries

- Production deploys MUST consume an immutable, CI-built artefact. Do not run
  `git pull`, dependency resolution, package installation, or source compilation
  as the deployment mechanism on the production host.
- Use versioned release directories, release metadata, and a stable activation
  pointer or equivalent platform-native indirection. Keep transfer and staging
  paths outside the live document root.
- Keep writable application state, databases, uploads, credentials, and logs
  outside immutable release directories. Deployment, rollback, and pruning do
  not imply permission to alter or delete persistent data.
- Give every deployment a validated release identifier and artefact digest.
  Validate identifiers, paths, digests, channels, and compatibility again at
  the host trust boundary.
- Stage and verify the full release before activation. Activation MUST be atomic
  where the platform supports it, so traffic sees either the old complete
  release or the new complete release.

## Identity and Privilege

- Run the service and deployment as dedicated, least-privilege identities.
- A privileged transition MUST use a persistent, reviewed, root-owned helper
  with an exact non-interactive sudo or forced-command boundary. Never execute
  a newly uploaded script as root and never grant CI a general root shell,
  package manager, container daemon, or unrestricted service manager.
- Pin SSH host identity. A deployment key MUST be scoped per repository and
  environment and SHOULD disable shell, PTY, forwarding, agent forwarding, X11,
  and arbitrary command selection.
- Secrets and private keys MUST remain outside release artefacts and logs.

## Activation, Health, and Recovery

- Serialize activation and pruning per environment with a host-side lock.
- Verify host and artefact compatibility before stopping the live release.
- Declare success only after checking release identity, expected process or
  container topology, loopback health, worker progress where applicable,
  reverse-proxy ingress, and representative application behaviour.
- Rollback MUST select a retained, verified artefact and use the same activation
  helper family. Do not rebuild, repair a checkout, or silently reverse an
  incompatible data migration.
- Retain at least the live release and a known-good rollback target. Cleanup
  MUST support dry-run, stay beneath the approved root, refuse symlink escapes,
  preserve active/rollback/pinned/held releases, and fail closed on malformed or
  unknown metadata.

## Host and Network Changes

Inventory listeners, IPv4 and IPv6, routes, forwarding, firewall, VPN, DNS,
TLS, reverse proxies, timers, containers, services, certificates, and recovery
access before mutation. Preserve unrelated services. Test loopback, origin
ingress with the real host name and SNI, and public ingress where applicable.
Changes to DNS, firewall, credentials, production data, privileged command
boundaries, or destructive retention require explicit operator approval and a
recovery path.

Read `.agents/skills/deploy-service/SKILL.md` before implementing or reviewing this
workflow.
