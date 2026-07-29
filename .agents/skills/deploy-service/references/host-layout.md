# Deployment-root and filesystem layout

## Select rather than assume

Inspect mounts, filesystem type, free space, inode capacity, ownership, backup,
restore evidence, and existing operator conventions. Preserve a secure working
layout instead of relocating production solely to satisfy this preference.

Unless a durable, reviewed project-specific deployment policy explicitly
states otherwise, automatic server deployment must use a dedicated data
filesystem. Choose in order:

1. An independently mounted or linked operator-approved data filesystem,
   normally `/data/www/<service>` or another canonical path beneath `/data/`.
2. A user-owned data filesystem for rootless/single-user operation, normally
   `~/data/www/<service>` or an approved equivalent beneath `~/data/`.
3. Another independently mounted operator-approved dedicated data volume, such
   as `/mnt/<data-volume>/www/<service>`.

Do not select `/var/`, `/srv/`, `/opt/`, `/usr/`, `/usr/local/`, or another
system-owned hierarchy as the default service root. A legacy system path may be
used only when a durable, reviewed project-specific deployment policy records
its reason, ownership boundary, migration/rollback plan, and operator approval.
Existing host convention alone is not an exception.

Resolve `~` during provisioning and write absolute paths into service and proxy
configuration. If a stable path is a symlink to a separate disk, resolve it and
verify every managed path stays on the approved dedicated data filesystem. Never
derive the root from release input.

## Canonical ownership

Unless a durable, reviewed project-specific deployment policy says otherwise,
create one unprivileged host deployment account named `deploy`. The approved
service root and its staging, releases, metadata, locks, and deploy-managed
persistent paths must be owned by `deploy`. For a rootless path, `~/data/`
means this account's home data root, normally `/home/deploy/data/`, and must be
resolved before it is written to configuration.

Keep privileged activation helpers, sudoers rules, unit policy, and proxy
configuration root-owned. A service runtime account receives only its required
read, traversal, or writable-state access. A self-hosted CI runner uses a
different principal and has no writable path beneath the `deploy`-owned root.
Scope each repository and environment to a separate credential and fixed helper
allow-list even when several services share the canonical account name.

## Recommended shape

```text
<deployment-root>/
|-- releases/<release-id>/
|-- staging/
|-- metadata/<release-id>.env
|-- shared/
|   |-- uploads/
|   `-- runtime-data/
|-- current -> releases/<release-id>
`-- locks/
```

The live server reads `current`; it does not expose `staging`, `metadata`,
helpers, credentials, or `.git`. Place databases, large mutable state, logs,
and secrets in explicitly managed persistent paths, possibly on a separate
data root. Document ownership and backup for each writable path.

Staging and final releases should share a filesystem when activation depends on
atomic rename. Capacity planning must allow the new staged release, live
release, rollback target, retained evidence, and growth during activation.

## Local database namespace

When the service requires a database on the host, keep it outside
`<deployment-root>` in a unified database namespace:

```text
<data-root>/
|-- www/<service>/
`-- database/<service-or-engine>/
```

Prefer `/data/database/<service-or-engine>`. For rootless or single-user
operation, use `~/data/database/<service-or-engine>` where `~` resolves to the
`deploy` account's home. Another dedicated data volume may use the same
`database/` namespace. Do not default to `/var/lib/`, `/srv/`, or a release
directory.

The database management root is created, maintained, and owned by `deploy`.
Database engines commonly need their own least-privilege runtime identity to
own raw data files; if so, delegate only the engine-specific child directory
and record its modes, backup, restore, retention, monitoring, and migration
boundary. Do not give the release workflow general read/write access to the
database merely because `deploy` maintains the parent namespace.

## Containment and modes

Canonicalize the trusted root and each candidate path before use. Reject
absolute archive members, `..`, unexpected links, device files, and paths that
resolve outside the root. Do not follow user-created symlinks during cleanup.
Use dedicated ownership and least-privilege modes; do not make parent trees or
release roots broadly writable merely to satisfy proxy traversal.
