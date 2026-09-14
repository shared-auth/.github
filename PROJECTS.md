# Shared Auth project and repository map

This document is the canonical routing guide for planning and delivery across the `shared-auth` GitHub organization. Detailed Linear and Projects-v2 operating rules live in [`docs/LINEAR.md`](docs/LINEAR.md) and [`docs/GITHUB-PROJECTS.md`](docs/GITHUB-PROJECTS.md).

For authentication architecture terminology and source precedence, read [`docs/AUTH-CONTEXT-PROOF-TAXONOMY-AND-SOURCE-PRECEDENCE.md`](docs/AUTH-CONTEXT-PROOF-TAXONOMY-AND-SOURCE-PRECEDENCE.md) before interpreting older “dual auth”, “dual provider”, “dual proof”, or “canonical authority” documents.

## Canonical systems

| System | Authority | Canonical location |
|---|---|---|
| Linear | priority, dependencies, ownership, milestones, planning history, cross-project relationships | [`github.com/shared-auth`](https://linear.app/denman/project/githubcomshared-auth-acbca07bb390) |
| GitHub repositories | source, commits, branches, pull requests, review, CI, releases, deployment evidence | [`github.com/shared-auth`](https://github.com/shared-auth) |
| GitHub issues | repository-scoped implementation/evidence tracking | issue in the owning repository |
| GitHub Project | configured organization-wide execution view; never a replacement for repository or Linear history | [`shared-auth-project`, project 1](https://github.com/orgs/shared-auth/projects/1) |
| Organization `.github` | organization architecture/policy, repository/project routing, contribution/security guidance | this repository |
| `shared-auth-docs` | maintained human-facing/published documentation mirrors and product documentation | [`shared-auth/shared-auth-docs`](https://github.com/shared-auth/shared-auth-docs) |

Linear and GitHub are linked ledgers, not competing sources of truth. Linear owns planning state. GitHub owns source and immutable delivery evidence. A Linear status never proves code execution, and a merged documentation pull request never proves deployment, migration, restore, load, or production behavior.

## Architecture source map

No one document is globally authoritative for every concern.

| Concern | Canonical architecture/source |
|---|---|
| Cross-document terminology and precedence | [`AUTH-CONTEXT-PROOF-TAXONOMY-AND-SOURCE-PRECEDENCE.md`](docs/AUTH-CONTEXT-PROOF-TAXONOMY-AND-SOURCE-PRECEDENCE.md) |
| Realm isolation and strict subsystem/application-grant proof | [`FEDERATED-DUAL-PROOF-ARCHITECTURE.md`](docs/FEDERATED-DUAL-PROOF-ARCHITECTURE.md) |
| Supabase+Neon canonical principal/session/root-admin model | [`CANONICAL-IDENTITY-DATABASE-AND-RLS-MODEL.md`](docs/CANONICAL-IDENTITY-DATABASE-AND-RLS-MODEL.md) |
| Async/concurrency/formal refinement | [`ASYNC-AUTH-STATE-MACHINES-AND-FORMAL-VERIFICATION.md`](docs/ASYNC-AUTH-STATE-MACHINES-AND-FORMAL-VERIFICATION.md) |
| Provider resource aliases/immutable IDs | [`PROVIDER-RESOURCE-NAMING-AND-IDENTITY-TOPOLOGY.md`](docs/PROVIDER-RESOURCE-NAMING-AND-IDENTITY-TOPOLOGY.md) |
| Executable deployment topology contract | `shared-auth-interfaces/DUAL_PROVIDER_TOPOLOGY.md` + `schema/auth-topology.schema.json` |
| Executable server runtime/schema | exact `shared-auth-server.rs` revision and its runtime/declarative schema contracts |
| Product roadmap/parity | `shared-auth-docs/docs/product/` subject to the platform authorization boundaries above |

## Current architecture program

The admin/customer realm, federation, provider-symmetry, and rollout program spans several intentionally separate workstreams.

| Workstream | Linear | GitHub / source boundary |
|---|---|---|
| Architecture parent | [DEN-2189](https://linear.app/denman/issue/DEN-2189/shared-auth-isolate-admin-and-customer-authentication-on-separate) | [`shared-auth-server.rs#1`](https://github.com/shared-auth/shared-auth-server.rs/issues/1) + organization architecture docs |
| RDS/network/secrets/backup/restore | [DEN-2191](https://linear.app/denman/issue/DEN-2191/shared-auth-infra-provision-isolated-admincustomer-rds-data-planes-and) | `shared-auth-infra` |
| Realm/server/schema/customer federation and canonical migration | [DEN-2193](https://linear.app/denman/issue/DEN-2193/shared-auth-server-add-realm-isolation-and-federated-customer) | `shared-auth-server.rs`, `shared-auth-orm-core`, related contracts |
| Strict subsystem dual-proof interface/lib contract | [DEN-3810](https://linear.app/denman/issue/DEN-3810/shared-auth-interfaceslib-publish-strict-dual-proof-federation) | `shared-auth-interfaces`, `shared-auth-lib` |
| Formal async/concurrency verification | [DEN-3812](https://linear.app/denman/issue/DEN-3812/shared-auth-formal-methods-verify-strict-dual-proof-authorization) | formal specs/refinement artifacts in owning repositories |
| Browser/API/database/outage/load/restore evidence | [DEN-2194](https://linear.app/denman/issue/DEN-2194/shared-auth-e2e-prove-cross-app-sso-audience-isolation-revocation-and) | `shared-auth-e2e`, `shared-auth-test` exact-source certification where appropriate |
| Consumer migration and application-DB decoupling | [DEN-2197](https://linear.app/denman/issue/DEN-2197/shared-auth-rollout-migrate-consumers-and-remove-authentication) | issues/PRs in each owning product repository |
| Edge/Supabase/Neon IaC/secrets/DR reconciliation | [DEN-606](https://linear.app/denman/issue/DEN-606/shared-auth-close-dual-auth-release-test-repository-policy-and-history) and related infra issues | `shared-auth-infra` and provider/edge integration repos |
| Historical realm/RDS architecture | [Linear architecture document](https://linear.app/denman/document/admincustomer-authentication-data-planes-and-federated-customer-sso-8a7890cb3c82) | preserved with current reconciliation note |

Architecture/docs establish reviewed intent. They do not close provisioning, runtime, schema, E2E, migration, restore, load, formal-refinement, or rollout acceptance by themselves.

## Repository ownership

| Repository | Owns | Does not own |
|---|---|---|
| `.github` | organization architecture/policy, source precedence, repository/project map, shared contribution/security guidance | runtime code, secrets, deployment state |
| `shared-auth-docs` | maintained published architecture mirrors, product/parity/roadmap documentation, human-facing docs organization | executable runtime authority or secret configuration |
| `shared-auth-server.rs` | central authentication/identity runtime, realm/session/token/revocation behavior, declarative server schema, OAuth/OIDC/federation implementation | child-product resource authorization, cloud provisioning |
| `shared-auth-orm-core` | private server persistence/ORM implementation behind published interfaces/contracts | public identity wire authority or product authorization |
| `shared-auth-interfaces` | machine-readable/versioned identity, token, introspection, federation, event, error, config/topology, and compatibility contracts | runtime persistence/deployment state |
| `shared-auth-lib` | reusable verification, provider/proof composition helpers, guards, fail-closed decision policy | canonical child-product membership or direct product DB authority |
| `shared-auth-clients` | consumer SDKs/adapters by supported runtime/language | server persistence or product policy |
| `shared-auth-web-server.rs` | customer/user-facing HTML/read surface for Shared Auth itself | write API authority or product tenant authorization |
| `shared-auth-api-server.rs` | customer/non-admin write API surface where split from the web server | admin write authority or product tenant authorization |
| `shared-auth-admin-web-server.rs` | isolated admin HTML/read surface and admin presentation boundary | customer runtime fallback or non-admin product authorization |
| `shared-auth-admin-api-server.rs` | isolated admin write/API surface and privileged API admission | customer runtime fallback or product-domain RBAC |
| `shared-auth-infra` | provider/cloud integration, RDS/network/KMS/secret/backup/restore contracts, edge infrastructure, IaC/runbooks | application business code, application-startup DDL |
| `shared-auth-e2e` | black-box browser/API/database/outage/load/restore evidence and exact-revision integration gates | production authority or mock-only feature claims |
| `shared-auth-sync` | bounded offline/reconnect synchronization contracts for approved non-secret state | password/raw refresh-token replication or identity decisions |
| `shared-auth-nats-bridge.rs` | authenticated bounded event/revocation propagation and delivery evidence | canonical identity decisions or unbounded personal-data transport |
| `shared-auth-mcp-server.rs` | read-oriented diagnostics, contract discovery, agent-facing integration | privileged identity mutation without an explicit reviewed API |
| `shared-auth-monorepo` | application-source inventory and compatible package/submodule integration | infrastructure deployment source or `*-infra` submodule ownership |
| `shared-auth.github.io` | public marketing/integration guidance and claim-only public capability/roadmap rendering | secrets, private operational data, runtime authority |

### Authorization ownership rule

Shared Auth may own identity-plane administration and Shared Auth **identity organizations** needed for SSO/SCIM/domain/identity-policy administration. It does not become the universal organization/workspace/RBAC database for child products. Product organizations own product-local tenant/resource membership, roles, billing/entitlement grants, domain state, and product RLS.

A mapping from a product tenant to a Shared Auth identity organization is an explicit opaque association. Neither side's role vocabulary implies the other side's authorization.

## Cross-organization routing

Shared Auth is a platform dependency for many product organizations. Work remains in the organization that owns the affected implementation.

| GitHub organization | Planning rule |
|---|---|
| `shared-auth` | platform architecture, identity/proof contracts, runtime, SDKs, platform infrastructure contract, and E2E proof |
| `fiducia-cloud` | Fiducia customer/admin application integration, local authorization, app sessions/cookies, and product cutover; relate to existing Shared Auth/Fiducia Linear work |
| `ORESoftware` | shared middleware/contract tooling, cluster/GitOps integration, and protected deployment workflows where those canonical repositories live |
| product orgs such as `sonus-auris`, `zed-pkg`, `memebank`, `hypesiege`, `streempilot`, `quaestor-ledger`, and `messaging-intel` | exact client registration, product-local tenant/resource authorization, migration, rollout, rollback; relate consumer work to DEN-2197 |
| `shared-auth-test` and product `*-test` orgs | bounded synthetic/destructive non-production validation and exact-source certification; never receive production credentials/authority |

Each organization keeps its canonical Linear project and GitHub history. Cross-org work is related through stable IDs/links; it is not copied into one giant duplicate issue tree.

## GitHub Project: `shared-auth-project` (project 1)

The configured organization-level Projects-v2 execution target is [`shared-auth-project`, project 1](https://github.com/orgs/shared-auth/projects/1). An organization owner with Projects-v2 access must verify the current title, accessibility, fields, views, and items against this contract. If the link is missing or inaccessible to intended members, repair project 1 rather than silently introducing an unreviewed replacement number.

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
3. **Auth architecture program** — DEN-2189/2191/2193/3810/3812/2194/2197 and relevant DEN-606 provider/edge items.
4. **Release evidence** — grouped by Evidence state.
5. **Blocked work** — Status=Blocked, sorted by Risk and target date.
6. **Repository map** — grouped by Owning repository.
7. **Production gates** — Environment=Production and Evidence state not complete.

### Initial / canonical items

- `shared-auth/shared-auth-server.rs#1` — architecture / DEN-2189;
- `shared-auth/shared-auth-infra#6` — infrastructure / DEN-2191;
- server/schema implementation items under DEN-2193;
- interface/lib strict-proof work under DEN-3810;
- formal/refinement work under DEN-3812;
- `shared-auth/shared-auth-e2e#12` and successors — E2E / DEN-2194;
- per-product migration items under DEN-2197;
- documentation changes as evidence links, not standalone implementation completion.

### Project access and automation status

The board contract is published here and in [`docs/GITHUB-PROJECTS.md`](docs/GITHUB-PROJECTS.md). The connected repository integration may not expose Projects-v2 read/mutation, so this document does not claim that the live board currently matches the desired fields/views/items.

Projects automation must run through an organization-admin integration with explicit Projects-v2 scope. Credentials stay in approved secret storage and never enter source, logs, issues, PRs, or artifacts. Automation resolves project 1 exactly and fails closed on ambiguous/missing mappings; it must not silently create duplicate boards.

Until project metadata is verified, Linear and repository issues remain the authoritative planning/implementation surfaces.

## Linkage rules

Every implementation pull request must:

- reference one canonical Linear issue;
- reference the owning repository's GitHub issue when Issues are enabled;
- explain what changed, why, impact/risk, and validation;
- link exact cross-repository dependencies rather than copying their descriptions;
- keep documentation-only and implementation completion distinct;
- attach/link exact-revision CI/deployment/restore/load evidence where required.

Every Linear implementation issue should attach exact GitHub PRs after publication and preserve dependencies/related work there. Linear status is not inferred merely from a merged documentation change.

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

When systems disagree, preserve both histories and resolve the mismatch explicitly. Do not silently rewrite either ledger.

## Adding a new repository or program

Before creating a repository:

1. prove that no existing repository owns the capability;
2. identify the canonical Linear project/parent issue;
3. define runtime, contract, SDK, infra, E2E, and deployment boundaries;
4. decide whether the repository is an application, library/package, interface, client, test, infrastructure, website, bridge, docs, ORM-private implementation, or inventory repo;
5. add the repository to this ownership map;
6. add the relevant GitHub Project item/fields once project access is verified;
7. create initial issues with acceptance evidence rather than placeholder work;
8. preserve `*-infra` outside application monorepo/submodule trees.

For the current realm/federation/canonical-identity program, existing repositories cover the required boundaries. Do not create a new repository merely to avoid deciding ownership.