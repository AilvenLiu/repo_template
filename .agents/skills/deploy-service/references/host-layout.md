# Deployment-root and filesystem layout

## Select rather than assume

Inspect mounts, filesystem type, free space, inode capacity, ownership, backup,
restore evidence, and existing operator conventions. Preserve a secure working
layout instead of relocating production solely to satisfy this preference.

For a new service, choose in order:

1. An independently mounted or linked operator-approved data filesystem,
   normally `/data/www/<service>` or another `www/` path beneath the data mount.
2. A user-owned data filesystem for rootless/single-user operation, normally
   `~/data/www/<service>` or an approved equivalent beneath `~/data/`.
3. An operator-owned local `www/<service>` path when project-local lifecycle and
   capacity are intentional.
4. `/var/www/<service>` when it is the existing host convention or the earlier
   choices are unsuitable. It is an alternative, not a mandatory migration.

Resolve `~` during provisioning and write absolute paths into service and proxy
configuration. If a stable path is a symlink to a separate disk, resolve it and
verify every managed path stays on the approved filesystem. Never derive the
root from release input.

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

## Containment and modes

Canonicalize the trusted root and each candidate path before use. Reject
absolute archive members, `..`, unexpected links, device files, and paths that
resolve outside the root. Do not follow user-created symlinks during cleanup.
Use dedicated ownership and least-privilege modes; do not make parent trees or
release roots broadly writable merely to satisfy proxy traversal.
