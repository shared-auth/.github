# GitHub Copilot repository instructions

`/AGENTS.md` is the canonical guidance for this repository. Keep this mirror aligned with it.

## Safe change control

**avoid git rebase in favor of git merge**

Inspect the worktree before mutation and publishing. Never run destructive Git commands such as `git rebase`, `git stash`, `git reset`, `git clean`, `git filter-repo`, `git checkout --`, `git restore`, `git branch -D`, `git reflog expire`, `git gc --prune`, `git push --force`, or `git push -f`. Never run destructive filesystem commands such as `rm`, `mv`, `sed`, `find -delete`, `xargs rm`, `truncate`, `shred`, or `dd`. Never force-push, bypass checks, or discard unfamiliar uncommitted or untracked work. Stop and report unexpected changes or ambiguous ownership.

## Linear tracking

Every discovered feature, fix, enhancement, bug, vulnerability, reliability concern, documentation gap, or technical-debt item requires a canonical Linear issue before implementation. Search first, create only when needed, link the issue in every pull request, keep status and evidence synchronized, and fail closed when GitHub-to-Linear routing is missing or ambiguous.

## Semantic conflict resolution

Resolve every Git conflict semantically and with full context. Read the merge base, both sides, surrounding code, documentation, tests, and contracts. When available, inspect at least 3 and up to 10 relevant prior commits using `git log`, `git show`, and `git blame`. Review related repositories in this organization and relevant external-organization repositories whenever shared APIs, schemas, libraries, generated artifacts, infrastructure, or behavior are involved.

Never hastily accept `ours`, `theirs`, current, or incoming, discard unfamiliar changes, or resolve only from conflict markers. Preserve compatible intent from every side, synthesize a conceptual merge, run the relevant validation, and document intentional tradeoffs in GitHub and Linear.
