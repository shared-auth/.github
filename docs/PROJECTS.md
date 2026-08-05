<!-- org-project-routing:start -->
# Project routing

- **GitHub organization:** [shared-auth](https://github.com/shared-auth)
- **Canonical GitHub Project:** [shared-auth-project](https://github.com/orgs/shared-auth/projects/1) (project 1)
- **Canonical Linear project:** [planning workspace](https://linear.app/denman/project/githubcomshared-auth-acbca07bb390)
- **Organization documentation repository:** [shared-auth/.github](https://github.com/shared-auth/.github)

## Source-of-truth boundaries

GitHub is authoritative for repositories, commits, pull requests, reviews, CI checks, releases, deployable artifacts, and runtime evidence. Linear is authoritative for product planning, priorities, ownership, dependencies, milestones, and status reporting. The GitHub Project is the organization-level execution board and should contain the governance issue maintained by this repository.

## Change and merge policy

Documentation branches must be reviewed through pull requests and merged after checks pass. Concurrent edits are reconciled semantically against the latest default branch: this managed routing block is regenerated while all unrelated prose outside the block is preserved. Do not resolve conflicts by blindly choosing one side.
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