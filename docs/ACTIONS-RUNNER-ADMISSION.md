# GitHub Actions runner admission

Shared Auth treats **runner admission** separately from source/build correctness.

A workflow conclusion is not source evidence when GitHub never allocates executable
steps. In particular, a job with `steps: null` or an empty step list is
classified as **NOT_EXECUTED** even when the workflow/job conclusion is
`failure`.

## Current incident

Issue #68 tracks the organization-wide admission incident. The quota-entitlement
contract job for `shared-auth/shared-auth-interfaces` PR #102 was re-run on
2026-10-18 at the same exact source head:

`6b73af14265a04b02bcdd8264dd4963a913d3033`

GitHub accepted the rerun request and created replacement job
`117718931386` in workflow run `36665846078`, but that job again completed
with `steps: null`. Therefore the current state is still **NOT_EXECUTED**.
It is neither a contract pass nor a contract failure.

## Canary contract

`.github/workflows/runner-admission-canary.yml` is intentionally tiny. A
successful run proves only that a hosted runner actually started and executed
steps. It records:

- repository and exact Git SHA;
- workflow run id and attempt;
- runner name, OS and architecture;
- a retained `shared-auth.actions-admission/v1` receipt.

The canary does not replace repository-specific Rust, PostgreSQL, TypeSpec,
TJSV, schema, OCI, or integration gates. After admission recovers, every owning
repository must rerun its exact required head and obtain its own stepful verdict.

## Evidence classification

`scripts/verify-stepful-actions-evidence.py` consumes the GitHub jobs response.

- at least one non-empty step list: `STEPFUL`; defer source verdict to the
  executed job;
- every job has null/empty steps: `NOT_EXECUTED`, source verdict `NONE`;
- no jobs: `NO_JOBS`, source verdict `NONE`.

This intentionally prevents red zero-step jobs from being counted as compiler,
test, or contract failures.

## Administrative recovery gate

Restoring hosted-runner admission requires organization/repository
administrative state that is not represented by source changes alone. An
authorized administrator should verify the live GitHub configuration for:

1. Actions enablement and allowed-actions policy;
2. hosted-runner eligibility/capacity and organization billing/usage state;
3. repository access to the selected runner class;
4. workflow approval/restriction state for private repositories;
5. GitHub App/token Actions permissions where relevant.

Do not work around this gate by committing PATs, weakening required workflows,
turning security jobs into skips, or declaring success from a different
organization's runner.

Once the canary becomes stepful, rerun the exact owning-repository heads
identified by their tracking issues and retain their actual job logs/artifacts.
