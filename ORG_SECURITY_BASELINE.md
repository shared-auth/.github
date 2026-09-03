# Shared Auth organization security baseline

This document is the minimum repository and evidence policy for every repository in the `shared-auth` organization. Repository-local policy may be stricter but may not weaken these controls.

## Repository settings

Every active repository must use `main` as its default branch and must:

- disable merge commits;
- allow squash and rebase merges;
- delete merged branches;
- allow maintainers to update pull-request branches;
- use read-only GitHub Actions token permissions by default;
- prohibit GitHub Actions from approving pull requests;
- enable dependency alerts and automated security updates when GitHub supports them;
- protect `main` from force-push and deletion;
- require pull-request review and resolution of review conversations before non-admin merges.

Administrators may retain an emergency bypass so a broken policy cannot permanently lock the organization. Any bypass must be documented in the pull request and linked to an incident or operational issue.

## Workflow supply chain

Third-party GitHub Actions must be pinned to a full 40-character commit SHA. Container actions must be pinned to a `sha256:` digest. Mutable tags such as `@main`, `@stable`, `@v4`, or `@v7` are prohibited.

Every workflow must declare top-level `permissions`, use `persist-credentials: false` for checkout unless a narrowly bounded write step proves why it is required, and set job timeouts. `pull_request_target`, `write-all`, and `secrets: inherit` are prohibited unless an approved security design documents the exact trust boundary.

Workflows receiving secrets must never execute unreviewed fork code. Secret-bearing steps must be isolated from checkout and other third-party actions wherever possible.

## Identity and authentication boundaries

- Authentication is not authorization. Every service must verify issuer, audience, assurance, scope, organization membership, and resource/project grants independently.
- JWT/JWKS and online introspection are production authorities only when exact issuer, audience, algorithm, expiry, revocation, and key-rotation behavior is tested.
- Platform WebAuthn may use local face or fingerprint verification. Shared Auth must not receive or retain raw biometric images, templates, embeddings, or sensor output.
- SSH authentication remains fail-closed until its exact source and live challenge ceremony are certified.
- Kerberos/SPNEGO remains contract-only until implemented and independently certified.
- OpenPGP/GPG is provenance-only and must never silently grant sessions, roles, scopes, or tokens.

## Secrets and environments

Encrypted configuration belongs in `env/enc/`; decrypted material belongs only in ignored, ephemeral `env/dec/`. Real SOPS recipients must be path-scoped and independently owned. Do not commit fabricated ciphertext, private age identities, plaintext `.env` files, service-role keys, session material, OTP seeds, recovery codes, or production data.

A credential exposed in chat, logs, issues, pull requests, commits, artifacts, screenshots, or test fixtures is compromised and must be revoked or rotated. Deleting it from the latest revision does not invalidate it.

## Evidence states

Evidence must be recorded as one of:

- `not_run` — the gate did not execute;
- `blocked` — execution was prevented before the relevant step;
- `failed` — the gate executed and failed;
- `passed` — the exact gate executed successfully against the stated source identity.

Every claim must identify repository, full source SHA, tree or artifact digest where applicable, workflow/run/job identifiers, and the tested boundary. A queued, skipped, `action_required`, billing-rejected, zero-step, preflight-only, stale-pin, or unrelated green job is not passing source evidence.

## Promotion order

1. Review source and dependency identities.
2. Produce committed dependency locks.
3. Pass formatting, static policy, tests, denied-warning linting, and release builds.
4. Pass disposable database migrations and tenant-isolation tests.
5. Pass test-organization API/browser/adversarial canaries at the exact source SHA.
6. Produce an immutable signed image with SBOM and vulnerability scan.
7. Review the GitOps change and secret/route/network boundaries.
8. Verify the deployed revision and only then activate public handoffs such as `PUBLIC_DASHBOARD_URL`.

Historical test pull requests must clearly state when their source pin is stale or their evidence is preflight-only. They must not remain presented as current release gates.
