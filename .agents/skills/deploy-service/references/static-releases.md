# Atomic static releases

Use this model when the deployable artefact is a complete static directory.
Select `<deployment-root>` through [host-layout.md](host-layout.md); typical new
roots are `/data/www/<service>`, `~/data/www/<service>`, or another
operator-approved dedicated data volume. Do not use `/var/`, `/srv/`, `/opt/`,
`/usr/`, `/usr/local/`, or another system-owned hierarchy unless a durable,
reviewed project-specific deployment policy explicitly permits that exception.

## Layout

```text
<deployment-root>/
|-- releases/<release-id>/
|-- staging/
|-- shared/uploads/
|-- current -> releases/<release-id>
`-- metadata/<release-id>.env
```

The reverse proxy serves only `current`. It must never expose `.git`, staging,
uploads unless explicitly routed, helpers, metadata, or secrets.

## Activation

1. Acquire an environment-specific host lock.
2. Receive an archive in a release-specific temporary path outside `current`.
3. Validate release id, expected digest, archive members, and path containment.
4. Extract into a new staging directory on the same filesystem as `releases/`.
5. Check required files, modes, ownership, compatibility, and static integrity.
6. Rename staging to the immutable final release directory.
7. Create a temporary relative symlink and atomically replace `current`.
8. Run direct-origin and public-ingress release-identity checks.
9. Durably record previous/current releases before pruning anything.

Do not overwrite a final release directory. If it exists, verify its digest and
metadata before treating activation as idempotent.

## Rollback and retention

Rollback atomically repoints `current` to a verified retained release and repeats
health checks. Retain live and known-good rollback targets. Pruning must refuse
either target, reject malformed metadata, avoid symlink traversal, and stay
beneath the canonical approved root.
