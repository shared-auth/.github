#!/usr/bin/env bash
set -euo pipefail

root="${1:-.}"
cd "$root"

errors=0
error() {
  printf 'ERROR: %s\n' "$*" >&2
  errors=$((errors + 1))
}

required_files=(
  agents.md
  AGENTS.md
  CLAUDE.md
  GEMINI.md
  OPENAI.md
  .github/copilot-instructions.md
  .github/PULL_REQUEST_TEMPLATE.md
  .github/ISSUE_TEMPLATE/config.yml
  CONTRIBUTING.md
  SECURITY.md
  SUPPORT.md
  CODE_OF_CONDUCT.md
  GOVERNANCE.md
)

for path in "${required_files[@]}"; do
  [[ -f "$path" ]] || error "missing required file: $path"
done

if [[ -f agents.md ]]; then
  required_phrases=(
    "avoid git rebase in favor of git merge."
    "resolve any and all git conflicts semantically"
    "3-10 commits"
    "3–10 relevant prior commits"
    'accepting `ours` or `theirs` wholesale'
    '`git stash`'
    '`git reset`'
    '`git clean`'
    '`git filter-repo`'
    '`git push --force`'
    "Canonical Linear project:"
    "authoritative evidence"
  )

  for phrase in "${required_phrases[@]}"; do
    grep -Fqi -- "$phrase" agents.md || error "agents.md is missing required declaration: $phrase"
  done
fi

pointer_files=(AGENTS.md CLAUDE.md GEMINI.md OPENAI.md .github/copilot-instructions.md)
for path in "${pointer_files[@]}"; do
  [[ -f "$path" ]] || continue
  grep -Fqi -- 'agents.md' "$path" || error "$path does not reference canonical agents.md"
  grep -Fqi -- 'avoid git rebase in favor of git merge.' "$path" || error "$path is missing the merge-over-rebase directive"
done

if conflict_output="$(grep -RInI -E \
  --exclude-dir=.git \
  --exclude-dir=node_modules \
  --exclude-dir=vendor \
  --exclude-dir=target \
  --exclude-dir=dist \
  --exclude-dir=build \
  '^(<<<<<<< .+|>>>>>>> .+|\|\|\|\|\|\|\| .+|=======$)' . 2>/dev/null)" && [[ -n "$conflict_output" ]]; then
  printf '%s\n' "$conflict_output" >&2
  error "unresolved conflict markers found"
fi

while IFS= read -r record; do
  [[ -n "$record" ]] || continue
  file="${record%%:*}"
  line="${record#*:}"

  if [[ "$line" =~ uses:[[:space:]]+[\"\']?\./ ]]; then
    continue
  fi
  if [[ "$line" =~ uses:[[:space:]]+[\"\']?docker://[^[:space:]\"\']+@sha256:[0-9a-f]{64}[\"\']?([[:space:]]*#.*)?$ ]]; then
    continue
  fi
  if [[ "$line" =~ uses:[[:space:]]+[\"\']?[^[:space:]\"\']+@[0-9a-f]{40}[\"\']?([[:space:]]*#.*)?$ ]]; then
    continue
  fi

  error "$file contains a mutable or malformed action reference: ${line#*uses:}"
done < <(grep -RHE --include='*.yml' --include='*.yaml' '^[[:space:]]*(-[[:space:]]+)?uses:' .github/workflows 2>/dev/null || true)

for workflow in .github/workflows/*.yml .github/workflows/*.yaml; do
  [[ -f "$workflow" ]] || continue
  grep -Eq '^permissions:' "$workflow" || error "$workflow lacks explicit top-level permissions"
  grep -Eq '^[[:space:]]+timeout-minutes:' "$workflow" || error "$workflow lacks an explicit job timeout"
done

if [[ -f scripts/scan-secrets.py ]]; then
  python3 scripts/scan-secrets.py . || errors=$((errors + 1))
else
  error "missing scripts/scan-secrets.py"
fi

if (( errors > 0 )); then
  printf 'Agent-policy validation failed with %d error(s).\n' "$errors" >&2
  exit 1
fi

printf 'Agent-policy validation passed.\n'
