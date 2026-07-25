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

For a PR/MR targeting `master`, the diff MUST NOT add, modify, delete, or
rename into or out of any of these paths:

- `.ai/`
- `.agents/`
- `.claude/`
- `.codex/`
- `agent_roadmaps/`
- `AGENTS.md`
- `CLAUDE.md`
- `CODEX.md`
- `docs/`, except `docs/changelog/`

The policy applies to both the current and previous name of a renamed file.
It is deliberately diff-based: a repository may have inherited development
assets in its historical `master` tree, but no master-bound PR/MR may carry a
change to one of these paths.

## 3. Release-shim workflow

Direct `develop` to `master` PRs/MRs are allowed by the source rule, but a
release branch is the strongly preferred buffer:

1. Select and record an immutable reviewed commit SHA on `develop`.
2. Create `release/<name>` from that exact commit; do not force-update it.
3. Run the profile-authoritative validation and the master merge gate.
4. Open a same-repository `release/<name>` to `master` PR/MR with the source
   SHA, validation evidence, and release notes.
5. Merge only after required checks and independent approval pass.

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
full paginated changed-file list.

For GitHub, use the checked-in `pull_request_target` workflow only to fetch and
run the trusted `master` policy; it MUST NOT check out or execute pull-request
code, receive production secrets, or have write permissions. Configure hosted
branch rules/rulesets to require a PR, independent approval, the required
checks, and protected workflow ownership. Repository files cannot configure or
verify those hosted controls on their own.

Read `.agents/skills/branch-governance/SKILL.md` before changing this policy,
the workflow, hosted branch rules, or release-shim automation.
