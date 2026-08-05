# MemeBank asynchronous-analysis authorization dependency

This document defines the cross-organization delivery boundary between `shared-auth` and `memebank` for authorized server-side image analysis.

## Planning systems

- **Shared-auth GitHub Project:** `shared-auth-project` — project 1
- **Shared-auth Linear project:** `github.com/shared-auth`
- **MemeBank GitHub Project:** `memebank-project` — project 1
- **MemeBank Linear issue:** `DEN-1535`
- **MemeBank implementation issue:** `memebank/mbk-ocr-api#23`
- **Merged provider reader:** `memebank/mbk-ocr-api#21`

GitHub is authoritative for repository code, pull requests, checks, releases, and runtime evidence. Linear is authoritative for priority, ownership, dependency status, milestones, and acceptance criteria. Both organization Project routing cards should link this dependency until production activation is complete.

## Context

MemeBank uses server-managed encryption for analyzable media so authorized asynchronous workers can run OCR, captions, tags, embeddings, perceptual hashes, moderation, thumbnails, and re-indexing. The worker now has an exact-version S3 reader that can open only the durable object version recorded by the job and has no mutable `latest` fallback.

Storage correctness is not sufficient. Before any S3 or KMS request, the worker must prove that the current tenant, library, asset, job, worker principal, object version, protection mode, and analysis policy are still authorized.

## Required shared-auth capability

Shared-auth must support a short-lived internal service-principal or workload-identity assertion for the OCR/enrichment worker. The MemeBank authorizer should be able to present or resolve:

```text
worker service principal
tenant ID
library ID
asset ID
analysis job ID
bucket/container
opaque object key
immutable version or provider generation
protection mode
analysis permission or policy snapshot
```

The authorization decision compares these values with current durable MemeBank state. Queue or client values are claims to verify, not independent sources of authority.

## Decision classes

The integration needs stable typed outcomes:

- **allowed** — the exact worker and object policy may proceed;
- **denied** — terminal authorization failure with zero storage calls;
- **revoked/canceled** — terminal because the job, asset, or policy changed;
- **wrong tenant/library/asset/version/principal** — terminal cross-boundary mismatch;
- **unavailable** — retryable authorization-service or dependency outage;
- **deadline/canceled** — propagate the active worker context.

Unknown backend messages must be redacted. Responses and logs must not contain raw media, OCR/caption content, signed URLs, cloud keys, shared-auth tokens, private object keys, or user filenames.

## Worker order of operations

The canonical MemeBank worker sequence is:

1. validate the immutable binding shape;
2. validate its current lease and fencing token;
3. call shared-auth-backed authorization for tenant/library/asset/job/worker/object policy;
4. issue one exact-version provider read;
5. verify response version and encryption metadata;
6. enforce bounded media and approved KMS policy;
7. run cancellable analysis in bounded memory;
8. publish results under the current fencing token;
9. clean abandoned private results by exact version.

Denial, cancellation, or dependency unavailability before step 4 produces zero S3/KMS calls.

## Workload identity requirements

- use short-lived workload identity or service-principal credentials;
- do not use a static PAT, personal user token, long-lived API key, or credential in a queue payload;
- bind the identity to the MemeBank OCR/enrichment service and environment;
- support rotation without changing application code;
- scope the principal to the required authorization API/claim audience;
- retain an opaque audit trail of principal, tenant, asset, job, outcome, policy version, and timestamp;
- exclude secret material and media-derived content from audit records.

## Durable MemeBank checks

The authorizer integration must compare shared-auth identity with MemeBank’s current records for:

- tenant ownership or access to the library;
- library membership of the asset;
- asset linkage to the exact immutable object version;
- job linkage to that asset/version;
- active worker lease or approved service-principal role;
- `server_managed` protection mode;
- analysis still enabled;
- region, residency, retention, deletion, and legal-hold policy;
- administrative cancellation or revocation.

## Interfaces and clients

The stable cross-org schema should live in `shared-auth-interfaces`, with generated or reviewed client support in `shared-auth-clients`. Server enforcement belongs in `shared-auth-server.rs` or the canonical shared-auth service path.

The contract should remain language-neutral and versioned. MemeBank’s current compatibility implementation is Go, while the canonical worker target is Rust; both must receive equivalent decision semantics.

## Test matrix

### Shared-auth contract tests

- valid internal principal and exact claims;
- expired, malformed, wrong-audience, wrong-environment, and revoked identity;
- wrong tenant/library/asset/job/version/principal;
- unavailable backend, timeout, and cancellation;
- redaction of token, credential, provider, and object detail.

### Cross-organization E2E

- create tenants, libraries, assets, immutable object versions, and jobs in test persistence;
- obtain a short-lived worker identity from shared-auth test infrastructure;
- prove an allowed binding reaches the versioned provider once;
- prove every denied/mismatched binding reaches the provider zero times;
- revoke access during a long-running job and verify heartbeat/context cancellation;
- prove stale workers publish zero visible observations;
- retain redacted evidence in both GitHub Projects and Linear.

## Delivery sequence

1. define the versioned authorization request/decision schema in `shared-auth-interfaces`;
2. implement server enforcement and workload-identity validation;
3. add Rust and Go-compatible clients or protocol bindings;
4. implement MemeBank’s concrete `AnalysisObjectAuthorizer` adapter;
5. add cross-org E2E in the shared-auth and MemeBank test environments;
6. document deployment audience, issuer, rotation, and incident procedures;
7. link exact PRs, checks, merge SHAs, and activation evidence in both org Projects and Linear.

## Completion boundary

This dependency is not complete merely because an interface or server endpoint is merged. Completion requires production workload identity, current durable-state comparison, zero-provider-call denial evidence, revocation/cancellation behavior, cross-tenant E2E, operational audit/redaction review, and integration into every MemeBank OCR and enrichment handler.