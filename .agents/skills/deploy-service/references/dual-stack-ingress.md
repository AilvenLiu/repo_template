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

## Diagnose a Cloudflare 525 without guessing

An edge `525` means the TLS handshake between Cloudflare and the origin did
not complete. Do not immediately change DNS records, reissue an Origin CA
certificate, or weaken the edge TLS mode. First collect evidence that separates
a shared origin failure from a hostname-specific virtual-host difference.

1. Record the failing hostname, UTC timestamp, Cloudflare Ray ID, and edge
   status. Test both the apex and canonical host when one redirects to the
   other.
2. Bypass Cloudflare while retaining the real hostname and SNI. Test every
   published origin address explicitly:

   ```bash
   curl -kI --resolve 'example.com:443:203.0.113.10' https://example.com/
   curl -g -kI --resolve 'example.com:443:[2001:db8::10]' https://example.com/
   ```

   `-k` is expected for a direct request to a Cloudflare Origin CA
   certificate; it is not appropriate for the public edge check.
3. If the direct requests succeed and another proxied hostname on the same
   origin succeeds, compare the effective TLS settings of the working and
   failing Nginx virtual hosts. Inspect `nginx -T`, not only the expected
   configuration file. Compare certificate and key paths, protocol versions,
   `ssl_ciphers`, `ssl_prefer_server_ciphers`, `ssl_ecdh_curve`, client-certificate
   verification, `ssl_conf_command`, `ssl_reject_handshake`, listener/default
   server selection, and included files.
4. Use one reviewed TLS policy for equivalent virtual hosts. When the working
   host has an explicit compatible policy that the failing host lacks, add the
   same policy to the failing host, validate with `sudo nginx -t`, then reload
   Nginx. For example, a policy already used by a working host may be:

   ```nginx
   ssl_ciphers HIGH:!aNULL:!MD5;
   ssl_prefer_server_ciphers on;
   ```

   This is a configuration-normalisation step, not a reason to disable Full
   (strict) or expose an Origin CA certificate directly to browsers.
5. Recheck the public path over IPv4 and IPv6 after the reload, including the
   redirect target. Keep the configuration backup until both paths have passed.

If a packet capture is needed, verify that it is non-empty before drawing any
conclusion. A zero-byte `.pcap` means the capture did not initialise; it is not
evidence that Cloudflare sent no traffic.

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
