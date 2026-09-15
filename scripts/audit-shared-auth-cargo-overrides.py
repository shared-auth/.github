#!/usr/bin/env python3
"""Reject repository-local Cargo mechanisms that can bypass reviewed runtime pins."""
from __future__ import annotations

import argparse
import importlib.util
import json
import os
import sys
import urllib.parse
from pathlib import Path
from typing import Any

BASE_PATH = Path(__file__).with_name("audit-shared-auth-runtime-adoption.py")
spec = importlib.util.spec_from_file_location("runtime_adoption", BASE_PATH)
assert spec and spec.loader
base = importlib.util.module_from_spec(spec)
spec.loader.exec_module(base)

CRITICAL = {"flags2env", "shared-auth-lib-core"}
CARGO_CONFIG_PATHS = (".cargo/config.toml", ".cargo/config")
DEPENDENCY_TABLES = ("dependencies", "build-dependencies", "dev-dependencies")
FORBIDDEN_GIT_SELECTORS = ("branch", "tag", "path")


def involved_critical(name: str, value: Any) -> str | None:
    if name in CRITICAL:
        return name
    if isinstance(value, dict) and value.get("package") in CRITICAL:
        return str(value["package"])
    return None


def allowed_location(repo_name: str, table: str, name: str, package: str, authority: dict[str, Any]) -> bool:
    if name != package:
        return False
    if table == "dependencies":
        return True
    if table == "build-dependencies" and package == "flags2env":
        return repo_name in set(authority["runtime_adoption"].get("flags2env_build_dependency_repositories", []))
    return False


def secure_git_url(value: Any) -> bool:
    if not isinstance(value, str):
        return False
    parsed = urllib.parse.urlparse(value)
    return (
        parsed.scheme == "https"
        and bool(parsed.hostname)
        and parsed.username is None
        and parsed.password is None
        and not parsed.query
        and not parsed.fragment
    )


def scan_dependency_table(
    repo: str,
    repo_name: str,
    table_name: str,
    table: Any,
    authority: dict[str, Any],
    *,
    target_scope: str | None = None,
) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    if not isinstance(table, dict):
        return findings
    location = f"target.{target_scope}.{table_name}" if target_scope is not None else table_name
    for name, value in table.items():
        if isinstance(value, dict) and "git" in value:
            git_url = value.get("git")
            rev = value.get("rev")
            if not secure_git_url(git_url):
                findings.append(
                    base.finding(
                        repo,
                        "cargo_override:git_dependency_url",
                        {"location": location, "name": name, "git": git_url},
                        "credential-free HTTPS Git URL",
                    )
                )
            if not base.is_sha(rev):
                findings.append(
                    base.finding(
                        repo,
                        "cargo_override:git_dependency_rev",
                        {"location": location, "name": name, "rev": rev},
                        "lowercase 40-character immutable Git revision",
                    )
                )
            for selector in FORBIDDEN_GIT_SELECTORS:
                if selector in value:
                    findings.append(
                        base.finding(
                            repo,
                            f"cargo_override:git_dependency_selector:{selector}",
                            {"location": location, "name": name, selector: value.get(selector)},
                            "absent",
                        )
                    )

        package = involved_critical(name, value)
        if package is None:
            continue
        if target_scope is not None or not allowed_location(repo_name, table_name, name, package, authority):
            findings.append(
                base.finding(
                    repo,
                    "cargo_override:critical_redeclaration",
                    {"location": location, "name": name, "package": package},
                    "critical packages declared only in reviewed canonical dependency slots",
                )
            )
    return findings


def audit_documents(
    repo_name: str,
    cargo_text: str | None,
    config_toml_text: str | None,
    config_legacy_text: str | None,
    authority: dict[str, Any],
) -> dict[str, Any]:
    repo = f"{authority['runtime_adoption']['owner']}/{repo_name}"
    findings: list[dict[str, Any]] = []
    evidence: dict[str, Any] = {"runtime_consumer": repo_name in set(authority["runtime"]["consumer_repositories"])}
    if not evidence["runtime_consumer"]:
        return {"repository": repo, "state": "passed", "findings": [], "evidence": evidence}

    if cargo_text is None:
        findings.append(base.finding(repo, "cargo_override:cargo_required", "missing", "Cargo.toml"))
    else:
        cargo, parse_findings = base.parse_toml(repo, "Cargo.toml", cargo_text)
        findings.extend(parse_findings)
        if cargo is not None:
            if cargo.get("patch"):
                findings.append(base.finding(repo, "cargo_override:patch", "present", "absent"))
            if cargo.get("replace"):
                findings.append(base.finding(repo, "cargo_override:replace", "present", "absent"))
            for table_name in DEPENDENCY_TABLES:
                findings.extend(scan_dependency_table(repo, repo_name, table_name, cargo.get(table_name), authority))
            targets = cargo.get("target")
            if isinstance(targets, dict):
                for target_scope, target_table in targets.items():
                    if not isinstance(target_table, dict):
                        continue
                    for table_name in DEPENDENCY_TABLES:
                        findings.extend(
                            scan_dependency_table(
                                repo,
                                repo_name,
                                table_name,
                                target_table.get(table_name),
                                authority,
                                target_scope=str(target_scope),
                            )
                        )

    if config_toml_text is not None and config_legacy_text is not None:
        findings.append(base.finding(repo, "cargo_override:config_collision", list(CARGO_CONFIG_PATHS), "at most one Cargo config"))

    for path, text in ((CARGO_CONFIG_PATHS[0], config_toml_text), (CARGO_CONFIG_PATHS[1], config_legacy_text)):
        if text is None:
            continue
        config, parse_findings = base.parse_toml(repo, path, text)
        findings.extend(parse_findings)
        if config is None:
            continue
        paths = config.get("paths")
        if paths:
            findings.append(base.finding(repo, f"cargo_override:{path}:paths", paths, "absent or empty"))
        sources = config.get("source")
        if sources:
            findings.append(base.finding(repo, f"cargo_override:{path}:source", "present", "absent"))

    hard = [item for item in findings if item["state"] == "failed"]
    blocked = [item for item in findings if item["state"] == "blocked"]
    return {
        "repository": repo,
        "state": "failed" if hard else "blocked" if blocked else "passed",
        "findings": findings,
        "evidence": evidence,
    }


def audit_repository(api: Any, owner: str, repo_name: str, authority: dict[str, Any]) -> dict[str, Any]:
    repo = f"{owner}/{repo_name}"
    status, metadata = api.request(f"/repos/{owner}/{repo_name}")
    if status != 200 or not isinstance(metadata, dict):
        return {"repository": repo, "state": "blocked", "findings": [base.finding(repo, "repository_metadata", status, 200, "blocked")], "evidence": {}}

    expected_full_name = f"{owner}/{repo_name}"
    if metadata.get("full_name") != expected_full_name:
        return {
            "repository": repo,
            "state": "failed",
            "findings": [base.finding(repo, "repository:identity", metadata.get("full_name"), expected_full_name)],
            "evidence": {},
        }
    if metadata.get("archived") is True or metadata.get("disabled") is True:
        return {
            "repository": repo,
            "state": "failed",
            "findings": [base.finding(repo, "repository:active", {"archived": metadata.get("archived"), "disabled": metadata.get("disabled")}, {"archived": False, "disabled": False})],
            "evidence": {},
        }

    branch = metadata.get("default_branch")
    if not isinstance(branch, str) or not branch:
        return {"repository": repo, "state": "blocked", "findings": [base.finding(repo, "repository:default_branch", branch, "non-empty branch", "blocked")], "evidence": {}}
    commit_status, commit_body = api.request(
        f"/repos/{owner}/{repo_name}/commits/{urllib.parse.quote(branch, safe='')}"
    )
    commit_sha = commit_body.get("sha") if isinstance(commit_body, dict) else None
    if commit_status != 200 or not base.is_sha(commit_sha):
        return {"repository": repo, "state": "blocked", "findings": [base.finding(repo, "repository:default_branch_sha", commit_sha or commit_status, "readable commit SHA", "blocked")], "evidence": {"default_branch": branch}}

    states: dict[str, str] = {}
    blobs: dict[str, str | None] = {}
    texts: dict[str, str | None] = {}
    for path in ("Cargo.toml", *CARGO_CONFIG_PATHS):
        state, text, blob = base.fetch_text(api, owner, repo_name, commit_sha, path)
        states[path] = state
        texts[path] = text if state == "present" else None
        blobs[path] = blob

    report = audit_documents(repo_name, texts["Cargo.toml"], texts[CARGO_CONFIG_PATHS[0]], texts[CARGO_CONFIG_PATHS[1]], authority)
    report["evidence"].update({"default_branch": branch, "default_branch_sha": commit_sha})
    for path in ("Cargo.toml", *CARGO_CONFIG_PATHS):
        report["evidence"][path] = states[path]
        report["evidence"][f"{path}:blob_sha"] = blobs[path]
    if any(state == "blocked" for state in states.values()):
        report["findings"].append(base.finding(repo, "cargo_override:read", "blocked", "readable immutable repository evidence", "blocked"))
    hard = any(item["state"] == "failed" for item in report["findings"])
    blocked = any(item["state"] == "blocked" for item in report["findings"])
    report["state"] = "failed" if hard else "blocked" if blocked else "passed"
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Audit Shared Auth Cargo source-override and Git-pin bypasses")
    parser.add_argument("--authority", default="config/shared-auth-config-authority.json")
    parser.add_argument("--output", default="artifacts/shared-auth-cargo-overrides-audit.json")
    parser.add_argument("--soft-fail", action="store_true")
    args = parser.parse_args(argv)

    try:
        authority = json.loads(Path(args.authority).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        print(f"cannot read runtime-adoption authority: {type(error).__name__}", file=sys.stderr)
        return 2
    errors = base.validate_authority(authority)
    if errors:
        for error in errors:
            print(f"invalid runtime-adoption authority: {error}", file=sys.stderr)
        return 2
    token = os.environ.get("GH_TOKEN", "").strip()
    if not token:
        print("GH_TOKEN is required for Cargo override audit", file=sys.stderr)
        return 2

    owner = authority["runtime_adoption"]["owner"]
    repos = sorted(authority["runtime"]["consumer_repositories"])
    api = base.GitHubAPI(token)
    reports = [audit_repository(api, owner, repo, authority) for repo in repos]
    failed = sum(report["state"] == "failed" for report in reports)
    blocked = sum(report["state"] == "blocked" for report in reports)
    state = "failed" if failed else "blocked" if blocked else "passed"
    payload = {
        "schema": "shared-auth/cargo-overrides-audit/v1",
        "authority_schema": authority["schema"],
        "owner": owner,
        "repository_count": len(reports),
        "failed_count": failed,
        "blocked_count": blocked,
        "state": state,
        "repositories": reports,
    }
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"audited {len(reports)} Cargo override surfaces; failed={failed} blocked={blocked} state={state}")
    if args.soft_fail:
        return 0
    return 1 if failed or blocked else 0


if __name__ == "__main__":
    raise SystemExit(main())
