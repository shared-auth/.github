#!/usr/bin/env python3
"""Validate the organization semantic Git conflict-resolution contract."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import sys
from typing import Iterable, Mapping, Sequence

MAX_POLICY_FILE_BYTES = 256 * 1024
CONFLICT_MARKER_RE = re.compile(r"^(?:<<<<<<<|=======|>>>>>>>)", re.MULTILINE)
HISTORY_RANGE_RE = re.compile(r"\b3\b[^\n]{0,48}\b10\b", re.IGNORECASE)

HUMAN_POLICY_FILES = (
    Path("AGENTS.md"),
    Path(".github/copilot-instructions.md"),
    Path("CONTRIBUTING.md"),
    Path(".github/pull_request_template.md"),
    Path("profile/README.md"),
    Path("agents/org-context.agent.md"),
)


def _display(path: Path, root: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return path.as_posix()


def _read_regular_text(path: Path, root: Path, errors: list[str]) -> str | None:
    label = _display(path, root)
    if not path.exists():
        errors.append(f"missing required file: {label}")
        return None
    if path.is_symlink() or not path.is_file():
        errors.append(f"required path must be a regular file: {label}")
        return None
    try:
        payload = path.read_bytes()
    except OSError as exc:
        errors.append(f"cannot read {label}: {exc}")
        return None
    if not payload:
        errors.append(f"required file is empty: {label}")
        return None
    if len(payload) > MAX_POLICY_FILE_BYTES:
        errors.append(f"policy file exceeds {MAX_POLICY_FILE_BYTES} bytes: {label}")
        return None
    try:
        text = payload.decode("utf-8")
    except UnicodeDecodeError:
        errors.append(f"required file is not valid UTF-8: {label}")
        return None
    if CONFLICT_MARKER_RE.search(text):
        errors.append(f"unresolved Git conflict marker found in {label}")
    return text


def _require_all(
    *,
    label: str,
    text: str,
    needles: Iterable[str],
    errors: list[str],
) -> None:
    lowered = text.casefold()
    for needle in needles:
        if needle.casefold() not in lowered:
            errors.append(f"{label} is missing required language: {needle}")


def _validate_human_policy(path: Path, text: str, errors: list[str]) -> None:
    label = path.as_posix()
    _require_all(
        label=label,
        text=text,
        needles=("semantic", "full context", "ours", "theirs", "conceptual merge"),
        errors=errors,
    )
    if not HISTORY_RANGE_RE.search(text):
        errors.append(f"{label} must require reviewing 3–10 relevant commits")
    lowered = text.casefold()
    if "organization" not in lowered or "external" not in lowered:
        errors.append(
            f"{label} must cover same-organization and relevant external repositories"
        )
    if not any(word in lowered for word in ("test", "validation", "check")):
        errors.append(f"{label} must require post-resolution validation")


def _validate_primary_agent_instructions(
    documents: Mapping[Path, str], errors: list[str]
) -> None:
    for path in (Path("AGENTS.md"), Path(".github/copilot-instructions.md")):
        text = documents.get(path)
        if text is None:
            continue
        _require_all(
            label=path.as_posix(),
            text=text,
            needles=("git log", "git show", "git blame"),
            errors=errors,
        )


def _validate_pull_request_template(text: str | None, errors: list[str]) -> None:
    if text is None:
        return
    checkbox_count = len(re.findall(r"^\s*-\s*\[[ xX]\]", text, re.MULTILINE))
    if checkbox_count < 5:
        errors.append(
            ".github/pull_request_template.md must contain at least five checklist items"
        )
    _require_all(
        label=".github/pull_request_template.md",
        text=text,
        needles=("merge base", "both sides", "conflict markers", "tradeoffs"),
        errors=errors,
    )


def _load_json_file(path: Path, root: Path, errors: list[str]) -> object | None:
    text = _read_regular_text(path, root, errors)
    if text is None:
        return None
    try:
        return json.loads(text)
    except (json.JSONDecodeError, UnicodeError) as exc:
        errors.append(f"invalid JSON in {_display(path, root)}: {exc}")
        return None


def _validate_machine_policy(root: Path, errors: list[str]) -> None:
    payload = _load_json_file(root / "project-context.yaml", root, errors)
    if not isinstance(payload, dict):
        if payload is not None:
            errors.append("project-context.yaml must contain a JSON object")
        return
    policy = payload.get("git_conflict_resolution")
    if not isinstance(policy, dict):
        errors.append("project-context.yaml lacks git_conflict_resolution")
        return
    if policy.get("mode") != "semantic_conceptual_merge":
        errors.append("machine policy mode must be semantic_conceptual_merge")

    history = policy.get("history_lookback_commits")
    expected_history = {
        "minimum": 3,
        "maximum": 10,
        "when_available": True,
        "inspect_both_sides": True,
        "inspect_merge_base": True,
        "path_scoped_history": True,
    }
    if history != expected_history:
        errors.append("machine policy must enforce the exact 3–10 commit history contract")

    scope = set(policy.get("context_scope", ()))
    required_scope = {
        "conflicted_repository",
        "same_github_organization_repositories",
        "relevant_external_github_organization_repositories",
        "linear_project_context",
        "pull_requests_issues_architecture_decisions_tests_and_docs",
    }
    missing_scope = sorted(required_scope - scope)
    if missing_scope:
        errors.append(f"machine policy context_scope is missing: {', '.join(missing_scope)}")

    forbidden = set(policy.get("forbidden_shortcuts", ()))
    required_forbidden = {
        "wholesale_ours",
        "wholesale_theirs",
        "wholesale_current",
        "wholesale_incoming",
        "discarding_one_side_without_conceptual_analysis",
    }
    missing_forbidden = sorted(required_forbidden - forbidden)
    if missing_forbidden:
        errors.append(
            "machine policy forbidden_shortcuts is missing: "
            + ", ".join(missing_forbidden)
        )

    outcome = policy.get("required_outcome")
    if not isinstance(outcome, str) or "preserve compatible intent" not in outcome:
        errors.append("machine policy must require preservation of compatible intent")


def _validate_manifest(root: Path, errors: list[str]) -> None:
    payload = _load_json_file(root / "org-context-manifest.json", root, errors)
    if not isinstance(payload, dict):
        if payload is not None:
            errors.append("org-context-manifest.json must contain a JSON object")
        return
    files = payload.get("files")
    if not isinstance(files, dict) or not files:
        errors.append("org-context-manifest.json must contain non-empty files hashes")
        return
    for relative, expected in sorted(files.items()):
        if not isinstance(relative, str) or not isinstance(expected, str):
            errors.append("manifest file paths and hashes must be strings")
            continue
        path = root / relative
        if not path.exists() or path.is_symlink() or not path.is_file():
            errors.append(f"manifest-managed path is missing or not regular: {relative}")
            continue
        actual = hashlib.sha256(path.read_bytes()).hexdigest()
        if actual != expected:
            errors.append(f"manifest hash mismatch: {relative}")


def validate_repository(root: Path) -> list[str]:
    root = root.resolve()
    errors: list[str] = []
    documents: dict[Path, str] = {}
    for relative in HUMAN_POLICY_FILES:
        text = _read_regular_text(root / relative, root, errors)
        if text is None:
            continue
        documents[relative] = text
        _validate_human_policy(relative, text, errors)

    _validate_primary_agent_instructions(documents, errors)
    _validate_pull_request_template(
        documents.get(Path(".github/pull_request_template.md")), errors
    )
    _validate_machine_policy(root, errors)
    _validate_manifest(root, errors)
    return sorted(set(errors))


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path("."))
    args = parser.parse_args(argv)
    errors = validate_repository(args.root)
    if errors:
        print("semantic conflict policy validation failed:", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1
    print("semantic conflict policy validation passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
