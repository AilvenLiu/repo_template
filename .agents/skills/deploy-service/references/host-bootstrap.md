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

- Use a dedicated service or deployment account with no broad sudo access.
- Keep private keys and privileged configuration root-owned with restrictive
  modes.
- Give the runtime only the read/write paths it needs. Keep releases immutable
  and persistent state outside release directories.
- Verify directory traversal permissions for the reverse-proxy worker without
  making unrelated directories broadly writable.

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
