# Contributing

## Mandatory semantic conflict resolution

Resolve every Git conflict semantically and with full context. Conflict markers are the starting point for analysis, not the complete context.

Before finalizing a resolution:

1. Inspect the merge base, both sides of the conflict, surrounding code or documentation, tests, schemas, migrations, and contracts.
2. When history is available, inspect at least 3 and up to 10 relevant commits from both sides. Use path-scoped `git log`, `git show`, and `git blame` where useful.
3. Review related repositories in this GitHub organization and relevant repositories in external organizations whenever APIs, shared libraries, generated artifacts, infrastructure, deployments, or documentation cross repository boundaries.
4. Never accept `ours`, `theirs`, current, or incoming wholesale merely to clear the conflict. Preserve compatible intent and produce a conceptual merge.
5. Scan the complete worktree for unresolved conflict markers. Run all affected tests, formatters, linters, builds, integrity checks, contract checks, and end-to-end validation.
6. Document non-obvious choices, incompatible requirements, discarded intent, and operational tradeoffs in the commit or pull-request description.

Full context means all relevant context the contributor is authorized to access. It never authorizes disclosure of credentials, private data, or customer information.

Repository-local instructions may add stricter requirements but must not weaken this policy.
