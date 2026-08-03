# .github

Organization-wide public context, AI-agent routing metadata, and community defaults.

## Mandatory semantic conflict-resolution policy

All contributors and agents must resolve every Git conflict semantically and with full context. Inspect the affected code or documentation and the relevant history—normally 3–10 prior commits via `git log`, `git show`, and `git blame` when available—before deciding. Review related repositories in this GitHub organization and relevant repositories in external organizations whenever contracts, schemas, APIs, generated code, infrastructure, or shared behavior cross repository boundaries.

Never hastily choose `ours` or `theirs`, discard unfamiliar changes, or resolve only from the conflict markers. Preserve compatible intent from both sides, synthesize a conceptual merge, validate it with the relevant tests and checks, and document intentional tradeoffs.

Canonical agent guidance: [`AGENTS.md`](AGENTS.md). GitHub Copilot mirror: [`.github/copilot-instructions.md`](.github/copilot-instructions.md).
