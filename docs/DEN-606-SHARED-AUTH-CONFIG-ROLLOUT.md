# DEN-606 — Shared Auth configuration rollout

This document is the organization-level rollout record for the typed Shared Auth consumer policy contract.

## File and authority contract

- `.shared-auth.toml` is the canonical consumer policy filename.
- `.auth-shared.toml` is a migration-only compatibility alias. If both are present, consumers fail closed instead of choosing precedence.
- `.shared-auth.toml` is policy, not an argv parser. Every executable continues to resolve argv/environment through root `.cli-flags.toml` and canonical `flags-2-env` first.
- The policy data contract has two peer engineering authorities in `shared-auth/shared-auth-interfaces`: independently human-authored TypeSpec and JSON Schema Draft 2020-12.
- The TypeSpec-generated JSON Schema witness, Contract IR, generated language types, runtime adapters and verification receipts are evidence only. They never overwrite either authority or win a disagreement.
- `ORESoftware/typespec-json-schema-validator` (TJSV) is the fail-closed convergence and promotion gate.

## Resolution and provenance

Shared Auth owns secure central defaults. A consumer may shadow only explicitly overridable policy fields. Scalars replace scalars and set/array fields replace the corresponding set; there is no implicit union. Unknown keys, unknown enum values, duplicate/empty sets and malformed values fail closed.

Every consumer policy declares `schema_version = 1` plus compatibility with `https://github.com/shared-auth/shared-auth-interfaces` as either:

1. one exact 40-character lowercase Git commit; or
2. an inclusive `{base, head}` Git ancestry range.

Range admission is an ancestry check, never lexical SHA ordering. A policy outside the running interfaces revision is a startup failure.

The first mainline `shared-auth-interfaces` revision containing this contract is merge commit `52b7ac7fbf0c7c169684f613eda923f3aa6c82e9`; central and consumer configs should prefer a durable mainline revision/range rather than an abandoned feature-branch-only SHA.

## Current delivery chain

- `shared-auth/shared-auth-interfaces#51` — **merged** as `52b7ac7fbf0c7c169684f613eda923f3aa6c82e9`; establishes peer TypeSpec + Draft 2020-12 authorities, exact/range provenance, typed 2FA/3FA/page/theme enums and the initial differential corpus.
- `shared-auth/shared-auth-interfaces#52` — open TJSV language/runtime promotion layer pinned to immutable TJSV GitHub commit `4a5d049218adc2740d4cf78f612caf7f38f6f64c`; requires Rust/native + TypeScript/Node ingress/egress evidence, parity receipt, Contract IR, exact artifact digests and `verifyLanguageBoundariesAgainstCurrentInputs()`. Its corpus currently contains 4 valid round-trip fixtures and 14 expected-invalid fixtures.
- `shared-auth/shared-auth-lib-core#15` — strict TOML deserialization, central defaults, deterministic project overlay, alias collision handling and revision admission. Its central policy is pinned to `52b7ac7...`.
- `shared-auth/shared-auth-cli#4` — canonical `flags-2-env` argv/env boundary with build-time `.cli-flags.toml` audit; `.shared-auth.toml` remains the separate policy layer and is pinned to `52b7ac7...`.
- `flags-2-env/flags-2-env#13` / DEN-1799 — **merged** as `b708a041531a830bd49f030250836896096e7abd` after all 17 exact-head repository workflows passed; the native parser now fails closed on unsupported `.cli-flags.toml` tables/keys without adding a second TOML parser.

Shared-auth **source** repository Actions are presently affected by DEN-2906. A zero-step Actions failure is an infrastructure/admission failure, not code-green evidence; affected PRs must not be merged merely because their diffs are mergeable. The `shared-auth/.github` policy repository currently executes its own policy workflows normally, so documentation/governance PRs still require and can obtain ordinary exact-head CI evidence.

## Workstream A — TJSV language/runtime admission

The schema parity check is necessary but not sufficient. Before config-derived runtime artifacts are promoted:

1. run `tjsv check` over the exact TypeSpec, authored JSON Schema and differential corpus;
2. retain the deterministic parity receipt and emit the parity-approved Contract IR;
3. run config-specific ingress and egress conformance in at least Rust and TypeScript using the same valid/invalid corpus;
4. declare `ores.typespec-json-schema-validator.language-boundaries/v1` with at least two required distinct languages and `generatedWitness = evidence_only`;
5. emit one closed evidence envelope per required language/runtime, binding the exact source revision, artifact digest, parity `runId`, Contract IR `irId`, generator/toolchain and validation results;
6. call TJSV `verifyLanguageBoundariesAgainstCurrentInputs()` against the exact current TypeSpec, generated witness and authored Schema A;
7. promote only when the verification status is `passed` and `zeroUnexplainedFindings` is true.

PR #52 implements this sequence. Until DEN-2906 clears, its GitHub job is created but executes zero steps; secondary local TypeScript evidence may catch implementation errors but does not replace the required exact-head GitHub Rust + TypeScript + TJSV evidence.

Related existing Linear work: DEN-3959, DEN-3596 and DEN-3830. A dedicated child issue was attempted on 2026-09-09 but Linear rejected creation because the workspace issue limit is exhausted; the work remains explicitly tracked under DEN-606 until the limit is lifted.

## Workstream B — runtime adoption

Apply the same startup sequence to the CLI, web server, API server, admin web server and admin API server:

1. locate the trusted packaged `.cli-flags.toml` contract;
2. audit it and resolve argv/env through `flags-2-env` exactly once;
3. cross into immutable typed runtime configuration;
4. load central Shared Auth policy from `shared-auth-lib-core`;
5. locate exactly one project policy filename and parse it strictly;
6. resolve the consumer overlay over central defaults;
7. verify the policy admits the exact interfaces revision;
8. only then initialize network/database/auth application state.

No executable may fall back to an ad-hoc argv parser, direct environment interpretation, an independent Shared Auth TOML parser or permissive defaults after a config error.

## Workstream C — fleet compliance

The organization-level audit must eventually scan Shared Auth consumers and report, without auto-rewriting policy:

- canonical/legacy filename presence and collisions;
- invalid or stale interface provenance;
- schema/TJSV failures;
- unknown/duplicate/empty enum-set values;
- consumers that still use only the legacy filename after the migration cutoff;
- whether runtime entrypoints actually load the resolved policy rather than merely carrying the file.

The output should be a deterministic adoption matrix suitable for DEN-2843-style rollout tracking.

## Merge evidence rule

A PR is ready only when its exact head has authoritative test evidence. Mergeability without executed validation is insufficient. Conflicts are resolved semantically using repository history and cross-repository contract context per `ORESoftware/my-ai/AGENTS.md`; do not rebase, force-push, reset or discard either side wholesale.
