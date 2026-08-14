# Shared Auth environment ownership

Every repository uses the same SOPS/Nix/Just path contract when it has environment state:

```text
env/enc/dev.env.enc
env/enc/prod.env.enc
env/dec/dev.env
env/dec/prod.env
```

Only the two ciphertext paths may be tracked. `env/dec` is ignored and owner-only. Production secrets remain in the protected deployment store; repository ciphertext is for local/dev/test or explicitly reviewed operator profiles.

| Repository | Classification | Allowed secret classes | Rollout |
|---|---|---|---|
| `shared-auth-server.rs` | auth runtime/provider owner | auth DB, Redis, signing, Supabase, SendGrid email OTP, Twilio Verify | SOPS PR #70; OTP-only PR #75 (semantically reconcile with delivery PR #74 before merge) |
| `shared-auth-web-server.js` | admin/read UI runtime | its own DB/session/runtime references only | SOPS PR #1 |
| `shared-auth-nats-bridge.rs` | internal event runtime | internal bearer token and NATS/webhook routing | SOPS PR #6 |
| `shared-auth-sync` | identity sync runtime | RDS, Redis, Supabase service role | SOPS PR #4 |
| `shared-auth-infra` | deployment/operator owner | scoped operator credential and opaque secret-store references | SOPS PR #16 |
| `shared-auth-e2e` | disposable test fixture owner | disposable test tokens/secrets only | SOPS PR #16 |
| `shared-auth-mcp-server.rs` | read-only diagnostic | none | credential-free SOPS PR #9 |
| `shared-auth-lib` | reusable library | none | credential-free SOPS PR #13 |
| `shared-auth-interfaces` | schemas/generated contracts | none | credential-free SOPS PR #23 |
| `shared-auth-clients` | generated/client SDKs | none | credential-free SOPS PR #46 |
| `shared-auth-monorepo` | workspace composition | references only; child repos own values | direct references-only SOPS PR #11; deterministic web-server seed PR #9 is separate |
| `shared-auth.github.io` | static Astro site | none | keyless static-site SOPS PR #7 |
| `.github` | governance/templates | none | this policy PR #32 |

Adding a credential class requires a reviewed update to this matrix before code or manifests. Libraries, interfaces, clients, static sites, MCP diagnostics, and governance repositories must fail CI if provider/database/signing/token variables appear.
