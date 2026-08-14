# Master Merge Policy

> Mandatory policy for pull requests and merge requests whose target branch is
> `master`. This is a branch-entry policy, separate from the rule that agents
> must never commit directly to protected branches.

## 1. Allowed master PR/MR sources

`master` accepts a pull request or merge request only when its source is a
branch in the **same repository** named exactly:

- `release/<name>`
- `hotfix/<name>`

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
2. Select an immutable reviewed commit SHA on `develop` and record it in the
   master PR/MR body as `Develop-Source-SHA: <full 40-character SHA>`.
3. Create the protected `release/<name>` ref at that exact commit; do not
   force-update it.
4. Create an unprotected `chore/release-<name>` staging branch from the same
   commit. Delete only the forbidden paths and make the mechanical cleanup
   commit there. Because the cleanup deliberately removes the local wrappers,
   ordinary Git is permitted only for this deletion-only staging commit after
   the source SHA has passed the full repository-owned validation.
5. Merge `chore/release-<name>` into `release/<name>` through a normal reviewed
   PR/MR. This keeps all changes to the protected release branch review-bound.
6. Run the master merge gate and full profile validation against the release
   branch.
7. Open `release/<name>` to `master` PR/MR with the source SHA, validation
   evidence, and release notes.
8. Merge only after required checks and independent approval pass.

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

An automated projection may create the release and staging branches after an
immutable `develop` source SHA is selected, but it MUST validate that SHA and
its ancestry, use narrowly scoped credentials, and create or update neither
`master` nor an existing release branch by force. The cleanup still reaches the
protected release branch through review.

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
branch rules/rulesets to require a PR, independent approval, the required
checks, and protected workflow ownership. Repository files cannot configure or
verify those hosted controls on their own.

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
