# Shared Auth security policy

## Report vulnerabilities privately

Do **not** open a public issue, discussion, pull request, commit, artifact, or public Linear comment for a suspected vulnerability, authentication bypass, exposed credential, data leak, or sensitive infrastructure weakness.

Use private vulnerability reporting from the affected repository's **Security** tab when available. Otherwise contact an organization owner through a previously verified private operational channel and request a secure reporting route. Share only the minimum information needed to establish that channel.

A useful report identifies the affected repository and full revision, impact, prerequisites, a minimal reproduction using synthetic identities and redacted artifacts, and a safe contact method. Do not access data beyond what is necessary to demonstrate the issue, disrupt production, persist access, or publish exploit details before coordinated remediation.

## Sensitive material

Never commit or publish live access or refresh tokens, session cookies, credentials, private keys, OTP seeds, recovery codes, raw biometric data or templates, customer data, production identity data, database exports, or decrypted environment files.

Treat any credential exposed in chat, logs, commits, issues, pull requests, build artifacts, screenshots, test fixtures, or public Linear content as compromised. Stop using it, revoke or rotate it through an approved human-run incident procedure, replace dependent configuration, and audit recent use. Removing a secret from the latest file does not invalidate it or erase earlier copies. Repository-history rewriting requires explicit authorization and coordinated review.

Automated agents must preserve evidence non-destructively and must not independently revoke production sessions or credentials unless a reviewed incident procedure expressly authorizes that exact action.

## Authentication-specific disclosure boundary

Do not include real provider tokens, WebAuthn assertions, SSH private keys, GPG private keys, Kerberos tickets, biometric sensor output, user directories, or production session identifiers in a report. Platform WebAuthn may perform local face or fingerprint verification; Shared Auth must never receive or retain raw face images, fingerprint images, biometric templates, or embeddings.

## Maintainer response

Maintainers should acknowledge valid reports privately, restrict access, preserve evidence, create or link a restricted Linear security issue, assess affected versions and blast radius, coordinate remediation and exact-source validation, rotate exposed material, and publish a GitHub security advisory or coordinated disclosure when appropriate.

Supported versions and response targets are repository-specific. Repository-local policies may add stricter requirements but may not weaken confidentiality, evidence handling, authentication boundaries, or coordinated disclosure.

See [`ORG_SECURITY_BASELINE.md`](ORG_SECURITY_BASELINE.md) for repository, workflow, evidence, secret, and promotion controls.
