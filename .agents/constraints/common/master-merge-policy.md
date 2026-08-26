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
source would authorise a PR that cannot succeed. A `release/*` ref is an
immutable, create-once candidate: the repository-owned release command creates
it directly at its final sanitised commit, and no actor may later update,
force-update, delete, or recycle it. A `hotfix/*` branch remains protected and
review-bound as described in section 5.

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
2. Fetch `origin` immediately before promotion so the remote-tracking develop
   and master refs are fresh; neither release command fetches or pushes.
   Ensure the authoritative version manifest on `develop` carries the release
   version before selecting a source SHA. Prefer bumping it in the same reviewed
   pull request as the change it describes. If an already-reviewed release train
   still needs only its version selected, section 8.4 permits the bounded
   `.agents/bin/agent-release bump <x.y.z>` exception: it changes and commits
   only the authoritative version fields on `develop`, without a full build.
3. Select an immutable reviewed commit SHA on `develop` and record it in the
   master PR/MR body as `Develop-Source-SHA: <full 40-character SHA>`. Read the
   version `<x.y.z>` from the authoritative manifest at that exact commit; every
   name below is derived from it.
4. Run `.agents/bin/agent-release prepare`. It builds the deletion-only
   projection through a temporary Git index, creates
   `release/v<x.y.z>` once at the final sanitised commit, and leaves the
   worktree and checked-out `develop` branch untouched. Do not hand-build the
   projection, switch branches, or stash unrelated work.
5. Push the candidate with the printed exact commit-to-ref mapping and without
   force. Hosted protection MUST allow creation of the absent release ref but
   reject every later update or deletion; a plain Git push alone does not
   provide that server-side guarantee. Open the sole ordinary-release PR/MR,
   `release/v<x.y.z>` to `master`, and include the printed source-SHA fields,
   validation evidence, and release notes.
6. Merge only after the master gate, profile validation or accepted provenance,
   and the applicable approval evidence pass. Tag the resulting `master`
   commit automatically after every required deployment gate succeeds; see
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

The projection MUST be produced by
`.agents/bin/agent-release prepare` or by project-specific automation that
implements the same contract. A person or interactive agent MAY invoke that
command, but MUST NOT reproduce its deletions by hand. The command validates
the recorded SHA and version, builds the projected tree through an isolated
temporary index, makes the source SHA the projection commit's only parent, and
creates the version-derived release ref only if it does not already exist.

The release ref is born at its final candidate commit. It MUST NOT first point
at the unsanitised source, accept a later cleanup commit, or receive any other
update. A retry accepts an existing ref only after independently proving its
parent and projected tree; a divergent ref is a hard failure. No route may
force-update, delete, or recycle it. This create-once contract removes the
staging branch without weakening the byte-for-byte projection proof.

The `release/v<x.y.z>` to `master` PR/MR is the single review boundary for
an ordinary promotion. Hosted protection MUST bind approval and required checks
to the current candidate head so that any attempted ref replacement invalidates
the evidence. The release namespace has no deployment, publication, secret, or
package-publishing authority.

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
status. Both statuses stay required for every master-bound PR/MR; section 9.1
governs only how an identity-proved release PR may satisfy the validation
status. The gate validates the source branch, same-repository ownership,
recorded ancestry, complete recursive trees, release version, create-once
projection shape, and any claimed version-only parent provenance. No PR targets
`release/*` in the ordinary workflow.

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
never be made on the release branch without violating that invariant.

The bump MUST therefore land on `develop` before a source SHA is selected.
Bumping in the same reviewed pull request as the change it describes remains
preferred. For an already-reviewed release train, the sole direct-commit
exception on protected `develop` is
`.agents/bin/agent-release bump <x.y.z>`. It requires a clean, current
`develop`, advances strict semantic versions, changes exactly the authoritative
manifest field and required hybrid mirror, verifies that normalising those
fields makes parent and child manifests byte-identical, and commits only those
paths. It performs no build and MUST be pushed without force.

The master PR body then records both
`Develop-Source-SHA: <version-only-child>` and
`Release-Metadata-Parent-SHA: <fully-validated-parent>`. The gate accepts
validation provenance from that parent only after independently proving the
child has exactly one parent and changes no byte outside the canonical version
fields. If the field is omitted, malformed, or the proof fails, parent
provenance satisfies nothing and the source SHA needs its own full validation
or the master PR must rebuild. Selecting an already-released version remains a
hard failure.

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
the merge, and after every required promotion and deployment gate for that exact
`master` SHA has succeeded. Never tag a release or hotfix branch before it
reaches `master`, and never tag a `master` commit whose required deployment has
not yet succeeded. The tag names one immutable promoted commit, so it MUST NOT be
moved, deleted, or re-pointed.

A repository with no deployment gate tags once the merge and its required checks
succeed. A repository whose promotion includes a deployment gate treats a
successful deployment of that exact SHA as a precondition of the tag, so the tag
records what actually shipped rather than what was expected to ship.

An operational deployment identifier such as `master-<timestamp>-<short-sha>` or
`release-<timestamp>-<short-sha>` is a host, artefact, retention, and rollback
join key. It is not a semantic version and MUST NOT be created as, or substituted
for, a `release-v<major>.<minor>.<patch>` Git tag. Where both exist, the
operational identifier records a deployment attempt and the semantic tag records
a completed release; a repository that conflates them loses the ability to state
which commits actually reached production. Existing operational tags are
historical evidence only and do not authorise a semantic release.

The tag MUST be created by automation, and MUST NOT be created by a person.
Manual tagging fails in a particular way: it is a separate action taken after the
merge has already succeeded, so the merge -- the step everyone is watching --
reports success whether or not the tag follows. Forgetting it leaves `master` in
a state the rest of this section treats as impossible, and nothing reports the
omission.

Automation that creates the tag MUST derive `<x.y.z>` from the authoritative
manifest at the exact resulting `master` merge commit rather than from a branch,
PR name, or workflow input, reject a version that is not strictly greater than
the preceding eligible `master` release, be idempotent so that a re-run neither
fails nor re-points an existing tag, and hold only the credential needed to
create a tag. An existing tag at the exact expected `master` SHA is success; an
existing tag at any other SHA is a hard failure rather than a silent overwrite.
The tag write MUST use a create-only operation and MUST expose no force-update,
move, or deletion path. That idempotent success holds only while the event SHA
remains the remote `master` tip and every policy-designated promotion ref retains
its reviewed identity; a stale event MUST fail closed rather than replay an
obsolete promotion.

The version contract MAY still be checked before the deployment gate, and
checking it early is preferred: a promotion whose version was never bumped is a
policy violation worth catching in seconds rather than after a long build. Only
the tag *write* waits for the deployment gate.

Tag presence MUST be verified independently of tag creation, from a fresh
read-only context that does not consume the publisher's outputs. Verification
MUST re-derive every governed eligible `master` commit, its manifest version, the
expected tag name, and the expected target, and MUST fail when a governed tag is
absent, moved, or mismatched. The verifier receives no production credential and
no write token, so it remains available to a repository that has no tagging
automation at all. It is what makes the mandate above enforceable rather than
aspirational: creation can be skipped silently, whereas a failing check cannot.

Because verification necessarily follows the merge and the deployment it depends
on, it cannot be a pre-merge required check for that same promotion. A project
MUST therefore treat it as a mandatory post-merge result and block or alert on
any later promotion until it succeeds.

A project MAY additionally reconcile missing historical semantic tags. If it
does, the recovery policy MUST already be reviewed into `master`; MUST fix the
repository identity and the historical promotion evidence, including the exact
successful deployment workflow and job; MUST record known evidence limitations
rather than asserting evidence that does not exist; and MUST accept no
user-supplied ref, tag, or SHA. Discovery MUST prove the `master` first-parent
history, the promoted branch identity, the manifest version, the source
relationship, and the required deployment evidence before any candidate is
eligible. Reconciliation then proceeds in ascending numeric release order using
the same create-only operations, and revalidates the current remote `master` and
every policy-designated promotion ref immediately before each write so that a
stale rerun or a changed branch identity fails closed.

A hotfix follows the same rules: it bumps the patch component on its own branch,
carries a `hotfix/v<x.y.z>` name, and is tagged `release-v<x.y.z>` on `master`.
Its back-merge to `develop` carries the version bump with the functional fix.

## 9. Promotion efficiency

The release-shim workflow is a defence-in-depth pipeline, and its integrity
guarantees are exactly what make most of its repeated validation redundant.
This section removes the redundancy without weakening any invariant. Every
provision below changes which evidence satisfies a requirement or when a cost
is paid; none removes a requirement.

### 9.1 Validation provenance

The deletion-only invariant is what makes revalidation redundant. Once the
master merge gate has proved that a release tree equals the recorded
`Develop-Source-SHA` tree minus deletions of the section 2 paths, comparing
leaf entries by object SHA, the functional content under validation is
byte-identical to content that the authoritative profile validation already
passed at that SHA. Rebuilding it proves nothing new.

Every section 2 path is agent tooling or documentation and MUST remain
build-irrelevant: no build, test, or packaging input may live under a forbidden
path. This is what keeps the substitution sound, and a project that violates it
has a defect independent of this section, because its shipped `master` tree
could not build either.

For a `release/*` to `master` PR/MR, the full profile validation requirement
MAY therefore be satisfied by validation provenance instead of a rebuild:
machine-verified evidence that the authoritative profile validation succeeded
at the recorded develop source SHA, bound to that exact SHA, together with the
gate's tree-identity proof. The substitution is valid ONLY where an automated
check verifies that evidence; the shipped gate does so through
`REQUIRED_SOURCE_CHECKS`, and the GitHub shape lives in
`common/github-actions-cicd.md`. Where no machine-checked verification exists,
the rebuild REMAINS required. Asserted evidence, such as a PR-body claim that
validation passed, satisfies nothing. A rebuild is the always-sound fallback
and a project MAY keep it.

A source commit created by the section 8.4 version-only exception MAY instead
inherit those workflow runs from the exact
`Release-Metadata-Parent-SHA`. The gate first proves that the source has that
commit as its only parent, that complete parent and source trees differ only in
the required manifests, that normalising exactly one authoritative version
field in each changed manifest makes their contents byte-identical, that
hybrid mirrors agree, and that the version increases. Only then does it verify
`REQUIRED_SOURCE_CHECKS` at the parent SHA. A path allow-list or commit-message
claim alone is never sufficient.

The hosted validation status itself stays required for every master-bound
PR/MR, exactly as section 6 demands. Substitution changes how an
identity-proved release PR satisfies that status: the workflow that reports it
MAY verify the provenance and report success without rebuilding. It never
removes the status from the branch rules. This is also what keeps the hotfix
requirement intact, because the same status stays required for a `hotfix/*`
PR/MR and MUST be satisfied there by the full available validation.

Provenance substitution NEVER applies to a `hotfix/*` PR/MR. A hotfix tree is
not identity-proved against any validated SHA, so it keeps the full available
validation requirement of section 5. Except for a gate-proved version-only
child, provenance presupposes that authoritative validation produced evidence
at the develop merge commit itself: run it on updates of `develop`, not only
on pull requests. A version-only push may run only its bounded metadata check;
its parent retains the full workflow evidence.

### 9.2 Required validation per promotion step

The single paid validation of any functional content is the one that runs where
that content is authored:

- Feature/fix to `develop`: the authoritative full profile validation. This is
  the validation every later step inherits.
- Version-only direct update on `develop`: the bounded metadata proof only.
  Its parent must carry authoritative validation before that provenance can be
  inherited.
- `release/v<x.y.z>` to `master`: the master merge gate, plus either validation
  provenance (section 9.1) or a full rebuild. This is the sole normal release
  PR.
- `hotfix/v<x.y.z>` to `master`: the master merge gate plus the full available
  validation. No substitution.

### 9.3 Release cadence

The promotion pipeline is priced per release, not per change, so its cost
amortises across everything a release carries. Default to release trains:
accumulate reviewed merges on `develop` and promote on a cadence or when the
accumulated value warrants it. Promoting every merge is a per-project choice,
not the default this policy assumes. An urgent fix either rides an immediate
single-change train, which under sections 9.1 and 9.2 costs one develop PR
round plus gate checks, or uses the section 5 hotfix path when `develop` has
diverged too far.

### 9.4 Pre-flight rehearsal

Before creating any release ref, rehearse the promotion locally and fix
findings there: derive the version and every release name from the
authoritative manifest at the candidate SHA, verify strict format and
monotonicity against `master`, and simulate the deletion-only projection,
reporting exactly what it will remove. The shipped gate provides a read-only,
network-free `--rehearse` mode for exactly this. The rehearsal fails closed:
an unresolvable `master` baseline is a failure, not a silent pass, and a
first-release bootstrap must be declared explicitly. A rehearsal failure costs
seconds; the same failure discovered on the master PR costs the whole
promotion cycle.

### 9.5 Single-PR deterministic projection

The direct deterministic projection of section 4 is the default. It removes
review of a mechanical staging commit whose complete result the master gate
independently re-derives byte-for-byte. Safety comes from the properties below,
not from trusting a local Git author:

1. The release command reads names and versions from an immutable develop SHA.
2. Its temporary index copies every source tree entry and removes only section 2
   paths; it neither checks out nor executes candidate code.
3. The resulting release commit has exactly the develop source as its parent.
4. The version-derived ref is created once at that final commit. Existing
   matching refs are verified and reused; mismatches fail without mutation.
5. The master PR is the sole ordinary-release review, and required checks bind
   to its current head.
6. Release and hotfix refs have no automatic deployment or publication
   authority.

A project MAY adopt the older staging-PR route only through a durable,
project-specific policy when organisational separation requires review of the
mechanical commit itself. That strict profile must ship and test its own route
gate; the generic workflow no longer triggers on or accepts
`chore/release-v*` to `release/v*` PRs. ADR 0005 records the default change.
