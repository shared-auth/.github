#!/usr/bin/env python3
from __future__ import annotations

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
    "runtime": {
        "policy_path": ".shared-auth.toml",
        "legacy_policy_path": ".auth-shared.toml",
        "strict_flags2env_revision": FLAGS_REV,
        "consumer_repositories": [CLI, RUNTIME],
    },
    "runtime_adoption": {
        "schema": "shared-auth/runtime-adoption/v1",
        "owner": "shared-auth",
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


def audit(policy=VALID_POLICY, cargo=VALID_CARGO, repo=RUNTIME, alias=False):
    return scanner.audit_documents(repo, policy, cargo, AUTHORITY, alias_present=alias)


def controls(report):
    return {item["control"] for item in report["findings"]}


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
        self.assertIn("runtime_policy:exact_revision_required", controls(audit(policy=policy)))

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


if __name__ == "__main__":
    unittest.main()
