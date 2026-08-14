#!/usr/bin/env python3
"""Small fail-closed credential-pattern scanner with no third-party dependencies."""

from __future__ import annotations

import os
import re
import sys
from pathlib import Path

ROOT = Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve()
SKIP_DIRS = {".git", "node_modules", "vendor", "target", "dist", "build", ".venv", "venv"}
MAX_BYTES = 2_000_000

# Split sensitive prefixes so this scanner does not match its own source.
PATTERNS = (
    ("GitHub classic token", re.compile(r"\b" + "gh" + r"p_[A-Za-z0-9]{36}\b")),
    ("GitHub fine-grained token", re.compile(r"\b" + "github" + r"_pat_[A-Za-z0-9_]{20,}\b")),
    ("Slack token", re.compile(r"\b" + "xox" + r"[abprs]-[A-Za-z0-9-]{20,}\b")),
    ("AWS access-key id", re.compile(r"\b" + "AK" + r"IA[0-9A-Z]{16}\b")),
    ("private-key header", re.compile("-" * 5 + r"BEGIN (?:RSA |EC |DSA |OPENSSH )?PRIVATE KEY" + "-" * 5)),
)


def iter_files(root: Path):
    for current, dirs, names in os.walk(root):
        dirs[:] = [name for name in dirs if name not in SKIP_DIRS]
        base = Path(current)
        for name in names:
            path = base / name
            try:
                if path.is_symlink() or not path.is_file() or path.stat().st_size > MAX_BYTES:
                    continue
            except OSError:
                continue
            yield path


def main() -> int:
    findings: list[str] = []
    for path in iter_files(ROOT):
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except OSError as exc:
            findings.append(f"{path.relative_to(ROOT)}: unreadable file: {exc}")
            continue

        for label, pattern in PATTERNS:
            for match in pattern.finditer(text):
                line = text.count("\n", 0, match.start()) + 1
                findings.append(f"{path.relative_to(ROOT)}:{line}: possible {label}")

    if findings:
        print("Credential-pattern scan failed:", file=sys.stderr)
        for finding in findings:
            print(f"  {finding}", file=sys.stderr)
        return 1

    print("Credential-pattern scan passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
