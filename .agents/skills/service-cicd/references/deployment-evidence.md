# CI deployment evidence and target identity

A green deployment job proves only that its configured workflow path succeeded.
It does not prove that the intended production server received the release.
Bind every deployment claim to the following tuple:

- workflow run and immutable source SHA
- release identifier and artefact digest
- protected environment and deployment target identity
- host activation timestamp and previous release
- service, worker, loopback, origin, and public ingress evidence

## Make target identity observable without leaking secrets

Configure the deployment target through protected environment secrets or an
approved identity mechanism. Do not print the host value, SSH private key,
environment file, or certificate material. The fixed host helper should return
a non-secret host identity such as a configured target label and hostname, plus
the activated release identifier and UTC timestamp.

The CI summary should compare that result with the intended environment and
release. If the reported host identity, release identifier, or activation time
does not match the run, fail the deployment rather than declaring success.

## Verify after activation

After the narrow host activation command returns, run release-specific checks
against the same target in this order:

1. Read the host helper release record and confirm source SHA, digest, and
   activation timestamp.
2. Confirm the expected service and worker units are active and the expected
   processes or containers are present.
3. Probe the loopback health endpoint.
4. Probe the origin with the real hostname and SNI over every published address
   family.
5. Probe the public hostname through its DNS and edge-proxy path.

An older unit timestamp, absent release record, disabled unit, or missing local
listener after a green CI run is evidence of target-secret drift, a different
server, or an incomplete host interface. Do not repeatedly rerun the workflow;
stop, preserve logs, compare the protected target configuration with the host
identity, and correct the boundary deliberately.

## Keep the host interface authoritative

Build and test the artefact once in CI. Transfer only that immutable artefact to
a release-specific staging path, verify its digest, and call one persistent,
root-owned helper with validated scalar arguments. The helper, not workflow
YAML or uploaded scripts, controls the fixed deployment root, image loading,
unit lifecycle, release record, and rollback selection.

Do not use a deployment job to run a general shell, load a mutable image, pull
from an untrusted registry, compile source, or mutate proxy configuration as
root. A successful workflow must be reproducible as a host-side release record
and health evidence, not inferred from CI status alone.
