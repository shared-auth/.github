# GitHub Projects operating model

The configured organization-level execution board is:

- **Organization:** [`shared-auth`](https://github.com/shared-auth)
- **Configured project:** [`shared-auth-project`](https://github.com/orgs/shared-auth/projects/1)
- **Project number:** `1`
- **Canonical planning project:** [`github.com/shared-auth` in Linear](https://linear.app/denman/project/githubcomshared-auth-acbca07bb390)

The configured URL and number are mirrored in the organization profile and project-routing documents. The connected GitHub App used for this documentation change can manage repositories, files, issues, and pull requests, but it cannot read or mutate Projects v2 metadata. Therefore this document treats project 1 as the configured execution-board target while avoiding unsupported claims about its current title, fields, views, items, or accessibility.

An organization owner with Projects v2 access must verify the link and reconcile the board against this contract. If project 1 does not exist or is inaccessible to intended members, create or repair it rather than changing documentation to an unreviewed replacement number.

## Responsibility boundary

The GitHub Project is a cross-repository execution view. It is not the product backlog and it is not delivery evidence by itself.

- Linear owns priorities, ownership, dependencies, milestones, parent/child planning, and target dates.
- Repository issues own bounded implementation discussions and acceptance evidence.
- Pull requests and commits own reviewed source history.
- Checks, releases, deployments, migrations, restore tests, and load tests own immutable delivery evidence.
- The GitHub Project summarizes that work across repositories and links back to the canonical records.

## Required fields

Reconcile project 1 to the following minimum schema:

| Field | Type / values | Purpose |
|---|---|---|
| Status | Backlog, Ready, In progress, In review, Blocked, Done | execution state mapped from Linear and GitHub evidence |
| Workstream | Architecture, Infrastructure, Server/schema, Interfaces, SDKs, E2E, Migration, Operations, Governance | cross-repository grouping |
| Realm | Shared, Customer, Admin, Product consumer | identity/data-plane boundary |
| Environment | Design, Local, Test, Staging, Production | target environment or evidence stage |
| Risk | Low, Medium, High, Critical | operational/security delivery risk |
| Linear ID | text | canonical `DEN-*` identifier |
| Owning repository | text or repository | implementation/evidence owner |
| Target date | date | execution target; Linear wins when values differ |
| Evidence state | None, PR, CI, Deployed, Restore-tested, Load-tested | strongest completed evidence |

Additional fields are allowed when they do not duplicate or contradict the canonical systems.

## Required views

1. **Delivery board** — grouped by Status.
2. **Repository map** — grouped by Owning repository.
3. **Realm isolation** — grouped by Realm, focused on customer/admin boundaries.
4. **RDS cutover** — the DEN-2189 architecture program and its infrastructure, server/schema, E2E, and migration work.
5. **Release evidence** — grouped by Evidence state.
6. **Blocked work** — Status=Blocked, sorted by Risk and target date.
7. **Production gates** — Environment=Production with incomplete evidence.

## Item policy

Add the canonical repository issue or pull request, not a duplicate draft item, whenever one exists. Store the canonical Linear identifier in the `Linear ID` field and link the Linear issue in the GitHub item body or issue description.

Initial and continuing program items should include:

- `shared-auth/shared-auth-server.rs#1` — architecture / DEN-2189;
- `shared-auth/shared-auth-infra#6` — infrastructure / DEN-2191;
- `shared-auth/shared-auth-e2e#12` — E2E / DEN-2194;
- bounded server/schema implementation issues under DEN-2193;
- per-product migration issues under DEN-2197;
- SDK, interface, release, and governance issues that span multiple repositories;
- merged documentation pull requests only as evidence, not as substitutes for unfinished implementation items.

## Automation rules

Automation may add or update project items only when it has explicit organization-project scope and can prove the target organization and project number. It must fail closed on ambiguous mappings.

Recommended behavior:

1. resolve the GitHub organization by immutable account ID where available;
2. resolve the canonical Linear project from the central registry;
3. add the owning repository issue or pull request;
4. write `Linear ID`, Workstream, Realm, Environment, Risk, Owning repository, and Evidence state;
5. never infer `Done` solely from a merge when deployment, migration, restore, or load evidence is required;
6. report drift instead of silently creating a second organization project.

Tokens used for Projects automation must be stored as organization or repository secrets, use the narrowest available scope, and never appear in source, workflow YAML, logs, artifacts, issues, pull requests, or Linear documents.

## Verification checklist

An organization owner should periodically confirm:

- project 1 resolves for intended users;
- its title and description identify it as the `shared-auth` execution board;
- required fields and views exist;
- initial architecture-program items are present;
- item `Linear ID` values link to the canonical project;
- stale duplicate draft items are removed or converted to canonical issue/PR items;
- project status does not falsely claim completion beyond immutable evidence;
- no credentials or restricted planning details are exposed.

Record material corrections in a GitHub pull request and the corresponding Linear issue or project update. Keep [`docs/LINEAR.md`](LINEAR.md), [`docs/PROJECTS.md`](PROJECTS.md), root [`PROJECTS.md`](../PROJECTS.md), the organization profile, and [`project-context.yaml`](../project-context.yaml) synchronized.
