# Shared Auth Cargo override audit

The runtime-adoption audit proves the reviewed `flags2env` and `shared-auth-lib-core` declarations are present at exact Git revisions. That evidence is incomplete if Cargo can redirect those declarations elsewhere or if another executable Git dependency still follows a moving branch/tag.

`scripts/audit-shared-auth-cargo-overrides.py` is the independent fail-closed companion gate. For each executable consumer it resolves the default branch to one immutable commit and audits `Cargo.toml`, `.cargo/config.toml`, and legacy `.cargo/config` at that same commit.

The gate rejects repository-local `[patch]` and `[replace]`, Cargo config `paths`, Cargo config `[source]` replacement, simultaneous legacy/canonical Cargo config names, target-specific critical dependency redeclarations, dev/build shadows, and aliases whose `package` points at either critical crate outside the reviewed canonical slots. The CLI's reviewed build-time `flags2env` edge is the one intentional extra critical-package slot.

In addition, **every Git dependency in an executable runtime**—normal, build, dev, or target-specific—must use a credential-free HTTPS Git URL and an exact lowercase 40-character `rev`. `branch`, `tag`, and `path` selectors are rejected. This broader rule was added after the customer web/API audit found `ores-transport` following `branch = "main"`; those consumers are being pinned to the exact reviewed `ORESoftware/ores-transport` revision rather than relying on lockfile refresh behavior.

This protects repository-controlled source resolution. It does not claim to prove the external runner's global `CARGO_HOME` is clean; execution environments must separately ensure global Cargo configuration cannot substitute reviewed sources. Lockfile reproducibility remains tracked in `.github#61` until all executable consumers have package-manager-generated `Cargo.lock` files and locked CI.
