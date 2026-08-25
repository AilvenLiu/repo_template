# Host, ingress, and network bootstrap

Use this reference for a fresh server or any change to reverse proxy, TLS, DNS,
firewall, VPN, systemd, users, or persistent storage.

## Inventory before mutation

Capture:

- operating-system and package baseline
- listening TCP and UDP sockets on IPv4 and IPv6
- addresses, routes, forwarding, firewall, NAT, VPN interfaces, and DNS paths
- running services, timers, containers, mounts, and disk capacity
- current DNS records, TLS mode, certificate coverage, and expiry ownership
- persistent application data, ownership, backup, and restore evidence

Treat existing network services as dependencies. Opening only SSH, HTTP, and
HTTPS can break a VPN gateway, local resolver, forwarding path, or monitoring
listener even when the new website itself works.

## Identities and filesystem boundaries

- Unless durable reviewed project policy says otherwise, create one
  unprivileged deployment account named `deploy` with no interactive shell or
  broad sudo access. Make it own the approved service deployment root; keep
  privileged helpers and host policy root-owned.
- GitHub Actions deploys through a repository- and environment-scoped
  credential for `deploy` and one fixed forced command or exact `sudo -n`
  allow-list. A self-hosted runner uses a different identity and cannot write
  `deploy`-owned production paths.
- Keep private keys and privileged configuration root-owned with restrictive
  modes.
- Give the runtime only the read/write paths it needs. Keep releases immutable
  and persistent state outside release directories.
- If a local database is required, create a deploy-managed root beneath
  `/data/database/`, `~/data/database/`, or another approved data volume.
  Delegate only the engine child that its runtime identity must own, and verify
  backup and restore before cutover.
- Verify directory traversal permissions for the reverse-proxy worker without
  making unrelated directories broadly writable.

## Supervision of host dependency services

Treat the recovery behaviour of every host service the deployment depends on as
part of the bootstrap. Do not assume a packaged unit restarts itself.

Inspect what the unit actually does before trusting it:

```bash
systemctl show <unit> -p Restart -p RestartSec -p OOMPolicy -p FragmentPath
```

`Restart=no` with `OOMPolicy=stop` means one OOM-killed child ends the service
permanently, and the unit then reports `Result: oom-kill` even though its main
process exited cleanly. That combination is common in distribution packages.

Install a drop-in rather than editing the packaged unit, at
`/etc/systemd/system/<unit>.service.d/restart-policy.conf`:

```ini
[Unit]
StartLimitIntervalSec=300
StartLimitBurst=10

[Service]
Restart=on-failure
RestartSec=5
OOMPolicy=continue
```

Reload, then verify the unit adopted it. `daemon-reload` updates a running
unit's properties without restarting it:

```bash
systemctl daemon-reload
systemctl show <unit> -p Restart -p OOMPolicy -p DropInPaths
```

Put that verification inside the installer and fail the run when it does not
match. An installed but ineffective drop-in looks identical to a working one
until the outage it was meant to prevent.

`OOMPolicy=continue` is right for a master/worker daemon because the master
respawns its children. It is wrong for a single-process service that cannot
recover from losing its only worker; there, let the unit stop and restart.

Remember the blast radius. These units are usually shared: a reverse proxy
serves every site on the host and an MTA carries every service's mail, so the
policy applies to co-tenants too. Confirm the other consumers still work after
the change, and note that a quietly self-healing unit no longer signals an OOM
kill through its unit state.

## TLS and DNS cutover

1. Configure and validate origin TLS before changing public DNS.
2. Test the new origin using the real host name and SNI while directing the
   request to the new address.
3. For a TLS-terminating proxy, require authenticated origin TLS. With
   Cloudflare Origin CA, use Full (strict), not Flexible or non-validating Full.
4. Change only the intended web records. Preserve mail and unrelated service
   records.
5. Test both IPv4 and IPv6 when both are published.
6. Keep the previous origin available until edge health and rollback are
   proven.

Track certificate expiry. Origin-only certificates are not necessarily trusted
by direct browser clients, so distinguish a direct origin diagnostic from the
public path.

## Firewall and recovery

Write a port-and-route plan before enabling or replacing firewall policy.
Preserve required UDP listeners, VPN-interface DNS, forwarding rules, and NAT.
Keep an out-of-band recovery route or provider console available while changing
remote access controls.

Test from three perspectives where possible:

1. host loopback to the application
2. host or trusted network through the reverse proxy with the real host name
3. external client through public DNS and any edge proxy

Diagnose DNS, transport, TLS, ingress, and application identity separately.
