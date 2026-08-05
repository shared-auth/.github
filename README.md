# shared-auth organization defaults

This public `.github` repository is the canonical home for shared-auth organization profile content, community-health defaults, contribution guidance, issue and pull-request templates, reusable policy checks, and public agent-safety declarations.

- GitHub organization: https://github.com/shared-auth
- Linear project: https://linear.app/denman/project/githubcomshared-auth-acbca07bb390
- Project and repository map: [`PROJECTS.md`](PROJECTS.md)
- Organization profile source: [`profile/README.md`](profile/README.md)
- Canonical agent policy: [`AGENTS.md`](AGENTS.md)
- Copilot mirror: [`.github/copilot-instructions.md`](.github/copilot-instructions.md)

## Mandatory operating policy

All contributors and agents must resolve Git conflicts semantically and with full context, normally reviewing 3–10 relevant prior commits when useful and inspecting related repositories across this organization and relevant external organizations. Never hastily choose `ours` or `theirs`; preserve compatible intent and validate the conceptual merge.

Agents must operate in deny-by-default non-destructive mode. `git stash`, `git reset`, `git clean`, `git filter-repo`, force pushes, history rewrites, recursive deletion, destructive database or infrastructure operations, credential/session invalidation, release deletion, and equivalent state-destroying actions are prohibited. See [`AGENTS.md`](AGENTS.md) for the complete policy.

## What GitHub inherits

GitHub can use a public organization `.github` repository as the fallback source for supported community-health files and can render `profile/README.md` on the organization page. Issue templates and pull-request templates here provide defaults when an individual repository does not define its own.

`AGENTS.md`, Copilot instructions, branch protections, repository settings, and workflows are **not automatically inherited merely because they exist here**. Every repository must carry compatible agent instructions, and repositories must explicitly call the reusable policy workflow where enforcement is desired.

Example reusable-workflow call:

```yaml
jobs:
  agent-policy:
    uses: shared-auth/.github/.github/workflows/agent-policy.yml@main
```

Repository-local policy may be stricter—particularly around tokens, sessions, OTP, biometrics, credentials, tenant isolation, and provider integrations—but must not weaken the organization baseline.

<!-- ore-org-baseline:begin -->
## Account-wide defaults

This public repository is the canonical source for GitHub-supported fallback community files, organization profile content, reusable workflow examples, and public contributor guidance for [`shared-auth`](https://github.com/shared-auth).

- GitHub owner: [`shared-auth`](https://github.com/shared-auth)
- Linear project: [github.com/shared-auth](https://linear.app/denman/project/githubcomshared-auth-acbca07bb390)
- Public context: [`ORG_CONTEXT.md`](ORG_CONTEXT.md)
- Canonical agent policy for this repository: [`agents.md`](agents.md)
- Governance: [`GOVERNANCE.md`](GOVERNANCE.md)
- Public repository graph: [`repository-relationships.json`](repository-relationships.json)
- Relationship guide: [`docs/REPOSITORY_RELATIONSHIPS.md`](docs/REPOSITORY_RELATIONSHIPS.md)
- Security reporting: [`SECURITY.md`](SECURITY.md)

GitHub applies only its documented fallback community files automatically. Agent instructions, relationship files, and reusable workflows are **not copied into sibling repositories**; repositories that need local enforcement must carry their own lowercase `agents.md` and explicitly call or copy the provided workflow.

`repository-relationships.json` retains the owner's existing contract. A generated public graph is staged under `.github-hardening/proposed/relationship-graph-v1/` for semantic compatibility review. It is public-safe: private repository names are omitted. The complete graph is synchronized separately to the approved private project registry.

## Safety baseline

Changes are pull-request driven. Contributors and agents must preserve concurrent work, avoid destructive Git operations, resolve conflicts semantically with full history and cross-repository context, validate affected contracts, and never claim a remote action completed without authoritative evidence.

Generated baseline version: `2026-08-04`.
<!-- ore-org-baseline:end -->
