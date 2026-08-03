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
