# Shared Auth Cargo override audit

The runtime-adoption audit proves the reviewed `flags2env` and `shared-auth-lib-core` declarations are present at exact Git revisions. That evidence is incomplete if Cargo can redirect those declarations elsewhere or if another executable Git dependency still follows a moving branch/tag.

`scripts/audit-shared-auth-cargo-overrides.py` is the independent fail-closed companion gate. For each executable consumer it resolves the default branch to one immutable commit and audits `Cargo.toml`, `.cargo/config.toml`, and legacy `.cargo/config` at that same commit.

The gate rejects repository-local `[patch]` and `[replace]`, Cargo config `paths`, Cargo config `[source]` replacement, simultaneous legacy/canonical Cargo config names, target-specific critical dependency redeclarations, dev/build shadows, and aliases whose `package` points at either critical crate outside the reviewed canonical slots. The CLI's reviewed build-time `flags2env` edge is the one intentional extra critical-package slot.

In addition, **every Git dependency in an executable runtime**—normal, build, dev, target-specific, or declared through `[workspace.dependencies]`—must use a credential-free HTTPS Git URL and an exact lowercase 40-character `rev`. `branch`, `tag`, and `path` selectors are rejected. Critical Shared Auth dependencies may not move into workspace-level indirection because their canonical runtime slots are independently verified by the runtime-adoption audit.

The broader rule was added after the customer web/API audit found `ores-transport` following `branch = "main"`; those consumers were pinned to exact reviewed `ORESoftware/ores-transport` revision `e48a8f006ab4a1221217d61e1a983ccc99e0da8e` in web #30 and API #28.

Machine output uses schema `shared-auth/cargo-overrides-audit/v1`. Its Draft 2020-12 contract is `config/shared-auth-cargo-overrides-audit.schema.json`; immutable repository and blob identities are SHA-typed while finding `actual`/`expected` values remain open so malformed evidence can still be represented in failed reports.

This protects repository-controlled source resolution. It does not claim to prove the external runner's global `CARGO_HOME` is clean; execution environments must separately ensure global Cargo configuration cannot substitute reviewed sources. Lockfile reproducibility remains tracked in `.github#61` until all executable consumers have package-manager-generated `Cargo.lock` files and locked CI.
