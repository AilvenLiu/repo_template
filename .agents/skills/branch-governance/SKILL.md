---
name: branch-governance
description: Design, implement, review, or troubleshoot protected branch policies, master-bound pull-request or merge-request gates, GitHub branch rules, changed-path deny lists, and release-shim branches. Use when changing master/develop/release/hotfix flow, GitHub Actions PR policy, required checks, or release promotion entry rules.
---

# Branch Governance

Use this skill with `service-cicd` when the branch policy affects CI, release,
or deployment channels. Read the branch, master-gate, and GitHub Actions
constraints before editing policy or workflow files.

## Establish the branch contract

| Target | Allowed source | Required purpose |
|---|---|---|
| `develop` | feature/fix/docs/chore branches | normal integration |
| `master` | same-repository `develop`, `release/*`, `hotfix/*` | reviewed production entry |

For every target, state whether direct pushes are denied, which approvals are
independent, which status checks are required, and which file paths cannot
cross the boundary. Treat the source branch name and changed paths as untrusted
event data until the gate validates them.

## Implement the master hard gate

1. Keep the deterministic policy in `master_merge_gate.py` and add tests for
   every allowed source, forbidden path, changelog exception, and rename case.
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

When a `develop` to `master` PR/MR is requested, strongly prefer a release shim:

1. Validate and record the immutable reviewed `develop` SHA.
2. Create `release/<name>` from that SHA without force-updating an existing ref.
3. **Strip development-stage assets:** before opening the master PR, delete all
   paths forbidden by the master merge policy from the release branch tree and
   commit the cleanup. The master-merge-gate will reject any PR whose source
   tree contains these paths:

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

4. Run the master gate and full profile validation against the release branch.
5. Open `release/<name>` to `master`, carrying source SHA, validation evidence,
   changelog, and rollback/release notes.
6. Merge only after the protected checks and independent approval pass.

An automated shim creator needs an identity that can create a new release
branch and PR, but cannot force-update branches or merge to `master`. Validate
the supplied SHA, its ancestry in `develop`, branch name, and existing remote
ref before any write. Preserve a deterministic source-SHA-to-release-branch
mapping so retries cannot create different candidates.

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
and force pushes, require independent review, dismiss stale approvals, and
require both `master-merge-gate` and profile validation. Report settings that
could not be verified; do not claim a workflow file alone protects `master`.
