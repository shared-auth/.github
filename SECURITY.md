# Security policy

## Reporting a vulnerability

Do not disclose vulnerabilities, exploit details, access or refresh tokens, session cookies, credentials, OTP material, recovery codes, biometric data, personal data, or production data in a public issue, discussion, pull request, commit, or Linear comment.

Use the affected repository's **Security** tab and private vulnerability-reporting flow when it is available. If private reporting is not enabled, contact the organization maintainers through a verified private channel shown on the organization or maintainer profile. Share only the minimum information needed to establish contact until a private channel is confirmed.

Include the affected repository and version, impact, prerequisites, reproducible steps, and a minimal proof of concept using synthetic identities and redacted artifacts. Maintainers should acknowledge, triage, remediate, validate, and coordinate disclosure before creating public follow-up work.

## Handling sensitive material

Never commit live credentials, tokens, cookies, OTP seeds, recovery codes, biometric templates, customer data, or production identity data. Rotate or revoke exposed credentials through an approved human-run incident procedure; automated agents must not invalidate production credentials or sessions on their own. Preserve evidence non-destructively and avoid commands that rewrite history or purge data.
