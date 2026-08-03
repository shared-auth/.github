# shared-auth organization defaults

This public `.github` repository is the canonical home for shared-auth organization profile content, community-health defaults, contribution guidance, issue and pull-request templates, reusable policy checks, and public agent-safety declarations.

- GitHub organization: https://github.com/shared-auth
- Linear project: https://linear.app/denman/project/githubcomshared-auth-acbca07bb390
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
