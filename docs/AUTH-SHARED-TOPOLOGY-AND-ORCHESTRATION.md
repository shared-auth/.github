# Shared Auth topology and orchestration contract

Status: accepted organization policy  
Decision date: 2026-09-14  
Tracking: DEN-2193

## Decision

Shared Auth uses a three-layer configuration model rather than making one file own unrelated concerns:

1. organization architecture defines canonical identity and authorization ownership;
2. `.auth-shared.toml` is the secret-free fleet/provider/application topology contract;
3. each runtime keeps an executable realm contract plus environment/secret-manager delivery for exact deployment values.

The first executable exemplar is `shared-auth/shared-auth-server.rs/.auth-shared.toml`, paired with `config/auth-realms.contract.json`, `.cli-flags.toml`, `src/realm.rs`, and the repository `Procfile`.

`.auth-shared.toml` must never become a second secret store or an independent runtime authority that can silently disagree with the server's executable startup contract.

## Identity ownership

The canonical identity is the opaque `shared_user_id` owned by `shared_auth.principals`. Provider-native authentication stores remain authentication evidence stores:

```text
Supabase auth.*         ─┐
                        ├─ exact (provider, issuer, subject, realm) binding
Neon Auth neon_auth.*  ─┘
                                  ↓
                       shared_auth.principals
                                  ↓
                    optional root-admin grant
                                  ↓
                 application enrollment only
```

Never merge principals because email, phone, display name, username, or another mutable attribute matches. Product membership, tenant/resource roles, entitlements, billing grants, and product RLS stay in the product database.

## Provider rules

### Supabase

Supabase owns its users, identities, sessions, credentials, refresh state, MFA state, and provider-local subjects. Shared Auth pins the accepted project/issuer/audience and binds the validated provider subject to the canonical principal. Provider `session_id` is provider-session evidence; it is not the Shared Auth canonical session id.

### Neon Auth

Current Neon Auth is managed Better Auth with users, sessions, organization/configuration state, and JWKS stored in the branch-local `neon_auth` schema. Each Neon branch has an isolated Auth endpoint, so branch/endpoint identity is part of the trust boundary.

Shared Auth must treat `neon_auth.*` as provider-owned. A cloned preview branch must not be accepted as the production authority merely because its rows originated from production. The exact validated provider authority and subject bind to `shared_user_id`; email equality never performs the binding.

## Realm isolation

`admin` and `customer` are independent authorities even though they run the same codebase. They require distinct:

- issuers and audiences;
- databases and database secret references;
- signing keys and key references;
- cookie namespaces;
- provider registries/credentials;
- session and revocation state;
- privileged policy and audit state.

A customer credential must not validate as an admin credential, and an admin credential must not become an application credential.

## Canonical tables

The cross-provider schema owns these semantic entities:

- `shared_auth.principals`
- `shared_auth.provider_identities`
- `shared_auth.root_admin_grants`
- `shared_auth.sessions`
- `shared_auth.provider_sessions`
- `shared_auth.applications`
- `shared_auth.application_accounts`
- `shared_auth.oauth_clients`
- `shared_auth.provider_oauth_clients`
- `shared_auth.revocation_outbox`
- `shared_auth.audit_events`

Provider-native tables are not duplicated into parallel writable canonical user/session tables.

## Initial application topology

The first explicit child entries in the server exemplar are:

- `zed-pkg`
- `sonus-auris`
- `fiducia-cloud`

The TOML records only non-secret hostnames and environment-variable names for project IDs, Auth endpoints, and audiences. Provider credentials, database URLs, private keys, tokens, and secret values are forbidden.

Additional organizations should follow the same model with explicit application keys and provider authority references. Enrollment in Shared Auth does not centralize product authorization.

## Local Overmind profile

The server repository's `Procfile` runs two local processes from the same binary:

```text
customer -> 127.0.0.1:8120
admin    -> 127.0.0.1:8121
```

Local development requires two distinct signing-key files. The wrappers map realm-specific local inputs into the server's existing environment/flags contract; they do not add secret-bearing CLI flags.

The DB-less Overmind profile is development-only. Production uses the exact runtime realm contract and protected secret delivery.

## Fleet enforcement

`ores-cli` should eventually validate `.auth-shared.toml` across participating repositories. That check should verify at least:

- TOML syntax and schema version;
- no committed secret values;
- canonical provider binding key `(provider, issuer, subject, realm)`;
- no email/phone/username identity merge policy;
- exact admin/customer realm separation;
- declared application/provider topology agrees with the runtime contract;
- application authorization ownership remains product-local;
- provider revocation is represented as durable canonical work rather than best-effort synchronous cleanup.

The linter should compare authorities, not regenerate one authority from another merely to force textual parity.

## References

- `CANONICAL-IDENTITY-DATABASE-AND-RLS-MODEL.md`
- `FEDERATED-DUAL-PROOF-ARCHITECTURE.md`
- `shared-auth/shared-auth-server.rs/.auth-shared.toml`
- `shared-auth/shared-auth-server.rs/docs/runtime-realm-contract.md`
- `shared-auth/shared-auth-server.rs/docs/auth-shared-topology-and-local-orchestration.md`
