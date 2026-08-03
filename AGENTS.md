# Organization-wide agent instructions

These instructions are mandatory for human and automated contributors working in this repository. Treat them as organization-level context when work spans related repositories.

## Semantic conflict resolution

Resolve every Git conflict semantically and with full context.

Before finalizing a conflict resolution:

1. Read both sides, the surrounding code or documentation, and the relevant tests and contracts—not only the conflict markers.
2. Inspect the relevant Git history. When available, review at least 3 and up to 10 prior commits for the affected files or subsystem with `git log`, `git show`, and `git blame` as useful.
3. Review related repositories in this GitHub organization and relevant repositories in external organizations whenever APIs, schemas, generated artifacts, infrastructure, shared libraries, deployment behavior, or documentation cross repository boundaries.
4. Preserve the intent and invariants of all compatible changes. Synthesize a conceptual merge instead of accepting `ours` or `theirs` wholesale.
5. Run the most relevant tests, formatters, linters, builds, contract checks, and end-to-end checks after resolving the conflict.
6. Document intentional behavioral choices, incompatible requirements, or discarded intent in the commit or pull-request description.

Never resolve a conflict by hastily picking one side, deleting unfamiliar changes, or relying only on the latest snapshot. Maximize contextual and conceptual awareness across the organization and its external dependencies before completing the merge.

## Precedence

Repository-local instructions may add stricter requirements, but they must not weaken this semantic conflict-resolution policy.
