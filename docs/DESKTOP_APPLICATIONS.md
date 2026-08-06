# Desktop application allocation

Verified **2026-08-06**.

Shared Auth requires a paired, native desktop program:

- Rust: [`shared-auth/shared-auth-desktop.rs`](https://github.com/shared-auth/shared-auth-desktop.rs) — **planned**, not yet verified as a published repository.
- Flutter: [`shared-auth/shared-auth-flutter`](https://github.com/shared-auth/shared-auth-flutter) — **planned**, not yet verified as a published repository.

Both names are allocation targets, not evidence that the repositories exist. Do not mark either implementation live until the remotes, native builds, packages, tests, signing/update configuration, and supported-platform matrices are verified.

## Why both Rust and Flutter remain active

The Rust and Flutter applications are first-class side-by-side implementations. Shared Auth will compare security boundaries, native performance, secure storage, external-browser authorization, device/session review, accessibility, mobile reuse, OS integration, packaging, signing, update reliability, developer velocity, and long-term maintenance using the same real authentication features.

Every desktop-facing feature must inspect both repositories, share acceptance criteria, route types, OAuth/OIDC fixtures, policy schemas, and release evidence, and normally update both. A one-sided change requires a documented no-change rationale, parity assessment, and follow-up issue. Completion in one repository is not full desktop completion.

Every future `shared-auth-desktop.rs` README, `AGENTS.md`, pull-request template, and `docs/DESKTOP_TOOLKIT.md` must state that Rust and Flutter development proceeds in parallel unless an explicit reviewed exception applies.

## Rust desktop kit: Floem

**Selected strategy:** Floem.

**WebView policy:** prohibited.

Floem is selected as a native Rust UI library with fine-grained reactivity and GPU-backed rendering. It supports native Windows, macOS, and Linux targets without requiring a browser-rendered application surface.

Pin an exact reviewed Floem release or commit because the upstream project remains pre-1.0 and may make breaking changes. Upgrades require native build, rendering, accessibility, input, secure-storage, packaging, and deep-link evidence on every supported desktop platform.

Rust owns:

- OAuth/OIDC state, PKCE, nonce, issuer, redirect, and audience validation;
- device, session, factor, approval, recovery, and policy state;
- secure storage, persistence, networking, and cryptographic boundaries;
- deep-link parsing, replay protection, authorization, and browser handoff state;
- audit-safe logging, error redaction, and all privileged operations.

Floem owns native presentation, fine-grained reactive view state, GPU-backed rendering, accessibility, keyboard navigation, and windowing. Sensitive tokens, credentials, recovery material, private keys, or raw session state must never be serialized into view markup, debug tools, or URLs.

The upstream framework authority is https://github.com/lapce/floem.

## External-browser authorization boundary

Shared Auth native clients must use the user's external system browser for OAuth/OIDC authorization. Embedded login WebViews are prohibited in both Rust and Flutter.

Use Authorization Code with PKCE for public native clients, together with:

- a high-entropy `state` value;
- nonce where applicable;
- exact issuer, audience, redirect URI, and provider-path validation;
- short-lived authorization sessions;
- one-time authorization-code redemption;
- secure storage for only the minimum pending authorization state;
- immediate deletion of completed or expired pending state.

Prefer a verified app-claimed HTTPS callback. Where claimed HTTPS is unavailable on desktop, use a loopback redirect bound only to `127.0.0.1` or `[::1]` on an ephemeral port, opened for one authorization attempt and closed immediately after completion. Do not use `localhost`, do not bind non-loopback interfaces, and do not treat a packaged client secret as confidential.

Follow the native-app security model in RFC 8252 and PKCE requirements.

## HTTPS-first deep linking

Canonical route family:

```text
https://<verified-shared-auth-owned-host>/open/<route>?<bounded-query>
```

Fallback scheme for non-OAuth navigation:

```text
sharedauth://<route>?<bounded-query>
```

The production host must not be guessed. OAuth callbacks should use verified claimed HTTPS or the constrained loopback flow above. `sharedauth://` must not carry OAuth authorization responses unless a reviewed ADR replaces it with a collision-resistant reverse-domain scheme backed by a verified owned domain.

Routes belong in the Shared Auth interfaces repository and must be shared by Rust, Flutter, generated clients, browser fallback pages, and service integrations.

Required behavior:

- support cold start and already-running/single-instance delivery;
- preserve only a validated pending route through authentication;
- validate the exact HTTPS host, route version, tenant, account, device, session, factor, approval, and recovery identifiers, action, and bounded query values;
- reject unknown routes, ambiguous encodings, duplicate security-sensitive parameters, unsafe returns, issuer/audience/redirect mismatches, replay, expiry, and unauthorized tenant or account access;
- use short-lived, single-use, audience-bound codes for sign-in, approval, recovery, device enrollment, and cross-application handoffs;
- require explicit confirmation before factor changes, device/session revocation, account recovery, approval, enrollment, or destructive actions;
- provide a browser fallback when the app is absent; and
- test macOS, Windows, Linux, Android, and iOS app/universal links plus browser authorization returns.

Passwords, bearer/refresh tokens, authorization codes after redemption, client secrets, recovery secrets, TOTP seeds, private keys, session cookies, and personally sensitive identity data are prohibited in URLs.

## Product boundary

Both implementations should support semantic parity for:

- sign-in and sign-out;
- OAuth/OIDC authorization and browser return handling;
- device and session review/revocation;
- factors, approvals, recovery, and enrollment;
- tenant/account selection and policy display;
- secure local storage and offline-safe pending operations;
- notifications, accessibility, audit evidence, error redaction, and deep links.

Shared schemas, policy types, clients, route fixtures, OAuth/OIDC test vectors, synthetic identities, redirect fixtures, and conformance tests must be versioned deliberately.

## Repository creation requirements

Both repositories must start as buildable scaffolds, not placeholders.

The Rust repository must include:

- `docs/DESKTOP_TOOLKIT.md` with the Floem pin, no-WebView rule, privilege boundary, browser authorization, deep links, platform matrix, and Flutter companion;
- a README naming `shared-auth-flutter` and stating that Rust and Flutter features are developed in parallel unless explicitly exempted;
- `AGENTS.md` and a pull-request template requiring companion inspection and a no-change rationale;
- native macOS/Windows/Linux CI and package/signing/update skeletons;
- secure-storage adapters and synthetic OAuth/OIDC test harnesses;
- deep-link, PKCE, state/nonce, redirect, replay, expiry, recovery, and device/session smoke tests.

The Flutter repository must reciprocally name `shared-auth-desktop.rs`, implement native desktop plus Android/iOS targets deliberately, use the external system browser, and consume the same route and authorization fixtures.

## Project routing

- GitHub Project: [`shared-auth-project` — Project 1](https://github.com/orgs/shared-auth/projects/1)
- Linear project: `github.com/shared-auth`
- Central registry: [`ORESoftware/project-registry`](https://github.com/ORESoftware/project-registry/blob/main/registry/desktop-applications.json)
- Central strategy: [`rust-desktop-strategies.md`](https://github.com/ORESoftware/project-registry/blob/main/docs/rust-desktop-strategies.md)
- Portfolio rollout: [`DEN-2469`](https://linear.app/denman/issue/DEN-2469/roll-out-paired-rust-flutter-desktop-repositories-across-the-portfolio)

Repository creation, toolkit changes, OAuth/OIDC changes, deep-link changes, transfers, archival, or platform-status changes must update this document, Linear, the central registry/strategy, and both companion repositories together.
