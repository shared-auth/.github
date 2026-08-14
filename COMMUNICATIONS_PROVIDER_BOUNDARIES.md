# Communications provider boundaries

## Authentication and security messages

`shared-auth-server.rs` owns authentication email OTP delivery through SendGrid and phone enrollment/step-up challenges through Twilio Verify. Email is numeric OTP only; no sign-in link or opaque bearer token may be rendered, sent, or consumed. Provider keys are separately issued per realm/environment and injected by the protected deployment store.

## General application communications

Fanwaave is the shared communications plane for non-auth email, SMS, and push notifications. Product servers publish typed jobs or call its authenticated service contract. They do not receive SendGrid/Twilio credentials directly.

## Event and sync components

`shared-auth-nats-bridge.rs` moves authenticated events; `shared-auth-sync` synchronizes identity/profile state. Neither sends provider messages or accepts provider credentials.

## Enforcement

- No full-access provider key may be copied across services.
- Prefer least-privilege, per-service, per-environment credentials.
- Production manifests carry opaque secret references, not values.
- Pull-request CI is keyless and never decrypts.
- Protected canaries must not print recipients, message bodies, tokens, provider headers, callback secrets, or raw upstream responses.
- Any credential exposed in chat, logs, tickets, or Git must be revoked and replaced before production use.
