# Shared Auth configuration authority audit

Status: executable organization policy  
Tracking: DEN-606, DEN-2193

## Purpose

Shared Auth has several configuration layers that deliberately own different concerns. The organization audit must reject filename and ownership drift before a runtime can accidentally interpret one layer as another.

The machine-readable authority contract is `config/shared-auth-config-authority.json`. The fleet scanner is `scripts/audit-shared-auth-config-authority.py` and its regression suite is `scripts/test_audit_shared_auth_config_authority.py`.

## File authority

| Path | Concern | Owner |
| --- | --- | --- |
| `.shared-auth.toml` | canonical typed consumer policy | consuming repository + `shared-auth-interfaces` contract |
| `.auth-shared.toml` | migration-only compatibility alias for consumer policy | consuming repository + DEN-606 |
| `config/shared-auth-topology.toml` | fleet/provider/application topology | central `shared-auth-server.rs` topology authority |
| `.cli-flags.toml` | argv/environment mapping | executable repository / flags-2-env |
| `config/auth-realms.contract.json` | executable Shared Auth realm startup | `shared-auth-server.rs` only |

A file being present does **not** prove that a runtime loads it. Runtime-adoption evidence remains a separate DEN-606 obligation.

## Enforced structural invariants

The scanner fails when:

- canonical and compatibility consumer-policy filenames coexist;
- a consumer-policy file contains fleet-topology-only sections;
- a consumer-policy file has unknown top-level sections, lacks required provenance, or has an invalid revision shape;
- fleet topology appears in a repository that is not an approved topology owner;
- the executable realm contract appears in a repository that is not an approved realm-contract owner;
- required evidence cannot be read with the audit credential.

A legacy-alias-only consumer is currently a warning so migration can be measured before a cutoff is selected. `--fail-warnings` converts warnings to a failing process result when the migration reaches enforcement phase.

The scanner intentionally does not duplicate the complete `.shared-auth.toml` semantic contract. TypeSpec + JSON Schema + TJSV and the runtime library remain responsible for policy semantics. This scanner enforces concern ownership and obvious structural collisions only.

## Evidence model

Each repository result is one of:

- `passed` — no structural findings;
- `warning` — migration debt such as alias-only policy;
- `failed` — an authority or structure violation;
- `blocked` — required evidence was unavailable.

Blocked evidence is never converted to passing evidence.

The JSON report is written to:

```text
artifacts/shared-auth-config-authority-audit.json
```

with schema:

```text
shared-auth/config-authority-audit/v1
```

Repository output is deterministic because the fleet manifest is sorted by repository name before auditing.

## Fleet scope

`config/shared-auth-repositories.json` is the explicit audit inventory. As of 2026-09-14 it covers 30 Shared Auth repositories, including governance, runtime servers, client/runtime libraries, CLI, infrastructure, formal verification, E2E, UI applications, ORM, sync/event bridges, docs and assets.

New repositories must be added to this inventory as part of bootstrap. A repository omitted from the manifest is outside this audit's evidence set and must not be described as audited merely because it belongs to the GitHub organization.

## CI

`.github/workflows/org-security-audit.yml` now:

1. runs the config-authority unit suite without network credentials;
2. requires the established `SHARED_AUTH_ORG_AUDIT_TOKEN` read credential;
3. runs the existing repository/security audit;
4. runs the config-authority fleet audit;
5. prints bounded summaries of both machine-readable reports.

The workflow keeps explicit read-only permissions, immutable action pins, disabled checkout credential persistence and a bounded timeout.

## Local commands

```sh
python3 -m unittest scripts/test_audit_shared_auth_config_authority.py

GH_TOKEN=... python3 scripts/audit-shared-auth-config-authority.py \
  --manifest config/shared-auth-repositories.json \
  --authority config/shared-auth-config-authority.json \
  --output artifacts/shared-auth-config-authority-audit.json
```

Use a least-privilege read credential. Do not put the token in argv, committed files, artifacts or logs.

## Next enforcement stages

1. run the fleet audit and classify all existing warnings/findings;
2. migrate alias-only consumers to `.shared-auth.toml`;
3. prove intended executable entrypoints actually load resolved typed policy;
4. select a reviewed alias migration cutoff;
5. switch CI to `--fail-warnings` after the fleet is clean;
6. delegate the same structural audit to `ORESoftware/ores-cli` for cross-organization enforcement without making `ores-cli` a new policy semantic authority.
