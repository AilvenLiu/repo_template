# Master Merge Policy

> Mandatory policy for pull requests and merge requests whose target branch is
> `master`. This is a branch-entry policy, separate from the rule that agents
> must never commit directly to protected branches.

## 1. Allowed master PR/MR sources

`master` accepts a pull request or merge request only when its source is a
branch in the **same repository** named exactly:

- `develop`
- `release/<name>`
- `hotfix/<name>`

All other sources, including feature branches and fork branches, are rejected.
`develop`, `release/*`, and `hotfix/*` remain protected: their changes still
arrive through their own reviewed PR/MR workflow.

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

To pass the gate, the source branch must be sanitised — see §3 below.

## 3. Release-shim workflow with mandatory sanitisation

Direct `develop` to `master` PRs/MRs are allowed by the source rule, but are
*practically* blocked by the tree check because `develop` always carries
agent tooling (`.agents/`, `.claude/`, etc.). Only `release/*` and `hotfix/*`
can pass after sanitisation.

The required release-shim workflow:

1. Select and record an immutable reviewed commit SHA on `develop`.
2. Create `release/<name>` from that exact commit; do not force-update it.
3. **Strip development-stage assets:** delete all forbidden paths from the
   release branch tree and commit the cleanup before opening the master PR.
   See the branch-governance skill for the exact command.
4. Run the master merge gate and full profile validation against the release
   branch.
5. Open `release/<name>` to `master` PR/MR with the source SHA, validation
   evidence, and release notes.
6. Merge only after required checks and independent approval pass.

An automated projection may create the release branch after a `develop` to
`master` request is opened, but it MUST validate the source SHA and ancestry,
use narrowly scoped credentials, and create or update neither `master` nor an
existing release branch by force.

A `release/*` branch is a review and validation buffer, not an automatic
production deployment or publication event. Unless a durable, reviewed
project-specific release policy says otherwise, auto-deployment and auto-release
occur only after `master` is updated and promote the immutable artefact for that
exact `master` SHA.

## 4. Required hard gate

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

## 5. Bootstrap: two-phase initial commit

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
