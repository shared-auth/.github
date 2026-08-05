# DEN-2259 — shared-auth delivery map for MemeBank and ClipTown

Linear `DEN-2259` is the authoritative cross-organization delivery issue. shared-auth owns factor mediation, normalized assurance, delegated-token issuance, protected introspection, session revocation, and official clients. It does not own ClipTown resource state or MemeBank product actions.

## Product boundary

MemeBank must never call a 3FA backend, import a 3FA service SDK, validate a factor-app proof, probe an installed mobile application, or deep-link into 3FA for authorization. shared-auth verifies configured factors and exposes only normalized identity, session, role, scope, `aal`, `acr`, `amr`, and `auth_time` claims.

For ClipTown interoperability, MemeBank exchanges its normal shared-auth user token for a short-lived delegated token. The configured tuple is:

- client: `memebank-api`
- audience: `cliptown-api`
- scopes: exactly one of `cliptown:memebank:read`, `cliptown:memebank:write`, or `cliptown:memebank:delete`
- recent LOA2: required for write and delete

A delegated token receives a new `jti`, preserves the revocation-aware session and assurance provenance, records `parent_jti`, is capped by both parent expiry and policy TTL, and cannot be recursively delegated.

## Active GitHub work

| Order | Repository item | shared-auth deliverable | Gate |
|---:|---|---|---|
| 1 | `shared-auth/shared-auth-server.rs#38` | Return the current delegated `jti` as well as `parent_jti` from successful protected exact-audience introspection. | Independent introspection credential required; inactive response remains minimal; format, Clippy, tests, locked release build. |
| 2 | `shared-auth/shared-auth-clients#34` | Official Rust client method for exact-audience protected introspection plus complete delegated claims and lineage. | HTTPS outside loopback, no redirects, bounded bodies, malformed input before transport, credential only on introspection. |
| 3 | `cliptown/cliptown-rust-backend.rs#8` | Consume the official transport and apply ClipTown authorization/persistence. | Depends on the two shared-auth contracts above. |
| 4 | `memebank/mbk-rest-api#7` | Compose official shared-auth delegation and ClipTown SDKs in the active product service. | No direct factor client and no broad bearer reuse. |

The shared-auth operational tracker is `shared-auth/shared-auth-server.rs#37`.

## Required server evidence

The server PR is not qualified merely because a workflow object exists. Evidence must show executed runner steps for:

- schema initialization against the supported PostgreSQL version;
- `cargo fmt --all --check`;
- locked Clippy with warnings denied;
- locked all-target tests;
- locked release build;
- delegated audience/session/scope/assurance and current-parent lineage tests.

Jobs that fail before checkout, contain zero steps, or produce no compiler/test logs are runner infrastructure failures and must not be interpreted as code failure or success.

## Required client evidence

The Rust SDK must prove:

- the request body contains the user token and exact expected audience;
- the independent service credential appears only in the introspection Authorization header;
- the credential never enters the JSON body, error, trace, or returned object;
- current `jti` and `parent_jti` decode separately and must be distinct for a complete delegation lineage;
- wrong audience, inactive token, missing session, wrong client/scope, stale assurance, malformed credentials, remote plaintext HTTP, redirect, and oversized response fail closed.

## GitHub Project mapping

Add the active items to the shared-auth organization project with:

- **Linear**: `DEN-2259`
- **Workstream**: `Product delegation`
- **Status**: In progress / In review / Qualified / Merged / Released / Deployed
- **Component**: server / Rust SDK / Go SDK / TypeScript SDK / policy / operations
- **Consumer**: MemeBank / ClipTown
- **Evidence**: exact workflow run or signed release
- **Blocked by**: upstream/downstream item URL

Keep the GitHub item open through release and deployment configuration. Merging code alone does not install the delegation policy, introspection secret, issuer/audience pins, session store, or downstream resource authorization.

## Release and rollout order

1. Produce real runner-backed server and SDK evidence.
2. Merge the server change.
3. Merge the official SDK change.
4. publish or otherwise pin immutable reviewed artifacts;
5. configure non-production delegation and introspection credentials;
6. allow ClipTown to qualify its backend against those exact artifacts;
7. canary the cross-product flow with no mobile applications involved.

Rollback must disable or narrow the delegation policy and roll back consumers; it must not issue broad tokens, bypass protected introspection, accept a direct 3FA proof, or place an introspection credential in a client product.
