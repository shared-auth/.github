# Async authentication state machines and formal verification

- Status: accepted hardening design; implementation and exact-revision evidence remain open
- Audit date: 2026-08-20
- Federation architecture: [Federated dual-proof subsystem authentication](FEDERATED-DUAL-PROOF-ARCHITECTURE.md)
- Execution issue: [DEN-3812](https://linear.app/denman/issue/DEN-3812/shared-auth-formal-methods-verify-strict-dual-proof-authorization)
- Contract issue: [DEN-3810](https://linear.app/denman/issue/DEN-3810/shared-auth-interfaceslib-publish-strict-dual-proof-federation)
- Server/schema: [DEN-2193](https://linear.app/denman/issue/DEN-2193/shared-auth-server-add-realm-isolation-and-federated-customer)
- Deployed evidence: [DEN-2194](https://linear.app/denman/issue/DEN-2194/shared-auth-e2e-prove-cross-app-sso-audience-isolation-revocation-and)

## Decision

Shared Auth will publish one versioned asynchronous protocol vocabulary and two related state machines:

1. `federation-authorization/v1` owns the durable server-side strict dual-proof transaction.
2. `client-session/v2` owns client attempts, asynchronous effects, credential-vault commits, cancellation, retry, and recovery.

The machines share event identifiers, generations, result envelopes, bounded failure reasons, and Interaction Trace Format (ITF) fixtures. They are separate because a server authorization transaction and a device credential lifecycle have different durability and trust boundaries.

The authoritative protocol specification is TLA+/PlusCal. TLC and Apalache check that same specification under declared finite bounds. A pure Rust reducer, Stateright actor model, PostgreSQL transactions, generated client reducers, and deployed E2E flows are refinement targets, not independent sources of semantics.

Thread safety is necessary but insufficient. Safe Rust, `Send + Sync`, a Swift actor, a Kotlin monitor, or a JavaScript event loop can prevent some memory races while still accepting a stale callback, duplicating a remote effect, exposing a credential before durable commit, or losing a cross-replica race. Authorization correctness therefore has three distinct layers:

| Layer | Required authority |
|---|---|
| In-process memory safety | language type system, actor/lock ownership, and runtime-specific concurrency tests |
| Cross-task and cross-replica authorization ordering | versioned events plus PostgreSQL constraints, row locks, and compare-and-swap transactions |
| Distributed convergence after retry, loss, and restore | durable idempotency keys, audit/outbox/inbox versions, reconciliation, and explicit liveness assumptions |

No process-local mutex is a substitute for a database linearization point. No model-check result substitutes for an implementation refinement test.

## Audit baseline and claim boundary

The audit inspected these `main` revisions:

| Repository | Revision | Relevant current evidence |
|---|---:|---|
| `shared-auth-server.rs` | `4fc6362` | bounded Rust refresh/revocation/key model, PostgreSQL two-contender refresh test, live server routes and JWKS cache |
| `shared-auth-interfaces` | `ce9071e` | current first-success authority-race contract |
| `shared-auth-lib` | `4972cfd` | Rust, TypeScript, JavaScript, Go, Dart, and Gleam race/guard implementations |
| `shared-auth-clients` | `a63d281` | generated lifecycle JSON, TLA+, Dart, Swift, and Kotlin machines |
| `shared-auth-e2e` | `964e885` | contract and synthetic federation fixtures |

The current artifacts are useful but do not prove asynchronous strict dual-proof authorization:

- the live reusable dual-authority behavior is a first-success OR race, not a two-proof AND join;
- the server bounded model is sequential and covers refresh, revocation, and key rotation, not proof collection, multiple replicas, cancellation, crash points, authorization-code redemption, application grants, or outbox delivery;
- the client TLA+ model has `state`, credential presence, and a last event, but no actors, queues, operation IDs, duplicate delivery, or result reordering;
- the current `SingleInFlight` invariant constructs an empty or singleton set from one enum state, so it does not verify the number of real tasks;
- the client configuration checks safety only and declares no fairness or temporal liveness property;
- generated clients mutate in-memory state and return a vault effect for later execution, while the abstract step changes both atomically;
- current late-verifier and PKCE-replay E2E fixtures are sequential simulations rather than concurrent database or deployed multi-replica tests;
- the active browser handoff and the current introspection call shapes still have the implementation gaps recorded in the federation architecture.

Passing the existing checks confirms their bounded synchronous assertions only. It must not be reported as evidence for this design.

## P0 counterexample: stale completion across attempts

Current lifecycle result events do not carry an operation or generation. The following trace is accepted by the existing state-only model:

```text
startSignIn(op1)                 signedOut -> authorizing
cancel(op1)                      authorizing -> signedOut
startSignIn(op2)                 signedOut -> authorizing
receiveAuthorizationCode(op1)   authorizing -> exchanging
authenticationSucceeded(op1)    exchanging -> authenticated
```

The machine cannot tell that the last two events belong to the cancelled attempt. Actor or monitor serialization does not fix this ABA problem: every callback can acquire the actor or lock in sequence and still be logically stale.

`client-session/v2` therefore requires all requests and completions to carry:

```text
contract_id
contract_major_version
model_fingerprint
session_epoch
operation_id
operation_kind
attempt
effect_id
expected_revision
```

A completion can mutate authority or the credential vault only when the complete active generation matches. An older, duplicated, wrong-kind, or post-terminal completion is an explicit idempotent stutter. Reuse of an identifier with conflicting content is a protocol violation.

## Concrete server audit findings

The server is plausibly memory-thread-safe, but several live workflows do not yet have cancellation-safe or cross-replica state transitions. These findings are implementation requirements, not claims that an exploit has occurred:

| Priority finding | Current evidence at `4fc6362` | Required state-machine correction |
|---|---|---|
| Recovery late result can regress state | evaluation awaits providers and later saves evidence; `save_evidence` can update an unconsumed ceremony without expected state/version (`src/recovery/mod.rs`, `src/recovery/store.rs`) | `state_version` plus evaluation lease/fencing token; `evaluating -> next` CAS; terminal rejection/cancellation irreversible |
| Password reset can race old-hash login | password verification is asynchronous and session creation is later; reset changes password and scans existing sessions without credential-version fencing (`src/http/local.rs`, `src/db/mod.rs`, `src/recovery/store.rs`) | verify a credential version; lock principal/credential at final issuance; reset increments credential version and auth epoch and revokes sessions/challenges atomically |
| Roles can be stale under a current epoch | roles and session epoch can be read in different phases/transactions (`src/db/mod.rs`) | create the session from one locked authorization snapshot, or issue identifiers only and resolve mutable grants server-side |
| Factor deletion and revocation are split | factor deletion and affected-session revocation are separate operations (`src/factors/api.rs`) | delete factor, bump epoch, revoke sessions, write audit, and enqueue outbox in one transaction |
| Webhook idempotency is after the effect | handler mutation precedes `record_webhook_event`; duplicate ID does not bind provider/type/payload hash (`src/http/webhook.rs`, `src/db/mod.rs`) | reserve inbox `(provider,event_id,payload_hash)` first; reject conflicting reuse; apply and mark in one transaction with source-version monotonicity |
| Active federation route is not dual proof | mounted `/authorize`/handoff and exchange flows accept Supabase authentication without the strict two-proof transaction; richer OAuth code is dormant (`src/http/mod.rs`, `src/http/handoff.rs`, `src/http/exchange.rs`) | route the live browser flow through `federation-authorization/v1`; code issuance requires the bound proof set |
| Handoff request is not a durable transaction | one CSRF cookie is not bound to the full request; concurrent tabs can collide; code is consumed before decrypt/response (`src/http/handoff.rs`, `src/handoff/mod.rs`) | durable request ID/browser hash/full parameter hash; generation fencing; explicit retry receipt or documented at-most-once recovery semantics |
| Refresh is atomic but family semantics are incomplete | old-token revoke and successor insert are transactional, but no family/generation/absolute lifetime; lost response burns the predecessor (`src/db/mod.rs`, `db/schema.sql`) | family ID, generation, absolute deadline, ancestor-replay family revocation, idempotent rotation receipt or explicit recovery path |
| Challenge delivery can be left unknown | OTP/magic-link records commit before provider awaits; cancellation can skip cleanup; quota is count-then-insert (`src/http/passwordless.rs`, `src/factors/api.rs`, `src/db/mod.rs`) | durable delivery intent/outbox, provider idempotency key, serialized quota reservation, and `delivery_unknown` reconciliation |
| Recovery provider creation lacks durable intent | provider calls begin before ceremony insert and daily quota is count-only (`src/recovery/mod.rs`, `src/recovery/store.rs`) | reserve ceremony/quota first; record each external operation; dispatch and reconcile by stable IDs |
| Outbox lacks a safe worker protocol | revocation writes durable outbox data, but no lease/fencing/ack worker or consumer dedupe contract is implemented (`src/db/mod.rs`, `db/schema.sql`) | `SKIP LOCKED` claim, lease expiry, fencing token, retry schedule, stable effect ID, and consumer inbox |
| Public-key quotas and mutation auth have TOCTOU gaps | count/insert and open-challenge updates are not one serialized transaction; authorization freshness precedes mutation (`src/pubkey/store.rs`, `src/http/sshkeys.rs`) | quota row or principal/key lock plus final epoch/session revalidation inside the mutation transaction |
| JWKS leader cancellation suppresses retry | `last_refresh` advances before the network await (`src/supabase/verifier.rs`) | advance successful-refresh metadata only on coherent cache commit; cancelled leader releases ownership and permits recovery |
| Global timeout drops handlers mid-protocol | the HTTP timeout can cancel a handler after provider or autocommit effects; database lock/statement budgets are not aligned (`src/http/mod.rs`) | per-operation deadline hierarchy, durable phases around effects, shorter DB deadlines, and failpoints before/after await/commit/mint/response |

Existing good foundations should be preserved: refresh uses a consistent principal/session lock order and an atomic predecessor/successor transaction; global revocation atomically records substantial local state plus outbox intent; Tokio synchronization prevents obvious in-process JWKS cache data races. The hardening task is to extend those patterns and prove their refinement, not replace them indiscriminately.

## Server machine: `federation-authorization/v1`

### Durable state

The abstract state includes:

- immutable federation principals and external identities keyed by exact issuer and subject;
- application-account status and pairwise application subject;
- transaction ID, row revision, deadline, terminal reason, and configuration/policy epoch;
- exact application, client, redirect hash, audience, scopes, state, nonce, PKCE S256 challenge, and browser-session binding;
- separate `native_shared_auth` and `root_supabase` proof slots;
- for each proof: request generation, result, issuer, subject, resolved principal, evidence ancestry, authentication time, expiry, and verification epoch;
- authorization-code hash and unused/consumed state;
- grant/session, refresh lineage, identity version, revocation epoch, and proof-policy lifetime;
- durable idempotency records, bounded audit event, and transactional outbox record;
- unordered in-flight result/message bag with loss, delay, duplication, and reordering;
- replica volatile state, crash/restart status, and logical/database time.

Do not store an independently mutable `both_verified` boolean. At issuance, derive eligibility from the current proof rows, immutable links, exact bindings, application-account status, deadline, policy epoch, and revocation epoch inside the committing transaction.

### Principal transitions

```text
begin/resume bound transaction
  -> dispatch either or both proof verifiers
  -> receive results in any order
  -> conditionally apply matching generations
  -> resolve both immutable identities to one principal
  -> evaluate current application and revocation policy
  -> atomically issue one authorization code, audit, and outbox record
  -> atomically redeem that code once
  -> issue/rotate bounded application session
```

From every nonterminal phase, the environment can delay, duplicate, reorder, or drop a result; cancel or expire the transaction; rotate keys/configuration; advance a revocation epoch; crash a replica; lose a response after commit; restart; and retry with the same idempotency key.

Terminal states are monotonic. `denied`, `cancelled`, `expired`, and `consumed` never reopen. A retry after a lost response returns the authoritative durable outcome and does not repeat the effect.

### Strict issuance invariant

```text
grant_issued =>
  native_shared_auth_proof = valid_and_fresh
  AND root_supabase_proof = valid_and_fresh
  AND evidence_is_independent(native_shared_auth_proof, root_supabase_proof)
  AND principal(native_shared_auth_proof) = principal(root_supabase_proof)
  AND root_supabase_proof.issuer = registered_federation_root_issuer
  AND application_account = active
  AND all_transaction_bindings_match
  AND transaction_is_nonterminal_and_unexpired
  AND observed_policy_epoch = current_policy_epoch
  AND observed_revocation_epoch = current_revocation_epoch
```

The legacy first-success race remains a separately named compatibility contract, such as `any-authority/v1`. Its result type cannot be converted into a strict proof set or application grant.

## Client machine: `client-session/v2`

### Durable and observable state

Each snapshot includes:

- contract version and model fingerprint;
- local revision and session epoch;
- lifecycle state and terminal/degraded reason;
- active operation ID, kind, attempt, and deadline;
- pending effect IDs and idempotency keys;
- credential generation and vault record generation;
- server transaction reference and last authoritative outcome;
- retry intent and reconciliation requirement.

Authenticated application capability is a derived value. It exists only when the vault contains a valid credential for the current session epoch and the machine has committed the matching generation.

### Reserve, execute, commit

All asynchronous client work follows one pattern:

1. Reserve the operation/effect and advance the local revision under the actor, owner task, or short critical section.
2. Release the coordinator and perform network or vault I/O.
3. Re-enter with a completion carrying the full operation/effect generation and expected revision.
4. Compare and apply the result, or stutter if it is stale/duplicate.
5. Expose authenticated capability only after the credential vault commit succeeds.

Never hold a mutex or actor-isolated synchronous critical section across network or database I/O. Never let an effect callback mutate lifecycle state directly.

Credential stores need compare-and-swap or a prepare/commit/recovery protocol. A crash after reserving an effect but before committing its credential must restart in a reconciling state, not an apparently authenticated state.

## Cancellation, timeout, and outcome unknown

Cancellation means “the caller no longer wants to wait.” It does not prove that a request already transmitted to a server did not commit.

- Dropping a Rust future stops local polling but cannot undo a remote commit.
- An `AbortSignal`, Go context, or task cancellation is cooperative.
- JavaScript and Dart promises/futures commonly keep running after a local race or timeout.
- Ignoring a loser prevents a late local return value from winning; it does not cancel its network side effects.

Mutating operations therefore use transaction-bound idempotency keys and expose an `outcome_unknown` or `reconciling` state when the response is lost. A retry reads or resumes the existing transaction. It does not issue a second code, rotate a second refresh generation, or repeat enrollment.

Verifier race arms must be observationally pure. If an arm can mutate state, its mutation must be part of the durable authorization transaction and idempotent under replay. Documentation must not claim that a losing arm was cancelled unless the implementation supplies and verifies that guarantee.

Timeout-versus-success at the same logical instant needs one specified tie-break. The server database commit is authoritative; the client may time out and then reconcile to an already-committed result, but a later callback cannot newly authorize a cancelled or expired transaction.

## PostgreSQL linearization and isolation

The customer-auth RDS is the shared serialization boundary for all server replicas. Suggested concrete points are:

| Abstract operation | Linearization point |
|---|---|
| Apply proof result | conditional `UPDATE`/insert on transaction ID, proof slot, request generation, current row revision, and nonterminal deadline |
| Link identity | unique constraint on exact `(issuer, subject)` plus transaction that binds one principal |
| Issue authorization code | one transaction that locks/CASes the authorization row, re-reads both proofs and epochs, inserts the hashed code/grant intent, audit, and outbox |
| Redeem code | atomic `unused -> consumed` CAS constrained by exact client, redirect, and PKCE verifier |
| Rotate refresh | lock/CAS current refresh generation; insert exactly one successor; detect replay |
| Cancel/expire | terminal-state CAS; later result applications require nonterminal state and therefore stutter |
| Revoke/disable | advance the relevant epoch/status under the same lock order used by issuance and refresh |
| Deliver projection | subsystem inbox uniqueness on event ID plus monotonic aggregate version; gaps trigger reconciliation |

Every transaction documents lock order, isolation level, retryable SQLSTATEs, statement/lock timeout, and stuttering behavior. PostgreSQL `Read Committed` does not make a multi-statement read/evaluate/write sequence atomic by itself. Use row locks and conditional writes where sufficient; use `Serializable` with bounded retry where the invariant spans predicates that cannot be protected otherwise.

Real contender tests use separate pools/connections and explicit barriers. In-memory mocks or `join!` over one logical connection do not constitute cross-replica evidence.

## Required server machine catalog

The two federation/client models are the first priority, but the same version, generation, terminal-state, and idempotency vocabulary applies to every live mutable auth route:

| Machine | Principal states | Required linearization/fencing |
|---|---|---|
| Dual proof set | `initiated -> proofs_pending -> bound -> consumed`, terminal `denied/expired/revoked/cancelled` | both independent proofs, one immutable principal, exact request bindings, proof generations, deadline |
| Handoff/OAuth code | `requested -> authorized -> code_issued -> redeemed`, terminal `denied/expired/cancelled` | request hash/browser binding; code issue from bound proof set; single-use redeem plus response-loss policy |
| Session/refresh family | `active(generation n) -> rotated(n+1)`, terminal `revoked/expired/reuse_detected` | family/current-generation lock; exact-one successor; absolute family deadline; replay handling |
| Recovery | `reserved -> providers_creating -> pending -> evaluating(lease) -> pending_review/cooldown/ready -> consumed`, terminal `rejected/expired/cancelled` | quota and intent first; lease fencing; late result requires state/version CAS |
| Delivery challenge | `created -> queued -> dispatching -> sent/delivery_unknown -> verifying -> consumed`, terminal `failed/expired/cancelled` | durable intent; provider idempotency; conditional consume; serialized quota |
| Identity link | `requested -> incumbent_verified -> candidate_verified -> committed`, terminal `rejected/expired/cancelled` | exact issuer/subject on both sides; no email linking; versioned CAS |
| Factor/key mutation | `authorized -> applying -> effective`, terminal `denied/cancelled` | final session/epoch/credential recheck; mutation, revocation, audit, and outbox atomically |
| Webhook inbox | `received -> applying -> applied`, terminal `rejected/dead` | reserve provider/event/payload hash before effect; source version advances |
| Grant/revocation | `previewed -> authorized -> locally_effective -> propagation_pending -> propagated/partial/failed` | local authorization and epoch change atomic; remote propagation status remains separate |
| Outbox | `queued -> claimed(lease,token) -> succeeded/retry_scheduled/dead` | `SKIP LOCKED` lease; ack requires fencing token; stable effect idempotency key |

Maintain a generated route-to-machine/obligation manifest. CI fails when a mounted authentication route, mutable status column, or new terminal state has no owning machine, legal transition table, safety obligation, SQL linearization point, and concrete integration test. Dormant/unrouted code is listed separately and cannot satisfy a live-route obligation.

## Thread-safety and async runtime assessment

| Runtime/component | Current boundary | Required hardening |
|---|---|---|
| Rust server `AppState` | cloneable handles and atomic readiness are suitable for Axum sharing | compile-time `Send + Sync + 'static` assertions; pure reducer; no authorization truth in process memory; async schedule/cancellation tests |
| Rust JWKS cache | Tokio `RwLock` and refresh mutex prevent memory corruption/same-process overlap | publish fetched keys and refresh metadata as one generation; commit cooldown only after a completed attempt; re-check after the refresh lock; negative-`kid` bound; cancellation/timeout tests |
| Rust/Go verification races | Rust drops pending futures; Go cancellation is cooperative | keep arms pure or transaction-bound/idempotent; prove late results cannot mutate; Go tagged result and race detector |
| TypeScript/JavaScript/Dart races | late outcomes can be ignored, but underlying work is not reliably cancelled | cancellation signal where supported; generation fencing; outcome-unknown reconciliation; runtime race tests |
| Swift lifecycle | actor serializes in-memory access | remove unjustified `@unchecked Sendable`; generation fencing; atomic vault refinement; task-group and TSAN tests |
| Kotlin lifecycle | `@Synchronized` serializes reducer methods | synchronize all mutable credentials/configuration; generation fencing; coroutine and Lincheck tests |
| Dart lifecycle | synchronous dispatch is atomic in one isolate | declare owner-isolate contract; external coordination for multiple isolates; fake-time/isolate tests |
| TypeScript/browser client | one event loop prevents memory data races only | multi-tab ownership/lease or vault CAS; Worker/fake-timer/reload tests |
| Go client | context-aware calls with immutable-by-copy configuration assumptions | tagged outcomes, transport-safety contract, operation generations, `go test -race` |
| Java/plain JS/Ruby/WASM/Gleam | no complete generated lifecycle coordinator | document single-owner assumptions or generate the coordinator; run common trace corpus |

Public native handles intended for sharing receive compile-time trait assertions. Intentionally single-threaded or WASM types explicitly document `!Send`/`!Sync` or owner-agent requirements.

Inventory every `unsafe` block and `unsafe impl Send/Sync`. Each requires a written synchronization invariant and targeted Miri/Loom evidence. Deny await-holding-lock and await-holding-refcell lints. Safe Rust prevents undefined-behavior data races; it does not prove the protocol is free of logical races.

## JWKS cache state machine

Key lookup is its own bounded state machine:

```text
fresh cache hit -> verify
unknown kid + refresh permitted -> one in-flight fetch generation
concurrent waiter -> join that generation, then re-check cache
fresh authoritative JWKS lacks kid -> definite invalid + bounded negative cache
fetch unavailable/invalid -> unavailable, fail closed, bounded backoff
cancelled fetch -> no successful-refresh timestamp; next permitted caller may retry
seed/config rotation -> newer generation cannot be overwritten by an older fetch
```

Refresh time, key set, ETag/source metadata, and generation must be published coherently. Setting a successful-refresh cooldown before the network fetch commits can turn cancellation or failure into an avoidable cold-cache outage. An attacker-controlled unknown `kid` must not trigger unbounded sequential refreshes or be classified as provider-unavailable after a fresh authoritative JWKS definitively omits it.

## Machine-readable safety obligations

Add these obligations to the existing formal review registry without weakening the completed refresh/revocation/key-rotation obligations:

| Obligation | Required property |
|---|---|
| `StrictConjunction` | grant implies both current required proofs |
| `IndependentEvidence` | native proof is not derived solely from the presented root proof |
| `SamePrincipal` | both immutable identities resolve to exactly one principal |
| `BindingIntegrity` | proof, callback, code, and result cannot cross client/redirect/state/nonce/PKCE/browser/audience/application |
| `ExactRootIssuer` | a subsystem Supabase issuer cannot satisfy the root slot |
| `SingleUse` | one code consumption, one refresh successor, and one durable effect |
| `TerminalMonotonicity` | denied/cancelled/expired/consumed states do not reopen |
| `LateResultStutters` | old, duplicate, wrong-kind, and post-terminal results cannot change authority or vault state |
| `FailClosed` | invalid, revoked, mismatched, or unavailable evidence never becomes allow through timeout or retry |
| `RevocationEpoch` | issuance/refresh cannot commit against stale policy or revocation state |
| `RealmAudienceIsolation` | admin/customer and App-A/App-B authority cannot cross |
| `EmailNonAuthority` | email change, reuse, or collision cannot alter identity resolution |
| `CrashAtomicity` | no half-issued code/grant/audit/outbox or half-committed credential is exposed |
| `IdempotentEffects` | duplicate callbacks/events create at most one durable effect |
| `ActiveApplicationAccount` | identity authentication alone never creates product authorization |
| `CredentialCapabilityConsistency` | client capability implies a current committed vault credential |
| `SecretFreeObservableState` | raw tokens, global subjects, and email do not enter public model output/log labels |
| `BoundedPendingWork` | every transaction and tracked task has a terminal deadline |

At least four mutation tests must demonstrate that the gates are meaningful: change AND to OR; remove a code/refresh CAS; accept an old-generation result; or let a subsystem issuer satisfy the root slot. Each mutation must fail a required gate.

## Liveness, fairness, and non-claims

Safety is checked with arbitrary finite message loss, duplication, delay, reordering, dependency outage, cancellation, and crashes.

Liveness is conditional. Under weak fairness for enabled internal actions, bounded clock skew, a persistent client, eventual database/provider recovery, eventual delivery of retried messages, a finite number of crashes followed by a stable period, and no later cancellation/revocation:

- a valid active transaction eventually issues or reaches a documented terminal denial;
- a collecting transaction eventually expires even if a provider never responds;
- idempotent retry eventually returns the authoritative committed outcome;
- refresh waiters eventually receive a result or deadline;
- cancellation cleanup eventually completes;
- audit/outbox projection eventually reaches an enrolled subsystem whose consumer recovers.

Do not add blanket fairness that hides starvation. Do not claim progress during a permanent partition, infinite crash loop, abandoned client, or permanent provider outage. Do not claim instantaneous distributed JWT revocation: a token issued before an epoch change may remain locally acceptable until its documented bounded expiry unless the operation requires current introspection.

## Verification and refinement stack

| Layer | Purpose | Permitted claim |
|---|---|---|
| TLA+/PlusCal + TLC | authoritative finite protocol semantics, exhaustive small-bound safety, narrowly fair liveness | exhaustive only for the exact recorded constants, symmetry, constraints, and state count |
| Apalache | larger-domain bounded symbolic safety | bounded, non-exhaustive beyond the positive recorded step/domain bounds |
| Pure Rust reducer | deterministic executable reference for server events/effects | conforms for replayed traces; not automatically the protocol authority |
| Stateright | Rust actor/network refinement, reordering/loss/duplication, linearizability | exhaustive only for the recorded bounded state space; liveness claims remain limited |
| Loom | in-process shared-memory interleavings | exhaustive only when all relevant synchronization is instrumented and bounds are recorded |
| Shuttle | wider reproducible Tokio schedules and cancellation | randomized/PCT evidence with persisted seed/schedule, not proof |
| Proptest | sequential command/refinement traces and shrinking | property evidence for generated cases, not concurrency proof |
| Real PostgreSQL | actual constraint, lock, isolation, retry, crash, and contender behavior | concrete refinement evidence for exact engine/schema/configuration |
| Cross-language ITF/JSONL | common counterexample and conformance replay | semantic parity for the declared observable trace corpus |
| Deployed E2E | browser, replicas, databases, Supabase projects, outage and restore | system evidence for exact recorded revisions/environment |

Apalache is not a blocking required gate until its isolated, pinned runtime is accepted under DEN-3752 or an approved exception records the exact toolchain. A CI run that is not admitted and explores zero states is not a pass.

## Secret material and evidence fixtures

Runtime-owner repositories use the organization [SOPS/Nix/Just environment contract](../ENVIRONMENT_OWNERSHIP.md):

```text
env/enc/*.env.enc   -> tracked ciphertext for an approved profile
env/dec/*.env       -> ignored owner-only plaintext for the same profile
```

The wildcard is a path grammar, not a broad allowlist. The exact profile and credential class must be approved for the owning repository. Prefer `sops exec-env` so a test process receives decrypted values without a persistent plaintext file. Where a tool requires `env/dec/<profile>.env`, the directory and file are owner-only and the value is never logged, uploaded, cached, or copied into a counterexample.

Formal states, ITF/JSONL traces, property-test seeds, database fixtures, screenshots, and CI artifacts are secret-free. They contain opaque synthetic identifiers and bounded enums only. Tests that need live integrations use disposable least-privilege credentials supplied from approved secret storage; the evidence records configuration hashes and secret versions/references, never the values.

Ephemeral access/refresh tokens, authorization codes, session cookies, OTP/recovery material, and user data remain protocol state. They are not converted into static environment variables or repository ciphertext. Crash/retry tests use synthetic substitutes and assert redaction at every observable boundary.

## Required conformance traces

Publish versioned, secret-free ITF/JSONL traces with virtual time for:

- cancel/restart ABA and stale callback;
- duplicate, reordered, delayed, and wrong-kind completions;
- simultaneous timeout and success under the specified tie-break;
- proof arrival in either order;
- two valid proofs for different principals despite equal email;
- subsystem Supabase token substituted for the root proof;
- concurrent proof commits and concurrent code redemption;
- two refresh callers and refresh racing sign-out/revocation;
- response loss after a successful server commit;
- crash between vault prepare and credential commit;
- vault compare-and-swap conflict and device reload recovery;
- App-A/App-B and admin/customer substitution;
- unknown contract version or model fingerprint;
- JWKS rotation, fetch cancellation, seeded-generation race, and random unknown-`kid` pressure;
- duplicate/out-of-order outbox delivery, version gap, restore, and reconciliation.

Every supported client consumes the same trace schema and emits canonical observable JSON. A counterexample from a model checker is committed as a minimized regression fixture and replayed against the pure reducer, applicable SDKs, database refinement tests, and E2E harness.

## Repository ownership

| Artifact | Repository | Planning owner |
|---|---|---|
| Versioned state/event/result/effect/ITF schema and model fingerprint | `shared-auth-interfaces` | DEN-3812 under DEN-3810 |
| Legacy OR-race separation and strict dual-proof join contract | `shared-auth-interfaces`, `shared-auth-lib` | DEN-3810 and DEN-3812 |
| Authoritative TLA+/PlusCal, TLC/Apalache configurations, obligation registry | `shared-auth-server.rs` with published interfaces | DEN-3812 |
| Pure reducer, PostgreSQL refinement map, transaction/CAS implementation, JWKS machine | `shared-auth-server.rs` | DEN-2193 and DEN-3812 |
| Generated lifecycle reducers and per-runtime concurrency/vault coordinators | `shared-auth-clients` | DEN-3812, related to DEN-568 |
| Cross-language guards and cancellation/result contracts | `shared-auth-lib` | DEN-3810 and DEN-3812 |
| Multi-tab, multi-replica, database, crash, replay, outage, and restore evidence | `shared-auth-e2e`, `shared-auth-test` | DEN-2194 and DEN-3812 |
| Reusable formal tooling | platform formal-method repositories | DEN-565; product semantics stay under DEN-3812 |

Dead or unrouted code is excluded from conformance claims. The live route-to-model-action map is a required review artifact.

## CI and evidence profiles

### Pull request

- schema/fingerprint generation and drift check;
- obligation-registry validation;
- TLC exhaustive small profile with recorded states/transitions/bounds;
- deterministic trace replay for every declared runtime available in that repository;
- at least one exhaustive tiny Loom test for each new shared primitive;
- focused PostgreSQL two-contender and stale-generation tests;
- mutation smoke tests for AND/OR, CAS, generation, and root issuer.

### Nightly

- deeper TLC profiles and bounded Apalache when the toolchain gate permits;
- Stateright network/crash exploration;
- Shuttle/PCT schedules with persisted failing seeds;
- full PostgreSQL contention, response-loss, restore, and serialization-retry suite;
- all language race/TSAN/Lincheck/isolate/Worker jobs;
- browser multi-tab and multiple server replicas.

### Release and production-readiness

- exact `main` revisions for server, interfaces, library, clients, E2E, schema, Supabase configuration, and application consumers;
- deployed root plus two subsystem projects;
- real browser/BFF authorization-code and PKCE paths;
- process death at declared crash points;
- backup restore and outbox/inbox replay;
- tool versions, checksums, model fingerprint, constants, fairness assumptions, state/transition counts, seeds/schedules, database version/configuration, CI run, and artifact hashes.

Local checks are development evidence. A release claim requires admitted exact-head CI and deployed evidence. Current source-organization CI billing/admission risk is tracked by DEN-2906.

## Completion criteria

This hardening design is implemented only when:

1. the versioned protocol and both machines are published;
2. live server routes and every supported client flow map to their actions and effects;
3. every asynchronous completion is generation-fenced;
4. authenticated capability cannot precede current credential-vault commit;
5. every cross-replica authority transition has a documented PostgreSQL linearization point;
6. every timeout-after-send is idempotent and reconcilable;
7. all named safety obligations and required mutations pass their declared profiles;
8. liveness claims record their fairness and environmental assumptions;
9. model counterexamples replay against implementations;
10. runtime-specific thread/concurrency gates pass;
11. deployed multi-replica, multi-tab, cancellation, crash, retry, code redemption, refresh, and restore evidence is linked to DEN-3812 and DEN-2194;
12. assurance reports distinguish exhaustive, bounded, randomized, concrete database, and deployed evidence without inflating any claim.

The completed DEN-97 and DEN-1055 refresh/revocation/key-rotation evidence remains valid within its recorded scope. This design extends that scope; it does not relabel the old evidence as an async federation proof.

## Primary references

- [Rust `Send` and `Sync`](https://doc.rust-lang.org/nomicon/send-and-sync.html) describes memory thread-safety traits; logical protocol races require additional invariants.
- [PostgreSQL transaction isolation](https://www.postgresql.org/docs/current/transaction-iso.html) defines the anomalies and retry behavior that the database refinement must account for.
- [TLA+](https://lamport.azurewebsites.net/tla/tla.html) provides the authoritative temporal specification language and TLC tooling used by this design.
- [Apalache](https://apalache-mc.org/docs/apalache/index.html) provides bounded symbolic checking; claims must state the exact bound.
- [Stateright](https://github.com/stateright/stateright) provides Rust actor and distributed-system model checking.
- [Loom](https://docs.rs/loom/latest/loom/) explores bounded thread interleavings for instrumented Rust synchronization.
- [Shuttle](https://github.com/awslabs/shuttle) provides reproducible randomized concurrency testing for Rust async code.
- [Tokio async tests](https://tokio.rs/tokio/topics/testing) documents paused-time testing for deterministic timer behavior.
