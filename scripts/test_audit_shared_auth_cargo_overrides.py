#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path

SCRIPT = Path(__file__).with_name("audit-shared-auth-cargo-overrides.py")
spec = importlib.util.spec_from_file_location("cargo_overrides", SCRIPT)
assert spec and spec.loader
scanner = importlib.util.module_from_spec(spec)
spec.loader.exec_module(scanner)

FLAGS_REV = "b708a041531a830bd49f030250836896096e7abd"
LIB_REV = "29cdb6e53e888c3f157f1371e6169fe8c3561be2"
OTHER_REV = "e48a8f006ab4a1221217d61e1a983ccc99e0da8e"
RUNTIME = "shared-auth-web-server.rs"
CLI = "shared-auth-cli"
AUTHORITY = {
    "schema": "shared-auth/config-authority/v1",
    "consumer_policy": {"allowed_top_level_sections": ["schema_version", "compatibility"], "required_top_level_sections": ["schema_version", "compatibility"]},
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
        "interfaces_revision": "f62d9dbed2db6774dda04586328e6c485423fff6",
        "flags2env_repository": "https://github.com/flags-2-env/flags-2-env",
        "shared_auth_lib_core_repository": "https://github.com/shared-auth/shared-auth-lib-core.git",
        "shared_auth_lib_core_revision": LIB_REV,
        "flags2env_build_dependency_repositories": [CLI],
    },
}
VALID_CARGO = f'''[package]\nname = "fixture"\nversion = "0.1.0"\n[dependencies]\nflags2env = {{ git = "https://github.com/flags-2-env/flags-2-env", rev = "{FLAGS_REV}" }}\nshared-auth-lib-core = {{ git = "https://github.com/shared-auth/shared-auth-lib-core.git", rev = "{LIB_REV}" }}\nores-transport = {{ git = "https://github.com/ORESoftware/ores-transport.git", rev = "{OTHER_REV}" }}\n'''
CLI_CARGO = VALID_CARGO + f'''\n[build-dependencies]\nflags2env = {{ git = "https://github.com/flags-2-env/flags-2-env", rev = "{FLAGS_REV}" }}\n'''


def audit(cargo=VALID_CARGO, config_toml=None, config_legacy=None, repo=RUNTIME):
    return scanner.audit_documents(repo, cargo, config_toml, config_legacy, AUTHORITY)


def controls(report):
    return {item["control"] for item in report["findings"]}


class CargoOverrideTests(unittest.TestCase):
    def test_01_valid_runtime_has_no_override_findings(self):
        self.assertEqual(audit()["state"], "passed")

    def test_02_patch_table_is_rejected(self):
        cargo = VALID_CARGO + '\n[patch."https://github.com/flags-2-env/flags-2-env"]\nflags2env = { path = "vendor/flags" }\n'
        self.assertIn("cargo_override:patch", controls(audit(cargo=cargo)))

    def test_03_replace_table_is_rejected(self):
        cargo = VALID_CARGO + '\n[replace]\n"flags2env:0.1.0" = { path = "vendor/flags" }\n'
        self.assertIn("cargo_override:replace", controls(audit(cargo=cargo)))

    def test_04_repo_local_paths_override_is_rejected(self):
        self.assertIn("cargo_override:.cargo/config.toml:paths", controls(audit(config_toml='paths = ["vendor/flags"]\n')))

    def test_05_repo_local_source_replacement_is_rejected(self):
        config = '[source.reviewed]\ngit = "https://github.com/flags-2-env/flags-2-env"\n[source.reviewed-mirror]\nreplace-with = "reviewed"\n'
        self.assertIn("cargo_override:.cargo/config.toml:source", controls(audit(config_toml=config)))

    def test_06_dual_cargo_config_names_are_rejected(self):
        self.assertIn("cargo_override:config_collision", controls(audit(config_toml="[net]\noffline=true\n", config_legacy="[net]\noffline=true\n")))

    def test_07_target_specific_critical_redeclaration_is_rejected(self):
        cargo = VALID_CARGO + f'''\n[target.'cfg(unix)'.dependencies]\nflags2env = {{ git = "https://github.com/flags-2-env/flags-2-env", rev = "{FLAGS_REV}" }}\n'''
        self.assertIn("cargo_override:critical_redeclaration", controls(audit(cargo=cargo)))

    def test_08_dev_dependency_shadow_is_rejected(self):
        cargo = VALID_CARGO + f'''\n[dev-dependencies]\nshared-auth-lib-core = {{ git = "https://github.com/shared-auth/shared-auth-lib-core.git", rev = "{LIB_REV}" }}\n'''
        self.assertIn("cargo_override:critical_redeclaration", controls(audit(cargo=cargo)))

    def test_09_alias_of_critical_package_is_rejected(self):
        cargo = VALID_CARGO + f'''\n[dev-dependencies]\nshadow = {{ package = "flags2env", git = "https://github.com/example/other", rev = "{'a'*40}" }}\n'''
        self.assertIn("cargo_override:critical_redeclaration", controls(audit(cargo=cargo)))

    def test_10_cli_reviewed_build_flags2env_slot_is_allowed(self):
        self.assertEqual(audit(cargo=CLI_CARGO, repo=CLI)["state"], "passed")

    def test_11_lib_core_build_redeclaration_is_not_allowed(self):
        cargo = VALID_CARGO + f'''\n[build-dependencies]\nshared-auth-lib-core = {{ git = "https://github.com/shared-auth/shared-auth-lib-core.git", rev = "{LIB_REV}" }}\n'''
        self.assertIn("cargo_override:critical_redeclaration", controls(audit(cargo=cargo)))

    def test_12_non_runtime_repo_is_ignored(self):
        report = scanner.audit_documents("shared-auth-docs", None, None, None, AUTHORITY)
        self.assertEqual(report["state"], "passed")

    def test_13_any_git_dependency_requires_rev(self):
        cargo = VALID_CARGO.replace(f'rev = "{OTHER_REV}"', 'branch = "main"')
        found = controls(audit(cargo=cargo))
        self.assertIn("cargo_override:git_dependency_rev", found)
        self.assertIn("cargo_override:git_dependency_selector:branch", found)

    def test_14_git_tag_selector_is_rejected_even_with_rev(self):
        cargo = VALID_CARGO.replace(f'rev = "{OTHER_REV}"', f'rev = "{OTHER_REV}", tag = "v1"')
        self.assertIn("cargo_override:git_dependency_selector:tag", controls(audit(cargo=cargo)))

    def test_15_git_path_selector_is_rejected(self):
        cargo = VALID_CARGO.replace(f'rev = "{OTHER_REV}"', f'rev = "{OTHER_REV}", path = "crate"')
        self.assertIn("cargo_override:git_dependency_selector:path", controls(audit(cargo=cargo)))

    def test_16_git_url_must_be_credential_free_https(self):
        cargo = VALID_CARGO.replace("https://github.com/ORESoftware/ores-transport.git", "http://token@example.invalid/ores-transport.git")
        self.assertIn("cargo_override:git_dependency_url", controls(audit(cargo=cargo)))

    def test_17_target_git_dependency_is_allowed_when_immutable(self):
        cargo = VALID_CARGO + f'''\n[target.'cfg(unix)'.dependencies]\nores-otel-web = {{ git = "https://github.com/ores-otel/ores.otel.log", rev = "{'a'*40}" }}\n'''
        self.assertNotIn("cargo_override:git_dependency_rev", controls(audit(cargo=cargo)))


if __name__ == "__main__":
    unittest.main()
