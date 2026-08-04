#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path
from typing import Iterable

ROOT = Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve()
MANDATORY_DIRECTIVE = (
    "resolve any and all git conflicts semantically, will full context, even looking back "
    "3-10 commits in git log history for more context - never hastily pick sides in a conflict "
    "but merge things conceptually, using max context and complete conceptual awareness for a "
    "given github organization's repos and external org repos too"
)

REQUIRED_FILES = (
    "README.md",
    "profile/README.md",
    "ORG_CONTEXT.md",
    "agents.md",
    "AGENTS.md",
    "CLAUDE.md",
    "GEMINI.md",
    ".claude/CLAUDE.md",
    ".gemini/GEMINI.md",
    ".openai/AGENTS.md",
    "CONTRIBUTING.md",
    "SECURITY.md",
    "SUPPORT.md",
    "CODE_OF_CONDUCT.md",
    "GOVERNANCE.md",
    "agents/org-context.agent.md",
    "organization-policy.json",
    "policies/REPOSITORY_BASELINE.md",
    "project-context.yaml",
    ".github/pull_request_template.md",
    ".github/copilot-instructions.md",
    ".github/dependabot.yml",
    ".github/ISSUE_TEMPLATE/bug_report.yml",
    ".github/ISSUE_TEMPLATE/feature_request.yml",
    ".github/ISSUE_TEMPLATE/config.yml",
    ".github/workflows/agent-policy.yml",
    ".github/workflows/baseline-policy.yml",
    ".github/workflows/reusable-policy.yml",
    "workflow-templates/organization-policy.properties.json",
    "workflow-templates/organization-policy.yml",
)

POINTER_FILES = (
    "CLAUDE.md",
    "GEMINI.md",
    ".claude/CLAUDE.md",
    ".gemini/GEMINI.md",
    ".openai/AGENTS.md",
)

AGENT_PHRASES = (
    "avoid git rebase in favor of git merge",
    "git stash",
    "git reset",
    "git clean",
    "git filter-repo",
    "3–10 relevant commits",
    "Never report",
)

SKIP_DIRS = {".git", "node_modules", "vendor", "target", "dist", "build", ".venv", "venv"}
MAX_BYTES = 2_000_000
PLACEHOLDER_RE = re.compile(r"\{\{[A-Z][A-Z0-9_]*\}\}")
CONFLICT_RE = re.compile(r"(?m)^(?:<{7}|>{7}|\|{7})(?: .*)?$|^={7}$")
ACTION_RE = re.compile(r"^\s*(?:-\s+)?uses:\s*([^\s#]+)")

SECRET_PATTERNS = (
    ("GitHub token", re.compile(r"\bgh[pousr]_[A-Za-z0-9]{20,}\b")),
    ("GitHub fine-grained token", re.compile(r"\bgithub_pat_[A-Za-z0-9_]{20,}\b")),
    ("Slack token", re.compile(r"\bxox[abprs]-[A-Za-z0-9-]{20,}\b")),
    ("AWS access key", re.compile(r"\bAKIA[0-9A-Z]{16}\b")),
    ("private key", re.compile(r"-----BEGIN (?:RSA |EC |DSA |OPENSSH )?PRIVATE KEY-----")),
    ("bearer credential", re.compile(r"(?i)authorization:\s*bearer\s+[A-Za-z0-9._-]{16,}")),
)


def _read_text(path: Path, errors: list[str]) -> str | None:
    try:
        return path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        errors.append(f"unable to read UTF-8 policy file {path}: {exc}")
        return None


def _iter_files(root: Path) -> Iterable[Path]:
    for current, directories, names in os.walk(root, followlinks=False):
        directories[:] = [name for name in directories if name not in SKIP_DIRS]
        base = Path(current)
        for name in names:
            yield base / name


def _validate_json(path: Path, errors: list[str]) -> dict | None:
    text = _read_text(path, errors)
    if text is None:
        return None
    try:
        value = json.loads(text)
    except json.JSONDecodeError as exc:
        errors.append(f"invalid JSON in {path}: {exc}")
        return None
    if not isinstance(value, dict):
        errors.append(f"expected JSON object in {path}")
        return None
    return value


def _validate_machine_context(root: Path, errors: list[str]) -> None:
    context = _validate_json(root / "project-context.yaml", errors)
    if context is not None:
        try:
            conflict = context["git_conflict_resolution"]
            history = conflict["history_lookback_commits"]
            scope = set(conflict["context_scope"])
            shortcuts = set(conflict["forbidden_shortcuts"])
            github = context["github"]
            linear = context["linear"]
        except (KeyError, TypeError) as exc:
            errors.append(f"project-context.yaml missing required structure: {exc}")
        else:
            if conflict.get("directive_verbatim") != MANDATORY_DIRECTIVE:
                errors.append("project-context.yaml does not preserve the mandatory directive verbatim")
            if history.get("minimum") != 3 or history.get("maximum") != 10:
                errors.append("project-context.yaml must require a 3–10 commit history window")
            for key in ("when_available", "inspect_both_sides", "inspect_merge_base", "path_scoped_history"):
                if history.get(key) is not True:
                    errors.append(f"project-context.yaml history policy must set {key}=true")
            required_scope = {
                "conflicted_repository",
                "same_github_organization_repositories",
                "relevant_external_github_organization_repositories",
                "linear_project_context",
            }
            if not required_scope.issubset(scope):
                errors.append("project-context.yaml is missing required same-org, external-org, or Linear context")
            if not {"wholesale_ours", "wholesale_theirs"}.issubset(shortcuts):
                errors.append("project-context.yaml must forbid wholesale ours/theirs selection")
            if not isinstance(github.get("login"), str) or not github["login"].strip():
                errors.append("project-context.yaml has no GitHub organization login")
            if not isinstance(linear.get("project_id"), str) or not linear["project_id"].strip():
                errors.append("project-context.yaml has no immutable Linear project ID")
            if not isinstance(linear.get("project_url"), str) or not linear["project_url"].startswith("https://linear.app/"):
                errors.append("project-context.yaml has no canonical Linear project URL")

    policy = _validate_json(root / "organization-policy.json", errors)
    if policy is not None:
        try:
            tracking = policy["work_tracking"]
            safe = policy["safe_change_policy"]
        except (KeyError, TypeError) as exc:
            errors.append(f"organization-policy.json missing required structure: {exc}")
        else:
            if tracking.get("require_issue_before_implementation") is not True:
                errors.append("organization-policy.json must require a Linear issue before implementation")
            if tracking.get("on_unmapped_or_ambiguous") != "stop_and_report":
                errors.append("organization-policy.json must fail closed for unmapped or ambiguous work")
            if safe.get("integration_strategy") != "merge":
                errors.append("organization-policy.json must prefer merge integration")
            if safe.get("force_push") != "forbidden":
                errors.append("organization-policy.json must forbid force pushes")


def _validate_workflows(root: Path, errors: list[str]) -> None:
    workflow_paths = sorted((root / ".github/workflows").glob("*.y*ml"))
    workflow_paths += sorted((root / "workflow-templates").glob("*.y*ml"))
    for path in workflow_paths:
        text = _read_text(path, errors)
        if text is None:
            continue
        relative = path.relative_to(root)
        if not re.search(r"(?m)^permissions:\s*(?:\n|$)", text):
            errors.append(f"workflow lacks explicit top-level permissions: {relative}")
        if "timeout-minutes:" not in text:
            errors.append(f"workflow lacks an explicit timeout: {relative}")
        for number, line in enumerate(text.splitlines(), 1):
            match = ACTION_RE.search(line)
            if not match:
                continue
            reference = match.group(1).strip('"\'')
            if reference.startswith("./"):
                continue
            if reference.startswith("docker://"):
                if not re.search(r"@sha256:[0-9a-fA-F]{64}$", reference):
                    errors.append(f"external Docker action is not digest-pinned: {relative}:{number}: {reference}")
                continue
            if not re.search(r"@[0-9a-fA-F]{40}$", reference):
                errors.append(f"external Action is not pinned to a full SHA: {relative}:{number}: {reference}")
        if "actions/checkout@" in text and "persist-credentials: false" not in text:
            errors.append(f"checkout credentials persist in {relative}")


def validate(root: Path) -> list[str]:
    root = root.resolve()
    errors: list[str] = []

    for relative in REQUIRED_FILES:
        path = root / relative
        if path.is_symlink():
            errors.append(f"required policy path must not be a symlink: {relative}")
        elif not path.is_file():
            errors.append(f"missing required file: {relative}")

    agents_path = root / "agents.md"
    if agents_path.is_file() and not agents_path.is_symlink():
        agents = _read_text(agents_path, errors)
        if agents is not None:
            if MANDATORY_DIRECTIVE not in agents:
                errors.append("agents.md does not preserve the mandatory directive verbatim")
            for phrase in AGENT_PHRASES:
                if phrase not in agents:
                    errors.append(f"agents.md missing required phrase: {phrase!r}")

    uppercase_path = root / "AGENTS.md"
    if uppercase_path.is_file() and not uppercase_path.is_symlink():
        uppercase = _read_text(uppercase_path, errors)
        if uppercase is not None and MANDATORY_DIRECTIVE not in uppercase:
            errors.append("AGENTS.md does not preserve the mandatory directive verbatim")

    for relative in POINTER_FILES:
        path = root / relative
        if not path.is_file() or path.is_symlink():
            continue
        text = _read_text(path, errors)
        if text is not None and "agents.md" not in text:
            errors.append(f"provider instruction file does not point to canonical agents.md: {relative}")

    copilot_path = root / ".github/copilot-instructions.md"
    if copilot_path.is_file() and not copilot_path.is_symlink():
        copilot = _read_text(copilot_path, errors)
        if copilot is not None:
            if "AGENTS.md" not in copilot and "agents.md" not in copilot:
                errors.append("Copilot instructions do not reference an organization agent-policy file")
            if "3–10" not in copilot or "external organizations" not in copilot:
                errors.append("Copilot instructions omit the history or external-organization conflict scope")

    _validate_machine_context(root, errors)

    for path in _iter_files(root):
        relative = path.relative_to(root)
        if path.is_symlink():
            errors.append(f"symlink is not allowed in the public policy baseline: {relative}")
            continue
        try:
            stat = path.stat()
        except OSError as exc:
            errors.append(f"unable to inspect {relative}: {exc}")
            continue
        if not path.is_file() or stat.st_size > MAX_BYTES:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        except OSError as exc:
            errors.append(f"unable to read {relative}: {exc}")
            continue
        if PLACEHOLDER_RE.search(text):
            errors.append(f"unrendered placeholder in {relative}")
        if CONFLICT_RE.search(text):
            errors.append(f"unresolved conflict marker in {relative}")
        for label, pattern in SECRET_PATTERNS:
            if pattern.search(text):
                errors.append(f"possible {label} in {relative}")
        if text and not text.endswith("\n"):
            errors.append(f"missing final newline: {relative}")

    _validate_workflows(root, errors)
    return errors


def main() -> int:
    errors = validate(ROOT)
    if errors:
        for message in errors:
            print(f"ERROR: {message}", file=sys.stderr)
        print(f"FAIL: {len(errors)} organization-baseline error(s)", file=sys.stderr)
        return 1
    print(f"PASS: validated {ROOT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
