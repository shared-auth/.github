# Shared Auth total-context audit — 2026-09-14

Status: evidence and reconciliation checkpoint  
Tracking: DEN-2193, DEN-606  
Scope: architecture, runtime docs, interface contracts, product docs, Linear planning, saved canonical-identity analysis, and current implementation/evidence boundaries

## Why this audit exists

Several generations of Shared Auth architecture were individually coherent but used overlapping words for different concerns. This audit cross-read the maintained sources instead of treating the newest document, the runtime README, or any single schema as globally authoritative.

The audit produced one canonical reconciliation document:

- `docs/AUTH-CONTEXT-PROOF-TAXONOMY-AND-SOURCE-PRECEDENCE.md`

That document should be read before older material using broad terms such as `dual auth`, `dual provider`, `dual proof`, `canonical authority`, or `organization`.

## Sources reviewed

### Organization architecture and policy

- `FEDERATED-DUAL-PROOF-ARCHITECTURE.md`
- `CANONICAL-IDENTITY-DATABASE-AND-RLS-MODEL.md`
- `ASYNC-AUTH-STATE-MACHINES-AND-FORMAL-VERIFICATION.md`
- `AUTH-DATA-PLANE-IMPLEMENTATION.md`
- `PROVIDER-RESOURCE-NAMING-AND-IDENTITY-TOPOLOGY.md`
- `AUTH-SHARED-TOPOLOGY-AND-ORCHESTRATION.md`
- `DEN-606-SHARED-AUTH-CONFIG-ROLLOUT.md`
- `PROJECTS.md`
- organization agent/repository policy

### Executable/runtime repository

- `shared-auth-server.rs/README.md`
- `docs/DESIGN.md`
- `docs/fiducia-dual-auth.md`
- `docs/auth-realms-and-federated-sso.md`
- `docs/identity-plane-authorization.md`
- `docs/runtime-realm-contract.md`
- `db/schema.sql`
- `config/auth-realms.contract.json`
- `.cli-flags.toml`
- `.auth-shared.toml`
- topology validator/test/evidence files
- current workflow execution state

### Interfaces/contracts

- `shared-auth-interfaces/README.md`
- `DUAL_PROVIDER_TOPOLOGY.md`
- `schema/auth-topology.schema.json`
- topology fixtures/tests
- `contracts/shared-auth-config/README.md`
- typed consumer-policy fixtures
- current interface repository provenance

### Published/product documentation

- `shared-auth-docs/docs/README.md`
- canonical architecture mirrors
- `docs/product/roadmap.md`
- `docs/product/parity-register.md`

### Planning/history

- canonical Shared Auth Linear project
- DEN-2189, DEN-2191, DEN-2193, DEN-2194, DEN-2197, DEN-3810, DEN-3812, DEN-606 and related material
- Linear architecture document for admin/customer data planes and federated customer SSO
- Linear edge/Supabase/Neon IaC/secrets/DR document

### Historical/personal saved context

A saved canonical-identity design analysis was reviewed for Supabase/Neon provider ownership, root-admin semantics, provider sessions, application accounts, revocation ordering, and product-authorization boundaries.

### Current implementation context

Open server/lib/interfaces/E2E work was reviewed to ensure the documentation taxonomy matches active implementation rather than inventing a theoretical split. In particular, current work already distinguishes Supabase+Neon provider-pair adjudication from the higher-level subsystem/application-grant transaction.

## Reconciled architecture

The system now documents five separate dimensions:

1. **realm** — customer vs admin;
2. **provider evidence** — native Shared Auth, Supabase, Neon, or another reviewed upstream provider;
3. **proof policy** — availability-first/reconcile, strict provider pair, or strict subsystem/application grant;
4. **canonical state/materialization** — one logical Shared Auth mutation authority, possibly materialized into several provider stores;
5. **product authorization** — product-local tenant/resource membership, roles, billing, entitlements and RLS.

These dimensions must not be collapsed because two of them happen to involve “two things.”

## Proof taxonomy result

### Ordinary customer continuity

Explicitly approved customer authentication/read paths may use availability-first or optimistic-with-reconciliation behavior. This never becomes admin/root authority or a different strict proof set merely because another verifier later succeeds.

### Strict Supabase + Neon provider pair

This is provider agreement for routes that explicitly require both provider lanes. Both exact identities must verify and resolve to the same canonical Shared Auth principal under the required realm/policy epoch.

### Strict subsystem/application grant

The accepted federation proof set remains independent native Shared Auth customer proof + federation-root Supabase proof + active application account + exact transaction/policy/revocation bindings until a new reviewed/versioned federation contract says otherwise.

A Neon proof does not silently substitute for one of those proofs.

## Identity vocabulary result

- cross-system canonical identity: `shared_user_id`;
- canonical provider tuple: `(provider, issuer, subject, realm)`;
- `provider_tenant` / `provider_subject` are transitional/compatibility representations where still present;
- `application_account_id` is application enrollment identity;
- public OIDC subjects should be pairwise/client-sector scoped when unlinkability is required;
- Shared Auth logical session identity is distinct from Supabase/Neon provider-native session IDs.

Email, phone, username, display name, provider display names, or other mutable profile/contact values never perform canonical linking.

## Root admin, identity-plane RBAC and product roles

These are three separate layers:

- sparse root-admin capability — global privileged Shared Auth authority;
- identity-plane RBAC — administration of Shared Auth directory/federation/credential/identity-organization surfaces;
- product roles — owned by each child product.

No product role implies Shared Auth root/identity-plane authority, and Shared Auth identity roles do not imply product access.

## Identity organizations versus product tenants

The product roadmap was reconciled so Shared Auth may add first-class **identity organizations** for enterprise SSO, SCIM, verified domains, identity policy, identity-service invitations and delegated Shared Auth administration.

That does not move child-product organizations/workspaces, memberships, roles, billing/resource grants, resources or product RLS into Shared Auth. Products may explicitly map a tenant to an identity organization by opaque stable ID, with no role implication in either direction.

## Logical organization placement versus provider display names

`SharedAuthTopology.githubOrg`, `runtimeOrg` and `targetOrg` are logical placement-owner keys. A provider resource may have a display name such as `shared-auth`, `ores-shared-auth`, or an immutable provider-generated identifier.

Runtime trust uses reviewed mappings plus immutable IDs/project refs/issuers, not display-name equality.

The existing topology v1 wire/deployment shape was not changed by this clarification.

## Critical config-authority collision found and corrected

This was the most consequential finding of the audit.

DEN-606 had already reserved:

```text
.shared-auth.toml  = canonical typed Shared Auth consumer policy
.auth-shared.toml  = migration-only compatibility alias for that policy
```

A later topology batch accidentally reused `.auth-shared.toml` as fleet/provider topology. That created two unrelated authorities under one filename.

The corrected boundary is:

```text
.shared-auth.toml                 consumer policy
.auth-shared.toml                 migration consumer-policy alias
config/shared-auth-topology.toml  fleet/provider/application topology
.cli-flags.toml                   argv/environment flags
config/auth-realms.contract.json  executable realm startup contract
```

The topology validator now rejects either reserved consumer-policy filename as a topology input and rejects topology-only sections found inside those reserved policy files.

The central server carries a minimal valid `.auth-shared.toml` compatibility-policy object, but does not currently claim to load that policy family at runtime. File presence is not runtime-adoption evidence.

## Source precedence result

No single document is globally authoritative.

- organization architecture owns realm/proof/canonical/product-authorization boundaries;
- `shared-auth-interfaces` owns versioned machine contracts and consumer-policy authored authorities;
- exact server/ORM revisions own executable runtime/schema state;
- `config/shared-auth-topology.toml` owns secret-free topology metadata, not runtime parsing;
- Linear owns planning/dependencies/history;
- GitHub exact revisions plus executed checks own implementation/evidence;
- product databases/contracts own product authorization.

A later document overrides an older one only for the same concern. It must not be used to override an older document that owns a different concern.

## Documents changed by this audit

### Canonical `.github`

- created `AUTH-CONTEXT-PROOF-TAXONOMY-AND-SOURCE-PRECEDENCE.md`;
- updated `AUTH-SHARED-TOPOLOGY-AND-ORCHESTRATION.md`;
- updated `DEN-606-SHARED-AUTH-CONFIG-ROLLOUT.md`;
- cleaned/reconciled `PROJECTS.md`;
- recorded planning clarification in Linear.

### `shared-auth-docs`

- published context/source-precedence mirror;
- published corrected topology/orchestration mirror;
- indexed the reconciliation document;
- rewrote the product roadmap's M3 as identity organizations with an explicit product-tenant boundary.

### `shared-auth-interfaces`

- clarified `DUAL_PROVIDER_TOPOLOGY.md` provider-pair versus subsystem-proof semantics;
- clarified logical placement-owner keys versus provider display names;
- clarified interface authority/provenance language in `README.md`.

### `shared-auth-server.rs`

- reconciled `docs/DESIGN.md`;
- reconciled `docs/fiducia-dual-auth.md`;
- reconciled `docs/auth-realms-and-federated-sso.md`;
- moved topology to `config/shared-auth-topology.toml`;
- restored `.auth-shared.toml` to consumer-policy compatibility semantics;
- hardened topology validation against future filename/authority collisions;
- expanded the test source from 25 to 28 cases;
- corrected the topology validation evidence chronology.

## Evidence status

### Executed before the filename correction

The original topology hardening revision executed:

```text
25 tests
OK
positive topology validation OK
both Procfile commands sh -n OK
```

### Executed during the correction

The exact corrected TOML contents were parsed and checked locally for the reserved-name boundary:

```text
TOML parse + reserved-filename boundary checks: OK
```

### Not yet exact-tree executed

The three newly added reserved-name unit cases bring the source suite to 28 cases, but the exact corrected private repository revision has not executed the full suite in an environment with repository bytes. The local container cannot resolve/clone GitHub, and the exact current hosted `repository-policy` job again received no runner and executed zero steps.

Therefore this audit does not claim `28/28` exact-head evidence yet.

## Known stale entry-point documentation

Two large documents still deserve a focused safe edit because replacing them through a contents-only integration without the full file is risky:

1. `shared-auth-server.rs/README.md` still contains older introductory/security wording such as coarse Shared Auth roles and `(provider, tenant, provider subject)` identity-key phrasing. The deeper server architecture docs now supersede that wording, but the README should receive a small semantic patch when edited from a full checkout.
2. `shared-auth-docs/docs/product/parity-register.md` still uses category-parity “organizations / memberships / roles” language that can be read as universal product RBAC. The roadmap now defines the intended narrower identity-organization model; the parity register should be updated from a full-file edit so the competitive matrix labels those entries as identity-organization capabilities.

These are documentation defects, not permission to reinterpret runtime/product authorization.

## Remaining implementation work discovered or confirmed

The audit did not mark these complete:

1. execute the expanded 28-case topology suite from the exact corrected revision;
2. implement/verify actual DEN-606 consumer-policy runtime adoption in the intended CLI/web/API/admin consumers;
3. migrate executable provider identity persistence to exact `(provider, issuer, subject, realm)` semantics where still transitional;
4. complete logical-session versus provider-session separation;
5. complete sparse root-admin capability migration/admission;
6. finish strict Supabase+Neon provider-pair adjudication in server/lib;
7. finish strict subsystem/application-grant implementation and formal refinement;
8. finish pairwise OIDC subject persistence/minting;
9. finish consent/logout/JWKS/revocation/provider federation work;
10. implement Supabase↔Neon canonical revision/event convergence checking and bounded repair;
11. implement provider OAuth-client materialization registry;
12. perform Neon Auth live-catalog certification only when compute start is explicitly approved;
13. finish intended Supabase/Neon admin/auth/canonical provider-plane provisioning where still target-only;
14. continuously prove private service schemas stay inaccessible to browser roles;
15. execute strict root-admin negative matrix;
16. execute child-product RLS compatibility fixtures;
17. reject stale canonical revision/revocation claims;
18. add contact-point provenance/versioning without making contacts identity keys;
19. attach writer/revision/event/idempotency identity to canonical mutations;
20. define/version the optional product-tenant ↔ Shared Auth identity-organization mapping contract;
21. extend fleet compliance to detect consumer-policy/topology authority collisions organization-wide;
22. add semantic mirror checks for canonical `.github` docs versus `shared-auth-docs` published copies without making the mirror an independent authority.

## CI / runner boundary

Current `shared-auth-server.rs` exact head after this audit is `5c6fe6b2338a369b4e23df1986aac73a398d5cef`.

Its `repository-policy` workflow run `34908399469` concluded failure with:

```text
steps: []
runner_id: 0
```

That is runner/allocation evidence, not repository-test execution. It is neither a code pass nor a code failure.

## Safety boundary

This audit did not mutate production schemas, provider projects/computes, credentials, signing keys, sessions, user accounts, DNS, or product authorization. It reconciled architecture/config authority, documentation, admission checks and planning context only.
