# Linear operating model

Linear is the planning system of record for the `shared-auth` GitHub organization. GitHub remains authoritative for source code, commits, pull requests, reviews, checks, releases, deployments, and exact-revision evidence.

## Canonical identity

- **Linear project:** [`github.com/shared-auth`](https://linear.app/denman/project/githubcomshared-auth-acbca07bb390)
- **Project ID:** `4bbe0ba4-d7f1-49ce-8f41-afd2cff6c2a2`
- **Workspace:** `denman`
- **Team:** `DEN` / `Denman`
- **Team ID:** `eb8ab169-5afe-4b6f-9cab-3f2aa3e887dc`
- **GitHub organization:** [`shared-auth`](https://github.com/shared-auth)
- **GitHub execution-board configuration:** [`shared-auth-project`, project 1](https://github.com/orgs/shared-auth/projects/1)

The immutable IDs above are authoritative when a display name or URL changes. The reviewed central mapping is maintained in `ORESoftware/ai-agent-coordinator.rs/config/org-project-registry.yaml`; the organization mirror is [`project-context.yaml`](../project-context.yaml).

## Source-of-truth boundaries

| Concern | Authority |
|---|---|
| Priorities, ownership, milestones, dependencies, parent/child planning, target dates | Linear |
| Repository ownership and implementation boundaries | [`PROJECTS.md`](../PROJECTS.md) and repository-local instructions |
| Code, branches, commits, pull requests, reviews, checks, releases | GitHub |
| Cross-repository execution view | GitHub Project, when accessible |
| Production, restore, load, migration, and rollback evidence | Exact GitHub revision plus the owning system's immutable evidence |

Do not copy a complete backlog between systems. Link the canonical record instead. A pull request does not become planning history, and a Linear status does not prove that code was built, reviewed, deployed, restored, or load-tested.

## Issue structure

Use one canonical Linear parent for a program that spans repositories. Create bounded child issues for work that has a distinct owner, repository, acceptance boundary, or rollout gate.

Every implementation issue should identify:

1. the owning GitHub repository;
2. the user, operator, security, or developer outcome;
3. explicit acceptance evidence;
4. blockers and related issues rather than copied descriptions;
5. rollout and rollback expectations when behavior, schema, tokens, sessions, realms, or infrastructure change;
6. the exact pull request, commit, workflow run, deployment, restore, or test evidence after publication.

Do not close an implementation issue merely because an architecture or documentation pull request merged. Close it only when its own acceptance criteria are complete.

## Status mapping

| Linear status | GitHub Project status | Required interpretation |
|---|---|---|
| Backlog | Backlog | useful work is described but not committed |
| Todo / Ready | Ready | owner, repository, scope, and acceptance criteria exist |
| In Progress | In progress | implementation or evidence work is active |
| In review | In review | a reviewable pull request or equivalent evidence is published |
| Blocked | Blocked | the blocker and required unblocking action are explicit |
| Done | Done | acceptance evidence is complete; merge alone may be insufficient |
| Canceled / Duplicate | Removed or archived | preserve the reason and canonical replacement |

When systems disagree, preserve both histories and resolve the mismatch explicitly. Never silently rewrite one ledger to make it resemble the other.

## GitHub linkage

A substantial pull request should reference its canonical `DEN-*` issue and explain:

- what changed and why;
- compatibility and security impact;
- affected repositories or consumers;
- validation performed at the exact head revision;
- rollout, rollback, migration, and evidence gaps;
- whether the pull request completes the Linear acceptance criteria or only advances them.

A Linear issue should link the final pull request and canonical merge commit. For cross-organization work, use related/blocking relationships and exact links; do not create a duplicate issue tree in every organization.

## Cross-organization routing

Work stays with the organization that owns the implementation:

- `shared-auth` owns identity/session/token/realm contracts, server behavior, SDKs, platform infrastructure contracts, and platform E2E proof.
- `ORESoftware` owns shared cluster and GitOps integration where the canonical cluster repository lives.
- Product organizations own product-local authorization, client registration, migration, rollout, and rollback.
- Test organizations own bounded synthetic and destructive non-production validation.

Each organization uses its own canonical Linear project from the central registry. Relate issues across projects instead of moving all work into `github.com/shared-auth`.

## Public and sensitive data boundary

This repository is public. Linear may contain private planning context. Never mirror credentials, tokens, OTP material, biometric material, customer data, incident details, private topology, unpublished commercial information, or other restricted content into public GitHub documentation, issues, pull requests, logs, or artifacts.

Use public identifiers, links, sanitized acceptance criteria, and redacted evidence only. If a public link cannot safely explain a private blocker, state the blocker category and keep sensitive detail in the authorized system.

## Routine maintenance

At each material delivery checkpoint:

1. update the Linear issue status and blockers;
2. attach the exact GitHub pull request or commit;
3. update the GitHub Project item when project access is available;
4. record deployment, migration, restore, load, or rollback evidence where required;
5. reconcile stale links or contradictory status without deleting historical context.

The organization profile, [`docs/PROJECTS.md`](PROJECTS.md), [`docs/GITHUB-PROJECTS.md`](GITHUB-PROJECTS.md), root [`PROJECTS.md`](../PROJECTS.md), and `project-context.yaml` must agree on canonical identifiers and authority boundaries.
