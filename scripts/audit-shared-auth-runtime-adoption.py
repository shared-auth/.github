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
import binascii
import json
import os
import re
import sys
import tomllib
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

API = "https://api.github.com"
REPO_COMPONENT = re.compile(r"^[A-Za-z0-9_.-]+$")
FORBIDDEN_GIT_SELECTORS = ("branch", "tag", "path")


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


def is_repo_component(value: Any) -> bool:
    return isinstance(value, str) and bool(REPO_COMPONENT.fullmatch(value))


def is_https_github_repository(value: Any) -> bool:
    if not isinstance(value, str):
        return False
    parsed = urllib.parse.urlparse(value)
    parts = [part for part in parsed.path.split("/") if part]
    return (
        parsed.scheme == "https"
        and parsed.netloc == "github.com"
        and not parsed.params
        and not parsed.query
        and not parsed.fragment
        and len(parts) == 2
        and all(is_repo_component(part.removesuffix(".git")) for part in parts)
    )


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
    expected_package: str,
) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    if dep is None:
        return [finding(repo, f"{control_prefix}:required", "missing", "git dependency")]
    if dep.get("git") != expected_git:
        results.append(finding(repo, f"{control_prefix}:git", dep.get("git"), expected_git))
    if dep.get("rev") != expected_rev:
        results.append(finding(repo, f"{control_prefix}:rev", dep.get("rev"), expected_rev))
    if dep.get("optional") is True:
        results.append(finding(repo, f"{control_prefix}:optional", True, False))
    package = dep.get("package")
    if package is not None and package != expected_package:
        results.append(finding(repo, f"{control_prefix}:package", package, expected_package))
    for selector in FORBIDDEN_GIT_SELECTORS:
        if selector in dep:
            results.append(finding(repo, f"{control_prefix}:selector:{selector}", dep.get(selector), "absent"))
    return results


def validate_authority(authority: Any) -> list[str]:
    errors: list[str] = []
    if not isinstance(authority, dict):
        return ["authority must be a JSON object"]
    if authority.get("schema") != "shared-auth/config-authority/v1":
        errors.append("authority.schema must be shared-auth/config-authority/v1")

    runtime = authority.get("runtime")
    adoption = authority.get("runtime_adoption")
    consumer_policy = authority.get("consumer_policy")
    if not isinstance(runtime, dict):
        errors.append("runtime must be an object")
        return errors
    if not isinstance(adoption, dict) or adoption.get("schema") != "shared-auth/runtime-adoption/v1":
        errors.append("runtime_adoption must use shared-auth/runtime-adoption/v1")
        return errors
    if not isinstance(consumer_policy, dict):
        errors.append("consumer_policy must be an object")

    owner = adoption.get("owner")
    if not is_repo_component(owner):
        errors.append("runtime_adoption.owner must be a safe GitHub owner component")

    consumers = runtime.get("consumer_repositories")
    if not isinstance(consumers, list) or not consumers:
        errors.append("runtime.consumer_repositories must be a non-empty array")
        consumers = []
    elif any(not is_repo_component(repo) for repo in consumers):
        errors.append("runtime.consumer_repositories entries must be safe GitHub repository names")
    if len(set(consumers)) != len(consumers):
        errors.append("runtime.consumer_repositories must not contain duplicates")

    build_consumers = adoption.get("flags2env_build_dependency_repositories", [])
    if not isinstance(build_consumers, list) or any(not is_repo_component(repo) for repo in build_consumers):
        errors.append("runtime_adoption.flags2env_build_dependency_repositories must be repository names")
        build_consumers = []
    if len(set(build_consumers)) != len(build_consumers):
        errors.append("runtime_adoption.flags2env_build_dependency_repositories must not contain duplicates")
    if not set(build_consumers).issubset(set(consumers)):
        errors.append("build-dependency repositories must be a subset of runtime consumers")

    if adoption.get("policy_schema_version") != 1:
        errors.append("runtime_adoption.policy_schema_version must be 1")
    compatibility_keys = adoption.get("compatibility_allowed_keys")
    if compatibility_keys != ["repository", "commit"]:
        errors.append("runtime_adoption.compatibility_allowed_keys must be [repository, commit]")

    for key, value in {
        "runtime.strict_flags2env_revision": runtime.get("strict_flags2env_revision"),
        "runtime_adoption.interfaces_revision": adoption.get("interfaces_revision"),
        "runtime_adoption.shared_auth_lib_core_revision": adoption.get("shared_auth_lib_core_revision"),
    }.items():
        if not is_sha(value):
            errors.append(f"{key} must be a lowercase 40-character Git SHA")

    for key in ("interfaces_repository", "flags2env_repository", "shared_auth_lib_core_repository"):
        if not is_https_github_repository(adoption.get(key)):
            errors.append(f"runtime_adoption.{key} must be an exact https://github.com/owner/repository URL")

    for key in ("policy_path", "legacy_policy_path"):
        value = runtime.get(key)
        if not isinstance(value, str) or not value or value.startswith("/") or ".." in Path(value).parts:
            errors.append(f"runtime.{key} must be a repository-relative path")
    if runtime.get("policy_path") == runtime.get("legacy_policy_path"):
        errors.append("runtime policy and legacy policy paths must differ")
    return errors


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
    consumer_policy = authority.get("consumer_policy", {})
    owner = adoption["owner"]
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
            expected_schema_version = adoption["policy_schema_version"]
            if policy.get("schema_version") != expected_schema_version:
                results.append(
                    finding(repo, "runtime_policy:schema_version", policy.get("schema_version"), expected_schema_version)
                )
            allowed_top = set(consumer_policy.get("allowed_top_level_sections", []))
            required_top = set(consumer_policy.get("required_top_level_sections", []))
            if allowed_top:
                unknown_top = sorted(set(policy) - allowed_top)
                if unknown_top:
                    results.append(finding(repo, "runtime_policy:unknown_top_level", unknown_top, sorted(allowed_top)))
            missing_top = sorted(required_top - set(policy))
            if missing_top:
                results.append(finding(repo, "runtime_policy:missing_top_level", missing_top, sorted(required_top)))

            compatibility = policy.get("compatibility")
            if not isinstance(compatibility, dict):
                results.append(finding(repo, "runtime_policy:compatibility", compatibility, "table"))
            else:
                expected_repo = adoption["interfaces_repository"]
                expected_rev = adoption["interfaces_revision"]
                evidence["policy_repository"] = compatibility.get("repository")
                evidence["policy_revision"] = compatibility.get("commit")
                allowed_compat = set(adoption["compatibility_allowed_keys"])
                unknown_compat = sorted(set(compatibility) - allowed_compat)
                if unknown_compat:
                    results.append(
                        finding(repo, "runtime_policy:compatibility_unknown_keys", unknown_compat, sorted(allowed_compat))
                    )
                if compatibility.get("repository") != expected_repo:
                    results.append(
                        finding(repo, "runtime_policy:interfaces_repository", compatibility.get("repository"), expected_repo)
                    )
                if "range" in compatibility:
                    results.append(finding(repo, "runtime_policy:exact_revision_required", "range", expected_rev))
                commit = compatibility.get("commit")
                if not is_sha(commit):
                    results.append(finding(repo, "runtime_policy:revision_shape", commit, "lowercase 40-char Git SHA"))
                elif commit != expected_rev:
                    results.append(finding(repo, "runtime_policy:interfaces_revision", commit, expected_rev))

    if alias_present:
        results.append(
            finding(
                repo,
                "runtime_policy:filename_collision",
                [runtime["policy_path"], runtime["legacy_policy_path"]],
                runtime["policy_path"],
            )
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
                    "flags2env",
                )
            )
            results.extend(
                check_git_dependency(
                    repo,
                    "runtime_cargo:shared_auth_lib_core",
                    lib_core,
                    adoption["shared_auth_lib_core_repository"],
                    adoption["shared_auth_lib_core_revision"],
                    "shared-auth-lib-core",
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
                        "flags2env",
                    )
                )
            evidence["flags2env_revision"] = flags.get("rev") if flags else None
            evidence["shared_auth_lib_core_revision"] = lib_core.get("rev") if lib_core else None

    hard = [item for item in results if item["state"] == "failed"]
    blocked = [item for item in results if item["state"] == "blocked"]
    return {
        "repository": repo,
        "state": "failed" if hard else "blocked" if blocked else "passed",
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
                "User-Agent": "shared-auth-runtime-adoption-audit/2",
            },
        )
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                payload = response.read()
                if not payload:
                    return response.status, None
                try:
                    return response.status, json.loads(payload)
                except json.JSONDecodeError:
                    return 0, {"message": "GitHub returned non-JSON success payload"}
        except urllib.error.HTTPError as error:
            payload = error.read()
            try:
                body = json.loads(payload) if payload else None
            except json.JSONDecodeError:
                body = {"message": payload.decode("utf-8", errors="replace")}
            return error.code, body
        except (urllib.error.URLError, TimeoutError, OSError) as error:
            return 0, {"message": f"GitHub request unavailable: {type(error).__name__}"}


def fetch_text(
    api: GitHubAPI,
    owner: str,
    repo: str,
    commit_sha: str,
    path: str,
) -> tuple[str, str | None, str | None]:
    encoded = urllib.parse.quote(path, safe="/")
    status, body = api.request(
        f"/repos/{owner}/{repo}/contents/{encoded}?ref={urllib.parse.quote(commit_sha, safe='')}"
    )
    if status == 404:
        return "missing", None, None
    if status != 200 or not isinstance(body, dict) or body.get("encoding") != "base64":
        return "blocked", None, None
    blob_sha = body.get("sha")
    if not is_sha(blob_sha):
        return "blocked", None, None
    try:
        return "present", base64.b64decode(body["content"]).decode("utf-8"), blob_sha
    except (KeyError, TypeError, ValueError, binascii.Error, UnicodeDecodeError):
        return "blocked", None, None


def audit_repository(api: GitHubAPI, owner: str, repo_name: str, authority: dict[str, Any]) -> dict[str, Any]:
    repo = f"{owner}/{repo_name}"
    status, metadata = api.request(f"/repos/{owner}/{repo_name}")
    if status != 200 or not isinstance(metadata, dict):
        return {
            "repository": repo,
            "state": "blocked",
            "findings": [finding(repo, "repository_metadata", status, 200, "blocked")],
            "evidence": {},
        }

    metadata_findings: list[dict[str, Any]] = []
    if metadata.get("archived") is True:
        metadata_findings.append(finding(repo, "repository:archived", True, False))
    if metadata.get("disabled") is True:
        metadata_findings.append(finding(repo, "repository:disabled", True, False))

    branch = metadata.get("default_branch")
    if not isinstance(branch, str) or not branch:
        return {
            "repository": repo,
            "state": "blocked",
            "findings": metadata_findings
            + [finding(repo, "repository:default_branch", branch, "non-empty branch name", "blocked")],
            "evidence": {},
        }

    commit_status, commit_body = api.request(
        f"/repos/{owner}/{repo_name}/commits/{urllib.parse.quote(branch, safe='')}"
    )
    commit_sha = commit_body.get("sha") if isinstance(commit_body, dict) else None
    if commit_status != 200 or not is_sha(commit_sha):
        return {
            "repository": repo,
            "state": "failed" if metadata_findings else "blocked",
            "findings": metadata_findings
            + [finding(repo, "repository:default_branch_sha", commit_sha or commit_status, "readable commit SHA", "blocked")],
            "evidence": {"default_branch": branch},
        }

    runtime = authority["runtime"]
    policy_state, policy_text, policy_blob = fetch_text(api, owner, repo_name, commit_sha, runtime["policy_path"])
    alias_state, _, alias_blob = fetch_text(api, owner, repo_name, commit_sha, runtime["legacy_policy_path"])
    cargo_state, cargo_text, cargo_blob = fetch_text(api, owner, repo_name, commit_sha, "Cargo.toml")
    report = audit_documents(
        repo_name,
        policy_text if policy_state == "present" else None,
        cargo_text if cargo_state == "present" else None,
        authority,
        alias_present=alias_state == "present",
    )
    report["findings"].extend(metadata_findings)
    report["evidence"].update(
        {
            "default_branch": branch,
            "default_branch_sha": commit_sha,
            runtime["policy_path"]: policy_state,
            f"{runtime['policy_path']}:blob_sha": policy_blob,
            runtime["legacy_policy_path"]: alias_state,
            f"{runtime['legacy_policy_path']}:blob_sha": alias_blob,
            "Cargo.toml": cargo_state,
            "Cargo.toml:blob_sha": cargo_blob,
        }
    )
    if "blocked" in {policy_state, alias_state, cargo_state}:
        report["findings"].append(
            finding(repo, "runtime_adoption:read", "blocked", "readable immutable repository evidence", "blocked")
        )

    hard = [item for item in report["findings"] if item["state"] == "failed"]
    blocked = [item for item in report["findings"] if item["state"] == "blocked"]
    report["state"] = "failed" if hard else "blocked" if blocked else "passed"
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Audit Shared Auth runtime-policy adoption")
    parser.add_argument("--authority", default="config/shared-auth-config-authority.json")
    parser.add_argument("--output", default="artifacts/shared-auth-runtime-adoption-audit.json")
    parser.add_argument("--soft-fail", action="store_true")
    args = parser.parse_args(argv)

    try:
        authority = json.loads(Path(args.authority).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        print(f"cannot read runtime-adoption authority: {type(error).__name__}", file=sys.stderr)
        return 2
    authority_errors = validate_authority(authority)
    if authority_errors:
        for error in authority_errors:
            print(f"invalid runtime-adoption authority: {error}", file=sys.stderr)
        return 2

    token = os.environ.get("GH_TOKEN", "").strip()
    if not token:
        print("GH_TOKEN is required for the runtime-adoption audit", file=sys.stderr)
        return 2

    adoption = authority["runtime_adoption"]
    owner = adoption["owner"]
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
