# GitHub Copilot repository instructions

`/AGENTS.md` is the canonical policy for this repository. Follow it in full. This organization-level file is not automatically inherited by other repositories, so each repository must maintain a compatible root `AGENTS.md`.

Resolve every Git conflict semantically and with full context. Read both sides plus surrounding code, documentation, tests, schemas, generated artifacts, identity/session contracts, and provider integrations. When relevant and available, inspect 3–10 prior commits using `git log`, `git show`, and `git blame`. Review related repositories in this organization and relevant external organizations when behavior crosses repository boundaries. Never hastily accept `ours` or `theirs`; preserve compatible intent and produce a conceptual merge.

Operate non-destructively. Do not use `git stash`, `git reset`, `git clean`, `git filter-repo`, `git filter-branch`, history-rewriting rebase or amend operations, destructive checkout/restore, force pushes, ref deletion, pruning, recursive deletion, destructive database or infrastructure commands, credential/session invalidation, package unpublishing, or any equivalent action that discards, hides, rewrites, purges, or deletes state. Do not bypass hooks, tests, reviews, branch protections, or security checks.

Leave unrelated work untouched. Prefer inspection, additive branches, separate clean worktrees or clones, explicit staging, normal non-force pushes, dry runs, backups, additive migrations, and reversible roll-forward changes. If safe progress is blocked, preserve state and report the blocker.

Never expose tokens, cookies, OTP data, recovery codes, biometric data, secrets, personal data, or production data. Run relevant validation and document conflict decisions, risks, auth/session effects, and the linked Linear work item.

Linear project: https://linear.app/denman/project/githubcomshared-auth-acbca07bb390

<!-- ore-org-baseline:begin -->
Read and obey [`../agents.md`](../agents.md); the lowercase file is canonical.

At minimum: preserve concurrent work; fetch before editing and before pushing; avoid git rebase in favor of git merge; never use `git stash`, `git reset`, `git clean`, `git filter-repo`, force-push, or another destructive operation without exact authorization; resolve conflicts semantically using the merge base, 3–10 relevant commits, tests, contracts, Linear context, and related repositories; never choose `ours` or `theirs` wholesale; scan for conflict markers; validate affected behavior; and never claim remote completion without authoritative evidence.
<!-- ore-org-baseline:end -->
