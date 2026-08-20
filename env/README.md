# Organization policy environment

The portable path grammar is:

```text
env/enc/*.env.enc
env/dec/*.env
```

The `*` represents the same reviewed profile name. Ciphertext may be tracked only at an explicitly allowlisted `env/enc/<profile>.env.enc` path; its optional local materialization is `env/dec/<profile>.env`. The current baseline allowlists only `dev` and `prod`.

Plaintext stays under ignored, owner-only `env/dec/`. This governance repository is not a secret owner, so ciphertext is normally unnecessary. The policy exists to make the organization convention self-validating and to prevent credentials from landing in shared templates or governance documents. The wildcard is a naming contract, not permission to add an unreviewed profile or credential class.
