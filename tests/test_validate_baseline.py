#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
import os
import tempfile
import unittest
from pathlib import Path

MODULE_PATH = Path(__file__).resolve().parents[1] / "scripts" / "validate_baseline.py"
SPEC = importlib.util.spec_from_file_location("validate_baseline", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
VALIDATOR = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(VALIDATOR)

CHECKOUT_SHA = "de0fac2e4500dabe0009e67214ff5f5447ce83dd"


def write(root: Path, relative: str, content: str = "placeholder\n") -> Path:
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return path


def workflow() -> str:
    return f"""name: policy\non:\n  workflow_dispatch:\npermissions:\n  contents: read\njobs:\n  validate:\n    runs-on: ubuntu-latest\n    timeout-minutes: 10\n    steps:\n      - uses: actions/checkout@{CHECKOUT_SHA}\n        with:\n          persist-credentials: false\n      - run: python3 scripts/validate_baseline.py .\n"""


def valid_context() -> dict:
    return {
        "github": {"login": "example-org"},
        "linear": {
            "project_id": "00000000-0000-4000-8000-000000000000",
            "project_url": "https://linear.app/example/project/example",
        },
        "git_conflict_resolution": {
            "directive_verbatim": VALIDATOR.MANDATORY_DIRECTIVE,
            "history_lookback_commits": {
                "minimum": 3,
                "maximum": 10,
                "when_available": True,
                "inspect_both_sides": True,
                "inspect_merge_base": True,
                "path_scoped_history": True,
            },
            "context_scope": [
                "conflicted_repository",
                "same_github_organization_repositories",
                "relevant_external_github_organization_repositories",
                "linear_project_context",
            ],
            "forbidden_shortcuts": ["wholesale_ours", "wholesale_theirs"],
        },
    }


def valid_policy() -> dict:
    return {
        "work_tracking": {
            "require_issue_before_implementation": True,
            "on_unmapped_or_ambiguous": "stop_and_report",
        },
        "safe_change_policy": {
            "integration_strategy": "merge",
            "force_push": "forbidden",
        },
    }


class BaselineValidatorTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory(prefix="org-baseline-")
        self.root = Path(self.temp.name)
        for relative in VALIDATOR.REQUIRED_FILES:
            write(self.root, relative)

        agents = "\n".join(
            [
                VALIDATOR.MANDATORY_DIRECTIVE,
                "avoid git rebase in favor of git merge",
                "git stash",
                "git reset",
                "git clean",
                "git filter-repo",
                "review 3–10 relevant commits",
                "Never report completion without evidence",
                "",
            ]
        )
        write(self.root, "agents.md", agents)
        write(self.root, "AGENTS.md", VALIDATOR.MANDATORY_DIRECTIVE + "\n")
        for relative in VALIDATOR.POINTER_FILES:
            write(self.root, relative, "Read canonical agents.md before changing files.\n")
        write(
            self.root,
            ".github/copilot-instructions.md",
            "Read AGENTS.md. Review 3–10 commits and relevant external organizations.\n",
        )
        write(self.root, "project-context.yaml", json.dumps(valid_context(), indent=2) + "\n")
        write(self.root, "organization-policy.json", json.dumps(valid_policy(), indent=2) + "\n")
        write(self.root, ".github/workflows/agent-policy.yml", workflow())
        write(self.root, ".github/workflows/baseline-policy.yml", workflow())
        write(self.root, ".github/workflows/reusable-policy.yml", workflow())
        write(self.root, "workflow-templates/organization-policy.yml", workflow())
        write(self.root, "workflow-templates/organization-policy.properties.json", "{}\n")

    def tearDown(self) -> None:
        self.temp.cleanup()

    def assert_error(self, needle: str) -> None:
        errors = VALIDATOR.validate(self.root)
        self.assertTrue(any(needle in error for error in errors), errors)

    def test_valid_fixture_passes(self) -> None:
        self.assertEqual([], VALIDATOR.validate(self.root))

    def test_missing_required_file_fails(self) -> None:
        (self.root / "GOVERNANCE.md").unlink()
        self.assert_error("missing required file: GOVERNANCE.md")

    def test_directive_must_be_verbatim(self) -> None:
        write(self.root, "agents.md", "semantic conflict resolution\n")
        self.assert_error("mandatory directive verbatim")

    def test_history_window_is_exact(self) -> None:
        context = valid_context()
        context["git_conflict_resolution"]["history_lookback_commits"]["maximum"] = 9
        write(self.root, "project-context.yaml", json.dumps(context) + "\n")
        self.assert_error("3–10 commit history window")

    def test_external_org_scope_is_required(self) -> None:
        context = valid_context()
        context["git_conflict_resolution"]["context_scope"].remove(
            "relevant_external_github_organization_repositories"
        )
        write(self.root, "project-context.yaml", json.dumps(context) + "\n")
        self.assert_error("external-org")

    def test_wholesale_side_selection_is_forbidden(self) -> None:
        context = valid_context()
        context["git_conflict_resolution"]["forbidden_shortcuts"] = []
        write(self.root, "project-context.yaml", json.dumps(context) + "\n")
        self.assert_error("wholesale ours/theirs")

    def test_conflict_marker_fails(self) -> None:
        write(self.root, "synthetic-conflict.txt", "<" * 7 + " branch\n")
        self.assert_error("unresolved conflict marker")

    def test_github_token_fails(self) -> None:
        write(self.root, "synthetic-secret.txt", "gh" + "p_" + "A" * 36 + "\n")
        self.assert_error("GitHub token")

    def test_slack_token_fails(self) -> None:
        write(self.root, "synthetic-secret.txt", "xox" + "b-" + "A" * 24 + "\n")
        self.assert_error("Slack token")

    def test_aws_key_fails(self) -> None:
        write(self.root, "synthetic-secret.txt", "AK" + "IA" + "A" * 16 + "\n")
        self.assert_error("AWS access key")

    def test_unpinned_action_fails(self) -> None:
        write(
            self.root,
            ".github/workflows/unpinned.yml",
            "name: bad\non:\n  workflow_dispatch:\npermissions:\n  contents: read\njobs:\n  bad:\n    runs-on: ubuntu-latest\n    timeout-minutes: 5\n    steps:\n      - uses: actions/setup-python@v5\n",
        )
        self.assert_error("not pinned to a full SHA")

    def test_symlink_substitution_fails(self) -> None:
        target = self.root / "real-policy.md"
        target.write_text("safe\n", encoding="utf-8")
        policy = self.root / "GOVERNANCE.md"
        policy.unlink()
        try:
            os.symlink(target.name, policy)
        except (OSError, NotImplementedError):
            self.skipTest("symlinks unavailable")
        self.assert_error("required policy path must not be a symlink")

    def test_invalid_machine_policy_fails_closed(self) -> None:
        policy = valid_policy()
        policy["work_tracking"]["on_unmapped_or_ambiguous"] = "guess"
        write(self.root, "organization-policy.json", json.dumps(policy) + "\n")
        self.assert_error("fail closed")


if __name__ == "__main__":
    unittest.main()
