#!/usr/bin/env python3
from __future__ import annotations

import base64
import importlib.util
import unittest
from pathlib import Path

SCRIPT = Path(__file__).with_name("audit-shared-auth-runtime-adoption.py")
spec = importlib.util.spec_from_file_location("runtime_adoption", SCRIPT)
assert spec and spec.loader
scanner = importlib.util.module_from_spec(spec)
spec.loader.exec_module(scanner)

FLAGS_REV = "b708a041531a830bd49f030250836896096e7abd"
POLICY_REV = "f62d9dbed2db6774dda04586328e6c485423fff6"
LIB_REV = "29cdb6e53e888c3f157f1371e6169fe8c3561be2"
RUNTIME = "shared-auth-web-server.rs"
CLI = "shared-auth-cli"

AUTHORITY = {
    "schema": "shared-auth/config-authority/v1",
    "consumer_policy": {
        "allowed_top_level_sections": ["schema_version", "compatibility", "factors", "pages", "styling"],
        "required_top_level_sections": ["schema_version", "compatibility"],
    },
    "runtime": {
        "policy_path": ".shared-auth.toml",
        "legacy_policy_path": ".auth-shared.toml",
        "strict_flags2env_revision": FLAGS_REV,
        "consumer_repositories": [CLI, RUNTIME],
    },
    "runtime_adoption": {
        "schema": "shared-auth/runtime-adoption/v1",
        "owner": "shared-auth",
        "policy_schema_version": 1,
        "compatibility_allowed_keys": ["repository", "commit"],
        "interfaces_repository": "https://github.com/shared-auth/shared-auth-interfaces",
        "interfaces_revision": POLICY_REV,
        "flags2env_repository": "https://github.com/flags-2-env/flags-2-env",
        "shared_auth_lib_core_repository": "https://github.com/shared-auth/shared-auth-lib-core.git",
        "shared_auth_lib_core_revision": LIB_REV,
        "flags2env_build_dependency_repositories": [CLI],
    },
}

VALID_POLICY = f'''schema_version = 1
[compatibility]
repository = "https://github.com/shared-auth/shared-auth-interfaces"
commit = "{POLICY_REV}"
'''

VALID_CARGO = f'''[package]
name = "fixture"
version = "0.1.0"
[dependencies]
flags2env = {{ git = "https://github.com/flags-2-env/flags-2-env", rev = "{FLAGS_REV}" }}
shared-auth-lib-core = {{ git = "https://github.com/shared-auth/shared-auth-lib-core.git", rev = "{LIB_REV}" }}
'''

CLI_CARGO = VALID_CARGO + f'''\n[build-dependencies]\nflags2env = {{ git = "https://github.com/flags-2-env/flags-2-env", rev = "{FLAGS_REV}" }}\n'''


def clone_authority():
    import copy

    return copy.deepcopy(AUTHORITY)


def audit(policy=VALID_POLICY, cargo=VALID_CARGO, repo=RUNTIME, alias=False, authority=None):
    return scanner.audit_documents(repo, policy, cargo, authority or AUTHORITY, alias_present=alias)


def controls(report):
    return {item["control"] for item in report["findings"]}


class FakeAPI:
    def __init__(self, *, archived=False, disabled=False, commit_status=200):
        self.paths: list[str] = []
        self.commit_sha = "e" * 40
        self.archived = archived
        self.disabled = disabled
        self.commit_status = commit_status

    @staticmethod
    def encoded(text: str, blob: str):
        return {
            "encoding": "base64",
            "content": base64.b64encode(text.encode()).decode(),
            "sha": blob,
        }

    def request(self, path: str):
        self.paths.append(path)
        prefix = f"/repos/shared-auth/{RUNTIME}"
        if path == prefix:
            return 200, {"default_branch": "main", "archived": self.archived, "disabled": self.disabled}
        if path == f"{prefix}/commits/main":
            if self.commit_status != 200:
                return self.commit_status, None
            return 200, {"sha": self.commit_sha}
        ref = f"?ref={self.commit_sha}"
        if path == f"{prefix}/contents/.shared-auth.toml{ref}":
            return 200, self.encoded(VALID_POLICY, "a" * 40)
        if path == f"{prefix}/contents/.auth-shared.toml{ref}":
            return 404, {"message": "Not Found"}
        if path == f"{prefix}/contents/Cargo.toml{ref}":
            return 200, self.encoded(VALID_CARGO, "b" * 40)
        return 500, {"message": "unexpected fake request"}


class RuntimeAdoptionTests(unittest.TestCase):
    def test_01_valid_server_passes(self):
        self.assertEqual(audit()["state"], "passed")

    def test_02_valid_cli_requires_build_flags2env_and_passes(self):
        self.assertEqual(audit(cargo=CLI_CARGO, repo=CLI)["state"], "passed")

    def test_03_non_runtime_repo_is_ignored(self):
        report = scanner.audit_documents("shared-auth-docs", None, None, AUTHORITY)
        self.assertEqual(report["state"], "passed")

    def test_04_missing_canonical_policy_fails(self):
        self.assertIn("runtime_policy:canonical_required", controls(audit(policy=None)))

    def test_05_alias_collision_fails(self):
        self.assertIn("runtime_policy:filename_collision", controls(audit(alias=True)))

    def test_06_stale_policy_revision_fails(self):
        stale = VALID_POLICY.replace(POLICY_REV, "a" * 40)
        self.assertIn("runtime_policy:interfaces_revision", controls(audit(policy=stale)))

    def test_07_policy_range_is_not_accepted_for_runtime(self):
        policy = f'''schema_version = 1\n[compatibility]\nrepository = "https://github.com/shared-auth/shared-auth-interfaces"\nrange = {{ base = "{'a'*40}", head = "{'b'*40}" }}\n'''
        found = controls(audit(policy=policy))
        self.assertIn("runtime_policy:exact_revision_required", found)
        self.assertIn("runtime_policy:compatibility_unknown_keys", found)

    def test_08_wrong_interfaces_repository_fails(self):
        wrong = VALID_POLICY.replace("shared-auth/shared-auth-interfaces", "example/other")
        self.assertIn("runtime_policy:interfaces_repository", controls(audit(policy=wrong)))

    def test_09_malformed_policy_revision_shape_fails(self):
        bad = VALID_POLICY.replace(POLICY_REV, "not-a-sha")
        self.assertIn("runtime_policy:revision_shape", controls(audit(policy=bad)))

    def test_10_comment_spoof_does_not_satisfy_flags2env(self):
        cargo = VALID_CARGO.replace(
            f'flags2env = {{ git = "https://github.com/flags-2-env/flags-2-env", rev = "{FLAGS_REV}" }}',
            f'# flags2env rev = "{FLAGS_REV}"',
        )
        self.assertIn("runtime_cargo:flags2env:required", controls(audit(cargo=cargo)))

    def test_11_wrong_flags2env_revision_fails(self):
        stale = VALID_CARGO.replace(FLAGS_REV, "c" * 40, 1)
        self.assertIn("runtime_cargo:flags2env:rev", controls(audit(cargo=stale)))

    def test_12_wrong_flags2env_source_fails(self):
        wrong = VALID_CARGO.replace("https://github.com/flags-2-env/flags-2-env", "https://github.com/example/flags")
        self.assertIn("runtime_cargo:flags2env:git", controls(audit(cargo=wrong)))

    def test_13_wrong_lib_core_revision_fails(self):
        stale = VALID_CARGO.replace(LIB_REV, "d" * 40)
        self.assertIn("runtime_cargo:shared_auth_lib_core:rev", controls(audit(cargo=stale)))

    def test_14_cli_requires_build_time_flags2env_pin(self):
        self.assertIn("runtime_cargo:build_flags2env:required", controls(audit(cargo=VALID_CARGO, repo=CLI)))

    def test_15_malformed_cargo_is_a_failure_not_a_string_match(self):
        cargo = f'''[dependencies\n# {FLAGS_REV}\n# {LIB_REV}\n'''
        report = audit(cargo=cargo)
        self.assertIn("Cargo.toml:toml", controls(report))
        self.assertEqual(report["state"], "failed")

    def test_16_policy_schema_version_is_exact(self):
        policy = VALID_POLICY.replace("schema_version = 1", "schema_version = 2")
        self.assertIn("runtime_policy:schema_version", controls(audit(policy=policy)))

    def test_17_unknown_policy_top_level_is_rejected(self):
        policy = VALID_POLICY + "\n[unexpected]\nenabled = true\n"
        self.assertIn("runtime_policy:unknown_top_level", controls(audit(policy=policy)))

    def test_18_optional_critical_dependency_is_rejected(self):
        cargo = VALID_CARGO.replace(
            f'rev = "{FLAGS_REV}" }}', f'rev = "{FLAGS_REV}", optional = true }}', 1
        )
        self.assertIn("runtime_cargo:flags2env:optional", controls(audit(cargo=cargo)))

    def test_19_extra_git_selector_is_rejected(self):
        cargo = VALID_CARGO.replace(
            f'rev = "{LIB_REV}" }}', f'rev = "{LIB_REV}", branch = "main" }}'
        )
        self.assertIn("runtime_cargo:shared_auth_lib_core:selector:branch", controls(audit(cargo=cargo)))

    def test_20_wrong_package_alias_is_rejected(self):
        cargo = VALID_CARGO.replace(
            f'rev = "{LIB_REV}" }}', f'rev = "{LIB_REV}", package = "other-core" }}'
        )
        self.assertIn("runtime_cargo:shared_auth_lib_core:package", controls(audit(cargo=cargo)))

    def test_21_authority_rejects_duplicate_runtime_consumers(self):
        authority = clone_authority()
        authority["runtime"]["consumer_repositories"].append(RUNTIME)
        errors = scanner.validate_authority(authority)
        self.assertTrue(any("duplicates" in error for error in errors))

    def test_22_authority_rejects_non_sha_revision(self):
        authority = clone_authority()
        authority["runtime_adoption"]["interfaces_revision"] = "main"
        errors = scanner.validate_authority(authority)
        self.assertTrue(any("interfaces_revision" in error for error in errors))

    def test_23_authority_rejects_build_dependency_repo_outside_consumers(self):
        authority = clone_authority()
        authority["runtime_adoption"]["flags2env_build_dependency_repositories"] = ["not-a-consumer"]
        errors = scanner.validate_authority(authority)
        self.assertTrue(any("subset" in error for error in errors))

    def test_24_repository_audit_pins_every_file_read_to_one_commit(self):
        api = FakeAPI()
        report = scanner.audit_repository(api, "shared-auth", RUNTIME, AUTHORITY)
        self.assertEqual(report["state"], "passed")
        self.assertEqual(report["evidence"]["default_branch_sha"], api.commit_sha)
        self.assertEqual(report["evidence"][".shared-auth.toml:blob_sha"], "a" * 40)
        self.assertEqual(report["evidence"]["Cargo.toml:blob_sha"], "b" * 40)
        content_paths = [path for path in api.paths if "/contents/" in path]
        self.assertEqual(len(content_paths), 3)
        self.assertTrue(all(path.endswith(f"?ref={api.commit_sha}") for path in content_paths))

    def test_25_archived_repository_is_failed_even_when_evidence_is_readable(self):
        report = scanner.audit_repository(FakeAPI(archived=True), "shared-auth", RUNTIME, AUTHORITY)
        self.assertEqual(report["state"], "failed")
        self.assertIn("repository:archived", controls(report))

    def test_26_unreadable_branch_sha_is_blocked(self):
        report = scanner.audit_repository(FakeAPI(commit_status=503), "shared-auth", RUNTIME, AUTHORITY)
        self.assertEqual(report["state"], "blocked")
        self.assertIn("repository:default_branch_sha", controls(report))


if __name__ == "__main__":
    unittest.main()
