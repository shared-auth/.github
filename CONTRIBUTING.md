# Contributing

Thank you for contributing to shared-auth.

## Before starting

1. Read [`AGENTS.md`](AGENTS.md), [`CODE_OF_CONDUCT.md`](CODE_OF_CONDUCT.md), and [`SECURITY.md`](SECURITY.md).
2. Find or create the relevant work item in the [shared-auth Linear project](https://linear.app/denman/project/githubcomshared-auth-acbca07bb390).
3. Confirm the affected repositories, identity/session contracts, providers, schemas, generated artifacts, infrastructure, tenant boundaries, supported clients, and deployment boundaries.

## Non-destructive workflow

Leave unrelated and uncommitted work untouched. Agents and automated contributors must not use `git stash`, `git reset`, `git clean`, `git filter-repo`, history rewrites, force pushes, recursive deletion, destructive database or infrastructure commands, credential/session invalidation, or equivalent operations. Use additive branches, clean worktrees or clones, explicit staging, normal pushes, dry runs, and reversible roll-forward changes.

Never revoke live credentials, invalidate production sessions, rotate keys, delete users, or rewrite authorization data to simplify development or testing. Use synthetic identities, isolated tenants, and test providers.

## Conflicts

Resolve every conflict semantically. Read both sides and the surrounding subsystem; inspect 3–10 relevant prior commits when useful; review related organization and external repositories when contracts cross boundaries; preserve compatible intent; run relevant validation; and explain tradeoffs in the pull request.

## Pull requests

Keep each pull request coherent and reviewable. Include:

- the linked Linear issue or project;
- the problem and intended outcome;
- important implementation and architecture choices;
- compatibility, migration, security, privacy, tenant-isolation, provider, session, and operational risks;
- tests, contract checks, threat-model checks, and end-to-end validation performed;
- conflict-resolution details, when applicable.

Never commit tokens, cookies, OTP material, recovery codes, biometric data, secrets, production data, personal data, generated credentials, or local environment files.

## AI-assisted pull-request promotion

This policy applies to AI agents and AI-assisted automation. Repository-specific rules may be stricter and take precedence.

An AI agent may merge only when all of the following are true:

1. All required status checks and all relevant tests pass on the exact commit to be merged.
2. The source branch is current with its target, and there are no merge conflicts.
3. There are no unresolved review threads, requested changes, missing required approvals, or known security, privacy, compliance, or data-integrity blockers.
4. The change matches the approved issue and pull-request scope, and compatibility, migration, observability, and rollback implications are understood.
5. The AI records an exact confidence percentage and a concise evidence-based rationale in the pull request.

Confidence is an additional gate, not a substitute for tests, reviews, approvals, or branch protection. Never bypass protections, force-merge, dismiss valid reviews, or represent a skipped, cancelled, neutral, stale, or failing check as passing.

### Feature branch to `dev`

When every gate above passes and the AI's calibrated confidence that the feature is correct, complete, and safe is **strictly greater than 99.1%**, retarget the pull request if necessary and merge it into `dev`, the integration branch.

If confidence is 99.1% or lower, cannot be calibrated, or depends on an unresolved assumption, leave the pull request open and request human review. If the repository has no `dev` branch, do not invent a substitute or merge to production; establish `dev` or follow a stricter repository-specific integration-branch policy first.

### `dev` to `main` or `master`

When every gate above passes for the exact `dev` head commit, all release-level tests pass, and the AI's calibrated confidence that the integrated result is production-ready is **strictly greater than 99.7%**, open or update the promotion pull request and merge `dev` into the repository's production branch: `main` when that is the production branch, otherwise `master`.

If confidence is 99.7% or lower, leave the promotion pull request open and request human review. Do not merge a feature branch directly into `main` or `master` under this confidence policy.

### Confidence discipline

The confidence assessment must account for test relevance and coverage, review findings, security and privacy risk, backward compatibility, data migrations, deployment behavior, observability, and rollback readiness. Do not round up to cross a threshold. Any material unknown or unverifiable assumption keeps confidence below the applicable threshold.

### Merge record

Use the repository's permitted merge method. Re-evaluate all gates whenever the head SHA changes. In the pull request, record the source and target branches, tested SHA, check results, confidence percentage, and rationale before merging.

<!-- ore-org-baseline:begin -->
Thank you for contributing to repositories owned by [`shared-auth`](https://github.com/shared-auth). Repository-local instructions take precedence when they are stricter.

## Before proposing a change

1. Read the repository README, contribution notes, lowercase `agents.md`, architecture documentation, linked issues, and relevant [Linear project](https://linear.app/denman/project/githubcomshared-auth-acbca07bb390).
2. Confirm the authoritative source repository and whether files are generated, vendored, mirrored, or owned by another repository.
3. Fetch current remote state and preserve concurrent work. Avoid git rebase in favor of git merge.
4. Do not use `git stash`, `git reset`, `git clean`, `git filter-repo`, force-push, destructive worktree/submodule operations, or broad deletion/rewrite commands without exact authorization.
5. Never include secrets, credentials, customer data, legal records, or other private information in issues, commits, test fixtures, screenshots, or logs.

## Pull requests

Use a focused feature branch and a draft pull request. Link the relevant issue or Linear work; explain behavior, risk, security impact, migration and rollback considerations, tests, and cross-repository dependencies. Resolve conflicts semantically with full context—normally including the merge base and 3–10 relevant commits—rather than selecting one side wholesale. Run all affected checks and scan the complete worktree for conflict markers.

External GitHub Actions must be pinned to full commit SHAs. Workflows must use explicit least-privilege permissions, explicit timeouts, and non-persisted checkout credentials.
<!-- ore-org-baseline:end -->
## Work tracking

Every discovered feature, fix, enhancement, bug, vulnerability, reliability concern, documentation gap, or technical-debt item must have a Linear issue in the canonical project before implementation starts. Search first, link the existing issue when possible, and create one only when necessary. Pull requests must include the Linear identifier or canonical Linear URL and keep acceptance criteria and validation evidence synchronized. Stop rather than guess when project routing is missing or ambiguous.

## Safe change control

**avoid git rebase in favor of git merge**

Preserve uncommitted and untracked work. Inspect the worktree before mutation and publishing. Do not use destructive Git commands, including `git rebase`, `git stash`, `git reset`, `git clean`, `git filter-repo`, `git checkout --`, `git restore`, `git branch -D`, `git reflog expire`, `git gc --prune`, `git push --force`, or `git push -f`. Do not use destructive filesystem commands, including `rm`, `mv`, `sed`, `find -delete`, `xargs rm`, `truncate`, `shred`, or `dd`. Never force-push, bypass required checks, or discard unfamiliar work. Stop and report unexpected changes or ambiguous ownership.

## Mandatory semantic conflict resolution

Resolve every Git conflict semantically and with full context. Conflict markers are the starting point for analysis, not the complete context.

Before finalizing a resolution:

1. Inspect the merge base, both sides of the conflict, surrounding code or documentation, tests, schemas, migrations, and contracts.
2. When history is available, inspect at least 3 and up to 10 relevant commits from both sides. Use path-scoped `git log`, `git show`, and `git blame` where useful.
3. Review related repositories in this GitHub organization and relevant repositories in external organizations whenever APIs, shared libraries, generated artifacts, infrastructure, deployments, or documentation cross repository boundaries.
4. Never accept `ours`, `theirs`, current, or incoming wholesale merely to clear the conflict. Preserve compatible intent and produce a conceptual merge.
5. Scan the complete worktree for unresolved conflict markers. Run all affected tests, formatters, linters, builds, integrity checks, contract checks, security checks, and end-to-end validation.
6. Document non-obvious choices, incompatible requirements, discarded intent, and operational tradeoffs in the commit, pull-request description, and Linear issue.

Full context means all relevant context the contributor is authorized to access. It never authorizes disclosure of credentials, private data, or customer information.

Repository-local instructions may add stricter requirements but must not weaken this policy.
