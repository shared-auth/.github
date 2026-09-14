# Canonical identity conformance — 2026-09-14

Status: verified evidence snapshot; target migrations remain open  
Owner: Shared Auth  
Tracking: [DEN-2193](https://linear.app/denman/issue/DEN-2193/shared-auth-server-add-realm-isolation-and-federated-customer)  
Target architecture: [Canonical identity database and RLS model](CANONICAL-IDENTITY-DATABASE-AND-RLS-MODEL.md)

This snapshot records live, read-only checks against the connected Shared Auth Supabase and Neon control planes. It is evidence of observed state, not a claim that the target schema is fully implemented.

## Ten completed conformance tasks

| # | Check | Result |
| --- | --- | --- |
| 1 | Supabase Shared Auth project health | Connected `ores-shared-auth` project is active and healthy. |
| 2 | Built-in Supabase Auth ownership | `auth.users`, `auth.identities`, `auth.sessions`, refresh/MFA/OAuth tables remain provider-owned under `auth.*`. |
| 3 | Canonical schema inventory | `shared_auth.principals`, `provider_identities`, sessions, applications/accounts, OAuth clients, roles/admin grants and revocation state are present. |
| 4 | Exact provider-binding constraint inspection | Current live uniqueness is `(provider, provider_tenant, provider_subject)`; this is recorded as a migration delta from explicit issuer + subject + realm. |
| 5 | Session-model inspection | Current sessions still include one provider tuple plus a Shared Auth refresh-token hash; separate provider-session materialization remains a target migration. |
| 6 | Private-schema exposure test | `anon` and `authenticated` have no SELECT/INSERT/UPDATE/DELETE access to inspected `shared_auth.*` objects. Private-schema RLS being disabled is therefore not treated as public exposure. |
| 7 | Public compatibility-table RLS test | `public.shared_auth_federated_identities` has RLS enabled and forced, a deny-direct-access policy, and no `anon`/`authenticated` table privileges. |
| 8 | Supabase security advisor | Current security advisor returned no findings. |
| 9 | Neon topology verification | The `shared-auth` Neon organization has separate `admin`, `auth`, and `canonical` projects, matching the target logical topology. |
| 10 | Neon Auth live-catalog probe | A read-only `neon_auth.*` catalog query was attempted; the auth compute is deliberately disabled, so the check stopped rather than changing compute state merely for inspection. |

## Observed Supabase schema versus target

### Already aligned in principle

- canonical principal key is `shared_user_id UUID`;
- provider identities map provider subjects to canonical principals;
- applications, application accounts and OAuth clients are explicit tables;
- session revocation and global revocation/outbox infrastructure already exist;
- service-owned `shared_auth.*` state is not directly accessible to browser `anon` or `authenticated` roles;
- built-in Supabase Auth remains provider-owned instead of being replaced by a custom password store.

### Migration deltas still open

1. `provider_identities` uses `provider_tenant` + `provider_subject`; target semantics should make exact issuer and realm first-class and unambiguous.
2. `sessions` is not yet a provider-neutral logical session plus separate provider-session bindings.
3. the live schema has generic `roles` and scoped `directory_admin_grants`; the target root-admin capability must be defined without confusing global root privilege, directory/operator authorization, Supabase/Postgres roles, or product roles.
4. `principals` currently stores email, phone, display name and profile projections. Those may remain useful projections, but identity linkage must never depend on them and their authority/version/provenance needs to be explicit.
5. `application_accounts` still uses `(application_id, shared_user_id)` as its primary key. Existing server PR #156 already owns the stable application-account ID work, so this snapshot does not duplicate it.
6. no separate provider-OAuth-client materialization registry was observed in this live schema.
7. the connected Supabase account currently exposes one Shared Auth project rather than separately visible `admin`, `auth`, and `canonical` projects. Three-plane Supabase symmetry remains target state, not current fact.
8. dual Supabase/Neon canonical convergence and revision/idempotency evidence remains to be implemented.

## RLS and access-control interpretation

Do not mechanically require RLS on every private service table. The security invariant is that browser-facing roles cannot bypass the intended API boundary. For the inspected live state, `anon` and `authenticated` have no table privileges on the private `shared_auth` schema. If any such object becomes Data-API exposed or receives browser-role grants, RLS plus explicit ownership/tenant predicates becomes mandatory.

Product applications still own their local memberships, roles, entitlements and product RLS. A Shared Auth identity or root enrollment must not imply product authorization.

## Provider topology

### Neon

Observed logical project names:

```text
shared-auth Neon organization
├── admin
├── auth
└── canonical
```

The `auth` project's compute endpoint is disabled. This is a useful fail-safe and a current test blocker. Starting or enabling it is an operational/cost-affecting action and was not performed merely to complete an audit.

### Supabase

The current connected account exposes an active project named `ores-shared-auth`. The target architecture's `admin` / `auth` / `canonical` separation should therefore be treated as provisioning/migration work until separate project identities are verified.

## Existing PR overlap checked

The open server stack was inspected before creating follow-up work:

- #149 — child-site OIDC foundation and compile repair;
- #155 — `azp`/`sid` ID-token binding;
- #156 — stable application-account ID plus pairwise subject sectors;
- #157 — userinfo live-session revocation fencing.

Those items are not duplicated in the new follow-up backlog. The stack also is not marked merge-ready merely to satisfy a task count: #149 records real remaining test failures and the later PRs are stacked on it.

## Conclusion

The live state supports the core architectural direction: provider-native auth remains provider-owned, Shared Auth already has a real canonical principal and provider-binding layer, and the private service schema is not directly exposed to browser roles. The remaining work is primarily semantic hardening and migration: exact issuer/realm identity keys, provider-neutral logical sessions, explicit root privilege, provenance/versioning, dual-store convergence, and provider-project symmetry.