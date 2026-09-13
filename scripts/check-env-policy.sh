#!/usr/bin/env bash
set -euo pipefail
cd "$(git rev-parse --show-toplevel)"
fail(){ echo "organization env policy: $*" >&2; exit 1; }
for f in .gitignore .gitattributes .sops.yaml .env.example justfile env/README.md ENVIRONMENT_OWNERSHIP.md COMMUNICATIONS_PROVIDER_BOUNDARIES.md policy/environment-ownership.json scripts/verify-sops-release-policy.py; do test -f "$f" || fail "missing $f"; done
jq -e '.version == 1 and .ciphertext_git_policy == "ignored" and .plaintext_git_policy == "ignored" and .communications.authentication and .communications.general and (.repositories | length == 13)' policy/environment-ownership.json >/dev/null || fail "invalid ownership matrix"
for pattern in '*.env' '**.env' '**/*.env' '**/**/*.env' '!.env.example' '/env/dec/' '/env/enc/'; do grep -Fxq "$pattern" .gitignore || fail "missing ignore rule $pattern"; done
git check-ignore --no-index -q .env || fail ".env not ignored"
! git check-ignore --no-index -q .env.example || fail ".env.example ignored"
git check-ignore --no-index -q nested/sample.env || fail "nested .env not ignored"
git check-ignore --no-index -q nested/deeper/sample.env || fail "deeply nested .env not ignored"
git check-ignore --no-index -q nested/deeper/still/sample.env || fail "multiply nested .env not ignored"
git check-ignore --no-index -q nested/sample.env.local || fail "nested dotenv variant not ignored"
git check-ignore --no-index -q env/dec/dev.env || fail "env/dec not ignored"
git check-ignore --no-index -q env/enc/dev.env.enc || fail "dev ciphertext not ignored"
git check-ignore --no-index -q env/enc/prod.env.enc || fail "prod ciphertext not ignored"
git check-ignore --no-index -q env/enc/unreviewed.bin || fail "env/enc directory not ignored"
grep -Fq 'path_regex: ^env/enc/dev\.env\.enc$' .sops.yaml || fail "missing dev rule"
grep -Fq 'path_regex: ^env/enc/prod\.env\.enc$' .sops.yaml || fail "missing prod rule"
python3 scripts/verify-sops-release-policy.py .sops.yaml prod
while IFS= read -r -d '' p; do case "$p" in env/enc/*) fail "tracked encrypted environment file $p" ;; .env|*.env|.env.*|*.env.*|env/dec/*) case "$p" in .env.example|*/.env.example) ;; *) fail "tracked plaintext $p" ;; esac ;; esac; done < <(git ls-files -z)
age_private='AGE-SE''CRET-KEY-1'
pem_private='-----BEGIN ''PRIVATE KEY-----'
openssh_private='-----BEGIN OPENSSH ''PRIVATE KEY-----'
if git grep -I -q -e "$age_private" -e "$pem_private" -e "$openssh_private" -- .; then fail "private-key material detected"; fi
for forbidden in DATABASE_URL SENDGRID_API_KEY TWILIO_AUTH_TOKEN SERVICE_ROLE SIGNING_KEY BEARER_TOKEN ACCESS_TOKEN CLIENT_SECRET AWS_SECRET_ACCESS_KEY CLOUDFLARE_API_TOKEN; do ! grep -Eq "^[A-Z0-9_]*${forbidden}[A-Z0-9_]*=" .env.example || fail "credential variable forbidden in governance schema: $forbidden"; done
echo "organization environment policy is valid"
