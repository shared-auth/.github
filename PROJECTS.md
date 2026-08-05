# Shared Auth project and repository map

This document is the canonical routing guide for planning and delivery across the `shared-auth` GitHub organization.

## Canonical systems

| System | Authority | Canonical location |
|---|---|---|
| Linear | priority, dependencies, ownership, milestones, planning history, cross-project relationships | [`github.com/shared-auth`](https://linear.app/denman/project/githubcomshared-auth-acbca07bb390) |
| GitHub repositories | source, commits, branches, pull requests, review, CI, releases, deployment evidence | [`github.com/shared-auth`](https://github.com/shared-auth) |
| GitHub issues | repository-scoped implementation and evidence tracker | issue in the owning repository |
| GitHub Project | organization-wide delivery view; never a replacement for repository or Linear history | proposed **Shared Auth Delivery** project |
| Organization `.github` | repository boundaries, project routing, contribution and security policy | this repository |

Linear and GitHub are linked ledgers, not competing sources of truth. Linear owns planning state. GitHub owns code and immutable delivery evidence.

## Current architecture program

The admin/customer authentication data-plane program is the first fully mapped program under this contract.

| Workstream | Linear | GitHub |
|---|---|---|
| Architecture parent | [DEN-2189](https://linear.app/denman/issue/DEN-2189/shared-auth-isolate-admin-and-customer-authentication-on-separate) | [`shared-auth-server.rs#1`](https://github.com/shared-auth/shared-auth-server.rs/issues/1) |
| RDS/network/secrets/backup/restore | [DEN-2191](https://linear.app/denman/issue/DEN-2191/shared-auth-infra-provision-isolated-admincustomer-rds-data-planes-and) | [`shared-auth-infra#6`](https://github.com/shared-auth/shared-auth-infra/issues/6), merged docs [`shared-auth-infra#7`](https://github.com/shared-auth/shared-auth-infra/pull/7) |
| Realm/server/schema/customer federation | [DEN-2193](https://linear.app/denman/issue/DEN-2193/shared-auth-server-add-realm-isolation-and-federated-customer) | architecture parent plus merged docs [`shared-auth-server.rs#36`](https://github.com/shared-auth/shared-auth-server.rs/pull/36) |
| Browser/API/database/outage/load/restore evidence | [DEN-2194](https://linear.app/denman/issue/DEN-2194/shared-auth-e2e-prove-cross-app-sso-audience-isolation-revocation-and) | [`shared-auth-e2e#12`](https://github.com/shared-auth/shared-auth-e2e/issues/12) |
| Consumer migration and application-DB decoupling | [DEN-2197](https://linear.app/denman/issue/DEN-2197/shared-auth-rollout-migrate-consumers-and-remove-authentication) | issues/PRs in each owning product repository, related back to the parent |
| Full architecture decision | [Linear document](https://linear.app/denman/document/admincustomer-authentication-data-planes-and-federated-customer-sso-8a7890cb3c82) | server and infrastructure docs above |

Documentation PRs establish the reviewed contract. They do not close provisioning, schema, E2E, migration, restore, or load-test issues unless those implementation acceptance criteria are actually complete.

## Repository ownership

| Repository | Owns | Does not own |
|---|---|---|
| `.github` | organization policy, repository/project map, templates, shared contribution/security guidance | runtime code, product backlog, secrets, deployment state |
| `shared-auth-server.rs` | principal/session/token/revocation/realm authority, server behavior, declarative schema contract, public/internal API implementation | product resource authorization, cloud provisioning |
| `shared-auth-interfaces` | machine-readable identity, token, introspection, event, error, and compatibility contracts | runtime persistence or deployment |
| `shared-auth-lib` | reusable verification/guard behavior and fail-closed decision policy | canonical product membership or direct DB access |
| `shared-auth-clients` | generated/handwritten consumer SDKs by supported runtime/language | server authority or product-specific policy |
| `shared-auth-infra` | cloud integration, RDS/network/KMS/secret/backup/restore contracts, edge infrastructure, runbooks | product application code, startup DDL |
| `shared-auth-e2e` | black-box browser/API/database/outage/load/restore evidence and exact-revision integration gates | production authority or mock-only feature claims |
| `shared-auth-sync` | bounded offline/reconnect synchronization contracts for approved non-secret state | password or refresh-token replication |
| `shared-auth-nats-bridge.rs` | authenticated bounded event/revocation propagation and delivery evidence | canonical identity decisions or unbounded personal data transport |
| `shared-auth-mcp-server.rs` | read-only diagnostics, contract discovery, and agent-facing integration | privileged identity mutation without an explicit reviewed API |
| `shared-auth-monorepo` | application-source inventory and compatible package/submodule integration | infrastructure deployment source or `*-infra` submodule ownership |
| `shared-auth.github.io` | public documentation and integration guidance | secrets, private operational data, runtime authority |

A change spanning repositories gets one canonical Linear parent and bounded repository issues/PRs. Do not create a new repository merely to avoid deciding ownership.

## Cross-organization routing

Shared Auth is a platform dependency for many product organizations. Work remains in the organization that owns the affected implementation.

| GitHub organization | Planning rule |
|---|---|
| `shared-auth` | owns platform architecture, contracts, server, SDKs, infrastructure contract, and E2E proof |
| `fiducia-cloud` | owns Fiducia customer/admin app integration, local authorization, app sessions/cookies, and product cutover; relate work to DEN-2189 and existing DEN-1376/DEN-1379 |
| `ORESoftware` | owns shared cluster/GitOps application registration and protected deployment workflows where the canonical cluster repository lives |
| product orgs such as `sonus-auris`, `memebank`, `hypesiege`, `streempilot`, `quaestor-ledger`, and `messaging-intel` | own exact client registration, product-local tenant/resource authorization, migration, rollout, and rollback; relate consumer issues to DEN-2197 |
| `shared-auth-test` and product `*-test` orgs | own bounded synthetic fixtures and destructive/non-production validation; never receive production credentials or authority |

Each organization keeps its canonical Linear project and GitHub repository history. Cross-org work is related through IDs/links; it is not copied into one giant duplicate issue tree.

## Proposed GitHub Project: Shared Auth Delivery

The organization-level Projects-v2 board should be named **Shared Auth Delivery**.

### Fields

| Field | Values/purpose |
|---|---|
| Status | Backlog, Ready, In progress, In review, Blocked, Done |
| Workstream | Architecture, Infrastructure, Server/schema, Interfaces, SDKs, E2E, Migration, Operations, Governance |
| Realm | Shared, Customer, Admin, Product consumer |
| Environment | Design, Local, Test, Staging, Production |
| Risk | Low, Medium, High, Critical |
| Linear ID | canonical `DEN-*` identifier |
| Owning repository | repository responsible for implementation/evidence |
| Target date | delivery target; Linear remains authoritative when values differ |
| Evidence state | None, PR, CI, Deployed, Restore-tested, Load-tested |

### Views

1. **Delivery board** — grouped by Status.
2. **Realm isolation** — grouped by Realm, filtered to customer/admin boundaries.
3. **RDS cutover** — DEN-2189, DEN-2191, DEN-2193, DEN-2194, and DEN-2197 items.
4. **Release evidence** — grouped by Evidence state.
5. **Blocked work** — Status=Blocked, sorted by Risk and target date.
6. **Repository map** — grouped by Owning repository.
7. **Production gates** — Environment=Production and Evidence state not complete.

### Initial items

- `shared-auth/shared-auth-server.rs#1` — architecture / DEN-2189;
- `shared-auth/shared-auth-infra#6` — infrastructure / DEN-2191;
- `shared-auth/shared-auth-e2e#12` — E2E / DEN-2194;
- server/schema implementation items created under DEN-2193;
- per-product migration items created under DEN-2197;
- merged documentation PRs `shared-auth-infra#7`, `shared-auth-server.rs#36`, and the `.github` project-map PR as evidence rather than standalone implementation completion.

### Board status

The board specification is published here. The connected GitHub integration used for this change can create repository branches, commits, issues, and pull requests, but it does not expose GitHub Projects-v2 mutation. The `.github` repository also has Issues disabled, so the board-creation action cannot be tracked as a local `.github` issue.

Create/populate the board through an organization-admin GitHub Projects workflow, then add its URL to this document and [`ORG_CONTEXT.md`](ORG_CONTEXT.md). Until that happens, Linear and repository issues remain the operative planning surfaces; this document prevents field/view/ownership drift.

## Linkage rules

Every implementation pull request must:

- reference one canonical Linear issue;
- reference the owning repository's GitHub issue when Issues are enabled;
- explain what changed, why, impact/risk, and validation;
- link exact cross-repository dependencies rather than copying their descriptions;
- keep documentation-only and implementation completion distinct;
- attach or link exact-revision CI/deployment/restore/load evidence where required.

Every Linear implementation issue should attach exact GitHub PRs after publication and preserve dependencies/related work there. Linear status is not inferred merely from a merged documentation PR.

Every GitHub issue should link the canonical Linear issue/document and remain open until its own acceptance criteria are complete. Duplicate GitHub issues are closed/marked duplicate rather than becoming parallel authorities.

## Status mapping

| Linear | GitHub Project | Pull request/repository evidence |
|---|---|---|
| Backlog | Backlog | no implementation commitment yet |
| Todo / Ready | Ready | bounded issue and owner exist |
| In Progress | In progress | branch/implementation activity exists |
| In review | In review | ready PR on exact intended scope |
| Blocked | Blocked | blocker and required action are explicit |
| Done | Done | acceptance evidence complete; merged PR alone may be insufficient |

When the systems disagree, preserve both histories and resolve the mismatch explicitly. Do not silently rewrite either ledger.

## Adding a new repository or program

Before creating a repository:

1. prove that no existing repository owns the capability;
2. identify the canonical Linear project/parent issue;
3. define runtime, contract, SDK, infra, E2E, and deployment boundaries;
4. decide whether the repository is an application, library/package, interface, client, test, infrastructure, website, bridge, or inventory repo;
5. add the repository to this ownership map;
6. add the relevant GitHub Project item/fields once the board exists;
7. create initial issues with acceptance evidence rather than placeholder work;
8. preserve `*-infra` outside application monorepo/submodule trees.

For the current RDS/federated-auth program, existing repositories already cover every required boundary, so no new repository is required.
