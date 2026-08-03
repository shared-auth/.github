# Governance

This public `.github` repository defines the minimum organization-wide community, contribution, automation, and agent-safety defaults for **shared-auth**. Repository-local policy may be stricter, but it must not weaken this baseline.

## Decision authority

- All changes are proposed through reviewable pull requests; direct default-branch edits are reserved for a documented human-operated emergency process.
- Routine wording and template maintenance requires maintainer review and passing policy validation.
- Security, privacy, identity, workflow, governance, or reusable-automation changes require an explicit maintainer decision and review from the relevant domain owner when they affect authentication, authorization, sessions, one-time passwords, biometrics, credentials, tenant isolation, or provider integrations.
- A change that weakens semantic conflict resolution, the destructive-operation denylist, secret handling, immutable Action pinning, or required validation requires explicit organization-owner approval and a documented rationale.

## Required change record

Substantial changes must include the linked Linear work item, affected repositories and contracts, risks, compatibility or migration effects, exact validation evidence, and a statement describing any conflicts and their semantic resolution.

Canonical Linear project: https://linear.app/denman/project/githubcomshared-auth-acbca07bb390

## Automation and releases

- Workflows use least-privilege permissions, explicit timeouts, concurrency controls where appropriate, checkout without persisted credentials, and immutable full-commit Action pins.
- Reusable workflow consumers must pin a reviewed 40-character commit SHA rather than a mutable branch or tag.
- Dependency updates remain reviewable; automated updates do not bypass required checks or human review.
- Branch protections, rulesets, organization settings, secret scanning, and private vulnerability reporting must be configured in GitHub settings because files in this repository do not enable those controls automatically.

## Security and sensitive information

Report vulnerabilities privately according to `SECURITY.md`. Never place authentication material, session artifacts, recovery data, biometric material, credentials, personal data, production data, or other sensitive material in public issues, pull requests, logs, examples, or fixtures.

## Review cadence

Review this baseline after material GitHub platform changes, security incidents, organization-wide tooling changes, or at least quarterly. Track identified drift in Linear and remediate it through reviewable pull requests.
