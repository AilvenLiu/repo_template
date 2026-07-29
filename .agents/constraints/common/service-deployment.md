# Service Deployment

This constraint governs host-side deployment and operation. GitHub Actions
workflow design, CI, auto-deployment, and auto-release are governed separately
by `common/github-actions-cicd.md`.

## Deployment Root Selection

Before changing the host, inventory mounts, ownership, free space, backups,
existing service layout, and operator conventions. Select the deployment root
deliberately, preserving a sound existing layout instead of moving a live
service merely to match a template.

Unless a durable, reviewed project-specific deployment policy explicitly
states otherwise, automatic server deployment MUST use an operator-approved,
dedicated data filesystem. Choose in this order:

1. An independently mounted data root, normally `/data/www/<service>` or
   another canonical path beneath `/data/`.
2. A user-owned dedicated data root for rootless or single-user operation,
   normally `~/data/www/<service>` or another approved path beneath `~/data/`.
3. Another independently mounted, operator-approved dedicated data volume with
   an explicit canonical root, such as `/mnt/<data-volume>/www/<service>`.

Do not use `/var/`, `/srv/`, `/opt/`, `/usr/`, `/usr/local/`, or another
system-owned hierarchy as the default service deployment root. An existing
system-path layout requires a durable, reviewed project-specific policy stating
its reason, ownership boundary, migration/rollback plan, and explicit operator
approval; host convention alone is not an exception.

The chosen root MUST be absolute in host configuration, resolve beneath the
approved dedicated data root after symlink resolution, have explicit ownership
and modes, and have enough capacity for staging plus rollback. User-controlled
release input MUST NOT select or interpolate the root.

## Default Deployment Identity and Ownership

Unless a durable, reviewed project-specific deployment policy explicitly
states otherwise, automatic deployment to a dedicated server MUST use one
canonical, unprivileged host account named `deploy`.
GitHub Actions is the recommended automatic-deployment orchestrator: an
isolated, protected deploy
job authenticates as `deploy` with a repository- and environment-scoped
credential and invokes one fixed host interface. Reusing the account name
across services does not permit shared credentials, unrestricted shell access,
or a helper that can select arbitrary services or paths.

The `deploy` account MUST own the approved service deployment root and the
staging, release, metadata, lock, and deploy-managed persistent-state paths
beneath it. It MUST NOT own privileged activation helpers, sudoers policy,
service-manager policy, reverse-proxy configuration, or other root trust
boundaries. A separate runtime identity MAY receive only the read, traversal,
or writable-state access its service needs. A co-located self-hosted Actions
runner MUST use a different principal and MUST NOT be able to write any
`deploy`-owned production path.

For rootless operation, `~/data/` means the `deploy` account's home data root,
normally `/home/deploy/data/`; provisioning MUST resolve it to an absolute
path. An alternate deployment account or ownership model requires the same
durable, reviewed project-specific exception as an alternate deployment root.

## Local Database Root

When a deployed project requires a database on the same host, its database
state MUST use a separately managed canonical root on the approved data
filesystem, outside every release directory. Choose in this order:

1. `/data/database/<service-or-engine>` or another canonical path beneath
   `/data/database/`.
2. `~/data/database/<service-or-engine>` beneath the `deploy` account's home
   for rootless or single-user operation.
3. A documented `database/` namespace on another operator-approved dedicated
   data volume.

Do not default local database state to `/var/lib/`, `/srv/`, an application
release, or another system-owned hierarchy. The canonical database management
root MUST be created, maintained, and owned by `deploy`, with explicit modes,
capacity, backup, restore, retention, and monitoring policy. When a database
engine requires its own runtime identity to own raw data files, delegate only
the engine-specific child directory, record that ownership boundary, and keep
the parent management root under `deploy`; do not broaden the deployment
workflow's access to database contents. Schema migration, database deletion,
restore, and retention remain separate explicitly authorised state operations,
not implied deployment permissions.

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

## Default Automatic Promotion Authority

Unless a durable, reviewed project-specific release policy states otherwise,
automatic production activation is authorised only by an update to `master`.
The deployment manifest and host record MUST identify the exact updated
`master` SHA and its immutable artefact digest. A `develop`, `release/*`, or
`hotfix/*` update may produce a validation candidate, but it has no default
authority to activate a production service or publish a release version.

A manual deployment or rollback is an explicitly approved operator action, not
an automatic channel. It MUST promote a verified artefact from `master` and use
the same activation, health, and rollback controls.

The default automated deploy job and host helper MUST reject a release metadata
root beneath a system-owned hierarchy. They MAY accept such a root only when the
reviewed project-specific deployment policy is supplied to the trusted host
configuration; a workflow input, branch, release id, or event payload cannot
create that exception.

## Identity and Privilege

- Use the canonical `deploy` account for automated host deployment and a
  separate least-privilege runtime identity where the service needs one.
- Self-hosted CI compute is not a deployment identity. If a persistent Actions
  runner shares the production machine, its principal, credentials, privileged
  groups, helpers, control sockets, and writable paths MUST NOT overlap the
  deploy principal or production service state. Restricted SSH deployment from
  an isolated GitHub-hosted job remains a separate boundary.
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
