# Provider resource naming and Shared Auth identity topology

Status: accepted organization architecture  
Decision date: 2026-09-14  
Owner: Shared Auth  
Tracking: DEN-2193  
Related: [Canonical identity database and RLS model](CANONICAL-IDENTITY-DATABASE-AND-RLS-MODEL.md), [Federated dual-proof architecture](FEDERATED-DUAL-PROOF-ARCHITECTURE.md)

## Decision

`shared-auth` is the logical product and GitHub-organization identity. It is **not** a requirement that every external provider resource use the literal display name `shared-auth`.

Across Supabase, Neon, Cloudflare, GCP, and other infrastructure providers, existing or future resources may legitimately use either `shared-auth`, `ores-shared-auth`, or a provider-generated immutable identifier. Infrastructure code, discovery, health checks, migration tooling, and documentation must therefore resolve the logical Shared Auth system through an explicit provider mapping rather than by assuming one display-name string.

Do not rename a healthy provider resource merely to make its display name match another provider. Renames can create avoidable DNS, issuer, project-reference, credential, deployment, or audit churn. Prefer stable provider IDs and explicit aliases.

## Logical name versus provider resource name

The canonical logical identity is:

```text
logical_system = shared-auth
```

Accepted provider-facing aliases include:

```text
shared-auth
ores-shared-auth
```

Those aliases are discovery metadata only. They are not security identities, user identities, token issuers, database principals, or authorization claims.

A provider mapping should retain the provider's immutable identifier wherever one exists:

```yaml
logical_system: shared-auth
provider: supabase
resource_name: ores-shared-auth
resource_id: <provider-immutable-id>
aliases:
  - shared-auth
  - ores-shared-auth
```

For Cloudflare the mapped object may be an account, zone, Worker/service, hostname, or project. For Supabase and Neon it may be an organization/project plus the provider-generated project identifier. The exact resource type is provider-specific; the logical Shared Auth identity is not.

## Discovery and configuration rules

Automation must follow this order:

1. Prefer an explicitly configured immutable provider resource ID/reference.
2. Otherwise resolve a reviewed provider mapping for logical system `shared-auth`.
3. Treat both `shared-auth` and `ores-shared-auth` as known aliases where the provider/account inventory documents them.
4. If multiple resources match and no immutable mapping disambiguates them, fail closed and require review.
5. Never choose a resource solely because its display name is lexically closest to the GitHub organization name.
6. Record the resolved provider, account/org, resource type, immutable ID/reference, display name, and logical plane in deployment evidence.

Configuration should distinguish semantic identity from presentation:

```text
SHARED_AUTH_LOGICAL_SYSTEM=shared-auth
SUPABASE_SHARED_AUTH_PROJECT_REF=<immutable ref>
NEON_SHARED_AUTH_PROJECT_ID=<immutable id>
CLOUDFLARE_SHARED_AUTH_RESOURCE_ID=<immutable id when available>
```

Human-readable aliases may appear in config or registries, but runtime authority should use immutable IDs, verified issuers, audiences, project refs, database endpoints, or other provider-native identifiers.

## Provider data-plane topology

The outer provider resource name does not change the three-plane model. Whether a provider container is named `shared-auth` or `ores-shared-auth`, the logical topology remains:

```text
Shared Auth logical system

Supabase provider mapping
├── auth
├── admin
└── canonical

Neon provider mapping
├── auth
├── admin
└── canonical

Cloudflare provider mapping
└── edge/DNS/proxy/runtime resources for the same logical system
```

The plane semantics are fixed:

- `auth`: provider-built-in customer authentication, provider-native users/identities/sessions/credentials.
- `admin`: isolated privileged authentication realm; no implicit fallback to customer auth.
- `canonical`: Shared Auth-owned canonical principals, provider bindings, logical sessions, revocation epochs, root-admin grants, application enrollment, OAuth/OIDC registry, audit, and outbox state.

Cloudflare is an edge/routing/runtime provider, not a canonical identity database. A Cloudflare resource name such as `ores-shared-auth` must never be treated as an identity authority merely because it fronts auth traffic.

## Canonical identity boundary

Provider-native authentication tables stay provider-owned:

```text
Supabase auth.*       -> provider evidence
Neon neon_auth.*      -> provider evidence
                         ↓
shared_auth.provider_identities
                         ↓
shared_user_id / canonical principal
```

The security-relevant binding remains:

```text
(provider, issuer, subject, realm)
```

Resource display names are deliberately absent from that tuple. Renaming `shared-auth` to `ores-shared-auth`, or the reverse, must not relink identities.

Provider-local user IDs also do not need to match one another. Both providers bind to the same canonical `shared_user_id` through exact issuer/subject evidence.

## Authorization boundary

Root Shared Auth owns only root/global identity concerns and the sparse root-admin capability. It does not centralize every product's roles.

Keep these concepts separate:

```text
Supabase/Postgres JWT role   = authenticated / anon / service_role
Shared Auth root grant       = root administrator
child application role       = product-specific role vocabulary
```

Applications such as `zed-pkg`, `sonus-auris`, and `benefactor-cc` own their memberships, product roles, entitlements, resource permissions, and product RLS policy. They consume `shared_user_id` as the stable external identity contract.

## Session and revocation boundary

Shared Auth owns a logical session above provider sessions. Provider session identifiers are attachments to the logical session, not the canonical session ID.

Normal customer authentication may use the explicitly configured availability-first/optimistic reconciliation path. Privileged/root-admin operations must use the strict configured provider pair and fail closed if the required proofs do not reconcile to the same canonical principal.

Logout/revocation semantics are:

```text
1. mark the logical Shared Auth session revoking/revoked
2. increment the monotonic revocation epoch
3. enqueue idempotent Supabase revocation
4. enqueue idempotent Neon revocation
5. retry provider cleanup without resurrecting the logical session
```

A provider display-name difference has no effect on revocation identity; the provider session binding must use the configured immutable project/resource reference.

## RLS and claims

Use Supabase Auth and Neon Auth as built-in authentication systems and preserve their provider-native RLS integration.

For Supabase, do not overload the JWT `role` claim with Shared Auth or product roles. Keep it as the Postgres/RLS role and carry canonical context separately, for example `shared_user_id`, `auth_realm`, `shared_auth_rev`, and—only for an authorized admin token—`root_admin`.

Neon should expose semantically equivalent canonical identity context while retaining its own provider-native auth schema and token mechanics.

Child applications authorize with local membership/role tables plus signed canonical identity. They must not perform cross-database authorization joins into Shared Auth on normal request paths.

## Canonical dual-provider writes

Supabase canonical storage and Neon canonical storage must not behave as two unrelated writable primaries racing each other.

For a canonical mutation, use one logical mutation authority and one generated event identity with stable values such as:

```text
event_id
shared_user_id
revision
idempotency_key
```

Materialize that logical mutation idempotently into both configured canonical stores and compare revisions to detect drift. The configured provider mapping identifies the target stores; display-name aliases never select a winner.

## Required validation

At minimum, conformance tests must prove:

- both `shared-auth` and `ores-shared-auth` aliases resolve correctly when explicitly mapped;
- immutable provider IDs beat display-name matching;
- ambiguous aliases fail closed;
- changing a provider display name does not relink canonical identities;
- the `auth`, `admin`, and `canonical` planes remain distinct regardless of outer provider name;
- same email with different issuer/subject does not merge principals;
- child-app roles grant no Shared Auth root privilege;
- Supabase JWT `role` remains provider/RLS-oriented;
- customer optimistic authentication cannot be promoted into admin authority without the strict provider pair;
- revocation epochs prevent a late provider success from resurrecting a revoked logical session;
- canonical Supabase/Neon revision drift is detected and reported.

## Documentation rule

Provider inventories, `.github` architecture docs, `shared-auth-docs`, Linear, and infrastructure configuration should all record **logical system + provider + immutable resource ID/reference + current display name + accepted aliases** where practical.

The human-facing phrase “Supabase/Neon/Cloudflare shared-auth resources” therefore means resources mapped to the logical Shared Auth system, not resources that must literally be named `shared-auth`.
