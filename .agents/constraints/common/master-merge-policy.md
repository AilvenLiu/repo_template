# Master Merge Policy

> Mandatory policy for pull requests and merge requests whose target branch is
> `master`. This is a branch-entry policy, separate from the rule that agents
> must never commit directly to protected branches.

## 1. Allowed master PR/MR sources

`master` accepts a pull request or merge request only when its source is a
branch in the **same repository** named exactly:

- `release/v<major>.<minor>.<patch>`
- `hotfix/v<major>.<minor>.<patch>`

Section 8 defines the version, its authoritative manifest, and the matching tag
name. A source branch whose name is not exactly one of these forms is rejected
even when its tree is otherwise clean.

All other sources, including feature branches and fork branches, are rejected.
`develop` is categorically rejected because its required development-stage
tooling can never pass the presence-based tree check. Listing it as an allowed
source would authorise a PR that cannot succeed. `release/*` and `hotfix/*`
remain protected: their changes still arrive through their own reviewed PR/MR
workflow.

## 2. Development-stage paths forbidden from master

For a PR/MR targeting `master`, the source branch's file tree MUST NOT contain
any of these paths — regardless of whether the paths were introduced in this
PR's diff or in an earlier commit:

- `.ai/`
- `.agents/`
- `.claude/`
- `.codex/`
- `agent_roadmaps/`
- `AGENTS.md`
- `CLAUDE.md`
- `CODEX.md`
- `docs/`, except `docs/changelog/`

The policy is **presence-based**: the gate enumerates every file in the source
branch tree via the Git Trees API. If a forbidden path exists anywhere in the
tree, the gate blocks. Historical master trees that already contain these
assets are unaffected; the gate only applies to future PRs.

To pass the gate, the source branch must be sanitised; see section 4 below.

## 3. One-directional branch relationship

`develop` is the source of truth. `master` is a derived, sanitised publication
of reviewed `develop` content. For an ordinary release, `develop` MUST NOT
rebase onto `master` and MUST NOT merge from `master`. Rebasing would replay
tooling-bearing commits onto a tree that deleted the tooling, create repeated
conflicts, risk deleting the toolkit from `develop`, rewrite shared protected
history, and require a forbidden force-push.

The only reverse-flow exception is a genuine `hotfix/*` cut from `master`.
After that fix reaches `master`, the functional fix MUST be back-merged into
`develop` through a normal reviewed PR, using a merge or cherry-pick and never
a rebase. The PR MUST preserve the development-stage tooling; cherry-picking
the functional hotfix commit is preferred when merging the sanitised branch
would carry unrelated deletions.

## 4. Release-shim workflow with mandatory sanitisation

The required release-shim workflow:

1. Author the functional change on a normal branch from `develop`, merge it
   into `develop` through review, and run the full repository-owned validation
   while all agent tooling is present.
2. Bump the authoritative version manifest on `develop` through the ordinary
   reviewed pull request, before selecting a source SHA. Section 8.4 explains
   why the bump can never happen later in this workflow.
3. Select an immutable reviewed commit SHA on `develop` and record it in the
   master PR/MR body as `Develop-Source-SHA: <full 40-character SHA>`. Read the
   version `<x.y.z>` from the authoritative manifest at that exact commit; every
   name below is derived from it.
4. Create the protected `release/v<x.y.z>` ref at that exact commit; do not
   force-update it.
5. Create an unprotected `chore/release-v<x.y.z>` staging branch from the same
   commit. Delete only the forbidden paths and make the mechanical cleanup
   commit there. The coding agent or other automation performs this step; a
   person MUST NOT hand-build the projection. Because the cleanup deliberately
   removes the local wrappers, ordinary Git is permitted only for this
   deletion-only staging commit after the source SHA has passed the full
   repository-owned validation.
6. Merge `chore/release-v<x.y.z>` into `release/v<x.y.z>` through a normal
   reviewed PR/MR. This keeps all changes to the protected release branch
   review-bound.
7. Run the master merge gate and full profile validation against the release
   branch.
8. Open `release/v<x.y.z>` to `master` PR/MR with the source SHA, validation
   evidence, and release notes.
9. Merge only after required checks and the applicable approval evidence pass.
10. Tag the resulting `master` merge commit `release-v<x.y.z>` after the merge.
    Automation performs this step and a separate check verifies it; see
    section 8.6.

A `release/*` tree MUST differ from its recorded `develop` source SHA only by
deletions of the forbidden paths in section 2. It MUST NOT add, modify, rename,
change the mode of, or delete any other path. This guarantees that the reviewed
and validated `develop` content is what ships, modulo mandatory removals. The
master merge gate enforces this invariant as a hard failure by validating the
recorded SHA's ancestry and comparing leaf Git tree entries by path, mode,
type, and object SHA.

The PR/MR body is the required source-SHA record because it is reviewable
metadata outside the release tree. A manifest in the release branch would be
an addition or modification and would violate the deletion-only invariant.
Merge-base is not authoritative because earlier promotions can make it resolve
to an older shared ancestor instead of the deliberately selected release SHA.
This check is a hard failure: warning-only enforcement would still permit code
that was not part of the reviewed `develop` input to reach `master`.

The projection MUST be produced by the repository's coding agent or by other
automation, and MUST NOT be produced by hand. A hand-built projection is a
policy violation even when the tree it produces is correct. The deletion set is
mechanical: it follows entirely from section 2 and from the authoritative
manifest at the recorded source SHA, so there is no judgement in it for a person
to contribute, and every manual execution is an opportunity to omit a path, skip
a step, or mistype a version.

Automation MUST validate the recorded SHA and its ancestry, use narrowly scoped
credentials, and create or update neither `master` nor an existing release
branch by force. The cleanup still reaches the protected release branch through
review.

Skipping the staging branch is the specific failure this rule exists to prevent,
and it is an observed one rather than a hypothetical. Committing the cleanup
directly onto `release/v<x.y.z>` yields a tree the master merge gate accepts,
because that gate compares the resulting tree against the recorded source SHA
and does not examine the route taken to build it. The deletion-only invariant
holds while the review the protected branch is meant to carry is silently
bypassed. Verification MUST therefore assert the route as well as the tree: on a
release branch built through this procedure, the cleanup MUST arrive as a merge
of `chore/release-v<x.y.z>` rather than as a direct commit.

A `release/*` branch is a review and validation buffer, not an automatic
production deployment or publication event. Unless a durable, reviewed
project-specific release policy says otherwise, auto-deployment and auto-release
occur only after `master` is updated and promote the immutable artefact for that
exact `master` SHA.

## 5. Emergency hotfix workflow and tooling trade-off

The normal way to ship an urgent fix is still to author it from `develop`, run
the full repository-owned tooling there, and promote it through a sanitised
`release/*` branch. A `hotfix/*` branch MAY be used only when `develop` has
diverged too far for that path to be safe during the incident.

A true hotfix starts from sanitised `master`, so `.agents/`, `.claude/`,
`CLAUDE.md`, `agent-precommit`, and `agent-commit` are absent by design. The
author MUST NOT pretend that the repository-owned local gate ran. Changes MUST
reach the protected `hotfix/*` branch through a reviewed PR from an unprotected
working branch, using ordinary Git only where the missing wrapper makes it
unavoidable. Run every standalone profile check that remains available and
require hosted profile validation plus `master-merge-gate` before merging.

The `hotfix/*` to `master` PR/MR body MUST contain exactly one non-empty
`Hotfix-Validation-Tradeoff: <checks run and omissions>` field. The master merge
gate treats a missing field as a hard failure. This makes the reduced local
validation a deliberate, reviewable emergency trade-off rather than an
accidental discovery. After merge, perform the mandatory reviewed back-merge
described in section 3.

## 6. Required hard gate

Every generated repository MUST configure the `master-merge-gate` CI status as
a required check for `master`, alongside the profile-authoritative validation
status. The gate validates source branch, same-repository ownership, and the
full recursive source-branch tree.

For GitHub, use the checked-in `pull_request_target` workflow only to fetch and
run the trusted `master` policy; it MUST NOT check out or execute pull-request
code, receive production secrets, or have write permissions. Configure hosted
branch rules/rulesets to require a PR, the applicable approval evidence, the
required checks, and protected workflow ownership. Independent approval is the
default; section 4.1 defines the narrow single-maintainer exception. Repository
files cannot configure or verify those hosted controls on their own.

### 4.1 Single-maintainer project exception

A durable project-specific release policy MAY replace independent human
approval only when the user explicitly confirms that exactly one accountable
human maintains the repository and identifies that maintainer by immutable
hosted user ID and login. This exception changes the human approval evidence
only; it does not weaken the ordinary pull request, expected-head,
required-check, immutable guard, full-tree, credential-separation, or
ref-monitoring requirements.

The single maintainer must authorise the exact candidate before merge through
one unedited hosted comment created before merge and bound to repository ID,
pull-request number, base SHA, and head SHA. The policy guard must verify the
maintainer identity, comment tuple and timestamp, successful named checks,
expected head, and merge actor. A missing, edited, post-merge, stale-head,
wrong-owner, or ambiguous attestation fails closed. Record explicitly that this
owner attestation is self-approval, not independent review and not server-side
enforcement.

Read `.agents/skills/branch-governance/SKILL.md` before changing this policy,
the workflow, hosted branch rules, or release-shim automation.

## 7. Bootstrap: two-phase initial commit

When a new project is created from the template, the initial commit uses a
two-phase strategy so that `master` is clean of agent tooling from the start:

- **Phase 1 (master):** commit only production files — no `docs/` (except
  `docs/changelog/`), no `.agents/`, `.claude/`, `.codex/`, `.ai/`,
  `agent_roadmaps/`, `AGENTS.md`, `CLAUDE.md`, or `CODEX.md`.
- **Phase 2 (develop):** commit all remaining files including agent tooling
  on the `develop` branch.

This means `master` never contains development-stage assets, even in the
initial commit. See `init.py` in the create-project skill for the
implementation.

A generated project starts at version `0.1.0` in its authoritative manifest and
promotes its first release as `release/v0.1.0`, tagged `release-v0.1.0`.

## 8. Release version identity

Every promotion to `master` carries exactly one semantic version. The version is
reviewed data inside the source tree. It is never an operator argument, a CI
input, a timestamp, or a value invented at promotion time.

### 8.1 Authoritative version manifest

Exactly one manifest is authoritative, selected by project profile:

| Profile | Authoritative manifest | Field |
|---|---|---|
| `python` | `pyproject.toml` | `[project].version`, else `[tool.poetry].version` |
| `cpp` | root `CMakeLists.txt` | `project(<name> VERSION <x.y.z>)` |
| `hybrid` | root `CMakeLists.txt` | `project(<name> VERSION <x.y.z>)` |

A hybrid project MUST also declare the identical version in `pyproject.toml`.
CMake owns the native build graph under the C++ First policy, so CMake is
authoritative and the Python packaging manifest mirrors it. Disagreement between
the two is a hard failure, not a warning, because it makes the shipped artefact
and the published package claim different versions.

### 8.2 Version format

A promoted version MUST be `<major>.<minor>.<patch>`, each a non-negative integer
without a leading zero. A promoted version MUST NOT carry a pre-release or
build-metadata suffix: `0.4.1-dev`, `1.0.0-rc1`, and `2.1.0+build7` are all
rejected. Development-stage suffixes may exist on `develop`, never on a version
promoted to `master`.

### 8.3 Required names

Derive every release name from that one version:

| Artefact | Required name |
|---|---|
| Release shim branch | `release/v<major>.<minor>.<patch>` |
| Deletion-only staging branch | `chore/release-v<major>.<minor>.<patch>` |
| Hotfix branch | `hotfix/v<major>.<minor>.<patch>` |
| Tag on the merged `master` commit | `release-v<major>.<minor>.<patch>` |

A branch name is a claim about the tree it carries. The gate MUST verify that
the version in the branch name equals the authoritative manifest version at the
recorded `Develop-Source-SHA`, so a name can never describe content it does not
carry.

Because the name is derived from the source commit rather than chosen, repeating
a promotion for the same source commit yields the same branch name. A retry is
then idempotent instead of producing a second, divergent candidate.

### 8.4 Bump before you cut

A release tree differs from its recorded `develop` source SHA only by deletions
of the section 2 forbidden paths. A version bump is a modification, so it can
never be made on the release or staging branch without violating that invariant.

The bump MUST therefore land on `develop` first, through the ordinary reviewed
pull request, before a source SHA is selected. Bump the version in the same pull
request as the change it describes, or in a dedicated reviewed pull request
immediately before promotion. Selecting a source SHA whose manifest still holds
an already-released version is a hard failure, not a warning.

### 8.5 Monotonicity

A candidate version MUST be strictly greater than the version currently on
`master`, compared component-wise as integers. This makes an accidental
re-release, a silent rollback, and a recycled branch name detectable rather than
merely discouraged.

Reusing a released version is forbidden even after deleting its branch or tag.
On a hosting plan without server-side ref protection, this monotonicity check is
the only remaining structural defence against name recycling. Record that
limitation rather than claiming the host prevents the reuse.

### 8.6 Tagging

Tag the resulting `master` merge commit `release-v<major>.<minor>.<patch>` after
the merge, never before. The tag names one immutable promoted commit, so it MUST
NOT be moved, deleted, or re-pointed. Where automatic release or deployment is
enabled, it promotes that exact tagged `master` SHA.

The tag MUST be created by automation, and MUST NOT be created by a person.
Manual tagging fails in a particular way: it is a separate action taken after the
merge has already succeeded, so the merge -- the step everyone is watching --
reports success whether or not the tag follows. Forgetting it leaves `master` in
a state the rest of this section treats as impossible, and nothing reports the
omission.

Automation that creates the tag MUST derive `<x.y.z>` from the authoritative
manifest at the recorded source commit rather than from a branch or PR name,
reject a version that is not strictly greater than the highest existing release
tag, be idempotent so that a re-run neither fails nor re-points an existing tag,
hold only the credential needed to create a tag, and run before any release or
deployment job that consumes it.

Tag presence MUST be verified independently of tag creation. A promoted `master`
head that carries no matching `release-v<x.y.z>` tag MUST fail a check.
Verification is read-only, needs no write credential, and so remains available to
a repository that has no tagging automation at all. It is what makes the mandate
above enforceable rather than aspirational: creation can be skipped silently,
whereas a failing check cannot.

A hotfix follows the same rules: it bumps the patch component on its own branch,
carries a `hotfix/v<x.y.z>` name, and is tagged `release-v<x.y.z>` on `master`.
Its back-merge to `develop` carries the version bump with the functional fix.
