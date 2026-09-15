#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path

SCRIPT = Path(__file__).with_name("audit-shared-auth-config-authority.py")
spec = importlib.util.spec_from_file_location("shared_auth_config_authority", SCRIPT)
assert spec and spec.loader
scanner = importlib.util.module_from_spec(spec)
spec.loader.exec_module(scanner)

STRICT_FLAGS_REV = "b708a041531a830bd49f030250836896096e7abd"
RUNTIME_CONSUMER = "shared-auth-web-server.rs"

AUTHORITY = {
    "schema": "shared-auth/config-authority/v1",
    "consumer_policy": {
        "canonical_path": ".shared-auth.toml",
        "compatibility_aliases": [".auth-shared.toml"],
        "fail_if_multiple_present": True,
        "allowed_top_level_sections": ["schema_version", "compatibility", "factors", "pages", "styling"],
        "required_top_level_sections": ["schema_version", "compatibility"],
        "legacy_alias_state": "warning",
    },
    "fleet_topology": {
        "canonical_path": "config/shared-auth-topology.toml",
        "allowed_repositories": ["shared-auth-server.rs"],
        "topology_only_sections": [
            "contract", "identity", "canonical_tables", "realms", "providers", "revocation", "root_admin", "applications"
        ],
    },
    "runtime": {
        "flags_path": ".cli-flags.toml",
        "strict_flags2env_revision": STRICT_FLAGS_REV,
        "consumer_repositories": [RUNTIME_CONSUMER],
        "realm_contract_path": "config/auth-realms.contract.json",
        "realm_contract_repositories": ["shared-auth-server.rs"],
    },
}

VALID_POLICY = '''schema_version = 1

[compatibility]
repository = "https://github.com/shared-auth/shared-auth-interfaces"
commit = "0123456789abcdef0123456789abcdef01234567"
'''

VALID_FLAGS = '''[parse]
allow_unknown = false
[env]
load = false
'''

VALID_CARGO = f'''[package]
name = "fixture"
version = "0.1.0"
[dependencies]
flags2env = {{ git = "https://github.com/flags-2-env/flags-2-env", rev = "{STRICT_FLAGS_REV}" }}
'''

VALID_TOPOLOGY = '''[contract]
name = "shared-auth"
schema_version = 1
secrets_allowed = false
'''


class FakeAPI:
    def __init__(self, repo_name: str, files: dict[str, str]) -> None:
        self.repo_name = repo_name
        self.files = files

    def request(self, path: str):
        if path == f"/repos/shared-auth/{self.repo_name}":
            return 200, {"default_branch": "main"}
        marker = "/contents/"
        if marker in path:
            file_path = path.split(marker, 1)[1].split("?", 1)[0]
            file_path = file_path.replace("%2F", "/")
            if file_path not in self.files:
                return 404, {"message": "Not Found"}
            import base64
            return 200, {
                "encoding": "base64",
                "content": base64.b64encode(self.files[file_path].encode()).decode(),
            }
        return 404, {"message": "Not Found"}


def audit(repo_name: str, files: dict[str, str]):
    return scanner.audit_repository(
        FakeAPI(repo_name, files),
        "shared-auth",
        {"name": repo_name, "classification": "test"},
        AUTHORITY,
        "main",
    )


class ConfigAuthorityTests(unittest.TestCase):
    def controls(self, report):
        return {item["control"] for item in report["findings"]}

    def test_no_files_is_structurally_valid_for_nonconsumer(self):
        self.assertEqual(audit("shared-auth-lib", {})["state"], "passed")

    def test_canonical_policy_is_valid(self):
        self.assertEqual(audit("shared-auth-lib", {".shared-auth.toml": VALID_POLICY})["state"], "passed")

    def test_legacy_alias_is_warning(self):
        report = audit("shared-auth-lib", {".auth-shared.toml": VALID_POLICY})
        self.assertEqual(report["state"], "warning")
        self.assertIn("consumer_policy:legacy_alias", self.controls(report))

    def test_policy_filename_collision_fails(self):
        report = audit("shared-auth-lib", {".shared-auth.toml": VALID_POLICY, ".auth-shared.toml": VALID_POLICY})
        self.assertEqual(report["state"], "failed")
        self.assertIn("consumer_policy:filename_collision", self.controls(report))

    def test_topology_section_in_policy_fails(self):
        report = audit("shared-auth-lib", {".shared-auth.toml": VALID_POLICY + "\n[identity]\nstable_id = 'x'\n"})
        self.assertIn(".shared-auth.toml:topology_leak", self.controls(report))

    def test_unknown_policy_section_fails(self):
        report = audit("shared-auth-lib", {".shared-auth.toml": VALID_POLICY + "\n[database]\nurl = 'x'\n"})
        self.assertIn(".shared-auth.toml:unknown_top_level", self.controls(report))

    def test_missing_policy_compatibility_fails(self):
        report = audit("shared-auth-lib", {".shared-auth.toml": "schema_version = 1\n"})
        self.assertIn(".shared-auth.toml:required_top_level", self.controls(report))

    def test_bad_policy_revision_shape_fails(self):
        policy = '''schema_version = 1
[compatibility]
repository = "https://github.com/shared-auth/shared-auth-interfaces"
'''
        report = audit("shared-auth-lib", {".shared-auth.toml": policy})
        self.assertIn(".shared-auth.toml:compatibility.revision", self.controls(report))

    def test_topology_allowed_on_central_server(self):
        report = audit("shared-auth-server.rs", {"config/shared-auth-topology.toml": VALID_TOPOLOGY})
        self.assertNotIn("config/shared-auth-topology.toml:owner", self.controls(report))

    def test_topology_forbidden_on_consumer_repo(self):
        report = audit("shared-auth-lib", {"config/shared-auth-topology.toml": VALID_TOPOLOGY})
        self.assertIn("config/shared-auth-topology.toml:owner", self.controls(report))

    def test_runtime_realm_contract_forbidden_on_consumer_repo(self):
        report = audit("shared-auth-lib", {"config/auth-realms.contract.json": "{}"})
        self.assertIn("config/auth-realms.contract.json:owner", self.controls(report))

    def test_runtime_realm_contract_allowed_on_server(self):
        report = audit("shared-auth-server.rs", {"config/auth-realms.contract.json": "{}"})
        self.assertNotIn("config/auth-realms.contract.json:owner", self.controls(report))

    def test_runtime_consumer_requires_canonical_policy(self):
        report = audit(RUNTIME_CONSUMER, {".cli-flags.toml": VALID_FLAGS, "Cargo.toml": VALID_CARGO})
        self.assertIn("consumer_policy:canonical_required", self.controls(report))

    def test_runtime_consumer_requires_flags_contract(self):
        report = audit(RUNTIME_CONSUMER, {".shared-auth.toml": VALID_POLICY, "Cargo.toml": VALID_CARGO})
        self.assertIn("runtime:flags_required", self.controls(report))

    def test_runtime_consumer_requires_strict_flags_revision(self):
        stale = VALID_CARGO.replace(STRICT_FLAGS_REV, "d7bad9ea7dfc657653368237e08903514cdca1ec")
        report = audit(
            RUNTIME_CONSUMER,
            {".shared-auth.toml": VALID_POLICY, ".cli-flags.toml": VALID_FLAGS, "Cargo.toml": stale},
        )
        self.assertIn("runtime:strict_flags2env_revision", self.controls(report))

    def test_runtime_consumer_baseline_passes(self):
        report = audit(
            RUNTIME_CONSUMER,
            {".shared-auth.toml": VALID_POLICY, ".cli-flags.toml": VALID_FLAGS, "Cargo.toml": VALID_CARGO},
        )
        self.assertEqual(report["state"], "passed")


if __name__ == "__main__":
    unittest.main()
