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
| `develop` | feature/fix/docs/chore branches | normal integration |
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
   required in the hosting provider's branch rules.
3. Run profile-authoritative format, lint, static analysis, build, and test
   validation as a separate required status check.
4. Use read-only permissions for the gate. A GitHub `pull_request_target` gate
   may run only trusted base-branch policy; never check out or run PR code, use
   production secrets, or grant write permissions.
5. Protect the workflow with hosted CODEOWNERS/ruleset review. A checked-in
   workflow alone cannot stop an authorised maintainer changing it later.

## Use a release shim

`develop` is the source of truth and `master` is a derived, sanitised
publication. `develop` MUST NOT target `master` directly. For an ordinary
release, it also MUST NOT merge from or rebase onto `master`.

Promote reviewed `develop` content through a release shim:

1. Author and review every functional change through `develop`, then run the
   repository-owned validation there while the complete tooling is present.
2. Bump the authoritative version manifest on `develop` through the ordinary
   reviewed pull request. Do this before selecting a source SHA: the release
   tree is deletion-only, so a bump made later would violate that invariant.
   The manifest is `pyproject.toml` for a `python` profile and the root
   `CMakeLists.txt` for `cpp` and `hybrid`; a hybrid `pyproject.toml` MUST
   declare the identical version.
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

4. Create the protected `release/v$VERSION` ref at that SHA without
   force-updating an existing ref.
5. Create an unprotected `chore/release-v$VERSION` staging branch from the same
   SHA. Before opening the master PR, delete only the paths forbidden by the
   master merge policy and commit the cleanup on that staging branch. The
   master-merge-gate will reject any master PR whose source tree contains these
   paths:

   ```bash
   rm -rf .ai .agents .claude .codex agent_roadmaps
   rm -f AGENTS.md CLAUDE.md CODEX.md
   # Remove docs/ content except docs/changelog/
   if [ -d docs ]; then
     find docs -mindepth 1 -maxdepth 1 ! -name changelog -exec rm -rf {} +
   fi
   git add -A
   git commit -m "chore: strip development-stage assets for master"
   ```

   The source SHA MUST pass the full repository-owned validation before this
   step. Because the deletion deliberately removes the wrappers, ordinary Git
   is permitted only for this mechanical deletion-only staging commit.

6. Merge the staging branch into `release/v$VERSION` through a normal reviewed
   PR/MR. Never commit the cleanup directly on the protected release branch.
7. Run the master gate and full profile validation against the release branch.
8. Open `release/v$VERSION` to `master`, carrying source SHA, validation
   evidence, changelog, and rollback/release notes.
9. Merge only after the protected checks and the applicable approval evidence
   pass.
10. Tag the resulting `master` merge commit `release-v$VERSION` after the merge.
    The tag names one immutable commit and MUST NOT be moved or re-pointed.

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

An automated shim creator needs an identity that can create the new release
and staging branches and PRs, but cannot force-update branches or merge to
`master`. Validate the supplied SHA, its ancestry in `develop`, branch names,
and existing remote refs before any write. Preserve a deterministic
source-SHA-to-release-branch mapping so retries cannot create different
candidates.

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

Configure the repository host separately to require pull requests, block direct
and force pushes, require the applicable independent review or documented
single-maintainer owner attestation, dismiss stale approvals where applicable,
and require both `master-merge-gate` and profile validation. Report settings that
could not be verified; do not claim a workflow file alone protects `master`.
