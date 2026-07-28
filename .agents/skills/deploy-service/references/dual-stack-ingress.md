# Dual-stack reverse-proxy and edge diagnostics

Use this reference after publishing both `A` and `AAAA` records, or when a
proxy, origin, IPv6 listener, TLS certificate, and application health check do
not agree. Obtain operator approval before changing public DNS, firewall rules,
certificate material, privileged proxy configuration, or live service state.

## Keep the address families symmetric

Retain the existing IPv4 listeners while adding IPv6. With current Nginx, use
separate HTTP/2 enablement rather than the deprecated `listen ... http2` form:

```nginx
server {
    listen 80;
    listen [::]:80;
}

server {
    listen 443 ssl;
    listen [::]:443 ssl;
    http2 on;
}
```

Reuse a certificate only after identifying a known-good vhost and confirming
that its subject alternative names cover the service hostname. Keep the key
root-owned; inspect its configured path and certificate metadata, not key
contents. For Cloudflare Origin CA, set the edge to Full (strict).

Validate the proxy before changing DNS or restarting it:

```bash
sudo nginx -t
sudo systemctl restart nginx
sudo ss -lntp '( sport = :80 or sport = :443 )'
```

Use `reload` only when Nginx is already active. A failed or inactive service
needs a validated restart and a fresh listener check.

## Separate DNS, edge, proxy, and application evidence

Cloudflare-proxied DNS normally returns Cloudflare addresses, not the origin.
Confirm the records separately from origin reachability:

```bash
dig @1.1.1.1 A <hostname>
dig @1.1.1.1 AAAA <hostname>
curl -g -k -i --resolve '<hostname>:443:[<origin-ipv6>]' https://<hostname>/healthz
curl -i https://<hostname>/healthz
```

The direct IPv6 request retains the real hostname and SNI while bypassing the
edge. Interpret the first failing layer rather than applying unrelated fixes:

| Evidence | Meaning | Next check |
| --- | --- | --- |
| Edge `521` | The edge cannot connect to the origin. | Listener, firewall, route, origin TLS, and IPv4/IPv6 reachability. |
| Direct origin `502` | Edge, TLS, and proxy reach the host; proxy cannot reach its upstream. | Loopback health, upstream port, service state, and proxy error log. |
| Direct origin healthy but public failure | Edge configuration or DNS differs from the validated origin path. | Proxy mode, record target, edge TLS mode, and cache/routing configuration. |
| Loopback connection refused | No application is accepting the configured upstream address. | Service unit, container state, port mapping, and release activation. |

Run the probes from the host and from an external client where feasible. A VPN
resolver can prove private DNS, but it cannot prove public edge reachability.

## Confirm the runtime, not only the proxy

Check the expected topology and loopback endpoint before treating a `502` as an
Nginx fault:

```bash
sudo systemctl status --no-pager <web-unit> <worker-unit>
curl -i http://127.0.0.1:<port>/healthz
sudo journalctl -u <web-unit> -n 150 --no-pager
```

For containers, inspect the Compose status and service logs. Do not repair a
production failure with `docker pull`, `docker login`, an ad-hoc build, or a
mutable `latest` image. The activation helper must load the CI-built immutable
artefact and select its validated image reference before starting units.

## Preserve the evidence chain

Record the exact hostname, address family, release identifier, proxy listener
state, unit state, loopback response, direct-origin response, and public
response. Restore the last known-good release rather than weakening a health
gate or guessing at several network layers at once.
