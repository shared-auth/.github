# Governance

<!-- ore-org-baseline:begin -->
## Sources of truth

- GitHub is authoritative for source, policy, architecture records, public organization context, reviewed implementation, and immutable commit history.
- [github.com/shared-auth](https://linear.app/denman/project/githubcomshared-auth-acbca07bb390) is the planning and delivery ledger.
- Repository-local documentation is authoritative for repository-specific behavior and may strengthen this baseline.
- Private member context belongs in an approved private system, such as `.github-private`, never in this public repository.

## Change control

Material policy and architecture changes use issues or pull requests, focused commits, reviewable diffs, tests, and linked planning context. Existing content must be preserved unless a change explicitly supersedes it. Generated and mirrored artifacts must be updated from their authoritative source.

Conflicts are resolved semantically with full history and cross-repository context. Destructive operations, history rewrites, force pushes, bypasses, and deletion of shared resources are default-deny and require exact authorization.

## Precedence

A repository may impose stricter requirements. It must not weaken secret handling, non-destructive collaboration, semantic conflict resolution, evidence-backed completion, or required review and checks.
<!-- ore-org-baseline:end -->
