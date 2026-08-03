## Summary

Describe the intent, affected repositories or contracts, and user or operator impact.

## Tracking

Linear issue or canonical URL: <!-- required, for example DEN-123 -->

Describe any related GitHub issues, dependencies, and cross-repository changes.

## Validation

List the tests, builds, linters, integrity checks, security checks, contract checks, and end-to-end checks that were run. Explain anything not run.

## Safe-change checklist

- [ ] I linked the canonical Linear issue and synchronized scope, acceptance criteria, and validation evidence.
- [ ] I inspected the worktree before mutation and before publishing and preserved all unfamiliar, uncommitted, and untracked work.
- [ ] I followed **avoid git rebase in favor of git merge** and did not rewrite shared history.
- [ ] I did not use prohibited destructive Git or filesystem commands, force-push, bypass checks, or disable security controls.
- [ ] Any newly discovered feature, fix, enhancement, bug, vulnerability, reliability concern, documentation gap, or technical debt has a linked Linear issue.

## Semantic conflict-resolution checklist

Resolve conflicts semantically and with full context; never clear conflict markers by hastily selecting a side.

- [ ] I inspected the merge base, both sides, surrounding code or documentation, and the affected tests and contracts.
- [ ] When history was available, I reviewed at least 3 and up to 10 relevant commits from both sides using path-scoped `git log`, `git show`, and `git blame` where useful.
- [ ] I reviewed related repositories in this GitHub organization and relevant repositories in external organizations for cross-repository APIs, schemas, generated artifacts, infrastructure, or behavior.
- [ ] I produced a conceptual merge and did not accept `ours`, `theirs`, current, or incoming wholesale.
- [ ] I scanned the complete worktree for unresolved conflict markers.
- [ ] I ran the affected tests and validation checks after resolving conflicts.
- [ ] I documented non-obvious decisions, incompatible requirements, discarded intent, and operational tradeoffs in GitHub and Linear.
- [ ] I confirmed that no credentials, private data, or customer information were exposed while gathering full context.
