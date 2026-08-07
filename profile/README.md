# Shared Auth

Shared Auth develops reusable authentication, authorization, session, OTP, biometric, identity-provider, and tenant-access components for applications across the wider portfolio. Its repositories provide shared contracts, clients, libraries, services, tooling, and integration surfaces for identity-sensitive systems.

This page is the public orientation point for people and authorized AI agents. Repository-specific READMEs and instructions remain authoritative for implementation details.

## Start here

### For people

- Use the [canonical Linear project](https://linear.app/denman/project/githubcomshared-auth-acbca07bb390) for planning, priorities, dependencies, and delivery context.
- Read the organization [contribution guide](https://github.com/shared-auth/.github/blob/main/CONTRIBUTING.md), [governance notes](https://github.com/shared-auth/.github/blob/main/GOVERNANCE.md), [support guide](https://github.com/shared-auth/.github/blob/main/SUPPORT.md), and [security policy](https://github.com/shared-auth/.github/security/policy).
- Start in the README, threat model, migration notes, and local instructions of the exact repository being changed; this profile is an index, not a substitute for repository documentation.
- Treat changes to public interfaces, token/session behavior, tenant boundaries, and authentication flows as cross-repository contracts that require explicit review.

### For AI agents

1. Read [`project-context.yaml`](https://github.com/shared-auth/.github/blob/main/project-context.yaml) for the canonical GitHub owner, Linear project, and reviewed runtime route.
2. Read [`repository-relationships.json`](https://github.com/shared-auth/.github/blob/main/repository-relationships.json) before inferring dependencies, ownership, or repository selection.
3. Read the organization [`AGENTS.md`](https://github.com/shared-auth/.github/blob/main/AGENTS.md), [`ORG_CONTEXT.md`](https://github.com/shared-auth/.github/blob/main/ORG_CONTEXT.md), and every applicable repository-local `AGENTS.md`, `agents.md`, Copilot instruction, and path-specific instruction.
4. For reviewed routed work, the default repository is `shared-auth/shared-auth-mcp-server.rs`, and it is the only repository in that runtime allowlist. Exact repository overrides take precedence. Ambiguous or unmapped work must stop rather than be guessed.
5. Never expose credentials, passwords, private keys, access or refresh tokens, session identifiers, OTP seeds or codes, biometric material, tenant data, customer information, incident details, or private topology in public outputs.

## Canonical identity and authority

- GitHub organization: [`shared-auth`](https://github.com/shared-auth)
- Immutable GitHub owner ID: `307325286`
- Linear project: [`github.com/shared-auth`](https://linear.app/denman/project/githubcomshared-auth-acbca07bb390)
- Immutable Linear project ID: `4bbe0ba4-d7f1-49ce-8f41-afd2cff6c2a2`
- Linear team: `DEN` (`eb8ab169-5afe-4b6f-9cab-3f2aa3e887dc`)
- Organization defaults and public policies: [`shared-auth/.github`](https://github.com/shared-auth/.github)

The reviewed central registry is authoritative for GitHub/Linear identity and routing. Repository-local instructions are authoritative for builds, tests, architecture, migrations, and implementation. Missing or contradictory context must be reported and resolved; it must not be invented.

## Security and compatibility invariants

- Keep credentials, token material, OTP secrets, biometric inputs, session state, and identity-provider secrets out of source, logs, fixtures, examples, issue text, pull requests, and generated artifacts.
- Preserve tenant isolation, authorization boundaries, revocation behavior, auditability, and least privilege across every change.
- Treat interface, schema, token-format, session-lifecycle, and migration changes as compatibility-sensitive. Update consumers, tests, documentation, and rollout or rollback plans together.
- Preserve identity and session state non-destructively. Do not use history rewrites, blanket resets, destructive cleanup, or wholesale side selection to make a change appear simple.
- Keep application code and infrastructure repositories separate. An `*-infra` repository does not belong under a monorepo `apps/` directory as a Git submodule.
- Link substantial work to Linear and a GitHub issue or pull request so humans and agents can recover intent.
- Resolve Git conflicts semantically: inspect the merge base, both sides, path-scoped history, and 3–10 relevant commits when available; read linked issues, pull requests, tests, schemas, migrations, architecture decisions, and relevant same-organization or external repositories. Never accept `ours`, `theirs`, current, or incoming wholesale without conceptual review.
- Preserve compatible intent, APIs, schemas, tests, documentation, security controls, and operational safeguards from every relevant side, then scan the complete worktree for unresolved conflict markers and run all affected validation.

## Public context boundary

This profile and the `.github` repository are intentionally public. They may contain public identifiers, links, policies, and operating guidance. They must not contain credentials, private identity data, customer records, private issue content, incident details, security-sensitive topology, or unpublished business information.

<!-- org-project-routing:start -->
## Planning and delivery

- [GitHub Project: shared-auth-project](https://github.com/orgs/shared-auth/projects/1)
- [Linear planning project](https://linear.app/denman/project/githubcomshared-auth-acbca07bb390)
- [Detailed project-routing contract](../docs/PROJECTS.md)

GitHub owns code and delivery evidence; Linear owns planning and dependencies. The linked organization Project provides the cross-repository execution view.
<!-- org-project-routing:end -->

<!-- ore-org-baseline:begin -->
This GitHub account maintains software, infrastructure, research, and supporting documentation under the [`shared-auth`](https://github.com/shared-auth) GitHub owner.

Planning and delivery context is tracked in [github.com/shared-auth](https://linear.app/denman/project/githubcomshared-auth-acbca07bb390). Public contribution, security, and governance defaults are maintained in [`.github`](https://github.com/shared-auth/.github).

Repository descriptions and repository-local documentation remain authoritative for each project. Do not infer production readiness, support commitments, or security guarantees from this profile alone.
<!-- ore-org-baseline:end -->
# shared-auth

This organization is mapped to the Linear project [github.com/shared-auth](https://linear.app/denman/project/githubcomshared-auth-acbca07bb390).

## AI agent context

- GitHub owner ID: `307325286`
- Linear project ID: `4bbe0ba4-d7f1-49ce-8f41-afd2cff6c2a2`
- Linear team: `DEN` (`eb8ab169-5afe-4b6f-9cab-3f2aa3e887dc`)
- Machine-readable context: [`project-context.yaml`](https://github.com/shared-auth/.github/blob/main/project-context.yaml)
- Canonical registry: [`ORESoftware/ai-agent-coordinator.rs/config/org-project-registry.yaml`](https://github.com/ORESoftware/ai-agent-coordinator.rs/blob/d3e03ecc2e175a7f6261523d35c73ac775c49942/config/org-project-registry.yaml)

The reviewed runtime entry defaults to [`shared-auth/shared-auth-mcp-server.rs`](https://github.com/shared-auth/shared-auth-mcp-server.rs) within its explicit allowlist.

Repository-local `AGENTS.md`, `agents.md`, and tool instructions remain authoritative for build, test, and implementation details. The central registry remains authoritative for GitHub/Linear identity and routing. Unmapped or ambiguous work must be rejected rather than guessed.

## Semantic Git conflict resolution

> resolve any and all git conflicts semantically, will full context, even looking back 3-10 commits in git log history for more context - never hastily pick sides in a conflict but merge things conceptually, using max context and complete conceptual awareness for a given github organization's repos and external org repos too

Before resolving a conflict, inspect the merge base and 3–10 relevant commits from both sides when available, including path-scoped history for every conflicted file. Read repository-local instructions, linked Linear issues, pull requests, architecture decisions, tests, migrations, schemas, and documentation. When a contract crosses repository boundaries, inspect relevant repositories in the same GitHub organization and relevant repositories in external GitHub organizations too.

Never resolve by blindly or wholesale selecting `ours`, `theirs`, current, or incoming. Produce a conceptual merge that preserves compatible intent, invariants, APIs, schemas, migrations, tests, documentation, security controls, and operational safeguards from all relevant sides. Document non-obvious decisions, scan the whole worktree for conflict markers, and run every affected validation contract. “Max context” means all relevant authorized context; it never authorizes exposing credentials, private data, or hidden reasoning.

This public repository contains identifiers, links, and public operating guidance only. Do not place credentials, private customer data, or private operational details here.
