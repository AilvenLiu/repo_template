# Self-hosted GitHub Actions runners

Use this reference when GitHub Actions build, test, lint, package, or GPU jobs
run on a persistent self-owned host. This is Pattern A: CI compute. It does not
replace Pattern B: deployment of an immutable artefact from an isolated
GitHub-hosted job through restricted SSH and the host contract in
`$deploy-service`.

## Contents

- [Select the patterns independently](#select-the-patterns-independently)
- [Establish the runner trust boundary](#establish-the-runner-trust-boundary)
- [Bootstrap through one committed idempotent script](#bootstrap-through-one-committed-idempotent-script)
- [Adapt workflows for a persistent host](#adapt-workflows-for-a-persistent-host)
- [Validate installation and maintenance](#validate-installation-and-maintenance)

## Select the patterns independently

| Need | Pattern | Trust boundary |
|------|---------|----------------|
| Move expensive or hardware-specific CI compute onto owned capacity | Pattern A: self-hosted Actions runner | The runner connects outbound to GitHub and executes repository job code as a dedicated unprivileged runner identity |
| Promote a verified artefact to a live service | Pattern B: GitHub-hosted deploy job plus scoped SSH identity | An isolated hosted job crosses inbound to one narrow host activation interface |

Projects may use either pattern or both. When both use the same machine, they
MUST use different operating-system principals with no shared credentials,
sudo rules, privileged groups, writable directories, helpers, or production
control sockets. Treat the CI principal as arbitrary code execution by anyone
who can cause an authorised workflow to run. It MUST NOT read the deployment
key, invoke the activation helper, or modify production releases or state.

Membership of a container-daemon group is root-equivalent. A runner with that
access does not satisfy process-only separation from production on the same
kernel; use stronger isolation or a different host, or record a durable,
reviewed risk exception that does not claim least privilege.

## Establish the runner trust boundary

- Prefer a private repository and a repository-scoped runner. An organisation
  runner needs an explicit repository allow-list and a reason to share capacity.
- Do not expose a persistent self-hosted runner to arbitrary public-fork code.
  A public-repository design needs a reviewed isolation and approval model,
  ephemeral disposable workers, and proof that untrusted jobs cannot reach
  secrets or persistent host state.
- Create a dedicated system user with no interactive login and no sudo. Grant
  only the device or build groups the declared job matrix requires.
- Use specific runner labels for repository, operating system, architecture,
  hardware, and trust class. Do not route a privileged job using only the
  generic `self-hosted` label.
- Keep registration tokens short-lived and out of files, logs, service
  environments, and shell history. Registration is administration, not a
  workflow step.

## Bootstrap through one committed idempotent script

Run the host bootstrap as root for first installation and maintenance. It MUST
be safe to re-run and MUST:

1. Create the runner identity, home, work, tool, cache, and service directories
   with deliberate ownership and modes. Correct the whole runner-owned cache
   tree, including parents created by root; fixing only one child cache leaves
   other tools unable to create siblings.
2. Install system packages, compilers, container support, and other privileged
   prerequisites. Workflow steps do not receive sudo.
3. Download a pinned Actions runner release and verify its recorded SHA-256
   digest before extraction. Never resolve `latest` during bootstrap.
4. Register the runner at the narrowest required scope with a short-lived
   token, then install it through the runner's supported service installer.
5. Add a systemd drop-in with `Restart=on-failure` and an explicit restart delay, such as `RestartSec=10`.
   Consider a protective `OOMScoreAdjust` for the listener, while documenting
   that it does not protect memory-heavy child job processes.
6. Set the service PATH explicitly. Service installation may capture the root
   installer's PATH; ensure the runner user's tool directories, such as
   `~/.local/bin`, are present in the service's effective PATH.
7. Provision host-level swap and persistent cache capacity once. Do not create
   a new swap device or other supposedly ephemeral host resource per job.
8. Check for an active job worker before restarting or upgrading the service.
   Skip with an actionable warning rather than terminating an in-flight job.

Monitor the service and queue state. Auto-restart handles listener failure; it
does not replace alerting, capacity monitoring, or a safe maintenance window.

## Adapt workflows for a persistent host

- Remove `sudo apt-get`, system service changes, user/group changes, and other
  privileged setup from workflow steps. Put stable host prerequisites in the
  bootstrap or a reviewed immutable worker image.
- Do not assume `runner.temp`, the workspace, caches, or tool directories are
  destroyed between jobs. Use release- or run-specific paths, clean sensitive
  temporary data, and make retries idempotent.
- Prefer a directly configured persistent local build cache when the same host
  handles repeat jobs. A remote cache action may be unnecessary overhead.
  Partition local caches by repository and trust class, include all
  ABI/toolchain inputs in keys, and make a cache miss affect speed only.
- Remove per-run swapfile creation. A persistent host otherwise accumulates
  active swap devices and files across jobs.
- Audit marketplace and composite actions that bootstrap an internal
  interpreter or toolchain. If their nested environment propagation fails on
  the host, use an explicitly pinned top-level setup action followed by the
  tool's pinned CLI. Do not weaken action pinning or patch runtime library paths
  globally to conceal the boundary.
- Declare and record the host compiler, standard library, runtime, container
  engine, and hardware contract. A first failure under a newer toolchain may be
  a genuine latent source or dependency defect; reproduce it and check reviewed
  upstream fixes before classifying it as runner noise.
- Keep matrix entries that represent supported product targets. Remove hosted
  image parity entries only when the product contract truly has one target;
  one self-hosted machine is not evidence for another OS, architecture, ABI, or
  GPU generation.

## Validate installation and maintenance

- Re-run bootstrap and verify it converges without duplicating registration,
  services, groups, swap, or directories.
- Confirm the listener restarts after failure and that its effective PATH finds
  every pre-provisioned tool.
- Run cache and package tools as the runner user and verify the entire
  runner-owned cache tree is writable without broadening unrelated modes.
- Exercise the busy guard against a running job before a service restart or
  upgrade.
- Inspect the runner user's groups, readable credentials, writable paths, sudo
  rules, service access, and sockets. When production is co-located, prove the
  CI user cannot reach the deploy identity or live service state.
- Run the authoritative workflow twice to expose persistent-state assumptions,
  cache contamination, duplicate resources, and non-idempotent cleanup.
- Record runner version and digest, labels and scope, bootstrap revision,
  toolchain and hardware identity, service policy, capacity, residual
  privileges, and every check not run.
