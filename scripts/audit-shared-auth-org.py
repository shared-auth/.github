#!/usr/bin/env python3
"""Audit Shared Auth repository settings and GitHub Actions supply-chain policy.

The script is read-only. It intentionally distinguishes unavailable evidence from
passing evidence and writes a machine-readable report suitable for a protected
GitHub App or fine-grained token ceremony.
"""

from __future__ import annotations

import argparse
import base64
import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

API = "https://api.github.com"
FULL_SHA = re.compile(r"^[0-9a-f]{40}$")
DIGEST = re.compile(r"^sha256:[0-9a-f]{64}$")
USES = re.compile(r"(?m)^\s*-?\s*uses:\s*['\"]?([^\s'\"#]+)")


class GitHubAPI:
    def __init__(self, token: str) -> None:
        self.token = token

    def request(self, path: str) -> tuple[int, Any | None]:
        request = urllib.request.Request(
            API + path,
            headers={
                "Accept": "application/vnd.github+json",
                "Authorization": f"Bearer {self.token}",
                "X-GitHub-Api-Version": "2022-11-28",
                "User-Agent": "shared-auth-organization-audit/1",
            },
        )
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                payload = response.read()
                return response.status, json.loads(payload) if payload else None
        except urllib.error.HTTPError as error:
            payload = error.read()
            try:
                body = json.loads(payload) if payload else None
            except json.JSONDecodeError:
                body = {"message": payload.decode("utf-8", errors="replace")}
            return error.code, body


def finding(repo: str, control: str, actual: Any, expected: Any) -> dict[str, Any]:
    return {
        "repository": repo,
        "control": control,
        "state": "failed",
        "actual": actual,
        "expected": expected,
    }


def unavailable(repo: str, control: str, status: int, body: Any) -> dict[str, Any]:
    return {
        "repository": repo,
        "control": control,
        "state": "blocked",
        "http_status": status,
        "detail": body,
    }


def decode_content(item: dict[str, Any]) -> str:
    if item.get("encoding") != "base64":
        raise ValueError("GitHub content response was not base64")
    return base64.b64decode(item["content"]).decode("utf-8")


def audit_workflow(repo: str, path: str, text: str) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    for reference in USES.findall(text):
        if reference.startswith("./"):
            continue
        if reference.startswith("docker://"):
            image = reference.removeprefix("docker://")
            digest = image.rsplit("@", 1)[-1] if "@" in image else ""
            if not DIGEST.fullmatch(digest):
                results.append(finding(repo, f"{path}:container_action_pin", reference, "sha256 digest"))
            continue
        if "@" not in reference:
            results.append(finding(repo, f"{path}:action_pin", reference, "full commit SHA"))
            continue
        revision = reference.rsplit("@", 1)[1]
        if not FULL_SHA.fullmatch(revision):
            results.append(finding(repo, f"{path}:action_pin", reference, "full 40-character commit SHA"))

    if not re.search(r"(?m)^permissions:\s*(?:\n|\{)", text):
        results.append(finding(repo, f"{path}:permissions", "missing", "explicit top-level permissions"))
    if "actions/checkout@" in text and "persist-credentials: false" not in text:
        results.append(finding(repo, f"{path}:checkout_credentials", "persisted or unspecified", False))
    if "timeout-minutes:" not in text:
        results.append(finding(repo, f"{path}:timeouts", "missing", "at least one bounded job timeout"))

    forbidden = {
        "pull_request_target:": "untrusted code and privileged context must be separated",
        "permissions: write-all": "least-privilege permissions",
        "secrets: inherit": "explicit secret allowlist",
        "persist-credentials: true": "checkout credentials disabled",
    }
    for token, expected in forbidden.items():
        if token in text:
            results.append(finding(repo, f"{path}:forbidden:{token.rstrip(':')}", token, expected))
    return results


def audit_repository(api: GitHubAPI, owner: str, name: str) -> dict[str, Any]:
    full_name = f"{owner}/{name}"
    findings: list[dict[str, Any]] = []
    evidence: dict[str, Any] = {}

    status, repository = api.request(f"/repos/{owner}/{name}")
    if status != 200 or not isinstance(repository, dict):
        return {
            "repository": full_name,
            "state": "blocked",
            "findings": [unavailable(full_name, "repository_metadata", status, repository)],
            "evidence": {},
        }

    # Auto-merge is an operational convenience, not a security control. GitHub
    # may report it unavailable on repositories that cannot enable protected
    # branch conditions, so the audit records but does not require it.
    expected_settings = {
        "default_branch": "main",
        "allow_merge_commit": False,
        "allow_squash_merge": True,
        "allow_rebase_merge": True,
        "delete_branch_on_merge": True,
        "allow_update_branch": True,
    }
    evidence["allow_auto_merge"] = repository.get("allow_auto_merge")
    for key, expected in expected_settings.items():
        actual = repository.get(key)
        evidence[key] = actual
        if actual != expected:
            findings.append(finding(full_name, f"repository_settings:{key}", actual, expected))

    status, workflow_permissions = api.request(f"/repos/{owner}/{name}/actions/permissions/workflow")
    evidence["actions_permissions_http_status"] = status
    if status == 200 and isinstance(workflow_permissions, dict):
        expected_actions = {
            "default_workflow_permissions": "read",
            "can_approve_pull_request_reviews": False,
        }
        for key, expected in expected_actions.items():
            actual = workflow_permissions.get(key)
            evidence[f"actions_{key}"] = actual
            if actual != expected:
                findings.append(finding(full_name, f"actions_permissions:{key}", actual, expected))
    else:
        findings.append(unavailable(full_name, "actions_permissions", status, workflow_permissions))

    branch = urllib.parse.quote(repository["default_branch"], safe="")
    status, protection = api.request(f"/repos/{owner}/{name}/branches/{branch}/protection")
    evidence["branch_protection_http_status"] = status
    if status == 200 and isinstance(protection, dict):
        reviews = protection.get("required_pull_request_reviews") or {}
        review_count = reviews.get("required_approving_review_count", 0)
        if review_count < 1:
            findings.append(finding(full_name, "branch_protection:approvals", review_count, ">= 1"))
        if reviews.get("dismiss_stale_reviews") is not True:
            findings.append(finding(full_name, "branch_protection:dismiss_stale_reviews", reviews.get("dismiss_stale_reviews"), True))
        conversation = (protection.get("required_conversation_resolution") or {}).get("enabled")
        if conversation is not True:
            findings.append(finding(full_name, "branch_protection:conversation_resolution", conversation, True))
        force_pushes = (protection.get("allow_force_pushes") or {}).get("enabled")
        if force_pushes is not False:
            findings.append(finding(full_name, "branch_protection:force_pushes", force_pushes, False))
        deletions = (protection.get("allow_deletions") or {}).get("enabled")
        if deletions is not False:
            findings.append(finding(full_name, "branch_protection:deletions", deletions, False))
    else:
        findings.append(unavailable(full_name, "branch_protection", status, protection))

    # GitHub's check endpoints intentionally use different success codes:
    # vulnerability alerts return 204 when enabled; Dependabot security updates
    # return 200 when enabled. The PUT enablement endpoints return 204, but this
    # audit is read-only and therefore checks the GET contracts.
    security_checks = [
        ("vulnerability-alerts", "vulnerability_alerts", 204),
        ("automated-security-fixes", "automated_security_fixes", 200),
    ]
    for endpoint, control, expected_status in security_checks:
        status, body = api.request(f"/repos/{owner}/{name}/{endpoint}")
        evidence[f"{control}_http_status"] = status
        if status != expected_status:
            findings.append(finding(full_name, control, status, expected_status))

    status, workflow_listing = api.request(f"/repos/{owner}/{name}/contents/.github/workflows?ref={repository['default_branch']}")
    evidence["workflow_listing_http_status"] = status
    if status == 200 and isinstance(workflow_listing, list):
        for item in workflow_listing:
            if item.get("type") != "file" or not str(item.get("name", "")).endswith((".yml", ".yaml")):
                continue
            file_status, file_content = api.request(
                f"/repos/{owner}/{name}/contents/{urllib.parse.quote(item['path'])}?ref={repository['default_branch']}"
            )
            if file_status != 200 or not isinstance(file_content, dict):
                findings.append(unavailable(full_name, f"workflow_content:{item['path']}", file_status, file_content))
                continue
            try:
                text = decode_content(file_content)
            except (KeyError, ValueError, UnicodeDecodeError) as error:
                findings.append(unavailable(full_name, f"workflow_decode:{item['path']}", file_status, str(error)))
                continue
            findings.extend(audit_workflow(full_name, item["path"], text))
    elif status != 404:
        findings.append(unavailable(full_name, "workflow_listing", status, workflow_listing))

    state = "passed" if not findings else "failed"
    return {"repository": full_name, "state": state, "findings": findings, "evidence": evidence}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", default="config/shared-auth-repositories.json")
    parser.add_argument("--output", default="artifacts/shared-auth-org-audit.json")
    parser.add_argument("--soft-fail", action="store_true")
    args = parser.parse_args()

    token = os.environ.get("GH_TOKEN", "").strip()
    if not token:
        print("GH_TOKEN is required for the organization-wide audit", file=sys.stderr)
        return 2

    manifest_path = Path(args.manifest)
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    owner = manifest["owner"]
    repository_names = [item["name"] for item in manifest["repositories"]]

    api = GitHubAPI(token)
    reports = [audit_repository(api, owner, name) for name in repository_names]
    findings = [item for report in reports for item in report["findings"]]
    result = {
        "schema": "shared-auth/organization-security-audit/v1",
        "owner": owner,
        "repository_count": len(reports),
        "finding_count": len(findings),
        "state": "passed" if not findings else "failed",
        "repositories": reports,
    }

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    print(f"audited {len(reports)} repositories; findings={len(findings)}")
    for item in findings:
        print(f"{item['state'].upper()}: {item['repository']} {item['control']}")
    if os.environ.get("GITHUB_STEP_SUMMARY"):
        with Path(os.environ["GITHUB_STEP_SUMMARY"]).open("a", encoding="utf-8") as summary:
            summary.write("## Shared Auth organization security audit\n\n")
            summary.write(f"- Repositories: `{len(reports)}`\n")
            summary.write(f"- Findings: `{len(findings)}`\n")
            summary.write(f"- State: `{result['state']}`\n")

    return 0 if args.soft_fail or not findings else 1


if __name__ == "__main__":
    raise SystemExit(main())
