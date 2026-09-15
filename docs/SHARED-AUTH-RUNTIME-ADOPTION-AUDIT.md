# Shared Auth runtime adoption audit

The runtime-adoption audit proves that the five reviewed Shared Auth executables are wired to the same policy and dependency authority. It complements, but does not replace, the broader configuration-authority scanner.

## Scope

The audited executables are:

- `shared-auth-cli`
- `shared-auth-web-server.rs`
- `shared-auth-api-server.rs`
- `shared-auth-admin-web-server.rs`
- `shared-auth-admin-api-server.rs`

For these repositories the audit requires the canonical `.shared-auth.toml`, rejects simultaneous `.auth-shared.toml`, and requires an exact compatibility commit for the reviewed `shared-auth-interfaces` policy revision. Runtime consumers do not use a compatibility range for this promotion gate.

The audit parses `Cargo.toml` with Python `tomllib`. A revision appearing only in a comment, string, unrelated package, or malformed TOML is not dependency evidence. The runtime `flags2env` dependency must point at the reviewed repository and strict revision. `shared-auth-lib-core` must likewise point at its reviewed repository and runtime-policy revision. The CLI additionally requires the same strict `flags2env` revision under `[build-dependencies]`, because its build script audits `.cli-flags.toml` before compilation.

## Authority

Machine-readable authority lives in `config/shared-auth-config-authority.json` under `runtime_adoption`. The current authority records:

- the exact `shared-auth-interfaces` policy revision;
- the reviewed `flags2env` repository and strict revision;
- the reviewed `shared-auth-lib-core` repository and revision;
- the executable fleet; and
- the CLI build-time `flags2env` requirement.

Policy semantics remain owned by `shared-auth-interfaces` and `shared-auth-lib-core`. This audit is structural evidence that each executable is attached to those authorities; it is intentionally not a third policy parser.

## States

`passed` means every readable runtime consumer satisfies the structural adoption contract.

`failed` means readable evidence contradicts the contract, such as a stale policy SHA, missing dependency, wrong Git source, wrong dependency revision, policy range, filename collision, or malformed TOML.

`blocked` means the auditor could not read required repository evidence. A blocked result is never promoted to passed and is distinct from a source failure.

## CI and organization audit

`policy-ci.yml` runs `scripts/test_audit_shared_auth_runtime_adoption.py` on ordinary policy changes. The suite contains 15 deterministic regressions, including comment-spoof and malformed-TOML cases.

`org-security-audit.yml` runs the live fleet scanner with `SHARED_AUTH_ORG_AUDIT_TOKEN` and emits `artifacts/shared-auth-runtime-adoption-audit.json`. Its output contract is Draft 2020-12 schema `config/shared-auth-runtime-adoption-audit.schema.json`.

A GitHub Actions job with no allocated runner and zero executed steps is infrastructure/admission evidence only. It is not runtime-adoption pass or fail evidence.
