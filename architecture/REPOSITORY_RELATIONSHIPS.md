# `shared-auth` repository relationships

Generated from reviewed policy and the current **public** repository inventory.

- Public repositories declared: **1**
- Private repository names withheld: **11**
- Relationship edges: **1**

## Repository roles

| Repository | Role | Lifecycle |
|---|---|---|
| [`.github`](https://github.com/shared-auth/.github) | `organization_governance` | `active` |

## Declared edges

| From | Relationship | To | Status/basis |
|---|---|---|---|
| `organization://shared-auth` | `integrates_with` | `organization://3FA-app` | `declared` / `explicit-product-decision`: optional second/third-factor verification |

## Composition, service, and observability contract

Git submodules compose editable source; Zed packages resolve packages/artifacts; dual-managed commits must match. Production deploys immutable image digests, not runtime source builds. Cross-service access uses APIs/SDKs/events rather than another service database. MCP uses the product API/SDK. Services emit OpenTelemetry traces, bounded metrics, and correlated structured logs.

## Privacy boundary

This public registry deliberately omits private repository names and edges; the count above makes the boundary explicit.
