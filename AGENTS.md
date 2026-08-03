# Organization-wide agent instructions

This is the canonical public agent-safety policy for **shared-auth**. It applies directly to this repository and is the minimum policy every repository in the organization must mirror in its root `AGENTS.md` or replace with a stricter equivalent.

An organization `.github/AGENTS.md` is not automatically inherited by coding agents. Repository owners must copy or synchronize this policy into each repository and must not weaken it locally.

## Required semantic conflict-resolution declaration

> Resolve any and all Git conflicts semantically, with full context, including reviewing 3–10 relevant prior commits when useful. Never hastily pick sides in a conflict; merge compatible intent conceptually using maximum context and complete awareness of this GitHub organization's repositories and relevant external-organization repositories.

Before finalizing any conflict resolution:

1. Read both sides, surrounding code and documentation, relevant tests, schemas, generated artifacts, deployment files, and public contracts—not only conflict markers.
2. Inspect the affected history. When available and relevant, review at least 3 and up to 10 prior commits with `git log`, `git show`, and `git blame`.
3. Inspect related repositories in this organization and relevant external organizations whenever APIs, schemas, shared libraries, identity providers, token/session contracts, infrastructure, generated code, release processes, or runtime behavior cross repository boundaries.
4. Preserve all compatible intent and invariants. Synthesize a conceptual merge instead of accepting `ours` or `theirs` wholesale.
5. Run the most relevant tests, formatters, linters, builds, contract checks, security checks, and end-to-end checks.
6. Document intentional tradeoffs, incompatible requirements, and discarded behavior in the commit or pull-request description.

Never resolve a conflict by deleting unfamiliar work, relying only on the newest snapshot, or choosing a side merely because it is easier.

## Deny-by-default destructive operations

Automated agents must not execute or recommend commands whose purpose or practical effect is to discard, hide, rewrite, purge, delete, or irreversibly mutate existing state. A dirty worktree, an inconvenient branch, a failed migration, or a conflict is never permission to destroy state.

The following operations are explicitly blacklisted for agents:

- **Git worktree/history destruction or concealment:** every form of `git stash`, every form of `git reset`, `git clean`, `git filter-repo`, `git filter-branch`, history-rewriting `git rebase`, `git commit --amend`, `git checkout -- <path>`, destructive `git restore`, `git branch -D`, deletion of refs or tags, `git reflog expire`, aggressive/pruning `git gc`, `git push --force`, `git push --force-with-lease`, and equivalent worktree or history rewrites.
- **Filesystem destruction:** `rm -rf`, recursive or bulk deletion, `find -delete`, destructive overwrites, disk formatting, mass moves that erase destinations, or permission/ownership changes that can remove access.
- **Data destruction:** `DROP`, `TRUNCATE`, unbounded `DELETE`, destructive schema rollback, irreversible migrations, identity/session purge, storage-bucket purge, queue/topic deletion, and bulk record mutation without a reviewed, bounded, reversible plan.
- **Infrastructure destruction:** `kubectl delete`, `helm uninstall`, `terraform destroy`, `pulumi destroy`, cloud-provider delete/purge commands, cluster or namespace teardown, secret/key/certificate revocation or rotation, identity-provider teardown, and equivalent destructive control-plane actions.
- **Release and governance destruction:** package or release unpublishing, artifact deletion, registry purges, disabling branch protection, bypassing required reviews, disabling tests or security checks, and use of `--no-verify` to evade repository policy.

This blacklist is illustrative, not exhaustive. When an operation may destroy, discard, conceal, or rewrite state, treat it as prohibited by default. Agents may prepare a reviewed runbook for a human, but must not execute the destructive operation themselves.

### Safe alternatives

- Inspect with `git status`, `git diff`, `git log`, `git show`, and `git blame`.
- Leave unrelated or uncommitted work untouched.
- Use a new additive branch, a separate clean worktree, or a separate clone when available.
- Stage explicit intended paths; do not stage unrelated work.
- Commit new work normally and push without force.
- Prefer dry runs, read-only queries, backups, additive migrations, and reversible roll-forward changes.
- When safe progress is impossible, report the exact blocker and preserve all state.

## Secrets, identity, and sensitive data

Never print, log, commit, paste into issues, or expose access tokens, refresh tokens, session cookies, credentials, private keys, OTP seeds or codes, biometric templates, recovery codes, personal data, production data, or secret-bearing environment variables. Use placeholders in examples and redact diagnostics.

Do not revoke or rotate live credentials, invalidate sessions, alter identity-provider configuration, or mutate production authorization state autonomously. Prepare a bounded human-run incident or migration plan instead.

## Pull requests and validation

Reference the relevant Linear issue or project in substantial pull requests. Keep changes scoped, explain risks and migration effects, list validation performed, and state whether conflicts occurred and how they were resolved.

Canonical Linear project: https://linear.app/denman/project/githubcomshared-auth-acbca07bb390

## Precedence

Repository-local instructions may add stricter requirements, especially for authentication, authorization, session integrity, OTP, biometrics, tenant isolation, and credential handling, but they must not weaken the semantic conflict-resolution policy, destructive-operation blacklist, secret-handling requirements, or validation expectations in this file.
