#!/usr/bin/env bash
set -euo pipefail

root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
validator="$root/scripts/validate-agent-policy.sh"

bash "$validator" "$root"

scratch="$(mktemp -d "${TMPDIR:-/tmp}/agent-policy-tests.XXXXXX")"

copy_fixture() {
  local name="$1"
  mkdir -p "$scratch/$name"
  cp -R "$root/." "$scratch/$name/"
  printf '%s\n' "$scratch/$name"
}

expect_failure() {
  local name="$1"
  local fixture="$2"
  local expected="$3"
  local status=0
  bash "$validator" "$fixture" >"$scratch/$name.stdout" 2>"$scratch/$name.stderr" || status=$?
  if [[ "$status" -ne 1 ]]; then
    printf 'expected policy exit 1 for %s, received %s\n' "$name" "$status" >&2
    exit 1
  fi
  if ! grep -Fq -- "$expected" "$scratch/$name.stderr"; then
    printf 'expected policy diagnostic missing: %s\n' "$name" >&2
    exit 1
  fi
}

check_failure_assertion() {
  # Test the assertion itself. This stub is never used for repository validation.
  local validator="$scratch/assertion-validator.sh"
  cat > "$validator" <<'SH'
#!/usr/bin/env bash
case "$1" in
  valid-rejection) printf 'synthetic policy invariant\n' >&2; exit 1 ;;
  wrong-diagnostic) printf 'unrelated runtime error\n' >&2; exit 1 ;;
  missing-diagnostic) exit 1 ;;
  success) printf 'synthetic policy invariant\n' >&2; exit 0 ;;
  usage-error) printf 'synthetic policy invariant\n' >&2; exit 2 ;;
  missing-tool) printf 'synthetic policy invariant\n' >&2; exit 127 ;;
  terminated) printf 'synthetic policy invariant\n' >&2; exit 143 ;;
  *) exit 99 ;;
esac
SH
  expect_failure assertion-valid valid-rejection 'synthetic policy invariant'
  local scenario
  for scenario in wrong-diagnostic missing-diagnostic success usage-error missing-tool terminated; do
    if (expect_failure "assertion-$scenario" "$scenario" 'synthetic policy invariant') \
      >"$scratch/assertion-$scenario.result" 2>&1; then
      printf 'failure assertion accepted invalid evidence: %s\n' "$scenario" >&2
      exit 1
    fi
  done
  printf 'Failure assertion contract passed: 7 cases.\n'
}

check_failure_assertion

missing_phrase="$(copy_fixture missing-phrase)"
python3 - "$missing_phrase/agents.md" <<'PY'
from pathlib import Path
import re
import sys
path = Path(sys.argv[1])
text = path.read_text()
needle = "avoid git rebase in favor of git merge."
pattern = re.compile(re.escape(needle), re.IGNORECASE)
text, replacements = pattern.subn("prefer a reviewed integration strategy.", text)
if replacements == 0:
    raise SystemExit("fixture prerequisite missing")
if pattern.search(text):
    raise SystemExit("required declaration survived fixture mutation")
path.write_text(text)
PY
expect_failure missing-phrase "$missing_phrase" \
  'agents.md is missing required declaration: avoid git rebase in favor of git merge.'

conflict_marker="$(copy_fixture conflict-marker)"
printf '%s%s\n' '<<<<<<<' ' synthetic-test' >> "$conflict_marker/synthetic-conflict.txt"
expect_failure conflict-marker "$conflict_marker" 'ERROR: unresolved conflict markers found'

unpinned_action="$(copy_fixture unpinned-action)"
cat > "$unpinned_action/.github/workflows/unpinned.yml" <<'YAML'
name: Synthetic unpinned action
on: workflow_dispatch
permissions:
  contents: read
jobs:
  test:
    runs-on: ubuntu-latest
    timeout-minutes: 5
    steps:
      - uses: actions/setup-python@v5
YAML
expect_failure unpinned-action "$unpinned_action" 'contains a mutable or malformed action reference:'

synthetic_secret="$(copy_fixture synthetic-secret)"
printf '%s%s\n' 'github' '_pat_ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789' > "$synthetic_secret/synthetic-secret.txt"
expect_failure synthetic-secret "$synthetic_secret" \
  'synthetic-secret.txt:1: possible GitHub fine-grained token'

printf 'Agent-policy validator tests passed. Scratch fixtures: %s\n' "$scratch"
