# Canonical identity database and RLS model

Status: accepted target design; schema/migration/runtime evidence remains open  
Decision date: 2026-09-14  
Owner: Shared Auth  
Tracking: [DEN-2193](https://linear.app/denman/issue/DEN-2193/shared-auth-server-add-realm-isolation-and-federated-customer)  
Related architecture: [Federated dual-proof subsystem authentication](FEDERATED-DUAL-PROOF-ARCHITECTURE.md)

## Executive decision

Shared Auth defines one canonical semantic identity model without trying to make Supabase Auth's `auth.*` tables and Neon Auth's `neon_auth.*` tables physically identical.

The ownership boundary is:

- Supabase Auth owns Supabase-native users, identities, sessions, credentials, refresh material, MFA state, and provider-local subjects.
- Neon Auth owns Neon-native users, accounts, sessions, credentials, auth configuration, and provider-local subjects.
- Shared Auth owns the canonical ORES identity, exact provider-to-canonical bindings, logical cross-provider sessions, revocation epochs, root-admin grants, application enrollment, OAuth client registry, and audit/outbox state.
- Product applications own product memberships, tenant/resource authorization, application roles, entitlements, billing grants, and product RLS policy.

Provider-native auth tables are authentication evidence stores. They are not the canonical cross-provider identity database merely because they contain a user row.

The central invariant is:

```text
provider auth tables are implementation-owned
           ↓
exact provider identities
           ↓
canonical shared_user_id
           ↓
minimal root-admin capability
           ↓
application-specific authorization belongs to each child app
```

## Compatibility with the existing strict dual-proof design

This document adds the Supabase + Neon root-provider data model. It does **not** relax the strict subsystem grant rules in `FEDERATED-DUAL-PROOF-ARCHITECTURE.md`.

In particular:

- availability-first verification may be used for ordinary root customer-session bootstrap only where the customer-realm contract explicitly permits an optimistic session followed by reconciliation;
- a Shared Auth session derived from a provider proof does not automatically become an independent second proof for a strict subsystem grant;
- strict subsystem grants continue to require the proof set defined by the federation contract;
- privileged/root-admin operations fail closed and require the configured strict provider pair.

Do not reinterpret a provider race as proof that two independent authenticators succeeded.

## Root topology

For the Shared Auth organization, and eventually for child organizations that need the same provider symmetry, use three logical projects/data planes per provider:

```text
Supabase / shared-auth
├── admin
├── auth
└── canonical

Neon / shared-auth
├── admin
├── auth
└── canonical
```

The meanings are rigid:

```text
auth
    built-in Supabase Auth / Neon Auth
    normal user authentication
    provider-native users, identities, sessions, and credentials
    customer-facing realm

admin
    built-in Supabase Auth / Neon Auth
    separate privileged realm
    admin-only identity/session boundary
    no fallback to the customer auth project

canonical
    Shared Auth-owned tables
    canonical shared_user_id/principal
    provider bindings
    logical sessions
    revocation epochs
    root-admin grants
    application registry/enrollment
    OAuth client registry
    audit and outbox state
```

The same shape applies conceptually to child systems such as `zed-pkg`, `sonus-auris`, and `benefactor-cc`, but their application roles and authorization remain local to those systems.

## Canonical identity name

The semantic entity is a **principal**. Existing Shared Auth contracts already use that term, and it avoids confusion with Supabase `auth.users` and Neon `neon_auth.user`.

The preferred physical table for the next canonical schema is therefore:

```text
shared_auth.principals
```

The externally stable identifier remains:

```text
shared_user_id UUID
```

If an existing migration or consumer currently uses `shared_auth.users`, migration may provide a temporary read-only compatibility view or adapter, but there must never be two writable canonical identity tables.

A principal is intentionally boring:

```sql
create table shared_auth.principals (
  id uuid primary key,

  status text not null
    check (status in ('active', 'disabled', 'deleted')),

  revision bigint not null default 1,

  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  disabled_at timestamptz,
  deleted_at timestamptz
);
```

Do not make email, phone, GitHub username, display name, avatar URL, provider metadata, OAuth tokens, or a mutable application role part of canonical identity.

The identity is the opaque UUID, not a contact point:

```text
shared_user_id = 4bf7...e126
```

Email and other contact data may exist as versioned/provenanced attributes, but they are not identity keys and must never silently merge principals.

## Canonical root tables

The next canonical schema should contain approximately these entities:

| Table | Purpose | Important fields |
| --- | --- | --- |
| `shared_auth.principals` | Globally stable ORES identity | `id`, `status`, `revision`, timestamps |
| `shared_auth.provider_identities` | Exact Supabase/Neon subject bindings | `shared_user_id`, `provider`, `realm`, `issuer`, `subject`, `project_ref` |
| `shared_auth.root_admin_grants` | Sparse global admin capability | `shared_user_id`, grant/revoke actor and timestamps |
| `shared_auth.sessions` | Logical cross-provider session | `id`, `shared_user_id`, `realm`, `state`, `revocation_epoch`, expiry |
| `shared_auth.provider_sessions` | Provider-local sessions participating in a logical session | canonical session ID, provider session reference/status |
| `shared_auth.applications` | Registry of child applications | app ID, GitHub org, audiences, realm, status |
| `shared_auth.application_accounts` | Enrollment of a principal in an application | stable application-account ID, app ID, principal ID, state |
| `shared_auth.oauth_clients` | Logical Shared Auth OAuth/OIDC clients | client ID, redirects, grants, scopes, audiences |
| `shared_auth.provider_oauth_clients` | Supabase/Neon materialization of logical clients | logical client ID plus provider-local client ID/config ref |
| `shared_auth.revocation_outbox` | Reliable provider revocation work | session, provider, operation, idempotency key, state |
| `shared_auth.audit_events` | Immutable privileged auth/admin audit | actor, subject, action, outcome, timestamp, correlation ID |

Do **not** put `zed-pkg`, `sonus-auris`, `benefactor-cc`, or other product role vocabularies into these root tables.

`application_accounts` means enrollment/identity projection only. It must not become a central product RBAC database.

## `provider_identities` is the critical binding table

Provider-native IDs do not need to equal one another. They only need to bind deterministically to the same canonical principal.

The security-relevant identity tuple is:

```text
(provider, issuer, subject, realm)
```

A target shape is:

```sql
create table shared_auth.provider_identities (
  id uuid primary key default gen_random_uuid(),

  shared_user_id uuid not null
    references shared_auth.principals(id),

  provider text not null
    check (provider in ('supabase', 'neon-auth')),

  realm text not null
    check (realm in ('auth', 'admin')),

  provider_org text not null,
  project_ref text not null,

  issuer text not null,
  subject text not null,

  email_verified boolean not null default false,

  aal smallint not null default 1
    check (aal between 1 and 3),

  first_seen_at timestamptz not null default now(),
  last_seen_at timestamptz not null default now(),
  disabled_at timestamptz,

  unique (provider, issuer, subject, realm),
  unique (shared_user_id, provider, realm, project_ref)
);
```

The critical uniqueness constraint is:

```text
UNIQUE(provider, issuer, subject, realm)
```

Example:

```text
shared_user_id = X

Supabase
  issuer  = https://<project>.supabase.co/auth/v1
  subject = <supabase auth.users.id>

Neon
  issuer  = <Neon Auth issuer>
  subject = <neon_auth user id>

Supabase identity ─┐
                    ├──> shared_user_id X
Neon identity ─────┘
```

Never merge identities by email, phone, display name, provider username, or other mutable metadata.

## Root admin is a grant, not a generic role

Do not overload the word `role` at the root.

These are distinct concepts:

```text
Supabase JWT role         = authenticated / anon / service_role
Shared Auth root grant    = root administrator
zed-pkg application role  = owner / maintainer / publisher / ...
```

Use a sparse grant table:

```sql
create table shared_auth.root_admin_grants (
  shared_user_id uuid primary key
    references shared_auth.principals(id),

  granted_at timestamptz not null default now(),
  granted_by uuid references shared_auth.principals(id),

  revoked_at timestamptz,
  revoked_by uuid references shared_auth.principals(id),

  reason text
);
```

Semantics:

```text
root_admin(user) = active row exists in root_admin_grants
```

No active row means the user is not a root administrator.

A non-root-admin principal may still be an owner/maintainer/researcher/billing admin inside a child application. Product privilege must never imply Shared Auth root privilege.

## Logical sessions and provider sessions

Do not use either Supabase's provider session ID or Neon's provider session ID as the Shared Auth root session ID.

Create a logical session:

```sql
create table shared_auth.sessions (
  id uuid primary key,

  shared_user_id uuid not null
    references shared_auth.principals(id),

  realm text not null
    check (realm in ('auth', 'admin')),

  state text not null
    check (state in (
      'optimistic',
      'reconciled',
      'revoking',
      'revoked',
      'expired'
    )),

  auth_level smallint not null,
  revocation_epoch bigint not null default 0,

  created_at timestamptz not null,
  reconciled_at timestamptz,
  expires_at timestamptz not null,
  revoked_at timestamptz
);
```

Then bind provider-local sessions to it:

```sql
create table shared_auth.provider_sessions (
  shared_session_id uuid not null
    references shared_auth.sessions(id),

  provider text not null,
  realm text not null,
  project_ref text not null,

  provider_session_id text not null,

  status text not null
    check (status in (
      'active',
      'unknown',
      'revocation_pending',
      'revoked'
    )),

  expires_at timestamptz,
  last_verified_at timestamptz,

  primary key (shared_session_id, provider, realm)
);
```

Never store provider refresh tokens or provider credentials in `provider_sessions`. Supabase owns Supabase refresh credentials; Neon owns Neon session credentials. Shared Auth stores binding identifiers and state, not copied credentials.

## Customer authentication versus admin authentication

For ordinary, non-privileged root customer authentication, the two providers may be queried concurrently for availability where the customer-session state machine permits optimistic entry followed by reconciliation:

```text
Supabase verification ─┐
                        ├─ availability-first bootstrap
Neon verification ─────┘
```

This is an availability mechanism, not a strict two-proof assertion.

For root-admin authentication and privileged operations, first-success semantics are forbidden. Require the configured strict pair:

```text
Supabase admin proof valid
       AND
Neon admin proof valid
       AND
both map to the same shared_user_id
       AND
realm = admin
       AND
active root_admin_grant exists
```

This applies to operations such as:

- `/admin/*` access;
- root-admin grant changes;
- OAuth/OIDC client administration;
- provider binding changes;
- disabling a principal;
- session revocation;
- impersonation/delegation controls;
- signing-key or trust configuration changes.

A provider outage during privileged evaluation means the admin plane is degraded and the privileged operation is denied. It must not silently downgrade to one provider.

## Signout and revocation

User-visible logout must not wait for two remote provider deletions to complete synchronously.

First revoke the logical Shared Auth session transactionally:

```text
BEGIN

shared_auth.sessions
  state = 'revoking'
  revoked_at = now()
  revocation_epoch += 1

INSERT revocation_outbox(supabase)
INSERT revocation_outbox(neon)

COMMIT
```

At commit, the Shared Auth session is dead for authorization purposes.

Then revoke provider sessions idempotently through the outbox:

```text
Supabase provider session -> revoke
Neon provider session     -> revoke
```

After both provider outcomes are terminal, advance the logical session to `revoked`.

The revocation epoch is monotonic. A delayed successful provider response may not resurrect an older session generation.

## Child application schema

A child application stores the canonical ID as an external identity contract, not as a cross-database foreign key.

Example for `zed-pkg`:

```sql
create table zed_pkg.users (
  shared_user_id uuid primary key,
  created_at timestamptz not null default now(),
  disabled_at timestamptz
);

create table zed_pkg.roles (
  id uuid primary key,
  name text unique not null
);

create table zed_pkg.user_roles (
  shared_user_id uuid not null
    references zed_pkg.users(shared_user_id),

  role_id uuid not null
    references zed_pkg.roles(id),

  primary key (shared_user_id, role_id)
);
```

There is deliberately no cross-provider/cross-project SQL foreign key to the Shared Auth canonical database.

The contract is:

```text
shared_user_id UUID
```

with application-level verification/provisioning and signed identity claims.

The same pattern can be used by `sonus-auris`, `benefactor-cc`, `ores-chat`, and other child systems while allowing each application to define its own role vocabulary.

## RLS contract

Both provider stacks use their built-in auth systems and their RLS integrations. Do not replace the provider-native auth tables with a homegrown password/session store.

### Supabase

Keep Supabase's `role` JWT claim for the Postgres role used by RLS (`authenticated`, `anon`, or server-side `service_role`). Do not repurpose that field to mean Shared Auth root admin or an application role.

Use signed custom claims for Shared Auth context, for example:

```json
{
  "sub": "<supabase-user-id>",
  "role": "authenticated",
  "shared_user_id": "<canonical-uuid>",
  "auth_realm": "auth",
  "shared_auth_rev": 27
}
```

Admin realm:

```json
{
  "sub": "<supabase-admin-auth-user-id>",
  "role": "authenticated",
  "shared_user_id": "<canonical-uuid>",
  "auth_realm": "admin",
  "root_admin": true,
  "shared_auth_rev": 27
}
```

Supabase Custom Access Token Hooks may add authorization claims. RLS may read signed claims from `auth.jwt()`. Never trust client-writable metadata as the source of root privilege.

### Neon

Neon Auth stores provider-owned users, sessions, accounts/organizations, and configuration under `neon_auth.*` and exposes authenticated identity to database/RLS flows. Shared Auth should consume that provider identity and bind it to `shared_user_id`; it should not try to force Neon's physical tables to match Supabase's physical tables.

The equivalent Neon JWT/RLS context should carry the same **semantic** Shared Auth claims even if provider-native claim names and transport differ.

### Child RLS

Child application RLS should authorize on child-owned membership/role tables plus the signed canonical identity. It must not reach across databases into Shared Auth at query time.

Where supported, prefer a signed `shared_user_id` claim. Otherwise use a local provider-subject-to-`shared_user_id` mapping materialized by the child bootstrap/reconciliation flow.

RLS is defense in depth; product APIs still scope authoritative reads/writes by tenant, owner, and resource.

## Two canonical physical stores, one logical writer

It is acceptable to materialize the canonical Shared Auth schema in both Supabase canonical and Neon canonical projects for availability and verification.

It is **not** acceptable to treat them as two unrelated writable masters.

Do not allow:

```text
request A -> writes only Supabase canonical
request B -> writes only Neon canonical
```

and attempt an ambiguous merge later.

Every canonical mutation has one logical command identity:

```text
event_id
shared_user_id
revision
idempotency_key
```

For example:

```text
CreateCanonicalPrincipal {
    event_id: E,
    shared_user_id: U,
    revision: 1
}
```

The same mutation is then materialized idempotently into both canonical stores.

Convergence can be asserted meaningfully:

```text
Supabase canonical U revision = 51
Neon canonical U revision     = 51
```

A provider response at an older revision may not overwrite a newer canonical revision.

## Application registry and OAuth/OIDC clients

Shared Auth may centrally own **identity-plane enrollment** and OAuth/OIDC client registration without owning product authorization.

`shared_auth.applications` should identify at least:

- stable application ID;
- GitHub organization/repository family;
- allowed audiences;
- realm;
- subject-sector/pairwise-subject policy where applicable;
- status and schema/config revision.

`shared_auth.application_accounts` should identify a stable application account/enrollment but contain no product role implication.

`shared_auth.oauth_clients` and `provider_oauth_clients` should separate the logical Shared Auth client from provider-local materialization. Exact redirect URIs, PKCE requirements, grant types, scopes, audiences, client state, and provider identifiers must be explicit.

OAuth 2.0/OIDC token issuance must preserve issuer, audience, subject, nonce/state/PKCE, proof-age, and realm invariants defined by the existing federation contract.

## Migration target

Treat the existing service-only federated-identity table as a v0 provider-binding model, not the final canonical schema.

The next schema release should be tracked as a versioned migration, for example:

```text
shared-auth-0002
```

The migration should converge on:

```text
provider-native auth tables
        ↓
provider_identities
        ↓
principals/shared_user_id
        ↓
logical sessions + root_admin_grants
        ↓
application enrollment only
        ↓
child-owned roles, memberships, entitlements, and RLS
```

The executable schema remains owned by Shared Auth interfaces/migrations. This document is the architecture contract, not a substitute for TypeSpec/JSON Schema/SQL migration sources.

## Required invariants

1. `shared_user_id` is globally stable and opaque.
2. Provider identity is keyed by exact provider + issuer + subject + realm, never email alone.
3. Admin and customer realms are isolated.
4. Provider-native tables remain provider-owned.
5. Root privilege is sparse and separate from provider/Postgres roles and product roles.
6. Product authorization remains local to each child app.
7. No cross-database foreign keys or runtime SQL joins are required for authorization.
8. Provider credentials and refresh tokens are never copied into canonical session tables.
9. Logical revocation becomes authoritative before remote provider cleanup completes.
10. Revocation epochs and canonical revisions are monotonic.
11. Two physical canonical stores never imply two independent logical writers.
12. Strict dual-proof subsystem grants remain strict; an availability race is not dual proof.
13. RLS consumes signed provider/canonical identity and child-owned authorization state.
14. Every privileged mutation is auditable and idempotent.

## Acceptance and test matrix

Before calling the schema complete, add automated evidence for at least:

- Supabase subject A + Neon subject B binding to one `shared_user_id`;
- rejecting attempts to bind one provider tuple to two canonical principals;
- rejecting email-only/phone-only identity linking;
- customer optimistic session reconciliation and stale-result suppression;
- admin denial when either strict provider proof is absent, invalid, unavailable, stale, or maps to a different principal;
- root-admin grant absence denying privileged access even when both provider proofs are valid;
- child role not implying root admin and root admin not implying child role;
- cross-app audience/role isolation for `zed-pkg`, `sonus-auris`, and another child fixture;
- logout becoming locally invalid before one intentionally delayed provider revocation completes;
- revocation epoch preventing stale provider completion from resurrecting a session;
- Supabase and Neon canonical replicas converging to the same revision/event IDs;
- RLS denying rows owned by another `shared_user_id`/tenant;
- no browser/client path able to mutate root-admin claims or canonical provider bindings;
- no copied provider refresh token/credential material in canonical tables or fixtures.

## Provider references

- Supabase JWT claims: https://supabase.com/docs/guides/auth/jwt-fields
- Supabase custom claims / RBAC: https://supabase.com/docs/guides/api/custom-claims-and-role-based-access-control-rbac
- Supabase Custom Access Token Hook: https://supabase.com/docs/guides/auth/auth-hooks/custom-access-token-hook
- Supabase Auth architecture: https://supabase.com/docs/guides/auth/architecture
- Neon Auth / Better Auth architecture and `neon_auth.*`: https://neon.com/blog/neon-auth-branchable-identity-in-your-database

## Summary

Global identity is strongly centralized around one stable canonical principal. Global privilege is intentionally tiny. Supabase and Neon remain first-class built-in authentication providers with their own native tables and RLS integrations. Logical sessions and revocation bind those providers without copying their credentials. Child applications receive a stable `shared_user_id` but keep their own roles, memberships, entitlements, and RLS rules.

That keeps provider implementations replaceable, root privilege auditable, application authorization decentralized, and dual-provider availability compatible with strict federation security boundaries.
