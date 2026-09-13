# Repository boundary: infrastructure stays separate

**Policy ID:** `repo-boundary/infra-not-app-submodule/v1`  
**Status:** Permanent organization architecture rule

- A repository named `*-infra` is a standalone infrastructure and deployment codebase.
- A `*-infra` repository **must not** be added to any `*-monorepo` as a Git submodule, including anywhere under `*-monorepo/apps/`.
- Application/source code and infrastructure code must remain in separate repositories with independent history, ownership, release, and deployment lifecycles.
- A monorepo may integrate with infrastructure only through documented configuration, versioned contracts, CI/CD inputs, published artifacts, or deployment APIs. It must not vendor, nest, or mount the `*-infra` repository.
- Any existing `*-monorepo/apps/...` submodule whose remote points to a `*-infra` repository is non-conforming and should be removed.

Repository scaffolding, migration tooling, and automated agents must preserve this boundary unless the policy is explicitly revised.

## Persistence contracts

`shared-auth-interfaces` owns independently authored, co-equal TypeSpec and JSON Schema/OpenAPI product database contracts. `shared-auth-lib-core` pins those sources and owns candidates, parity evidence, PostgreSQL extension SQL, and certified desired-state releases. `shared-auth-orm-core` owns Diesel and SeaORM runtime access; `shared-auth-infra` alone owns reviewed DPM plan/verify/apply. See [docs/PERSISTENCE_AUTHORITY.md](docs/PERSISTENCE_AUTHORITY.md). `ORESoftware/k8s-libs-and-shared-defs` retains platform SQL and the fleet catalog only.
