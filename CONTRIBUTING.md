# Contributing

## Work tracking

Every discovered feature, fix, enhancement, bug, vulnerability, reliability concern, documentation gap, or technical-debt item must have a Linear issue in the canonical project before implementation starts. Search first, link the existing issue when possible, and create one only when necessary. Pull requests must include the Linear identifier or canonical Linear URL and keep acceptance criteria and validation evidence synchronized. Stop rather than guess when project routing is missing or ambiguous.

## Safe change control

**avoid git rebase in favor of git merge**

Preserve uncommitted and untracked work. Inspect the worktree before mutation and publishing. Do not use destructive Git commands, including `git rebase`, `git stash`, `git reset`, `git clean`, `git filter-repo`, `git checkout --`, `git restore`, `git branch -D`, `git reflog expire`, `git gc --prune`, `git push --force`, or `git push -f`. Do not use destructive filesystem commands, including `rm`, `mv`, `sed`, `find -delete`, `xargs rm`, `truncate`, `shred`, or `dd`. Never force-push, bypass required checks, or discard unfamiliar work. Stop and report unexpected changes or ambiguous ownership.

## Mandatory semantic conflict resolution

Resolve every Git conflict semantically and with full context. Conflict markers are the starting point for analysis, not the complete context.

Before finalizing a resolution:

1. Inspect the merge base, both sides of the conflict, surrounding code or documentation, tests, schemas, migrations, and contracts.
2. When history is available, inspect at least 3 and up to 10 relevant commits from both sides. Use path-scoped `git log`, `git show`, and `git blame` where useful.
3. Review related repositories in this GitHub organization and relevant repositories in external organizations whenever APIs, shared libraries, generated artifacts, infrastructure, deployments, or documentation cross repository boundaries.
4. Never accept `ours`, `theirs`, current, or incoming wholesale merely to clear the conflict. Preserve compatible intent and produce a conceptual merge.
5. Scan the complete worktree for unresolved conflict markers. Run all affected tests, formatters, linters, builds, integrity checks, contract checks, security checks, and end-to-end validation.
6. Document non-obvious choices, incompatible requirements, discarded intent, and operational tradeoffs in the commit, pull-request description, and Linear issue.

Full context means all relevant context the contributor is authorized to access. It never authorizes disclosure of credentials, private data, or customer information.

Repository-local instructions may add stricter requirements but must not weaken this policy.
