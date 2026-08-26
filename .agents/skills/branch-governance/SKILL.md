---
name: branch-governance
description: Design, implement, review, or troubleshoot protected branch policies, master-bound pull-request or merge-request gates, GitHub branch rules, presence-based deny lists, and release-shim branches. Use when changing master/develop/release/hotfix flow, GitHub Actions PR policy, required checks, or release promotion entry rules.
---

# Branch Governance

Use this skill with `service-cicd` when the branch policy affects CI, release,
or deployment channels. Read the branch, master-gate, and GitHub Actions
constraints before editing policy or workflow files.

## Establish the branch contract

| Target | Allowed source | Required purpose |
|---|---|---|
| `develop` | feature/fix/docs/chore branches; bounded `agent-release bump` exception | normal integration and release version metadata |
| `master` | same-repository `release/v<x.y.z>`, `hotfix/v<x.y.z>` | reviewed production entry |

For every target, state whether direct pushes are denied, which approvals are
independent, which status checks are required, and which file paths cannot
cross the boundary. Treat the source branch name and changed paths as untrusted
event data until the gate validates them.

## Implement the master hard gate

1. Keep the deterministic policy in `master-merge-gate.py` and add tests for
   every allowed source, forbidden tree path, changelog exception, release
   projection change type, required PR body field, and hotfix trade-off.
2. Run the gate for master-bound PRs/MRs and configure its status check as
   required for `master`. The generic one-PR route has no PR targeting
   `release/*`.
3. Run profile-authoritative format, lint, static analysis, build, and test
   validation as a separate required status check. That status stays required
   for every master-bound PR; `master-merge-policy.md` section 9.1 governs how
   an identity-proved release PR may satisfy it without a rebuild.
4. Use read-only permissions for the gate. A GitHub `pull_request_target` gate
   may run only trusted base-branch policy; never check out or run PR code, use
   production secrets, or grant write permissions.
5. Protect the workflow with hosted CODEOWNERS/ruleset review. A checked-in
   workflow alone cannot stop an authorised maintainer changing it later.

## Choose a release cadence

The shim pipeline is priced per release, not per change. Default to release
trains: accumulate reviewed merges on `develop` and promote on a cadence or
when the accumulated value warrants it, rather than promoting every merge. An
urgent fix rides an immediate single-change train, or the hotfix path when
`develop` has diverged too far. See `master-merge-policy.md` section 9.3.

## Rehearse before you cut

Before creating any release ref, rehearse the promotion locally with the
shipped gate. The rehearsal is read-only and needs no network or token:

```bash
# python and hybrid profiles
poetry run python .github/scripts/master-merge-gate.py --rehearse \
  --source-ref develop --master-ref origin/master
# cpp profile
python3 .github/scripts/master-merge-gate.py --rehearse \
  --source-ref develop --master-ref origin/master
```

It derives the version and every release name from the authoritative manifest
at the candidate SHA, verifies strict format and monotonicity against
`master`, and simulates the deletion-only projection, reporting what it will
remove. It fails closed: an unresolvable master baseline is a failure, and a
first release with no master yet must be declared with
`--allow-missing-master-ref`. Fix every finding on `develop` first: a
rehearsal failure costs seconds, while the same failure on the master PR costs
the whole promotion cycle. On success it prints the `Develop-Source-SHA` body
line to paste into the master PR.

## Use a release shim

`develop` is the source of truth and `master` is a derived, sanitised
publication. `develop` MUST NOT target `master` directly. For an ordinary
release, it also MUST NOT merge from or rebase onto `master`.

Promote reviewed `develop` content through a release shim:

1. Author and review every functional change through `develop`, then run the
   repository-owned validation there while the complete tooling is present.
2. Fetch `origin` immediately before the operation so `origin/develop` and
   `origin/master` are fresh; the wrapper does not perform network writes.
   Then ensure the authoritative manifest on `develop` already declares the
   release version. Prefer updating it in the functional PR. For an
   already-reviewed train that needs only version selection, run
   `.agents/bin/agent-release bump <x.y.z>` on clean, current `develop`.
   This bounded exception commits only `pyproject.toml` for Python,
   `CMakeLists.txt` for C++, or both required hybrid manifests; it performs
   no full build. Push normally and never force.
3. Validate and record the immutable reviewed `develop` SHA. The master PR
   body MUST contain `Develop-Source-SHA: <full 40-character SHA>`. Read
   `<x.y.z>` from the authoritative manifest at that exact SHA and derive every
   name below from it; never type the version by hand.

   ```bash
   # python profile
   SOURCE_SHA=$(git rev-parse develop)
   VERSION=$(git show "$SOURCE_SHA:pyproject.toml" \
     | sed -n 's/^version[[:space:]]*=[[:space:]]*"\(.*\)"/\1/p' | head -1)
   # cpp and hybrid profiles
   VERSION=$(git show "$SOURCE_SHA:CMakeLists.txt" \
     | sed -n 's/.*VERSION[[:space:]]\+\([0-9]\+\.[0-9]\+\.[0-9]\+\).*/\1/p' | head -1)
   ```

4. Run `.agents/bin/agent-release prepare --master-ref origin/master`.
   The command rehearses the candidate, constructs the deletion-only tree in a
   temporary index, creates `release/v$VERSION` once at its final commit, and
   prints the exact non-force commit-to-ref mapping plus required master-PR
   body fields. It does not switch branches, stash, push, merge, deploy, or tag.
5. Push the printed mapping without force. Hosted protection MUST allow the
   ref's creation but reject every later update or deletion. Never update, delete,
   or recycle an existing release ref.
6. Open the sole ordinary release PR/MR, `release/v$VERSION` to `master`,
   carrying the printed source fields, validation evidence, changelog, and
   rollback/release notes. If a bounded version-only commit was used, include
   `Release-Metadata-Parent-SHA`; the gate will re-prove its entire shape.
7. Merge only after the master gate, profile validation or accepted provenance,
   and applicable approval evidence pass.
8. Tag the resulting `master` merge commit `release-v$VERSION` only after every
   required deployment gate for that exact SHA succeeds. The tag is create-only
   and independently verified; ADR 0004 governs the ordering.

The candidate version MUST be strictly greater than the version currently on
`master`. Reusing a released version is forbidden even after deleting its branch
or tag; without server-side ref protection this check is the only structural
defence against name recycling.

The release branch MUST contain only deletions of paths forbidden by the
master policy relative to the recorded `develop` SHA. It MUST NOT contain a
functional change, addition, rename, mode change, or any other deletion. The
gate verifies the recorded SHA's ancestry and compares leaf tree entries by
path, mode, type, and object SHA as a hard failure. This invariant makes the
validated `develop` content, modulo removals, the content that ships.

The release ref is a create-once candidate, not a working branch. The command
may be invoked by a person or interactive agent because safety is independently
derived from source identity and complete trees, not Git author fields. A
project-specific controller may create the same ref, but it gains no authority
to update it or merge to `master`. The older staging-PR route is an optional
strict project profile, not the generic default; see ADR 0005.

## Handle an emergency hotfix

Prefer a fix based on `develop` followed by the release-shim workflow, even
when the fix is urgent. Reserve `hotfix/*` for an incident where `develop` has
diverged too far to ship safely.

A true hotfix is cut from sanitised `master` and therefore has no `.agents/`,
`.claude/`, `CLAUDE.md`, `agent-precommit`, or `agent-commit`. Changes MUST
arrive on the protected hotfix branch through a reviewed PR from an
unprotected working branch. Run every standalone profile check that is
available and require hosted profile validation and `master-merge-gate`.
Where the absent wrappers make ordinary Git unavoidable, record that reduced
local validation explicitly; do not claim the wrappers ran.

The master PR body MUST contain exactly one non-empty
`Hotfix-Validation-Tradeoff: <checks run and omissions>` field, which the gate
enforces as a hard failure. After the hotfix reaches `master`, its functional
change MUST return to `develop` through a normal reviewed merge or cherry-pick
PR, never by rebase. Preserve all development-stage tooling; prefer
cherry-picking the functional commit if merging the sanitised branch would
carry deletions.

## Default automatic promotion

A release branch is a reviewed buffer between `develop` and `master`, not the
default production trigger. Unless a durable, reviewed project-specific release
policy explicitly says otherwise, automatic deployment and release occur only
when `master` is updated and promote the immutable artefact for that exact
`master` SHA. Require a protected `push` to `master`, preserve the source SHA in
release evidence, and keep manual deployment, release, and rollback as explicit
operator actions.

## Finish with hosted configuration

Configure the repository host separately to require pull requests and block
direct updates to `master`, `release/*`, and `hotfix/*`. Keep force updates and
deletions blocked everywhere. To permit the bounded direct bump, give only an
explicit maintainer or narrowly scoped automation identity a `develop`
direct-push bypass; hosts generally cannot restrict that bypass to a manifest
shape, so require the metadata guard, monitor every bypass push, and retain the
ordinary PR fallback where the risk is unacceptable. Require the applicable
independent review or documented single-maintainer owner attestation, dismiss
stale approvals where applicable, and require both `master-merge-gate` and
profile validation for every master-bound PR (`master-merge-policy.md` section
9.1 governs how the validation status may be satisfied on an identity-proved
release PR). Protect release refs against force updates, deletion, and
recycling; bind master checks and approvals to the current PR head. Report
verified; do not claim a workflow file alone protects refs.
