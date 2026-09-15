#!/usr/bin/env python3
"""Audit Shared Auth repositories for configuration-authority collisions.

This scanner is intentionally structural. It does not become another parser for
Shared Auth policy semantics; those remain owned by shared-auth-interfaces and
runtime libraries. The scanner enforces which file is allowed to own which
concern and reports unavailable evidence separately from passing evidence.
"""

from __future__ import annotations

import argparse
import base64
import json
import os
import sys
import tomllib
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

API = "https://api.github.com"


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
                "User-Agent": "shared-auth-config-authority-audit/1",
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


def decode_content(item: dict[str, Any]) -> str:
    if item.get("encoding") != "base64":
        raise ValueError("GitHub content response was not base64")
    return base64.b64decode(item["content"]).decode("utf-8")


def result(repo: str, control: str, state: str, actual: Any, expected: Any) -> dict[str, Any]:
    return {
        "repository": repo,
        "control": control,
        "state": state,
        "actual": actual,
        "expected": expected,
    }


def blocked(repo: str, control: str, status: int, detail: Any) -> dict[str, Any]:
    return {
        "repository": repo,
        "control": control,
        "state": "blocked",
        "http_status": status,
        "detail": detail,
    }


def parse_toml(repo: str, path: str, text: str) -> tuple[dict[str, Any] | None, list[dict[str, Any]]]:
    try:
        return tomllib.loads(text), []
    except tomllib.TOMLDecodeError as error:
        return None, [result(repo, f"{path}:toml", "failed", str(error), "valid TOML")]


def audit_policy_document(
    repo: str,
    path: str,
    text: str,
    authority: dict[str, Any],
) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    parsed, parse_findings = parse_toml(repo, path, text)
    findings.extend(parse_findings)
    if parsed is None:
        return findings

    policy = authority["consumer_policy"]
    topology = authority["fleet_topology"]
    keys = set(parsed)
    allowed = set(policy["allowed_top_level_sections"])
    required = set(policy["required_top_level_sections"])
    topology_only = set(topology["topology_only_sections"])

    leaked = sorted(keys & topology_only)
    if leaked:
        findings.append(
            result(
                repo,
                f"{path}:topology_leak",
                "failed",
                leaked,
                "no fleet-topology sections in a consumer-policy file",
            )
        )

    unknown = sorted(keys - allowed)
    if unknown:
        findings.append(
            result(repo, f"{path}:unknown_top_level", "failed", unknown, sorted(allowed))
        )

    missing = sorted(required - keys)
    if missing:
        findings.append(
            result(repo, f"{path}:required_top_level", "failed", missing, sorted(required))
        )

    if parsed.get("schema_version") != 1:
        findings.append(
            result(repo, f"{path}:schema_version", "failed", parsed.get("schema_version"), 1)
        )

    compatibility = parsed.get("compatibility")
    if not isinstance(compatibility, dict):
        findings.append(
            result(repo, f"{path}:compatibility", "failed", compatibility, "table")
        )
    else:
        repository = compatibility.get("repository")
        expected_repository = "https://github.com/shared-auth/shared-auth-interfaces"
        if repository != expected_repository:
            findings.append(
                result(repo, f"{path}:compatibility.repository", "failed", repository, expected_repository)
            )
        has_commit = isinstance(compatibility.get("commit"), str)
        has_range = isinstance(compatibility.get("range"), dict)
        if has_commit == has_range:
            findings.append(
                result(
                    repo,
                    f"{path}:compatibility.revision",
                    "failed",
                    compatibility,
                    "exactly one of commit or range",
                )
            )
    return findings


def audit_topology_document(
    repo: str,
    repo_name: str,
    path: str,
    text: str,
    authority: dict[str, Any],
) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    allowed_repositories = set(authority["fleet_topology"]["allowed_repositories"])
    if repo_name not in allowed_repositories:
        findings.append(
            result(repo, f"{path}:owner", "failed", repo_name, sorted(allowed_repositories))
        )

    parsed, parse_findings = parse_toml(repo, path, text)
    findings.extend(parse_findings)
    if parsed is None:
        return findings

    if not isinstance(parsed.get("contract"), dict):
        findings.append(result(repo, f"{path}:contract", "failed", None, "[contract] table"))
    else:
        if parsed["contract"].get("name") != "shared-auth":
            findings.append(
                result(repo, f"{path}:contract.name", "failed", parsed["contract"].get("name"), "shared-auth")
            )
        if parsed["contract"].get("secrets_allowed") is not False:
            findings.append(
                result(repo, f"{path}:contract.secrets_allowed", "failed", parsed["contract"].get("secrets_allowed"), False)
            )
    return findings


def fetch_text(
    api: GitHubAPI,
    owner: str,
    repo_name: str,
    branch: str,
    path: str,
) -> tuple[str, str | None, dict[str, Any] | None]:
    encoded = urllib.parse.quote(path, safe="/")
    status, body = api.request(f"/repos/{owner}/{repo_name}/contents/{encoded}?ref={urllib.parse.quote(branch, safe='')}")
    if status == 404:
        return "missing", None, None
    if status != 200 or not isinstance(body, dict):
        return "blocked", None, {"status": status, "body": body}
    try:
        return "present", decode_content(body), None
    except (KeyError, ValueError, UnicodeDecodeError) as error:
        return "blocked", None, {"status": status, "body": str(error)}


def audit_repository(
    api: GitHubAPI,
    owner: str,
    item: dict[str, Any],
    authority: dict[str, Any],
    default_branch: str,
) -> dict[str, Any]:
    repo_name = item["name"]
    repo = f"{owner}/{repo_name}"
    findings: list[dict[str, Any]] = []
    evidence: dict[str, Any] = {"classification": item.get("classification")}

    metadata_status, metadata = api.request(f"/repos/{owner}/{repo_name}")
    if metadata_status != 200 or not isinstance(metadata, dict):
        return {
            "repository": repo,
            "state": "blocked",
            "findings": [blocked(repo, "repository_metadata", metadata_status, metadata)],
            "evidence": evidence,
        }
    branch = str(metadata.get("default_branch") or default_branch)
    evidence["default_branch"] = branch

    policy = authority["consumer_policy"]
    canonical = policy["canonical_path"]
    aliases = list(policy["compatibility_aliases"])
    policy_paths = [canonical, *aliases]
    policy_docs: dict[str, str] = {}

    for path in policy_paths:
        state, text, error = fetch_text(api, owner, repo_name, branch, path)
        evidence[path] = state
        if state == "present" and text is not None:
            policy_docs[path] = text
        elif state == "blocked" and error is not None:
            findings.append(blocked(repo, f"{path}:read", int(error["status"]), error["body"]))

    present_policy_paths = sorted(policy_docs)
    if len(present_policy_paths) > 1 and policy.get("fail_if_multiple_present") is True:
        findings.append(
            result(repo, "consumer_policy:filename_collision", "failed", present_policy_paths, f"exactly one of {policy_paths}")
        )
    elif len(present_policy_paths) == 1 and present_policy_paths[0] != canonical:
        state = str(policy.get("legacy_alias_state", "warning"))
        findings.append(
            result(repo, "consumer_policy:legacy_alias", state, present_policy_paths[0], canonical)
        )

    for path, text in policy_docs.items():
        findings.extend(audit_policy_document(repo, path, text, authority))

    topology_path = authority["fleet_topology"]["canonical_path"]
    topology_state, topology_text, topology_error = fetch_text(api, owner, repo_name, branch, topology_path)
    evidence[topology_path] = topology_state
    if topology_state == "present" and topology_text is not None:
        findings.extend(audit_topology_document(repo, repo_name, topology_path, topology_text, authority))
    elif topology_state == "blocked" and topology_error is not None:
        findings.append(blocked(repo, f"{topology_path}:read", int(topology_error["status"]), topology_error["body"]))

    realm_path = authority["runtime"]["realm_contract_path"]
    realm_state, _, realm_error = fetch_text(api, owner, repo_name, branch, realm_path)
    evidence[realm_path] = realm_state
    if realm_state == "present" and repo_name not in set(authority["runtime"]["realm_contract_repositories"]):
        findings.append(
            result(
                repo,
                f"{realm_path}:owner",
                "failed",
                repo_name,
                sorted(authority["runtime"]["realm_contract_repositories"]),
            )
        )
    elif realm_state == "blocked" and realm_error is not None:
        findings.append(blocked(repo, f"{realm_path}:read", int(realm_error["status"]), realm_error["body"]))

    hard = [item for item in findings if item["state"] in {"failed", "blocked"}]
    warnings = [item for item in findings if item["state"] == "warning"]
    state = "failed" if hard else "warning" if warnings else "passed"
    return {"repository": repo, "state": state, "findings": findings, "evidence": evidence}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Audit Shared Auth config authority across the repository fleet")
    parser.add_argument("--manifest", default="config/shared-auth-repositories.json")
    parser.add_argument("--authority", default="config/shared-auth-config-authority.json")
    parser.add_argument("--output", default="artifacts/shared-auth-config-authority-audit.json")
    parser.add_argument("--soft-fail", action="store_true")
    parser.add_argument("--fail-warnings", action="store_true")
    args = parser.parse_args(argv)

    token = os.environ.get("GH_TOKEN", "").strip()
    if not token:
        print("GH_TOKEN is required for the fleet config-authority audit", file=sys.stderr)
        return 2

    manifest = json.loads(Path(args.manifest).read_text(encoding="utf-8"))
    authority = json.loads(Path(args.authority).read_text(encoding="utf-8"))
    if authority.get("schema") != "shared-auth/config-authority/v1":
        print("unsupported config authority schema", file=sys.stderr)
        return 2

    owner = manifest["owner"]
    default_branch = manifest.get("default_branch", "main")
    repositories = sorted(manifest["repositories"], key=lambda item: item["name"])
    api = GitHubAPI(token)
    reports = [audit_repository(api, owner, item, authority, default_branch) for item in repositories]
    findings = [finding for report in reports for finding in report["findings"]]
    hard = [item for item in findings if item["state"] in {"failed", "blocked"}]
    warnings = [item for item in findings if item["state"] == "warning"]
    state = "failed" if hard else "warning" if warnings else "passed"

    payload = {
        "schema": "shared-auth/config-authority-audit/v1",
        "authority_schema": authority["schema"],
        "owner": owner,
        "repository_count": len(reports),
        "finding_count": len(findings),
        "hard_finding_count": len(hard),
        "warning_count": len(warnings),
        "state": state,
        "repositories": reports,
    }
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    print(
        f"audited {len(reports)} repositories; hard={len(hard)} warnings={len(warnings)} state={state}"
    )
    for item in findings:
        print(f"{item['state'].upper()}: {item['repository']} {item['control']}")

    if os.environ.get("GITHUB_STEP_SUMMARY"):
        with Path(os.environ["GITHUB_STEP_SUMMARY"]).open("a", encoding="utf-8") as summary:
            summary.write("## Shared Auth config authority audit\n\n")
            summary.write(f"- Repositories: `{len(reports)}`\n")
            summary.write(f"- Hard findings: `{len(hard)}`\n")
            summary.write(f"- Warnings: `{len(warnings)}`\n")
            summary.write(f"- State: `{state}`\n")

    should_fail = bool(hard) or (args.fail_warnings and bool(warnings))
    return 0 if args.soft_fail or not should_fail else 1


if __name__ == "__main__":
    raise SystemExit(main())
