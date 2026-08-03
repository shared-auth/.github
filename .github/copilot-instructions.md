# GitHub Copilot repository instructions

`/AGENTS.md` is the canonical policy for this repository. Follow it in full. This organization-level file is not automatically inherited by other repositories, so each repository must maintain a compatible root `AGENTS.md`.

Resolve every Git conflict semantically and with full context. Read both sides plus surrounding code, documentation, tests, schemas, generated artifacts, identity/session contracts, and provider integrations. When relevant and available, inspect 3–10 prior commits using `git log`, `git show`, and `git blame`. Review related repositories in this organization and relevant external organizations when behavior crosses repository boundaries. Never hastily accept `ours` or `theirs`; preserve compatible intent and produce a conceptual merge.

Operate non-destructively. Do not use `git stash`, `git reset`, `git clean`, `git filter-repo`, `git filter-branch`, history-rewriting rebase or amend operations, destructive checkout/restore, force pushes, ref deletion, pruning, recursive deletion, destructive database or infrastructure commands, credential/session invalidation, package unpublishing, or any equivalent action that discards, hides, rewrites, purges, or deletes state. Do not bypass hooks, tests, reviews, branch protections, or security checks.

Leave unrelated work untouched. Prefer inspection, additive branches, separate clean worktrees or clones, explicit staging, normal non-force pushes, dry runs, backups, additive migrations, and reversible roll-forward changes. If safe progress is blocked, preserve state and report the blocker.

Never expose tokens, cookies, OTP data, recovery codes, biometric data, secrets, personal data, or production data. Run relevant validation and document conflict decisions, risks, auth/session effects, and the linked Linear work item.

Linear project: https://linear.app/denman/project/githubcomshared-auth-acbca07bb390
