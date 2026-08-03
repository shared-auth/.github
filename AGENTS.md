# Organization-wide agent instructions

These instructions are mandatory for human and automated contributors working in this repository. Treat them as organization-level context whenever work spans related repositories.

## Safe change control

Preserve existing work and use reversible, reviewable operations.

- **avoid git rebase in favor of git merge**
- Inspect `git status --short --branch` before making changes and again before publishing them.
- Never run destructive Git commands, including `git rebase`, `git stash`, `git reset`, `git clean`, `git filter-repo`, `git checkout --`, `git restore`, `git branch -D`, `git reflog expire`, `git gc --prune`, `git push --force`, or `git push -f`.
- Never run destructive filesystem commands, including `rm`, `mv`, `sed`, `find -delete`, `xargs rm`, `truncate`, `shred`, or `dd`. Use explicit, reviewable file APIs or targeted patch operations instead.
- Never force-push, bypass required reviews or checks, disable security controls, or discard unfamiliar, uncommitted, or untracked work.
- When unexpected worktree changes, ambiguous ownership, or a potentially destructive requirement is encountered, stop and report the condition. Do not hide it with a stash, reset, cleanup, or history rewrite.

## Mandatory Linear tracking

Every discovered feature, fix, enhancement, bug, vulnerability, reliability concern, documentation gap, or technical-debt item must be represented by a Linear issue in the canonical project before implementation begins.

1. Search Linear first and link the existing issue when one already covers the work.
2. Create a new issue when no suitable issue exists.
3. Include the Linear identifier or canonical Linear URL in every pull request and material implementation commit.
4. Keep scope, acceptance criteria, validation evidence, dependencies, and final status synchronized between GitHub and Linear.
5. If the GitHub-to-Linear mapping is missing or ambiguous, stop and report it rather than guessing or making an untracked drive-by change.

## Semantic conflict resolution

Resolve every Git conflict semantically and with full context.

Before finalizing a conflict resolution:

1. Read both sides, the merge base, surrounding code or documentation, and the relevant tests and contracts—not only the conflict markers.
2. Inspect the relevant Git history. When available, review at least 3 and up to 10 prior commits for the affected files or subsystem with `git log`, `git show`, and `git blame` as useful.
3. Review related repositories in this GitHub organization and relevant repositories in external organizations whenever APIs, schemas, generated artifacts, infrastructure, shared libraries, deployment behavior, or documentation cross repository boundaries.
4. Preserve the intent and invariants of all compatible changes. Synthesize a conceptual merge instead of accepting `ours`, `theirs`, current, or incoming wholesale.
5. Run the most relevant tests, formatters, linters, builds, contract checks, security checks, and end-to-end checks after resolving the conflict.
6. Document intentional behavioral choices, incompatible requirements, or discarded intent in the commit or pull-request description and its Linear issue.

Never resolve a conflict by hastily picking one side, deleting unfamiliar changes, or relying only on the latest snapshot. Maximize contextual and conceptual awareness across the organization and its external dependencies before completing the merge.

## Precedence

Repository-local instructions may add stricter requirements, but they must not weaken this safe-change, Linear-tracking, or semantic conflict-resolution policy.
