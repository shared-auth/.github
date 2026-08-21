# Organization policy environment

The portable path grammar is:

```text
env/enc/*.env.enc
env/dec/*.env
```

The `*` represents the same reviewed profile name. Ciphertext is created locally at `env/enc/<profile>.env.enc`; its optional local materialization is `env/dec/<profile>.env`. Both directories are Git-ignored, and the current SOPS creation policy recognizes only `dev` and `prod`.

Plaintext stays under ignored, owner-only `env/dec/`; ciphertext under `env/enc/` must not be force-added. The repository ignore baseline includes the literal rules `*.env`, `**.env`, `**/*.env`, and `**/**/*.env`. This governance repository is not a secret owner, so ciphertext is normally unnecessary. The policy exists to make the organization convention self-validating and to prevent credentials from landing in shared templates or governance documents. The wildcard is a naming contract, not permission to add an unreviewed profile or credential class.
