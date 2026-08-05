# Security policy

## Reporting a vulnerability

Do not disclose vulnerabilities, exploit details, access or refresh tokens, session cookies, credentials, OTP material, recovery codes, biometric data, personal data, or production data in a public issue, discussion, pull request, commit, or Linear comment.

Use the affected repository's **Security** tab and private vulnerability-reporting flow when it is available. If private reporting is not enabled, contact the organization maintainers through a verified private channel shown on the organization or maintainer profile. Share only the minimum information needed to establish contact until a private channel is confirmed.

Include the affected repository and version, impact, prerequisites, reproducible steps, and a minimal proof of concept using synthetic identities and redacted artifacts. Maintainers should acknowledge, triage, remediate, validate, and coordinate disclosure before creating public follow-up work.

## Handling sensitive material

Never commit live credentials, tokens, cookies, OTP seeds, recovery codes, biometric templates, customer data, or production identity data. Rotate or revoke exposed credentials through an approved human-run incident procedure; automated agents must not invalidate production credentials or sessions on their own. Preserve evidence non-destructively and avoid commands that rewrite history or purge data.

<!-- ore-org-baseline:begin -->
## Reporting a vulnerability

Do **not** open a public issue for a suspected vulnerability, exposed credential, authentication bypass, data leak, or sensitive infrastructure weakness.

Use private vulnerability reporting from the **Security** tab of the affected repository when available. Otherwise contact the organization owners through an established private operational channel and identify the affected repository, impact, reproduction conditions, and a safe contact method. Provide only the minimum evidence needed; do not include live credentials, private keys, customer data, or destructive proof-of-concept payloads.

## Handling exposed credentials

Treat any credential pasted into chat, logs, commits, issues, pull requests, build artifacts, screenshots, or test fixtures as compromised. Stop using it, revoke or rotate it, replace dependent configuration, and audit recent use. Removing a secret from the latest file does not invalidate it or erase earlier copies. Repository-history rewriting requires exact authorization and coordinated review.

## Supported versions and response expectations

Each repository documents its own supported versions. No service-level response commitment is implied by this fallback policy. Maintainers should acknowledge valid reports privately, limit access, preserve evidence, coordinate remediation, test the fix, rotate affected secrets, and disclose responsibly when appropriate.

Linear planning context: [github.com/shared-auth](https://linear.app/denman/project/githubcomshared-auth-acbca07bb390).
<!-- ore-org-baseline:end -->
