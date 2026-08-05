<!-- org-project-routing:start -->
# Project routing

- **GitHub organization:** [`shared-auth`](https://github.com/shared-auth)
- **Configured GitHub Project:** [`shared-auth-project`](https://github.com/orgs/shared-auth/projects/1) (project 1)
- **Canonical Linear project:** [`github.com/shared-auth`](https://linear.app/denman/project/githubcomshared-auth-acbca07bb390)
- **Organization documentation repository:** [`shared-auth/.github`](https://github.com/shared-auth/.github)
- **Detailed repository/program map:** [`../PROJECTS.md`](../PROJECTS.md)
- **Linear operating model:** [`LINEAR.md`](LINEAR.md)
- **GitHub Projects operating model:** [`GITHUB-PROJECTS.md`](GITHUB-PROJECTS.md)

## Source-of-truth boundaries

GitHub is authoritative for repositories, commits, pull requests, reviews, CI checks, releases, deployable artifacts, and runtime evidence. Linear is authoritative for product planning, priorities, ownership, dependencies, milestones, and status reporting. The configured organization Project is the cross-repository execution view; it does not replace either system.

The connected GitHub App cannot read or mutate Projects v2 metadata, so project 1 is documented as the configured target rather than represented as independently verified. An organization owner with project access must reconcile its fields, views, items, and accessibility against [`GITHUB-PROJECTS.md`](GITHUB-PROJECTS.md). Automation must fail closed rather than silently create a second board.

## Linkage rules

Substantial work should have one canonical `DEN-*` issue, one owning repository, and exact GitHub evidence. Pull requests link the Linear issue and explain scope, risk, compatibility, validation, rollout, rollback, and remaining evidence. Linear issues attach the final pull request and merge commit. Cross-organization work is related by exact IDs and links rather than copied into parallel issue trees.

## Change and merge policy

Documentation branches must be reviewed through pull requests and merged after available checks pass. Concurrent edits are reconciled semantically against the latest default branch: managed routing blocks may be regenerated while unrelated prose and newer security/operational safeguards are preserved. Do not resolve conflicts by blindly choosing one side.
<!-- org-project-routing:end -->

## Active cross-organization dependency

### MemeBank asynchronous-analysis authorization

- **Dependency plan:** [MEMEBANK_ANALYSIS_AUTHORIZATION.md](./MEMEBANK_ANALYSIS_AUTHORIZATION.md)
- **MemeBank Linear issue:** [DEN-1535](https://linear.app/denman/issue/DEN-1535/implement-no-plaintext-disk-analysis-streams-and-client-vault-fail)
- **MemeBank execution issue:** [mbk-ocr-api#23](https://github.com/memebank/mbk-ocr-api/issues/23)
- **Shared-auth interface issue:** [shared-auth-interfaces#16](https://github.com/shared-auth/shared-auth-interfaces/issues/16)
- **Shared-auth server issue:** [shared-auth-server.rs#39](https://github.com/shared-auth/shared-auth-server.rs/issues/39)
- **Cross-org E2E issue:** [shared-auth-e2e#13](https://github.com/shared-auth/shared-auth-e2e/issues/13)
- **Merged exact-version provider:** [mbk-ocr-api#21](https://github.com/memebank/mbk-ocr-api/pull/21)
- **Shared-auth durable Project card:** [.github#16](https://github.com/shared-auth/.github/issues/16)

Shared-auth must provide short-lived workload identity and stable allow/deny/unavailable decision semantics before MemeBank performs any object-store or KMS access. Completion requires interfaces, server enforcement, client support, durable MemeBank state comparison, revocation behavior, cross-tenant E2E, audit redaction, and production activation—not documentation alone.
