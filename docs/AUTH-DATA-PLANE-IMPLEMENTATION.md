# Admin/customer auth data-plane implementation checkpoint

**Checkpoint date:** 2026-08-05  
**Canonical Linear project:** [`github.com/shared-auth`](https://linear.app/denman/project/githubcomshared-auth-acbca07bb390)  
**Architecture parent:** [DEN-2189](https://linear.app/denman/issue/DEN-2189/shared-auth-isolate-admin-and-customer-authentication-on-separate)  
**Architecture decision:** [Admin/customer authentication data planes and federated customer SSO](https://linear.app/denman/document/admincustomer-authentication-data-planes-and-federated-customer-sso-8a7890cb3c82)

This checkpoint records what is merged in Git and what remains a protected operational gate. It is not a production-completion declaration.

## Merged implementation evidence

| Workstream | Linear | GitHub evidence | What is now in source |
|---|---|---|---|
| Isolated PostgreSQL data planes | [DEN-2191](https://linear.app/denman/issue/DEN-2191/shared-auth-infra-provision-isolated-admincustomer-rds-data-planes-and) | [`shared-auth-infra#8`](https://github.com/shared-auth/shared-auth-infra/pull/8), squash commit [`a2902bb`](https://github.com/shared-auth/shared-auth-infra/commit/a2902bb3130f8ae3706540a8a75c5bf720142034) | reusable private encrypted RDS module; exactly one admin and one customer plane; separate network, KMS, secrets, backups, deletion protection, monitoring, and blocking runtime-SG isolation; no application-database fallback |
| Runtime realms and customer application federation | [DEN-2193](https://linear.app/denman/issue/DEN-2193/shared-auth-server-add-realm-isolation-and-federated-customer) | [`shared-auth-server.rs#40`](https://github.com/shared-auth/shared-auth-server.rs/pull/40), squash commit [`8547270`](https://github.com/shared-auth/shared-auth-server.rs/commit/854727049ec31ebf754e6d6c0472b4105fd1a523) | fail-closed admin/customer startup contract; exact expected RDS host; separate issuer, resource, secret, signing key, cookie, deployment, and Supabase project; global customer principal with per-application enrollment, OAuth client, consent, and session-to-client grant schema |
| Federation, realm, revocation, migration, and restore contracts | [DEN-2194](https://linear.app/denman/issue/DEN-2194/shared-auth-e2e-prove-cross-app-sso-audience-isolation-revocation-and) | [`shared-auth-e2e#14`](https://github.com/shared-auth/shared-auth-e2e/pull/14), squash commit [`16e2035`](https://github.com/shared-auth/shared-auth-e2e/commit/16e2035d76c781010d87fe1702d3d75ac97e391c) | dependency-free real-ES256/PKCE contract harness; App-A/App-B audience isolation; admin/customer separation; auth-DB-free local verification; fail-closed revocation/order; synthetic credential-scanned migration and independent restore fixtures; opt-in deployed evidence suites |

The earlier reviewed architecture/runbook PRs remain useful context:

- [`shared-auth-infra#7`](https://github.com/shared-auth/shared-auth-infra/pull/7);
- [`shared-auth-server.rs#36`](https://github.com/shared-auth/shared-auth-server.rs/pull/36);
- [`shared-auth/.github#14`](https://github.com/shared-auth/.github/pull/14).

## Validation actually completed

| Repository | Exact local validation | GitHub Actions state on exact PR head |
|---|---|---|
| `shared-auth-infra` | seven Node policy tests and the production data-plane contract passed | jobs failed before execution with `runner_id: 0` and no steps |
| `shared-auth-server.rs` | seven Python policy tests passed; realm/schema contract passed; CLI TOML and workflow YAML parsed | jobs failed before execution with `runner_id: 0` and no steps; dependent jobs skipped |
| `shared-auth-e2e` | clean dependency-free `npm ci`; syntax checks; ten always-on tests passed; four unrequested deployed suites remained inactive | all five jobs failed before execution with `runner_id: 0` and no steps |

Pre-run runner-allocation failures are not CI test failures, but they are also not successful CI evidence. The strongest completed evidence state for these merged PRs is **PR/local contract**, not **CI**, **Deployed**, **Restore-tested**, or **Load-tested**.

## Explicitly not performed

This checkpoint makes no claim that any of the following occurred:

- creation or modification of live AWS RDS resources;
- Terraform plan or apply against the production account;
- production database-user creation or runtime-secret materialization;
- application of the new schema to admin or customer RDS;
- Kubernetes/ArgoCD realm-overlay activation;
- Supabase admin/customer project creation or credential rollout;
- customer or administrator migration;
- production traffic cutover;
- independent RDS restore drills;
- load/latency or application-RDS auth-query measurements;
- controlled one-realm outage/failover drills;
- rollback execution.

## Remaining protected gates

### DEN-2191 — infrastructure

1. Run `terraform fmt`, provider initialization, validation, and a reviewed plan with protected remote state.
2. Verify the plan creates exactly two auth RDS instances and does not mutate the application RDS instance.
3. Apply with scoped AWS roles.
4. Create separate least-privilege migration/runtime users and realm-scoped secret values; do not use the RDS master credential for application or proxy traffic.
5. Record backup/PITR settings, alarms, endpoint outputs, and independent restore evidence.
6. Add RDS Proxy only if measured connection churn justifies it and a dedicated runtime-user secret exists.

### DEN-2193 — runtime and schema

1. Run the exact merge revision through Rust format, Clippy, tests, disposable-Postgres schema application, browser WebAuthn, audit, and image build on a functioning runner.
2. Create reviewed admin/customer deployment overlays only after the new databases and secret mappings exist.
3. Configure one dedicated Supabase project per realm and exact realm-specific endpoint/key/cookie/issuer values.
4. Prove customer tokens fail at admin and admin tokens fail at customer.
5. Prove App A rejects App B tokens and vice versa against the deployed implementation.

### DEN-2194 — evidence

1. Run the exact E2E merge revision on a functioning runner.
2. Inject disposable realm, App-A/App-B, and pre-revoked-session fixtures through approved secret storage.
3. Record revocation latency, application-RDS auth-query count, connection use, and authentication p95/p99 under load.
4. Restore admin and customer snapshots independently and record snapshot IDs, timestamps, recovered revision/schema, and verification results.
5. Perform the reviewed one-realm outage drill and prove the other realm remains healthy.

### DEN-2197 — migration and cutover

1. Register each consumer as an exact OAuth/OIDC client with a unique audience and redirect allowlist.
2. Migrate customers incrementally with deterministic principal mappings and per-application enrollment.
3. Migrate administrators separately with reauthentication and MFA enrollment; never promote a customer identity through an `is_admin` flag.
4. Remove auth reads/writes and credentials from application databases only after observation and rollback windows.
5. Record product-by-product rollback criteria and execution evidence.

## Recommended GitHub Project state

Until Projects-v2 access is available, an organization owner should reconcile project 1 to the following honest state:

| Item | Status | Environment | Evidence state | Risk |
|---|---|---|---|---|
| `shared-auth-infra#6` / DEN-2191 | In progress | Production | PR | Critical |
| `shared-auth-server.rs#1` and DEN-2193 implementation | In progress | Test / Production | PR | Critical |
| `shared-auth-e2e#12` / DEN-2194 | In progress | Test | PR | High |
| DEN-2197 consumer migration items | Ready or Backlog by product | Production | None | Critical |

Add the merged PRs as evidence links or project items without marking the owning issues Done. Advance `Evidence state` only when exact-revision CI, deployment, restore, or load evidence actually exists.

## Linear synchronization

DEN-2191, DEN-2193, and DEN-2194 remain **In Progress** with their merged PR and squash-commit links attached. DEN-2197 remains the protected migration/cutover workstream. The parent DEN-2189 remains open until its production acceptance evidence is complete.
