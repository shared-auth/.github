# Provider resource naming and identity regression matrix

Status: required regression coverage  
Decision date: 2026-09-14  
Owner: Shared Auth  
Tracking: DEN-2191, DEN-2193, DEN-2194  
Normative policy: [Provider resource naming and Shared Auth identity topology](PROVIDER-RESOURCE-NAMING-AND-IDENTITY-TOPOLOGY.md)

The alias policy is security-sensitive because provider display names are convenient discovery metadata but are not canonical identity. Tests must prove both interoperability and fail-closed ambiguity handling.

## Required matrix

| Case | Expected result |
| --- | --- |
| Supabase resource is named `shared-auth` and immutable project ref matches reviewed mapping | accept |
| Supabase resource is named `ores-shared-auth` and immutable project ref matches reviewed mapping | accept |
| Neon resource is named `shared-auth` and immutable project ID matches reviewed mapping | accept |
| Neon resource is named `ores-shared-auth` and immutable project ID matches reviewed mapping | accept |
| Cloudflare edge resource uses either reviewed alias with immutable account/zone/worker ID | accept as edge infrastructure only |
| only a display name is available, with no immutable provider ID/ref | fail closed |
| two resources share the same provider + plane + display alias and no reviewed immutable mapping disambiguates them | fail closed |
| provider display name changes while issuer + subject + realm stay the same | canonical `shared_user_id` binding does not change |
| Supabase/Neon `auth`, `admin`, or `canonical` plane is substituted for another plane | fail closed |
| Cloudflare claims identity-authority or canonical-database status | fail closed |
| provider resource name is used as an identity key | fail closed |
| email/phone/name is used to reconcile two provider identities | fail closed |
| admin request has only one valid provider proof | deny privileged operation |
| ordinary customer optimistic session receives a later authoritative revocation | monotonic transition to revoked; no resurrection |
| child app role exists in one application but not another | role grants nothing outside the owning child app |

## Machine-enforced coverage

`shared-auth/shared-auth-infra` owns the secret-neutral provider-resource mapping contract and validator. CI must cover the two accepted display aliases, immutable-ID requirement, ambiguity rejection, plane completeness, Cloudflare non-authority, and canonical identity-key invariants.

`shared-auth/shared-auth-orm-core` owns typed runtime database capability selection. Rust tests must distinguish logical GitHub organization identity from provider resource display names and must include the `canonical` plane in addition to customer/admin auth planes.

`shared-auth-test` remains the correct location for live cross-provider and end-to-end evidence. Unit/contract tests in policy repositories do not claim that a live provider inventory is correctly provisioned.

## Evidence rule

A passing alias test is not permission to select resources by display name at runtime. Runtime evidence must record the immutable provider ID/reference, resolved logical system, provider, logical plane/role, issuer where applicable, release/schema marker, and configuration generation. If the resolver cannot produce an unambiguous mapping, it must stop rather than guess.
