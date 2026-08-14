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
  if bash "$validator" "$fixture" >"$scratch/$name.stdout" 2>"$scratch/$name.stderr"; then
    printf 'expected validator failure: %s\n' "$name" >&2
    exit 1
  fi
}

missing_phrase="$(copy_fixture missing-phrase)"
python3 - "$missing_phrase/agents.md" <<'PY'
from pathlib import Path
import sys
path = Path(sys.argv[1])
text = path.read_text()
needle = "avoid git rebase in favor of git merge."
if needle not in text:
    raise SystemExit("fixture prerequisite missing")
path.write_text(text.replace(needle, "prefer a reviewed integration strategy.", 1))
PY
expect_failure missing-phrase "$missing_phrase"

conflict_marker="$(copy_fixture conflict-marker)"
printf '%s%s\n' '<<<<<<<' ' synthetic-test' >> "$conflict_marker/synthetic-conflict.txt"
expect_failure conflict-marker "$conflict_marker"

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
expect_failure unpinned-action "$unpinned_action"

synthetic_secret="$(copy_fixture synthetic-secret)"
printf '%s%s\n' 'github' '_pat_ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789' > "$synthetic_secret/synthetic-secret.txt"
expect_failure synthetic-secret "$synthetic_secret"

printf 'Agent-policy validator tests passed. Scratch fixtures: %s\n' "$scratch"
