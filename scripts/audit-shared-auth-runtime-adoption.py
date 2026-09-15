#!/usr/bin/env python3
"""Audit executable Shared Auth consumers for actual runtime-policy adoption.

This is intentionally narrower than the config-authority scanner. It proves that
reviewed runtime consumers carry the canonical policy revision and structurally
pin the reviewed Rust dependencies. Policy semantics remain owned by
shared-auth-lib-core / shared-auth-interfaces.
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


def finding(repo: str, control: str, actual: Any, expected: Any, state: str = "failed") -> dict[str, Any]:
    return {
        "repository": repo,
        "control": control,
        "state": state,
        "actual": actual,
        "expected": expected,
    }


def is_sha(value: Any) -> bool:
    return isinstance(value, str) and len(value) == 40 and all(c in "0123456789abcdef" for c in value)


def parse_toml(repo: str, path: str, text: str) -> tuple[dict[str, Any] | None, list[dict[str, Any]]]:
    try:
        value = tomllib.loads(text)
    except tomllib.TOMLDecodeError as error:
        return None, [finding(repo, f"{path}:toml", str(error), "valid TOML")]
    return value, []


def dependency(table: dict[str, Any], name: str) -> dict[str, Any] | None:
    value = table.get(name)
    return value if isinstance(value, dict) else None


def check_git_dependency(
    repo: str,
    control_prefix: str,
    dep: dict[str, Any] | None,
    expected_git: str,
    expected_rev: str,
) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    if dep is None:
        return [finding(repo, f"{control_prefix}:required", "missing", "git dependency")]
    if dep.get("git") != expected_git:
        results.append(finding(repo, f"{control_prefix}:git", dep.get("git"), expected_git))
    if dep.get("rev") != expected_rev:
        results.append(finding(repo, f"{control_prefix}:rev", dep.get("rev"), expected_rev))
    return results


def audit_documents(
    repo_name: str,
    policy_text: str | None,
    cargo_text: str | None,
    authority: dict[str, Any],
    *,
    alias_present: bool = False,
) -> dict[str, Any]:
    runtime = authority["runtime"]
    adoption = authority["runtime_adoption"]
    owner = adoption.get("owner", "shared-auth")
    repo = f"{owner}/{repo_name}"
    results: list[dict[str, Any]] = []
    evidence: dict[str, Any] = {}

    if repo_name not in set(runtime.get("consumer_repositories", [])):
        return {"repository": repo, "state": "passed", "findings": [], "evidence": {"runtime_consumer": False}}
    evidence["runtime_consumer"] = True

    if policy_text is None:
        results.append(finding(repo, "runtime_policy:canonical_required", "missing", runtime["policy_path"]))
    else:
        policy, parse_results = parse_toml(repo, runtime["policy_path"], policy_text)
        results.extend(parse_results)
        if policy is not None:
            compatibility = policy.get("compatibility")
            if not isinstance(compatibility, dict):
                results.append(finding(repo, "runtime_policy:compatibility", compatibility, "table"))
            else:
                expected_repo = adoption["interfaces_repository"]
                expected_rev = adoption["interfaces_revision"]
                evidence["policy_repository"] = compatibility.get("repository")
                evidence["policy_revision"] = compatibility.get("commit")
                if compatibility.get("repository") != expected_repo:
                    results.append(
                        finding(repo, "runtime_policy:interfaces_repository", compatibility.get("repository"), expected_repo)
                    )
                if "range" in compatibility:
                    results.append(
                        finding(repo, "runtime_policy:exact_revision_required", "range", expected_rev)
                    )
                commit = compatibility.get("commit")
                if not is_sha(commit):
                    results.append(finding(repo, "runtime_policy:revision_shape", commit, "lowercase 40-char Git SHA"))
                elif commit != expected_rev:
                    results.append(finding(repo, "runtime_policy:interfaces_revision", commit, expected_rev))

    if alias_present:
        results.append(
            finding(repo, "runtime_policy:filename_collision", [runtime["policy_path"], runtime["legacy_policy_path"]], runtime["policy_path"])
        )

    if cargo_text is None:
        results.append(finding(repo, "runtime_cargo:required", "missing", "Cargo.toml"))
    else:
        cargo, parse_results = parse_toml(repo, "Cargo.toml", cargo_text)
        results.extend(parse_results)
        if cargo is not None:
            deps = cargo.get("dependencies") if isinstance(cargo.get("dependencies"), dict) else {}
            build_deps = cargo.get("build-dependencies") if isinstance(cargo.get("build-dependencies"), dict) else {}
            flags = dependency(deps, "flags2env")
            lib_core = dependency(deps, "shared-auth-lib-core")
            results.extend(
                check_git_dependency(
                    repo,
                    "runtime_cargo:flags2env",
                    flags,
                    adoption["flags2env_repository"],
                    runtime["strict_flags2env_revision"],
                )
            )
            results.extend(
                check_git_dependency(
                    repo,
                    "runtime_cargo:shared_auth_lib_core",
                    lib_core,
                    adoption["shared_auth_lib_core_repository"],
                    adoption["shared_auth_lib_core_revision"],
                )
            )
            if repo_name in set(adoption.get("flags2env_build_dependency_repositories", [])):
                results.extend(
                    check_git_dependency(
                        repo,
                        "runtime_cargo:build_flags2env",
                        dependency(build_deps, "flags2env"),
                        adoption["flags2env_repository"],
                        runtime["strict_flags2env_revision"],
                    )
                )
            evidence["flags2env_revision"] = flags.get("rev") if flags else None
            evidence["shared_auth_lib_core_revision"] = lib_core.get("rev") if lib_core else None

    hard = [item for item in results if item["state"] == "failed"]
    return {
        "repository": repo,
        "state": "failed" if hard else "passed",
        "findings": results,
        "evidence": evidence,
    }


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
                "User-Agent": "shared-auth-runtime-adoption-audit/1",
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


def fetch_text(api: GitHubAPI, owner: str, repo: str, branch: str, path: str) -> tuple[str, str | None]:
    encoded = urllib.parse.quote(path, safe="/")
    status, body = api.request(f"/repos/{owner}/{repo}/contents/{encoded}?ref={urllib.parse.quote(branch, safe='')}")
    if status == 404:
        return "missing", None
    if status != 200 or not isinstance(body, dict) or body.get("encoding") != "base64":
        return "blocked", None
    try:
        return "present", base64.b64decode(body["content"]).decode("utf-8")
    except (KeyError, ValueError, UnicodeDecodeError):
        return "blocked", None


def audit_repository(api: GitHubAPI, owner: str, repo_name: str, authority: dict[str, Any]) -> dict[str, Any]:
    status, metadata = api.request(f"/repos/{owner}/{repo_name}")
    if status != 200 or not isinstance(metadata, dict):
        return {
            "repository": f"{owner}/{repo_name}",
            "state": "blocked",
            "findings": [finding(f"{owner}/{repo_name}", "repository_metadata", status, 200, "blocked")],
            "evidence": {},
        }
    branch = str(metadata.get("default_branch") or "main")
    runtime = authority["runtime"]
    policy_state, policy_text = fetch_text(api, owner, repo_name, branch, runtime["policy_path"])
    alias_state, _ = fetch_text(api, owner, repo_name, branch, runtime["legacy_policy_path"])
    cargo_state, cargo_text = fetch_text(api, owner, repo_name, branch, "Cargo.toml")
    report = audit_documents(
        repo_name,
        policy_text if policy_state == "present" else None,
        cargo_text if cargo_state == "present" else None,
        authority,
        alias_present=alias_state == "present",
    )
    report["evidence"].update({
        "default_branch": branch,
        runtime["policy_path"]: policy_state,
        runtime["legacy_policy_path"]: alias_state,
        "Cargo.toml": cargo_state,
    })
    if "blocked" in {policy_state, alias_state, cargo_state}:
        report["state"] = "blocked"
        report["findings"].append(
            finding(report["repository"], "runtime_adoption:read", "blocked", "readable repository evidence", "blocked")
        )
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Audit Shared Auth runtime-policy adoption")
    parser.add_argument("--authority", default="config/shared-auth-config-authority.json")
    parser.add_argument("--output", default="artifacts/shared-auth-runtime-adoption-audit.json")
    parser.add_argument("--soft-fail", action="store_true")
    args = parser.parse_args(argv)

    token = os.environ.get("GH_TOKEN", "").strip()
    if not token:
        print("GH_TOKEN is required for the runtime-adoption audit", file=sys.stderr)
        return 2
    authority = json.loads(Path(args.authority).read_text(encoding="utf-8"))
    adoption = authority.get("runtime_adoption")
    if not isinstance(adoption, dict) or adoption.get("schema") != "shared-auth/runtime-adoption/v1":
        print("unsupported or missing runtime_adoption authority", file=sys.stderr)
        return 2

    owner = str(adoption.get("owner", "shared-auth"))
    repos = sorted(authority["runtime"]["consumer_repositories"])
    api = GitHubAPI(token)
    reports = [audit_repository(api, owner, repo, authority) for repo in repos]
    failed = [report for report in reports if report["state"] == "failed"]
    blocked = [report for report in reports if report["state"] == "blocked"]
    state = "failed" if failed else "blocked" if blocked else "passed"
    payload = {
        "schema": "shared-auth/runtime-adoption-audit/v1",
        "authority_schema": authority["schema"],
        "owner": owner,
        "repository_count": len(reports),
        "failed_count": len(failed),
        "blocked_count": len(blocked),
        "state": state,
        "repositories": reports,
    }
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"audited {len(reports)} runtime consumers; failed={len(failed)} blocked={len(blocked)} state={state}")
    for report in reports:
        for item in report["findings"]:
            print(f"{item['state'].upper()}: {item['repository']} {item['control']}")
    if args.soft_fail:
        return 0
    return 1 if failed or blocked else 0


if __name__ == "__main__":
    raise SystemExit(main())
