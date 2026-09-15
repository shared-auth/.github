# Shared Auth context, proof taxonomy, and source precedence

Status: accepted architecture reconciliation  
Decision date: 2026-09-14  
Owner: Shared Auth  
Tracking: DEN-2193  
Related: DEN-3810, DEN-3812, DEN-2194, DEN-2197, DEN-606

## Purpose

Shared Auth has several generations of architecture that are all useful but describe different dimensions of the system. The terms **dual auth**, **dual provider**, **dual proof**, **canonical authority**, **realm**, **provider**, **organization**, and **configuration** have sometimes been used for different boundaries.

This document reconciles those meanings. It does not delete historical decisions, change a wire contract, migrate a database, or enable a provider. It defines how maintained architecture must be read together.

The most important rule is:

> **Dual provider is not the same thing as dual proof. Provider topology, proof composition, canonical storage, realm isolation, product authorization, and configuration authority are separate concerns.**

## The five security/data dimensions

### 1. Realm

The top-level security realms are:

```text
customer
admin
```

They do not share issuer, signing keys, cookies, runtime database credentials, recovery policy, provider registry, OAuth clients, sessions, or privileged policy. Customer authority never promotes itself into admin authority.

### 2. Provider evidence

Provider evidence may originate from:

```text
native Shared Auth
Supabase Auth
Neon Auth
other explicitly registered upstream providers
```

Provider-native authentication stores remain provider-owned. Supabase `auth.*` and Neon Auth `neon_auth.*` are evidence stores, not the canonical ORES identity merely because they contain a user or session row.

The canonical provider identity binding is:

```text
(provider, issuer, subject, realm)
```

`provider_tenant`, project display names, organization display names, email, phone, username, and profile metadata may be compatibility/provenance metadata, but none replaces that security tuple.

### 3. Proof policy

A **proof policy** says which independently established proofs must be present before a particular operation may authorize. It is not implied by how many providers exist.

### 4. Canonical state and materialization

Shared Auth owns one logical canonical identity/session mutation authority. Canonical state may be materialized into more than one configured storage system, but two materializations are not two unrelated writable primaries.

A canonical mutation carries one stable identity such as:

```text
event_id
shared_user_id
revision
idempotency_key
```

Provider materializations apply that logical mutation idempotently and compare revisions. Drift creates bounded reconciliation work; it does not elect whichever provider wrote last or answered first.

### 5. Product authorization

Products own their memberships, tenant/resource roles, billing grants, entitlements, resource permissions, and product RLS. Shared Auth establishes identity, authentication assurance, root/identity-plane capabilities, application enrollment, and bounded OAuth/OIDC policy. It is not the universal product authorization database.

## Proof-policy taxonomy

### Customer bootstrap / ordinary authentication

For explicitly approved customer authentication-only/read paths, the configured policy may be availability-first or optimistic-with-reconciliation.

A cryptographically valid route-acceptable provider result may create a short-lived **optimistic** customer session only when the versioned policy permits it. Remaining authority checks continue through durable reconciliation. A later hard deny, revocation, immutable-identity conflict, realm mismatch, or canonical-principal disagreement monotonically revokes that session epoch.

An optimistic/provider-only decision:

- is not admin authority;
- is not a strict subsystem grant;
- cannot manufacture local Shared Auth root/identity-plane grants;
- cannot claim reconciliation or revocation freshness that has not been established;
- cannot be promoted merely because a second verifier returns late.

### Strict Supabase + Neon provider pair

The Supabase+Neon topology contract defines a separate **strict provider-pair** policy for configured admin/sensitive paths and for consumers that explicitly require both provider bindings.

Both exact provider identities must verify and resolve through canonical bindings to the same `shared_user_id` under the required realm/policy epoch. This proves **provider agreement**. It does not automatically prove the separate strict subsystem/application-grant ceremony below.

### Strict subsystem / application grant

The accepted `federation-authorization/v1` subsystem policy remains the strict dual-proof rule defined by `FEDERATED-DUAL-PROOF-ARCHITECTURE.md` unless a future versioned contract explicitly changes it.

Its required independent proof set is:

```text
native Shared Auth customer proof
AND federation-root Supabase proof
AND active application account
AND exact client / redirect / nonce / PKCE / audience / scope / transaction bindings
AND current policy + revocation epochs
```

A Shared Auth session created only by exchanging the same root Supabase proof does not become an independent native Shared Auth proof merely by being reissued.

A Neon proof does not silently substitute for either strict subsystem proof. If the subsystem proof set ever changes, it requires a new reviewed/versioned contract, corresponding formal model, interfaces, runtime implementation, and E2E evidence.

### Root-admin / privileged identity-plane operations

Root administration is a sparse capability, not a product role and not the Supabase JWT `role` claim.

The target boundary is:

```text
current strict configured provider proof policy
AND canonical shared_user_id
AND active shared_auth.root_admin_grants capability
AND required assurance / freshness / session epoch
```

The current target provider pair is Supabase + Neon where that provider-symmetric policy is enabled. Missing, stale, invalid, unavailable, mismatched, or conflicting required proof fails closed.

Identity-plane RBAC such as directory/federation/credential administration remains distinct from the sparse global root-admin grant. Product roles never imply either one.

### Legacy/compatibility first-success race

Existing `shared-auth-lib` first-success/availability-oriented races are compatibility mechanisms for bounded authentication availability. Their output cannot be converted into a strict provider-pair result, a strict subsystem proof set, or a root-admin authorization merely because one arm succeeded.

## Realm × provider × proof matrix

| Operation class | Realm | Provider topology | Required proof policy | May be degraded/optimistic? |
| --- | --- | --- | --- | --- |
| Ordinary customer bootstrap/read | customer | configured Supabase/Neon/native lanes | versioned availability-first/reconcile policy | yes, only when explicitly allowed |
| Sensitive customer mutation | customer | configured provider lanes | strict policy for that operation | normally no |
| Subsystem application grant | customer | federation provider registry | native Shared Auth + federation-root Supabase + active app account | no |
| Admin authentication / sensitive admin | admin | isolated admin provider lanes | configured strict provider pair | no |
| Root-admin mutation | admin | isolated admin provider lanes | strict provider pair + sparse root-admin capability + freshness | no |
| Product tenant/resource authorization | product | consumes signed/introspected Shared Auth identity | product-local membership/role/RLS | product policy only |

No row authorizes a caller merely because multiple databases or provider projects exist.

## Canonical identifier vocabulary

### `shared_user_id` and `principal_id`

The semantic entity is a principal. The stable cross-system ORES identity contract is `shared_user_id`.

Older documents and some internal schemas use `principal_id`. Treat that as an internal/historical spelling only where the owning contract explicitly says so. New cross-repository contracts should prefer `shared_user_id` unless a versioned interface has a compatibility field that cannot yet be renamed.

### Provider identity

Current canonical semantic key:

```text
(provider, issuer, subject, realm)
```

Older `(provider_tenant, provider_subject)` or `(provider_id, issuer, subject)` shapes are migration/compatibility representations. `provider_tenant` may preserve immutable project/resource provenance but does not replace exact issuer + realm identity.

### Application identity

`application_account_id` is the stable enrollment identity for one principal in one application. Public OIDC clients should receive pairwise/client-sector subjects where the contract requires unlinkability; public tokens should not leak the global `shared_user_id` unless a reviewed contract explicitly requires it.

### Session identity

Shared Auth owns a logical session above provider-native sessions. Supabase and Neon session identifiers attach to provider-session bindings; they are not the canonical Shared Auth session ID.

## Storage and authority reconciliation

### Provider-native auth stores

```text
Supabase auth.*
Neon Auth neon_auth.*
```

own provider users, credentials, sessions, MFA/provider-local state, and provider subjects.

### Current executable Shared Auth runtime

The executable server still has its own reviewed PostgreSQL schema and realm startup contract. Current runtime authority is defined by the exact server revision, `db/schema.sql`, the realm/runtime configuration contract, and deployed database evidence.

Target architecture documents must not be read as proof that a target table already exists or that a provider migration has occurred.

### Target canonical provider planes

Desired Supabase and Neon `canonical` planes are materialization/reconciliation targets for Shared Auth-owned canonical state. They use one logical mutation/event/revision identity and fail closed on unexplained divergence.

They are **not** an active-active last-write-wins pair. Backup/DR copies are likewise not selected per request because they responded faster.

### Product stores

Product databases store local user/account mappings, tenant/resource membership, roles, billing/domain state, and local RLS. Normal authorization must not require a synchronous cross-database join into Shared Auth.

## Identity organizations versus product tenants

Shared Auth may own **identity organizations** required to administer the identity service itself: enterprise SSO connections, SCIM directories, verified domains, identity policy, identity-service invitations, and delegated Shared Auth administration.

A child product still owns its organizations/workspaces, memberships, product roles, billing grants, resources, and product RLS. A product may explicitly map one of its tenants to a Shared Auth identity organization using an opaque stable ID, but neither side's roles imply the other side's authorization.

## Provider resource names versus logical organization placement

The dual-provider deployment contract requires a **logical dedicated organization placement key** (`githubOrg`, `runtimeOrg`, `targetOrg`) so a product cannot silently point authentication at another product's provider allocation.

Provider infrastructure may instead have a **physical display name** such as `shared-auth`, `ores-shared-auth`, or a provider-generated immutable identifier.

Therefore:

```text
logical placement owner key != provider display name
```

Runtime trust and discovery use reviewed provider mappings and immutable provider IDs/project refs/issuers. Do not rename healthy provider resources merely to make display names equal the GitHub organization string.

The existing `SharedAuthTopology` v1 schema is unchanged by this clarification; `runtimeOrg`/`targetOrg` are logical placement-owner keys, not literal provider-console display names.

## Configuration authority taxonomy

The total-context audit found that similarly named files had been assigned two different meanings. The accepted boundary is now explicit:

| Path | Meaning | Authority |
| --- | --- | --- |
| `.shared-auth.toml` | canonical project-level Shared Auth **consumer policy** | independent TypeSpec + authored Draft 2020-12 JSON Schema in `shared-auth-interfaces/contracts/shared-auth-config` |
| `.auth-shared.toml` | migration-only compatibility alias for that consumer policy | same consumer-policy authorities; if both policy filenames exist, fail closed |
| `config/shared-auth-topology.toml` | secret-free fleet/provider/application **topology** metadata for the central Shared Auth server | topology admission rules + organization architecture; not a consumer-policy parser |
| `.cli-flags.toml` | argv/environment flag contract | `flags-2-env` boundary |
| `config/auth-realms.contract.json` | executable realm startup invariants | server runtime contract |

The topology contract must never be stored in `.shared-auth.toml` or `.auth-shared.toml`. Conversely, the topology validator must not become an independent parser for the consumer-policy schema.

The central server may carry a valid compatibility-alias consumer-policy object without loading it. File presence is not runtime-adoption evidence; DEN-606 requires actual loader/resolution/revision-admission evidence before that claim is made.

## Source precedence by concern

No single document is globally authoritative for every concern. Use the owning source for the question being asked.

| Concern | Primary authority | Important supporting context |
| --- | --- | --- |
| Cross-document terminology / precedence | this document | `PROJECTS.md`, Linear architecture |
| Realm isolation and customer/application SSO target | `FEDERATED-DUAL-PROOF-ARCHITECTURE.md`, this document | Linear admin/customer architecture; server realm docs |
| Canonical Supabase+Neon identity/session model | `CANONICAL-IDENTITY-DATABASE-AND-RLS-MODEL.md`, this document | provider naming/topology docs; conformance evidence |
| Async/concurrency semantics | `ASYNC-AUTH-STATE-MACHINES-AND-FORMAL-VERIFICATION.md` | Rust reducer/Postgres/refinement/E2E evidence |
| Provider resource mapping/naming | `PROVIDER-RESOURCE-NAMING-AND-IDENTITY-TOPOLOGY.md` | infrastructure inventory and immutable IDs |
| Deployment topology data contract | `shared-auth-interfaces/DUAL_PROVIDER_TOPOLOGY.md` + `schema/auth-topology.schema.json` | product `*-infra` fixtures/tests |
| Consumer policy | `shared-auth-interfaces/contracts/shared-auth-config` TypeSpec + authored JSON Schema | DEN-606 rollout and language-boundary evidence |
| Central fleet/provider topology | `shared-auth-server.rs/config/shared-auth-topology.toml` + topology validator | `AUTH-SHARED-TOPOLOGY-AND-ORCHESTRATION.md` |
| Executable server startup/runtime | exact `shared-auth-server.rs` revision, `config/auth-realms.contract.json`, `.cli-flags.toml`, source | topology metadata is admission/context, not runtime parser |
| Executable physical DB schema | exact server/ORM declarative schema revision | target architecture docs are migration intent only |
| Wire/data-model contracts | owning versioned `shared-auth-interfaces` authored authorities | generated bindings are evidence/projections, not independent authority |
| Product authorization | owning product database/contracts | Shared Auth identity/assurance input only |
| Planning/priority/dependencies | Linear | GitHub issues/PRs link execution evidence |
| Code/review/test evidence | GitHub exact revision + executed checks | zero-step runner failures are non-evidence |

When an older document conflicts with a newer accepted decision for the **same concern**, preserve the older document as historical context and follow the newer accepted decision. Do not use a newer document to override an older document that owns a different concern.

## Historical document interpretation

### `shared-auth-server.rs/docs/DESIGN.md`

Useful as an implementation baseline, but its older `(provider, provider_tenant, provider_subject)` link shape and flat `roles` description are not the final canonical identity/root-admin model.

### `shared-auth-server.rs/docs/fiducia-dual-auth.md`

Its “dual auth” term describes the legacy Shared Auth/Supabase availability race and Fiducia customer/admin Supabase separation. It is not the Supabase+Neon strict pair and not the strict subsystem dual-proof ceremony.

### `shared-auth-server.rs/docs/auth-realms-and-federated-sso.md`

The realm/application-account/OIDC boundaries remain useful. Its Supabase-centric provider-link sketch predates the explicit Supabase+Neon canonical binding tuple and should be read through this reconciliation document.

### `AUTH-DATA-PLANE-IMPLEMENTATION.md`

This is an evidence checkpoint, intentionally not a current-production completion declaration. Its dated claims should not be silently promoted to current runtime state.

### `DEN-606-SHARED-AUTH-CONFIG-ROLLOUT.md`

This owns the consumer-policy filename contract. Its `.shared-auth.toml` / `.auth-shared.toml` semantics take precedence over the later accidental topology reuse of `.auth-shared.toml`; topology has therefore moved to `config/shared-auth-topology.toml`.

## Current implementation and evidence map

As of 2026-09-14, important work is intentionally split across separate changes and must not be collapsed into one “done” claim:

- `shared-auth-server.rs` has merged realm/runtime foundations and secret-free topology admission work;
- open server work includes Supabase+Neon adjudication cores, child-site OIDC, pairwise-subject persistence, upstream federation, and other security hardening;
- `shared-auth-lib` has separate strict Supabase+Neon provider-pair work that explicitly does not replace the higher-level application-grant transaction;
- `shared-auth-interfaces` has topology and consumer-policy contract families on main and open federation/broker work;
- `shared-auth-e2e` has open canonical-identity hardening contracts;
- canonical Supabase/Neon target schema still has migration deltas from the executable server schema;
- exact-head hosted CI frequently receives zero executed steps in the current environment, so local/independent evidence must be labeled honestly and cannot be represented as CI execution.

A document or contract test is not production migration evidence. A merged schema is not deployed behavior. A model proof is not automatically a proof of independently written runtime implementations. A provider configuration target is not evidence that a provider resource exists. A valid config file is not evidence that a runtime has loaded it.

## Rules for future documents

New Shared Auth documents must state which concern they define: realm boundary, provider evidence, proof policy, canonical storage/materialization, wire/data model, consumer policy, fleet topology, identity-plane authorization, product authorization, infrastructure/resource naming, or evidence checkpoint.

If “dual auth” or “dual proof” is used, name the exact proofs/providers and whether policy is availability-first, reconcile-later, or strict/fail-closed.

If “canonical” is used, distinguish logical canonical identity/mutation authority from a physical canonical materialization.

If “organization” is used for a provider, distinguish logical placement owner key from provider-console display name and immutable resource ID. If an identity organization is meant, distinguish it from a child-product tenant.

If a target schema/table is shown, state whether it exists in the current executable schema or is migration intent.

If a config filename is named, state whether it is consumer policy, topology, argv/env flags, or runtime realm authority.

## Non-goals of this reconciliation

This document does not change current wire payloads, `SharedAuthTopology` v1, provider enablement, customer availability policy, the strict subsystem proof set, database schemas, open PR state, credentials, sessions, keys, DNS, or production data. Any of those requires its owning versioned contract, implementation, tests, rollout plan, and exact-revision evidence.
