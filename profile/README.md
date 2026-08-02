# shared-auth

This organization is mapped to the Linear project [github.com/shared-auth](https://linear.app/denman/project/githubcomshared-auth-acbca07bb390).

## AI agent context

- GitHub owner ID: `307325286`
- Linear project ID: `4bbe0ba4-d7f1-49ce-8f41-afd2cff6c2a2`
- Linear team: `DEN` (`eb8ab169-5afe-4b6f-9cab-3f2aa3e887dc`)
- Machine-readable context: [`project-context.yaml`](https://github.com/shared-auth/.github/blob/main/project-context.yaml)
- Canonical registry: [`ORESoftware/ai-agent-coordinator.rs/config/org-project-registry.yaml`](https://github.com/ORESoftware/ai-agent-coordinator.rs/blob/7929612d92e6aa37f966326cc1a50b4dcd150f3a/config/org-project-registry.yaml)

The reviewed runtime entry defaults to [`shared-auth/shared-auth-mcp-server.rs`](https://github.com/shared-auth/shared-auth-mcp-server.rs) within its explicit allowlist.

Repository-local `AGENTS.md`, `agents.md`, and tool instructions remain authoritative for build, test, and implementation details. The central registry remains authoritative for GitHub/Linear identity and routing. Unmapped or ambiguous work must be rejected rather than guessed.

## Semantic Git conflict resolution

> resolve any and all git conflicts semantically, will full context, even looking back 3-10 commits in git log history for more context - never hastily pick sides in a conflict but merge things conceptually, using max context and complete conceptual awareness for a given github organization's repos and external org repos too

Before resolving a conflict, inspect the merge base and 3–10 relevant commits from both sides when available, including path-scoped history for every conflicted file. Read repository-local instructions, linked Linear issues, pull requests, architecture decisions, tests, migrations, schemas, and documentation. When a contract crosses repository boundaries, inspect relevant repositories in the same GitHub organization and relevant repositories in external GitHub organizations too.

Never resolve by blindly or wholesale selecting `ours`, `theirs`, current, or incoming. Produce a conceptual merge that preserves compatible intent, invariants, APIs, schemas, migrations, tests, documentation, security controls, and operational safeguards from all relevant sides. Document non-obvious decisions, scan the whole worktree for conflict markers, and run every affected validation contract. “Max context” means all relevant authorized context; it never authorizes exposing credentials, private data, or hidden reasoning.

This public repository contains identifiers, links, and public operating guidance only. Do not place credentials, private customer data, or private operational details here.
