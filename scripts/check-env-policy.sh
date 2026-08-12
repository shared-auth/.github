#!/usr/bin/env bash
set -euo pipefail
cd "$(git rev-parse --show-toplevel)"
fail(){ echo "organization env policy: $*" >&2; exit 1; }
for f in .gitignore .gitattributes .sops.yaml .env.example justfile env/README.md ENVIRONMENT_OWNERSHIP.md COMMUNICATIONS_PROVIDER_BOUNDARIES.md policy/environment-ownership.json scripts/verify-sops-release-policy.py; do test -f "$f" || fail "missing $f"; done
jq -e '.version == 1 and .communications.authentication and .communications.general and (.repositories | length == 13)' policy/environment-ownership.json >/dev/null || fail "invalid ownership matrix"
git check-ignore --no-index -q .env || fail ".env not ignored"
git check-ignore --no-index -q nested/sample.env.local || fail "nested dotenv not ignored"
git check-ignore --no-index -q env/dec/dev.env || fail "env/dec not ignored"
! git check-ignore --no-index -q env/enc/dev.env.enc || fail "dev ciphertext ignored"
! git check-ignore --no-index -q env/enc/prod.env.enc || fail "prod ciphertext ignored"
grep -Fq '^env/enc/dev\.env\.enc$' .sops.yaml || fail "missing dev rule"
grep -Fq '^env/enc/prod\.env\.enc$' .sops.yaml || fail "missing prod rule"
python3 scripts/verify-sops-release-policy.py .sops.yaml prod
while IFS= read -r -d '' p; do case "$p" in env/enc/dev.env.enc|env/enc/prod.env.enc) ;; env/enc/*) fail "unexpected encrypted path $p" ;; .env|*.env|.env.*|*.env.*|env/dec/*) case "$p" in .env.example|*/.env.example) ;; *) fail "tracked plaintext $p" ;; esac ;; esac; done < <(git ls-files -z)
if git grep -I -q -e 'AGE-SE''CRET-KEY-1' -e '-----BEGIN PRIVATE KEY-----' -e '-----BEGIN OPENSSH PRIVATE KEY-----' -- .; then fail "private-key material detected"; fi
for forbidden in DATABASE_URL SENDGRID_API_KEY TWILIO_AUTH_TOKEN SERVICE_ROLE SIGNING_KEY BEARER_TOKEN ACCESS_TOKEN CLIENT_SECRET AWS_SECRET_ACCESS_KEY CLOUDFLARE_API_TOKEN; do ! grep -Eq "^[A-Z0-9_]*${forbidden}[A-Z0-9_]*=" .env.example || fail "credential variable forbidden in governance schema: $forbidden"; done
echo "organization environment policy is valid"
