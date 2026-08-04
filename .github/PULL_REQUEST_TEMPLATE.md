## Linear

- Issue or project: <!-- Required for substantial changes; include a canonical identifier such as DEN-123 -->

## GitHub issue relationship

- Closing relationship: <!-- Required for managed changes; for example Closes #123 or Closes owner/repository#123 -->

## Delivery lane

- [ ] `integration`
- [ ] `main` / `master`
- [ ] Other branch (explain below)

## Summary

<!-- What changed, and why? -->

## Architecture, security, and compatibility

<!-- Repositories, APIs, schemas, identity/session/token contracts, providers, generated artifacts, migrations, infrastructure, tenant boundaries, supported clients, or external dependencies affected. -->

## Validation

- [ ] Relevant tests, formatting, linting, builds, contract checks, threat-model checks, and security checks passed
- [ ] Manual, provider, multi-client, or end-to-end validation is described below
- [ ] The referenced GitHub issue and Linear issue are present on the organization Project

Validation details:

## Conflict-resolution record

- [ ] No conflicts occurred, or every conflict was resolved semantically
- [ ] Both sides and surrounding code/docs/tests/contracts were reviewed
- [ ] 3–10 relevant prior commits were inspected when useful
- [ ] Related repositories in this and relevant external organizations were reviewed when behavior crossed boundaries
- [ ] Compatible intent was preserved; no wholesale `ours`/`theirs` selection was used

## Non-destructive and security checks

- [ ] No `git stash`, `git reset`, `git clean`, `git filter-repo`, force push, destructive history rewrite, recursive delete, destructive data/infra operation, credential/session invalidation, or policy bypass was used
- [ ] Unrelated work was left untouched and only intended paths were staged
- [ ] No tokens, cookies, credentials, OTP material, recovery codes, biometric data, secrets, personal data, or production data are included

## Risks and rollout

<!-- Operational risk, auth/session impact, tenant isolation, provider compatibility, migration/rollback strategy, monitoring, and follow-up work. Prefer reversible roll-forward changes. -->
