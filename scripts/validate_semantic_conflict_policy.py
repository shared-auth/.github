#!/usr/bin/env python3
"""Validate the organization safe-change and semantic conflict-resolution contract."""

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
LINEAR_REFERENCE_RE = re.compile(
    r"(?:https://linear\.app/[^\s)]+|\b[A-Z][A-Z0-9]{1,15}-[1-9][0-9]*\b)"
)

HUMAN_POLICY_FILES = (
    Path("AGENTS.md"),
    Path(".github/copilot-instructions.md"),
    Path("CONTRIBUTING.md"),
    Path(".github/pull_request_template.md"),
    Path("profile/README.md"),
    Path("agents/org-context.agent.md"),
)
PRIMARY_CONTROL_FILES = (
    Path("AGENTS.md"),
    Path(".github/copilot-instructions.md"),
    Path("CONTRIBUTING.md"),
)
COMMUNITY_FILES = (
    Path("SECURITY.md"),
    Path("SUPPORT.md"),
    Path("CODE_OF_CONDUCT.md"),
    Path(".github/ISSUE_TEMPLATE/bug_report.yml"),
    Path(".github/ISSUE_TEMPLATE/feature_request.yml"),
    Path(".github/ISSUE_TEMPLATE/config.yml"),
)
PROHIBITED_GIT_COMMANDS = (
    "git rebase",
    "git stash",
    "git reset",
    "git clean",
    "git filter-repo",
    "git checkout --",
    "git restore",
    "git branch -D",
    "git reflog expire",
    "git gc --prune",
    "git push --force",
    "git push -f",
)
PROHIBITED_FILESYSTEM_COMMANDS = (
    "rm",
    "mv",
    "sed",
    "find -delete",
    "xargs rm",
    "truncate",
    "shred",
    "dd",
)
TRACKED_CATEGORIES = {
    "feature",
    "fix",
    "enhancement",
    "bug",
    "security",
    "reliability",
    "documentation",
    "technical_debt",
}


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


def _validate_primary_controls(path: Path, text: str, errors: list[str]) -> None:
    label = path.as_posix()
    _require_all(
        label=label,
        text=text,
        needles=(
            "avoid git rebase in favor of git merge",
            "git stash",
            "git reset",
            "git clean",
            "git filter-repo",
            "uncommitted",
            "untracked",
            "linear",
            "before implementation",
            "stop",
        ),
        errors=errors,
    )
    lowered = text.casefold()
    for command in PROHIBITED_GIT_COMMANDS:
        if command.casefold() not in lowered:
            errors.append(f"{label} must name prohibited Git command: {command}")
    for command in PROHIBITED_FILESYSTEM_COMMANDS:
        if command.casefold() not in lowered:
            errors.append(f"{label} must name prohibited filesystem command: {command}")
    for category in ("feature", "fix", "enhancement", "bug"):
        if category not in lowered:
            errors.append(f"{label} must require Linear tracking for category: {category}")


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
    if checkbox_count < 10:
        errors.append(
            ".github/pull_request_template.md must contain at least ten checklist items"
        )
    _require_all(
        label=".github/pull_request_template.md",
        text=text,
        needles=(
            "merge base",
            "both sides",
            "conflict markers",
            "tradeoffs",
            "linear issue",
            "avoid git rebase in favor of git merge",
            "uncommitted",
            "prohibited destructive",
        ),
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


def _validate_machine_conflict_policy(root: Path, errors: list[str]) -> None:
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


def _validate_organization_policy(root: Path, errors: list[str]) -> None:
    payload = _load_json_file(root / "organization-policy.json", root, errors)
    if not isinstance(payload, dict):
        if payload is not None:
            errors.append("organization-policy.json must contain a JSON object")
        return
    if payload.get("schema_version") != 1:
        errors.append("organization-policy.json schema_version must equal 1")

    tracking = payload.get("work_tracking")
    if not isinstance(tracking, dict):
        errors.append("organization-policy.json lacks work_tracking")
    else:
        expected = {
            "provider": "Linear",
            "search_before_create": True,
            "require_issue_before_implementation": True,
            "require_pull_request_reference": True,
            "require_status_and_validation_sync": True,
            "on_unmapped_or_ambiguous": "stop_and_report",
            "untracked_drive_by_changes": "forbidden",
        }
        for key, value in expected.items():
            if tracking.get(key) != value:
                errors.append(f"work_tracking.{key} must equal {value!r}")
        categories = set(tracking.get("tracked_categories", ()))
        missing = sorted(TRACKED_CATEGORIES - categories)
        if missing:
            errors.append("work_tracking.tracked_categories is missing: " + ", ".join(missing))

    safe = payload.get("safe_change_policy")
    if not isinstance(safe, dict):
        errors.append("organization-policy.json lacks safe_change_policy")
        return
    expected_safe = {
        "integration_strategy": "merge",
        "directive": "avoid git rebase in favor of git merge",
        "inspect_worktree_before_mutation_and_publish": True,
        "preserve_uncommitted_and_untracked_work": True,
        "on_unexpected_worktree_changes": "stop_and_report",
        "force_push": "forbidden",
        "bypass_required_checks": "forbidden",
        "disable_security_controls": "forbidden",
    }
    for key, value in expected_safe.items():
        if safe.get(key) != value:
            errors.append(f"safe_change_policy.{key} must equal {value!r}")
    git_commands = set(safe.get("prohibited_git_commands", ()))
    missing_git = sorted(set(PROHIBITED_GIT_COMMANDS) - git_commands)
    if missing_git:
        errors.append("safe_change_policy.prohibited_git_commands is missing: " + ", ".join(missing_git))
    filesystem_commands = set(safe.get("prohibited_filesystem_commands", ()))
    missing_fs = sorted(set(PROHIBITED_FILESYSTEM_COMMANDS) - filesystem_commands)
    if missing_fs:
        errors.append("safe_change_policy.prohibited_filesystem_commands is missing: " + ", ".join(missing_fs))


def _validate_reusable_workflow(root: Path, errors: list[str]) -> None:
    path = root / ".github/workflows/reusable-organization-policy.yml"
    text = _read_regular_text(path, root, errors)
    if text is None:
        return
    _require_all(
        label=".github/workflows/reusable-organization-policy.yml",
        text=text,
        needles=(
            "workflow_call",
            "contents: read",
            "pull-requests: read",
            "persist-credentials: false",
            "avoid git rebase in favor of git merge",
            "linear",
        ),
        errors=errors,
    )
    if not re.search(r"actions/checkout@[0-9a-f]{40}\b", text):
        errors.append("reusable workflow must pin actions/checkout to a full commit SHA")
    if re.search(r"permissions:\s*write-all", text, re.IGNORECASE):
        errors.append("reusable workflow must not request write-all permissions")


def _validate_community_files(root: Path, errors: list[str]) -> None:
    for relative in COMMUNITY_FILES:
        text = _read_regular_text(root / relative, root, errors)
        if text is None:
            continue
        lowered = text.casefold()
        if relative == Path("SECURITY.md"):
            _require_all(
                label=relative.as_posix(),
                text=text,
                needles=("do not open a public issue", "private", "linear", "credentials"),
                errors=errors,
            )
        elif relative == Path("SUPPORT.md"):
            _require_all(
                label=relative.as_posix(),
                text=text,
                needles=("security.md", "credentials", "linear"),
                errors=errors,
            )
        elif relative.suffix == ".yml" and relative.name != "config.yml":
            if "required: true" not in lowered:
                errors.append(f"{relative} must include required fields")


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
        if relative in PRIMARY_CONTROL_FILES:
            _validate_primary_controls(relative, text, errors)

    _validate_primary_agent_instructions(documents, errors)
    _validate_pull_request_template(
        documents.get(Path(".github/pull_request_template.md")), errors
    )
    _validate_machine_conflict_policy(root, errors)
    _validate_organization_policy(root, errors)
    _validate_reusable_workflow(root, errors)
    _validate_community_files(root, errors)
    _validate_manifest(root, errors)
    return sorted(set(errors))


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path("."))
    args = parser.parse_args(argv)
    errors = validate_repository(args.root)
    if errors:
        print("organization policy validation failed:", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1
    print("organization policy validation passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
