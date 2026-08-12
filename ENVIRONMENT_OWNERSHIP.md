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
| `shared-auth-server.rs` | auth runtime/provider owner | auth DB, Redis, signing, Supabase, SendGrid email OTP, Twilio Verify | SOPS branch `feat/sops-just-nix-env`; OTP-only branch `fix/sendgrid-email-otp-only` |
| `shared-auth-web-server.js` | admin/read UI runtime | its own DB/session/runtime references only | existing SOPS rollout PR |
| `shared-auth-nats-bridge.rs` | internal event runtime | internal bearer token and NATS/webhook routing | `feat/sops-nix-just-env` |
| `shared-auth-sync` | identity sync runtime | RDS, Redis, Supabase service role | `feat/sops-nix-just-env` |
| `shared-auth-infra` | deployment/operator owner | scoped operator credential and opaque secret-store references | `feat/sops-nix-just-env` |
| `shared-auth-e2e` | disposable test fixture owner | disposable test tokens/secrets only | `feat/sops-nix-just-env` |
| `shared-auth-mcp-server.rs` | read-only diagnostic | none | credential-free guard branch |
| `shared-auth-lib` | reusable library | none | credential-free guard branch |
| `shared-auth-interfaces` | schemas/generated contracts | none | credential-free guard branch |
| `shared-auth-clients` | generated/client SDKs | none | credential-free guard branch |
| `shared-auth-monorepo` | workspace composition | references only; child repos own values | existing SOPS seed PR |
| `shared-auth.github.io` | static Astro site | none | static-site no-secret policy |
| `.github` | governance/templates | none | this policy branch |

Adding a credential class requires a reviewed update to this matrix before code or manifests. Libraries, interfaces, clients, static sites, MCP diagnostics, and governance repositories must fail CI if provider/database/signing/token variables appear.
