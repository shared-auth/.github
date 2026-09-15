# Shared Auth Cargo override audit

The runtime-adoption audit proves the reviewed `flags2env` and `shared-auth-lib-core` declarations are present at exact Git revisions. That evidence is incomplete if Cargo is allowed to redirect those declarations elsewhere.

`scripts/audit-shared-auth-cargo-overrides.py` is the independent fail-closed companion gate. For each executable consumer it resolves the default branch to one immutable commit and audits `Cargo.toml`, `.cargo/config.toml`, and legacy `.cargo/config` at that same commit.

The gate rejects repository-local `[patch]` and `[replace]`, Cargo config `paths`, Cargo config `[source]` replacement, simultaneous legacy/canonical Cargo config names, target-specific critical dependency redeclarations, dev/build shadows, and aliases whose `package` points at either critical crate outside the reviewed canonical slots. The CLI's reviewed build-time `flags2env` edge is the one intentional extra slot.

This protects repository-controlled source resolution. It does not claim to prove the external runner's global `CARGO_HOME` is clean; execution environments must separately ensure global Cargo configuration cannot substitute reviewed sources. Lockfile reproducibility remains tracked in `.github#61` until all executable consumers have package-manager-generated `Cargo.lock` files and locked CI.
