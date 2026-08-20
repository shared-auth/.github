# Federated dual-proof subsystem authentication

Status: accepted target design; implementation and production evidence remain open
Decision date: 2026-08-20
Linear architecture: [Admin/customer authentication data planes and federated customer SSO](https://linear.app/denman/document/admincustomer-authentication-data-planes-and-federated-customer-sso-8a7890cb3c82)
Contract issue: [DEN-3810](https://linear.app/denman/issue/DEN-3810/shared-auth-interfaceslib-publish-strict-dual-proof-federation)
Server/schema: [DEN-2193](https://linear.app/denman/issue/DEN-2193/shared-auth-server-add-realm-isolation-and-federated-customer)
E2E evidence: [DEN-2194](https://linear.app/denman/issue/DEN-2194/shared-auth-e2e-prove-cross-app-sso-audience-isolation-revocation-and)
Consumer rollout: [DEN-2197](https://linear.app/denman/issue/DEN-2197/shared-auth-rollout-migrate-consumers-and-remove-authentication)

## Executive decision

Shared Auth is the federation broker and OIDC provider. A user may enter a subsystem only after Shared Auth binds two current proofs to the same immutable federation principal:

1. an independently authenticated Shared Auth customer session; and
2. a valid session from the allowlisted parent Supabase Auth project.

This is a strict conjunctive policy:

    Shared Auth proof AND parent Supabase proof AND active application account

The existing dual-path verification race is an OR-style availability mechanism. It is not evidence of dual authentication and must never mint or refresh a strict subsystem grant.

Every subsystem has its own Supabase organization and at least one project per environment. The parent or master Supabase organization has a dedicated federation-root Auth project. Supabase organizations are management and billing boundaries; Supabase Auth users, JWT issuers, sessions, and signing keys are project-scoped. Runtime trust therefore keys on exact project issuers and subjects, never on an organization name or a dashboard account.

Shared Auth uses three PostgreSQL RDS data planes:

1. admin-auth RDS for operator identities and sessions;
2. customer-auth RDS for regular-user identities and the federation control plane;
3. application-data RDS for subsystem-local users, profiles, memberships, roles, and domain data.

The three-RDS count excludes the PostgreSQL databases managed inside Supabase projects.

User and email data may exist in several databases, but only as explicitly owned records or versioned projections. There is one writer for each field. Email is never a primary key, foreign key, recurring authentication join, or automatic account-link key.

## Non-negotiable invariants

1. The canonical federation key is an opaque UUID plus verified issuer/subject links.
2. A Supabase identity is keyed by exact project issuer and subject.
3. The root Supabase project is the only Supabase project whose proof can satisfy the parent proof requirement.
4. A Shared Auth session created only by exchanging that same Supabase proof does not count as an independent Shared Auth proof.
5. Both proofs are bound to one client, redirect URI, nonce, PKCE challenge, audience, scope request, browser transaction, and short expiry.
6. Missing, stale, invalid, revoked, mismatched, or unavailable proof denies new subsystem login and refresh.
7. Each subsystem gets an application-specific authorization code and audience-specific token or local Supabase session.
8. Cross-subsystem bearer-token reuse is rejected.
9. Global federation enrollment does not grant product roles, tenant membership, billing authority, or resource access.
10. Product authorization and fast domain joins stay in the subsystem's application database.
11. There are no cross-RDS foreign keys, synchronous SQL joins, foreign-data wrappers, or direct subsystem access to Shared Auth tables.
12. Password hashes, raw refresh tokens, OTP secrets, private signing keys, and Supabase service-role credentials are never copied between planes.
13. Customer authentication cannot create, unlock, recover, or promote an administrator.
14. Every replicated personal-data field has an authority, purpose, version, retention rule, and deletion/reconciliation path.

## Current implementation gap

This document is a target contract, not a description of current runtime behavior. Review of the current main revisions on 2026-08-20 found:

- shared-auth-lib dual-auth guards implement a first-success OR race, and a presented Shared Auth token can bypass evaluation of a Supabase proof;
- direct Supabase and Shared Auth exchange winners can produce different user identifiers for the same person;
- the server schema declares applications, application accounts, OAuth clients, consent, and session-to-application grants, but the active browser login path does not yet enforce that complete model;
- the current browser handoff returns an encrypted Supabase token bundle for later exchange rather than atomically producing a strict dual-proof federation session;
- the current realm contract assumes one Supabase project per realm and must be extended to distinguish one root proof project from registered subsystem projects;
- current provider tenancy can depend on a mutable configured project name; strict identity must migrate to the cryptographically verified issuer or immutable project ref plus subject;
- current delegated claims expose global/provider compatibility identifiers and need a versioned pairwise-subject migration;
- current client and E2E introspection request shapes have drifted from the server's strict request contract;
- existing federation E2E tests model token minting and verification but do not yet prove the deployed browser-to-server-to-database flow.

No current OR/race, handoff, exchange, or synthetic test result may be represented as satisfying this design. DEN-3810, DEN-2193, and DEN-2194 own the contract, runtime, and executable-evidence gaps.

## Supabase organization and project topology

### Current management topology

The parent and subsystem organizations may initially be administered by the same Supabase account owners:

    current Supabase owner accounts
      |
      +-- shared-auth-federation organization
      |     +-- federation-root-prod project
      |     +-- federation-root-staging project
      |
      +-- subsystem-a organization
      |     +-- subsystem-a-prod project
      |     +-- subsystem-a-staging project
      |
      +-- subsystem-b organization
            +-- subsystem-b-prod project
            +-- subsystem-b-staging project

The account is not a runtime trust anchor. Shared Auth stores allowlisted, non-secret project metadata and validates exact project issuers and JWKS.

### Long-term management topology

The parent organization should ultimately have dedicated owner accounts and recovery controls:

    dedicated federation owner accounts
      +-- shared-auth-federation organization

    subsystem/platform owner accounts
      +-- subsystem-a organization
      +-- subsystem-b organization

Supabase supports adding another owner before the current owner leaves an organization. The ownership transition must be rehearsed and audited. It should not require an identity migration when the organization and project remain in place. If a plan or operational constraint requires a new project, the new project has a new issuer and must use the explicit provider-link migration procedure.

### Supabase management controls

- Use separate organizations even while owner membership overlaps.
- Require MFA on every owner account and keep at least two governed recovery paths.
- Use project-scoped roles where the Supabase plan supports them.
- Do not use a shared human login.
- Do not put personal access tokens or Management API credentials in application runtimes.
- Give each environment a distinct project, callback allowlist, signing-key lifecycle, and secret set.
- Store project refs, issuers, JWKS locations, environment, application owner, and status in the federation registry; store credentials only in the approved secret manager.
- A subsystem project token cannot be substituted for the root project token.
- Organization membership, project ownership, billing state, and dashboard email are never human-federation identifiers.

## Three-RDS topology

    ADMIN PLANE
    admin clients
        -> shared-auth-admin
        -> admin-auth RDS
           admin principals, factors, sessions, recovery,
           operator grants, revocation, audit, outbox

    CUSTOMER / FEDERATION PLANE
    root Supabase Auth project ----+
                                    |
    Shared Auth native login -------+-> shared-auth-customer
                                          -> customer-auth RDS
                                             principals, provider links,
                                             applications, application accounts,
                                             proof sets, sessions, OIDC clients,
                                             grants, revocation, audit, outbox

    SUBSYSTEM PLANES
    subsystem Supabase project
        -> local Supabase Auth session and optional browser RLS identity
        -> subsystem BFF/API
        -> application-data RDS
           subsystem-local users, profiles, tenant membership,
           roles, billing/domain data, event inbox

The admin and customer RDS instances have different network paths, KMS keys, database credentials, backup policies, restore drills, connection budgets, deployment identities, issuers, signing keys, cookies, and audit streams.

The application-data RDS instance is a separate failure and capacity plane from authentication. If several subsystems share that instance, use a separate PostgreSQL database per subsystem where operational tooling permits. Otherwise use a separate schema, owner role, runtime role, migration role, connection pool, and secret per subsystem. Revoke all cross-subsystem grants.

This three-instance design isolates authentication from domain workload. It does not provide full subsystem-to-subsystem database failure isolation. A high-risk or high-volume subsystem can later move its database to another RDS instance without changing the federation protocol.

## Authority matrix

| Data or decision | Parent Supabase project | Customer-auth RDS | Subsystem Supabase project | Application-data RDS | Admin-auth RDS |
|---|---|---|---|---|---|
| Root password, magic link, social login, Supabase MFA | owns | never copies secrets | does not own root credential | does not own | does not own |
| Root Supabase subject and session | owns | stores verified link and bounded proof metadata | does not become canonical | optional non-authoritative reference only | never copied |
| Federation principal | upstream evidence only | owns | receives pairwise subject | stores local mapping/projection | separate namespace |
| Shared Auth native credential/factor | does not own | owns customer factor/session | does not own | does not own | owns separate admin factor/session |
| Dual-proof set and federation session | evidence source | owns | consumes broker result | may cache opaque session/account refs | never shared |
| Application enrollment and client registration | does not imply | owns | configured as one client/provider boundary | may cache enrollment status | admin clients are separate |
| Subsystem local user ID | does not own | does not own | owns local auth.users ID when used | owns domain user UUID and mapping | does not own |
| Email | root credential source | owns selected verified contact and provenance | may hold OIDC-created snapshot | optional versioned projection | separate admin contact |
| Product tenant, role, billing, resource grants | does not own | does not centralize | RLS may consume local claims | owns | does not own |
| Revocation | root-session source | owns federation epoch/session revocation | owns local session termination | owns local suspension/session | owns admin revocation |

## Identity model

### Canonical identifiers

Use four distinct identifier layers:

1. principal_id: internal global customer identity in customer-auth RDS.
2. external identity: exact issuer plus subject, linked to one principal.
3. application_account_id: one principal's enrollment in one application.
4. local_user_id: subsystem-owned UUID used by local foreign keys and fast joins.

Each application or OIDC sector receives a pairwise subject. The broker can correlate it to principal_id; other subsystems cannot.

The application database stores the application-scoped identity, not a reusable global email key. It may store application_account_id as an opaque event and reconciliation reference.

### Email rule

Email is a mutable verified contact attribute. It is useful for:

- delivering a login or recovery message under the owning authority's policy;
- displaying a profile field;
- finding an invitation candidate;
- a one-time, human-visible migration hint;
- support search under an audited and rate-limited procedure.

Email is not suitable for:

- a users table primary key;
- a foreign key from domain records;
- linking a Shared Auth principal to a Supabase user;
- recurring login reconciliation;
- granting membership or roles;
- automatically merging two accounts;
- identifying an administrator and customer as the same account.

If two verified proofs contain the same email but different issuer/subject pairs, they remain separate identities until a recent dual-proof linking ceremony succeeds. If an email changes while issuer and subject remain unchanged, the identity link remains and only the contact projection changes.

## Customer-auth RDS schema

The following is an ownership sketch. The exact schema belongs in the declarative shared-auth-server.rs database source and is applied outside application startup.

### Federation principals and provider links

    federation.principals (
      principal_id uuid primary key,
      status text not null,
      auth_epoch bigint not null,
      identity_version bigint not null,
      created_at timestamptz not null,
      updated_at timestamptz not null
    )

    federation.external_identities (
      external_identity_id uuid primary key,
      principal_id uuid not null references federation.principals,
      authority text not null,
      issuer text not null,
      subject text not null,
      provider_tenant text not null,
      link_state text not null,
      linked_at timestamptz not null,
      last_authenticated_at timestamptz,
      unique (issuer, subject)
    )

The parent Supabase identity is one external identity. A Shared Auth native credential is a separate credential/factor bound to the same principal, not a second row created from email equality.

provider_tenant is an immutable project ref or a value derived from the cryptographically verified issuer. A mutable display name, registry alias, organization slug, or dashboard project name cannot participate in the uniqueness key.

### Contact points

    federation.contact_points (
      contact_id uuid primary key,
      principal_id uuid not null references federation.principals,
      kind text not null,
      normalized_value text not null,
      display_value text not null,
      verified_at timestamptz,
      source_external_identity_id uuid,
      status text not null,
      version bigint not null,
      created_at timestamptz not null,
      updated_at timestamptz not null
    )

Do not make normalized_value the identity key. A separate reviewed policy may enforce that one active primary email is claimed by at most one principal, but a uniqueness conflict must quarantine or reject the claim; it must never trigger an account merge.

The current principals.email column can remain as a compatibility projection during migration. New authentication and linking code must stop depending on its uniqueness before any later schema cleanup is considered.

### Supabase project registry

    federation.supabase_projects (
      project_ref text primary key,
      organization_ref text not null,
      issuer text not null unique,
      jwks_uri text not null,
      environment text not null,
      project_role text not null,
      application_id uuid,
      status text not null,
      reviewed_at timestamptz not null
    )

project_role distinguishes federation_root from subsystem. Only a federation_root project may provide the mandatory parent Supabase proof. No API keys, JWT secrets, private keys, or Management API tokens belong in this table.

### Applications, accounts, sectors, and clients

    federation.applications (
      application_id uuid primary key,
      application_key text not null unique,
      status text not null,
      enrollment_policy text not null
    )

    federation.application_accounts (
      application_account_id uuid primary key,
      application_id uuid not null references federation.applications,
      principal_id uuid not null references federation.principals,
      status text not null,
      profile_version bigint not null,
      unique (application_id, principal_id)
    )

    federation.subject_sectors (
      sector_id uuid primary key,
      application_id uuid not null references federation.applications,
      sector_identifier text not null unique
    )

    federation.pairwise_subjects (
      sector_id uuid not null references federation.subject_sectors,
      principal_id uuid not null references federation.principals,
      pairwise_subject text not null,
      primary key (sector_id, principal_id),
      unique (sector_id, pairwise_subject)
    )

    federation.oidc_clients (
      client_id text primary key,
      application_id uuid not null references federation.applications,
      sector_id uuid not null references federation.subject_sectors,
      subsystem_project_ref text,
      exact_redirect_uris jsonb not null,
      exact_audiences jsonb not null,
      allowed_scopes jsonb not null,
      client_type text not null,
      require_pkce boolean not null,
      status text not null
    )

Web, mobile, desktop, CLI, BFF, and subsystem Supabase OIDC callbacks are separate registered clients unless they intentionally share a reviewed subject sector.

### Proofs and binding

    federation.authentication_proofs (
      proof_id uuid primary key,
      principal_id uuid not null references federation.principals,
      authority text not null,
      external_identity_id uuid,
      source_session_ref_hash text not null,
      evidence_hash text not null,
      auth_time timestamptz not null,
      expires_at timestamptz not null,
      assurance_level text not null,
      auth_methods jsonb not null,
      status text not null,
      created_at timestamptz not null
    )

    federation.proof_sets (
      proof_set_id uuid primary key,
      principal_id uuid not null references federation.principals,
      shared_auth_proof_id uuid not null unique,
      root_supabase_proof_id uuid not null unique,
      policy_version text not null,
      bound_at timestamptz not null,
      expires_at timestamptz not null,
      revoked_at timestamptz
    )

    federation.authorization_transactions (
      transaction_id uuid primary key,
      client_id text not null references federation.oidc_clients,
      proof_set_id uuid,
      redirect_uri text not null,
      state_hash text not null,
      nonce_hash text not null,
      pkce_challenge text not null,
      requested_audience text not null,
      requested_scopes jsonb not null,
      browser_binding_hash text not null,
      created_at timestamptz not null,
      expires_at timestamptz not null,
      consumed_at timestamptz
    )

Persist hashes or opaque references, not raw bearer, refresh, authorization, or proof tokens. A transaction receives exactly one valid proof set. The proof-set expiry is no later than the earlier underlying proof expiry or the policy freshness deadline.

### Sessions, grants, revocation, and events

    federation.sessions (
      session_id uuid primary key,
      principal_id uuid not null references federation.principals,
      proof_set_id uuid not null references federation.proof_sets,
      auth_epoch bigint not null,
      refresh_token_hash text unique,
      created_at timestamptz not null,
      expires_at timestamptz not null,
      revoked_at timestamptz
    )

    federation.application_grants (
      grant_id uuid primary key,
      session_id uuid not null references federation.sessions,
      application_account_id uuid not null references federation.application_accounts,
      client_id text not null references federation.oidc_clients,
      audience text not null,
      scopes jsonb not null,
      created_at timestamptz not null,
      expires_at timestamptz not null,
      revoked_at timestamptz
    )

    federation.outbox_events (
      event_id uuid primary key,
      aggregate_type text not null,
      aggregate_id uuid not null,
      aggregate_version bigint not null,
      application_id uuid,
      event_type text not null,
      payload jsonb not null,
      occurred_at timestamptz not null,
      published_at timestamptz,
      unique (aggregate_type, aggregate_id, aggregate_version)
    )

    federation.audit_events (
      audit_id uuid primary key,
      actor_ref uuid,
      principal_ref uuid,
      session_ref uuid,
      client_id text,
      event_type text not null,
      outcome text not null,
      bounded_reason text,
      correlation_id uuid not null,
      occurred_at timestamptz not null
    )

Audit and metrics use opaque references and bounded enums. Raw email, provider subject, tokens, cookies, secrets, and arbitrary error bodies are excluded.

## Admin-auth RDS schema boundary

Admin Auth has an analogous but separate set of:

- admin principals;
- workforce-provider links;
- native factors and recovery records;
- devices and sessions;
- operator invitations and grants;
- admin clients and exact audiences;
- revocation epochs;
- privileged audit and outbox events.

It has no foreign key to customer-auth RDS. If a person has both accounts, any association is an explicit audited record using opaque references and has no authentication, enrollment, recovery, or role-propagation effect.

Admin Auth must not read customer application accounts to decide operator access. Customer Auth must not read admin grants. A customer email match never creates or promotes an admin identity.

## Application-data RDS schema

Each subsystem owns a local users table in the same PostgreSQL database or schema as its domain tables. All product foreign keys point to local_user_id, which provides fast, ordinary local joins.

    subsystem.users (
      local_user_id uuid primary key,
      federation_issuer text not null,
      federation_subject text not null,
      application_account_id uuid not null,
      subsystem_supabase_user_id uuid,
      status text not null,
      primary_email text,
      email_verified_at timestamptz,
      identity_version bigint not null,
      source_version bigint not null,
      created_at timestamptz not null,
      updated_at timestamptz not null,
      unique (federation_issuer, federation_subject),
      unique (application_account_id),
      unique (subsystem_supabase_user_id)
    )

    subsystem.identity_event_inbox (
      event_id uuid primary key,
      aggregate_version bigint not null,
      event_type text not null,
      payload_hash text not null,
      received_at timestamptz not null,
      applied_at timestamptz,
      failure_reason text
    )

    subsystem.memberships (
      membership_id uuid primary key,
      local_user_id uuid not null references subsystem.users,
      tenant_id uuid not null references subsystem.tenants,
      role_id uuid not null references subsystem.roles,
      status text not null
    )

application_account_id is a logical remote reference, not a PostgreSQL foreign key. Product roles and memberships reference local_user_id only.

If a subsystem uses its own Supabase Auth project, subsystem_supabase_user_id maps the project-local auth.users ID to the same local user. The mapping is established from the verified Shared Auth OIDC issuer and pairwise subject. It is never established from the local Supabase email.

## Subsystem Supabase integration

### Recommended path for browser/RLS consumers

Configure Shared Auth as a custom OIDC provider in each subsystem Supabase project:

1. The subsystem starts sign-in through its own Supabase project using the registered Shared Auth OIDC provider.
2. Supabase redirects to Shared Auth with the subsystem-specific OIDC client.
3. Shared Auth creates a short-lived authorization transaction.
4. Shared Auth validates a current native Shared Auth customer session.
5. Shared Auth validates a current parent Supabase project proof.
6. Shared Auth confirms both immutable identities resolve to the same principal.
7. Shared Auth checks the independent application account, invitation/consent policy, and requested client.
8. Shared Auth issues a one-use code and OIDC result with an application-pairwise subject and strict dual-proof authentication context.
9. The subsystem Supabase project validates Shared Auth discovery, issuer, JWKS, signature, nonce, code, and PKCE, then creates or resolves its project-local Auth user and session.
10. The subsystem BFF idempotently creates or resolves its application-data RDS user from the verified issuer/subject and application account.

The production gate must prove how the validated upstream subject and strict authentication context are preserved or rechecked when the local Supabase token is issued. If the project cannot carry trustworthy upstream identity and assurance into the BFF or an approved server-side mapping hook, the custom-OIDC path is not production-eligible; use the direct BFF path.

### Direct BFF path

A subsystem that does not need a browser-held Supabase session can register its BFF directly with Shared Auth:

1. Authorization Code plus PKCE terminates at the BFF.
2. The BFF validates the dual-proof OIDC result.
3. The BFF creates its own host-only product session.
4. Server-side product access to Supabase or application data uses a narrowly scoped service identity and product-local authorization.

The direct path avoids duplicating a browser identity in the subsystem Supabase project. It does not weaken the dual-proof requirement.

### Prohibited path

Subsystems do not accept a Shared Auth bearer and a Supabase bearer, compare their email claims, and choose a result. They do not use the first successful verifier to mint a strict session. They do not pass parent Supabase access or refresh tokens through browser URLs.

## Strict login transaction

### First link or enrollment

1. Start with exact state, nonce, redirect URI, audience, scopes, and PKCE S256.
2. Require recent independent Shared Auth authentication.
3. Require recent parent Supabase authentication.
4. Verify Supabase algorithm, signature, exact issuer, audience, expiry, not-before, session, subject, and required assurance.
5. Resolve the Supabase issuer/subject link.
6. If no link exists, require an explicit linking ceremony that proves current control of both identities, displays the intended accounts, expires quickly, and is replay-safe.
7. Reject a link when either external identity is already linked to another principal.
8. Treat email equality only as a confirmation hint or invitation rule.
9. Bind both proofs into one proof_set transactionally.
10. Check application-account and consent/invitation state.
11. Mint one opaque, short-lived, single-use authorization code.
12. Exchange it for an application-specific result.
13. Idempotently create the local user by application account and issuer/subject.
14. Resolve tenant, membership, role, billing, and resource authorization locally.

### Returning SSO

When a user enters App B after App A:

- App B starts a new authorization request.
- Shared Auth may reuse the central customer session and parent Supabase proof only while each is still active and fresh enough for App B policy.
- Shared Auth checks App B's separate application account and consent/invitation.
- App B receives a newly minted App-B code/token or local Supabase session.
- App A and App B never share bearer tokens or product cookies.

### Failure matrix

| Shared Auth proof | Parent Supabase proof | Immutable link | Application account | Result |
|---|---|---|---|---|
| valid/fresh | valid/fresh | same principal | active | issue application-bound code |
| missing or stale | valid | any | any | interaction required; no grant |
| valid | missing or stale | any | any | interaction required; no grant |
| invalid or revoked | any | any | any | deny |
| any | invalid or revoked | any | any | deny |
| valid | valid | different principals | any | deny and bounded audit |
| valid | valid | same email only, no link | any | link ceremony or deny |
| unavailable | valid | any | any | degraded; deny new login/refresh |
| valid | unavailable | any | any | degraded; deny new login/refresh |
| valid | valid | same principal | suspended/missing | deny or enrollment flow |

An already-issued short-lived local session may continue only until its documented expiry and revocation bound. An outage never creates a new strict session from one proof.

## Token and session contract

The Shared Auth OIDC result contains bounded claims:

    iss        exact customer realm issuer
    sub        pairwise application/sector subject
    aud        exact subsystem client or API audience
    azp        exact authorized client
    sid        opaque federation session identifier
    iat/nbf/exp bounded token lifetime
    auth_time  completion time of the older required proof
    acr        urn:shared-auth:acr:dual-proof:v1
    amr        bounded methods including shared-auth and root-supabase
    proof_ver  versioned strict-proof policy
    acct       opaque application-account reference
    idv        identity/contact projection version

Email is omitted by default. A client receives email and email_verified only when its approved scope and data-minimization policy require them.

Do not expose the root Supabase subject, raw provider tokens, global principal ID, product roles, or other applications' enrollment in subsystem tokens.

Access and ID tokens are short-lived. Refresh-token rotation, reuse detection, proof freshness, auth_epoch, principal status, application-account status, and underlying proof expiry bound refresh. Sensitive operations use authenticated introspection or step-up.

## Replication and consistency

### Single-writer rule

| Field | Authoritative writer | Other copies |
|---|---|---|
| Root Supabase credential email and session | parent Supabase project | customer-auth and enrolled subsystem projections |
| Federation principal status and identity links | customer-auth RDS | opaque local projections |
| Shared Auth native factors and federation sessions | customer-auth RDS | never copied |
| Admin identity/factor/session | admin-auth RDS | never copied to customer/app planes |
| Subsystem local profile | owning subsystem | optional display copy elsewhere only by explicit contract |
| Tenant membership, role, billing, resources | owning subsystem application DB | bounded token/cache views only |
| Subsystem Supabase auth.users ID/session | subsystem Supabase project | local mapping only |

No field is resolved by last-write-wins across systems.

### Outbox and inbox

Customer Auth writes a state change and its outbox event in the same database transaction. Delivery is at least once. Each subsystem:

- deduplicates by event_id;
- applies only the next aggregate version;
- detects version gaps and invokes reconciliation;
- records the payload hash and apply outcome;
- can replay after restore;
- never authorizes solely from an unverified event;
- receives events only for its enrolled application accounts.

Events carry pairwise/application-scoped references. Personal data is minimized, encrypted in transit, access-controlled, and omitted when the subsystem does not need it.

### Email updates

1. The parent Supabase project verifies an email change under its policy.
2. Shared Auth revalidates the exact root issuer/subject and updates the contact point and identity_version.
3. A versioned application-scoped event is emitted only to enrolled applications that require the email.
4. The subsystem updates its projection if the version is newer.
5. Authentication remains keyed by immutable issuer/subject throughout.

Email delivery failures or stale projections do not change identity. A product may own a separate billing/support email; that field is not overwritten by an auth-contact event.

### Disablement and deletion

Principal disablement advances auth_epoch before best-effort fan-out. New grants and refresh fail immediately at Shared Auth. Subsystems receive suspension/logout events and enforce their documented local revocation SLO.

Deletion is a governed state machine, not an unbounded distributed DELETE. Each authority applies its legal retention and tombstone rules, records completion, and supports reconciliation without resurrecting deleted accounts from a stale projection.

### Backup and restore

The three RDS instances restore independently. Cross-database snapshots are not assumed to be transactionally consistent.

- Customer-auth RDS is authoritative for federation state and outbox history.
- Application projections rebuild from retained events and a signed reconciliation endpoint.
- Inbox deduplication makes replay safe after an application restore.
- Outbox retention and snapshots must cover the maximum recovery window.
- Admin restore never depends on customer or application restore.
- Restore drills prove that no stale application projection can mint identity authority.

## Network, roles, and operations

Each RDS instance has:

- private network placement and TLS-required connections;
- its own KMS key, secrets, backup/PITR policy, deletion protection, and restore drill;
- separate migration, runtime, audit-reader, support, and backup roles;
- a bounded connection pool and capacity budget;
- no use of the RDS master credential by application runtimes;
- declarative schema application outside server startup;
- independent metrics, alerts, runbooks, and SLOs.

Within application-data RDS, every subsystem has:

- a separate database or schema owner;
- a least-privilege runtime role;
- an independent migration role and secret;
- an independent connection pool and statement timeout;
- no USAGE, CONNECT, or table grants to sibling subsystem namespaces beyond an explicit reviewed shared-data contract.

Normal product requests validate local tokens and perform local user/authorization joins. They do not query customer-auth RDS. Immediate federation revocation is obtained through authenticated introspection or bounded revocation events, not direct SQL.

## Threat model

The implementation and E2E suite must cover:

- Alice's Shared Auth session combined with Bob's Supabase proof;
- a subsystem Supabase token substituted for the parent project token;
- a Shared Auth token derived solely from the same Supabase proof presented as independent proof;
- same-email/different-subject collision, email change, alias reuse, and deleted/recreated Supabase user;
- concurrent link attempts and uniqueness races;
- login CSRF, session fixation, open redirect, state/nonce/PKCE swapping, and code/proof replay;
- wrong issuer, audience, algorithm, key, project, client, redirect, or subject sector;
- App-A token used at App B;
- compromised subsystem client attempting to mint for another subsystem;
- stale JWKS, key rotation, provider outage, timeout, and late verifier completion;
- outbox duplication, reordering, loss, replay, and restore gaps;
- local role or membership suspension while federation identity remains active;
- federation-wide signing-key compromise;
- accidental owner-account overlap between parent and subsystem Supabase organizations;
- PII or token leakage through logs, traces, metrics, support tools, or dead-letter queues.

Two account sign-ins are not automatically two independent authentication factors. If both accounts recover through the same mailbox or provider, compromise is correlated. Any policy that intends MFA-level assurance must require an independent phishing-resistant factor such as a Shared Auth passkey and encode that requirement separately.

## Migration and rollout

### Phase 0: inventory and decisions

- Inventory Supabase organizations, projects, refs, issuers, owners, environments, callbacks, and signing-key types.
- Inventory admin, customer, and application PostgreSQL tables and every email/user foreign key.
- Classify each field by authoritative writer and retention policy.
- Decide which subsystems need a browser-held Supabase session and which use direct BFF OIDC.
- Baseline auth/application DB queries, connections, p95/p99, login/refresh volume, and restore objectives.

### Phase 1: additive central schema

- Add project registry, application-account IDs, subject sectors, pairwise subjects, strict proofs/proof sets, transaction binding, outbox, and audit.
- Keep compatibility columns while all readers move to immutable identifiers.
- Publish DEN-3810 interfaces and strict SDK guard behavior.
- Ensure the old OR/race result cannot satisfy the new policy.

### Phase 2: parent Supabase and Shared Auth linking

- Register the exact federation-root project and asymmetric JWKS.
- Require dual reauthentication for first link.
- Quarantine collisions; do not bulk auto-link on email.
- Add recovery, unlink/relink, notifications, cooldown, and operator dual-control procedures.

### Phase 3: first subsystem pilot

- Create the subsystem Supabase organization/project and exact OIDC client.
- Add the subsystem-local users mapping and event inbox.
- Migrate local foreign keys to local_user_id.
- Use one-time dual-proof enrollment to bind legacy rows.
- Run shadow comparisons without authorizing from email or shadow state.

### Phase 4: second subsystem and SSO proof

- Register a second application with a different audience and pairwise subject.
- Prove central-session convenience with new application-specific issuance.
- Prove cross-audience denial, independent enrollment/suspension, email change, revocation, outage, and restore behavior.

### Phase 5: fleet rollout

- Migrate one subsystem at a time.
- Keep a per-product rollback switch to the last reviewed authentication path.
- Remove legacy auth reads/writes and email joins only after observation and rollback windows.
- Promote high-volume or high-risk product databases to separate RDS instances when measured isolation needs justify it.

### Phase 6: Supabase parent-owner separation

- Add dedicated federation owner accounts and require MFA.
- Verify accepted ownership, recovery, billing, audit, GitHub integration, and Management API automation.
- Remove broad overlapping owner access only through the approved human-run procedure.
- Prove project refs, issuers, callbacks, JWKS, secrets, and runtime behavior are unchanged.

No phase is complete merely because its documentation or schema merged. Exact-revision CI, deployed negative tests, restore evidence, and rollback evidence are required where applicable.

## Minimum acceptance suite

### Identity and linking

- both proofs for the same linked principal succeed;
- either proof alone fails;
- two valid proofs for different principals fail;
- same verified email with different subjects does not link;
- changed email with unchanged issuer/subject preserves the account;
- deleted/recreated Supabase user with a new subject requires relinking;
- concurrent link attempts produce one deterministic mapping;
- local user upsert is idempotent by issuer/subject and application account.

### Protocol

- exact issuer, signature, algorithm, kid, audience, azp, expiry, not-before, auth_time, acr, and proof policy are enforced;
- state, nonce, PKCE, redirect URI, authorization code, proof handle, and browser binding cannot be swapped or replayed;
- App A rejects App B tokens and local sessions;
- a subsystem project cannot impersonate the federation-root project;
- raw Supabase tokens never appear in URLs, logs, traces, metrics, or application tables.

### Authorization

- authenticated but uninvited users are denied when enrollment is gated;
- suspended application account blocks only that subsystem;
- disabled global principal blocks all customer subsystems;
- product tenant, role, billing, and resource checks remain local;
- admin/customer cross-realm credentials and cookies are mutually rejected.

### Failure and operations

- either authority outage denies new strict login/refresh;
- existing local-session behavior matches its documented short revocation bound;
- revocation, logout, email change, and disablement events are idempotent and ordered;
- independent admin/customer/application restores pass;
- application restore followed by event replay does not duplicate or resurrect a user;
- parent Supabase ownership separation is rehearsed without runtime identity drift.

## Repository and planning ownership

| Workstream | Repository | Linear |
|---|---|---|
| Organization architecture and routing | shared-auth/.github | DEN-2189 |
| Versioned identity/proof/guard contract | shared-auth-interfaces, shared-auth-lib | DEN-3810 |
| Federation server, OIDC, schema, sessions, linking | shared-auth-server.rs | DEN-2193 |
| RDS, network, secrets, backup, restore | shared-auth-infra | DEN-2191 |
| Cross-project, cross-RDS, outage, replay, restore tests | shared-auth-e2e and shared-auth-test | DEN-2194 |
| Per-subsystem migration and local data ownership | owning product repositories | DEN-2197 plus product issues |

## Standards and platform references

- [OpenID Connect Core 1.0](https://openid.net/specs/openid-connect-core-1_0-errata2.html) defines stable and pairwise subject identifiers, nonce, authentication context, and authorization-code behavior.
- [OAuth 2.0 Security Best Current Practice](https://www.rfc-editor.org/rfc/rfc9700.html) defines current redirect, mix-up, CSRF, and authorization-code protections.
- [PKCE](https://www.rfc-editor.org/rfc/rfc7636.html) defines proof-key binding for authorization codes.
- [Supabase JWT claims](https://supabase.com/docs/guides/auth/jwt-fields) documents project-scoped issuers, subjects, session IDs, assurance, and authentication methods.
- [Supabase custom OIDC providers](https://supabase.com/docs/guides/auth/custom-oauth-providers) documents OIDC discovery, JWKS validation, callbacks, and provider PKCE.
- [Supabase access control](https://supabase.com/docs/guides/platform/access-control) documents organization ownership and organization/project-scoped member roles.

## Final decision summary

The federation is conventional OIDC brokerage with strong data-plane separation:

- root Supabase authenticates the parent Supabase identity;
- Shared Auth independently authenticates and binds the human federation principal;
- customer-auth RDS owns global customer identity, linking, sessions, enrollment, and grants;
- each subsystem receives only an application-scoped identity;
- each subsystem keeps a local user row beside its product data for fast joins;
- email can be copied where needed but never carries identity authority;
- admin identities remain in a separate RDS realm;
- the same Supabase owner accounts may administer all organizations temporarily, while the runtime contract is already ready for later parent-owner separation.
