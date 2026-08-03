from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "policy_validator", ROOT / "scripts" / "validate_semantic_conflict_policy.py"
)
assert SPEC is not None and SPEC.loader is not None
validator = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(validator)


SEMANTIC_POLICY_TEXT = """Resolve every Git conflict semantically and with full context.
Inspect the merge base and at least 3 and up to 10 relevant commits from both sides
using git log, git show, and git blame. Review related repositories in this GitHub
organization and relevant repositories in external organizations. Never accept ours
or theirs wholesale; perform a conceptual merge. Run tests and validation checks,
scan conflict markers, and document intentional tradeoffs.
"""

CONTROL_POLICY_TEXT = SEMANTIC_POLICY_TEXT + """
avoid git rebase in favor of git merge. Never use git rebase, git stash, git reset,
git clean, git filter-repo, git checkout --, git restore, git branch -D,
git reflog expire, git gc --prune, git push --force, or git push -f. Never use rm,
mv, sed, find -delete, xargs rm, truncate, shred, or dd. Preserve uncommitted and
untracked work and stop on unexpected changes. Every feature, fix, enhancement, and
bug requires a Linear issue before implementation.
"""


class OrganizationPolicyValidatorTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self._write_fixture()

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def _write(self, relative: str, content: str) -> None:
        path = self.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")

    def _write_fixture(self) -> None:
        self._write("AGENTS.md", CONTROL_POLICY_TEXT)
        self._write(".github/copilot-instructions.md", CONTROL_POLICY_TEXT)
        self._write("CONTRIBUTING.md", CONTROL_POLICY_TEXT)
        pull_request_template = (
            "# Pull request\n\nLinear issue: DEN-1\n\n"
            + CONTROL_POLICY_TEXT
            + "\n- [ ] I inspected the merge base and both sides.\n"
            + "- [ ] I inspected 3–10 commits from both sides.\n"
            + "- [ ] I reviewed same-org and external repositories.\n"
            + "- [ ] I scanned the worktree for conflict markers.\n"
            + "- [ ] I ran affected tests and checks.\n"
            + "- [ ] I documented non-obvious tradeoffs.\n"
            + "- [ ] I linked the Linear issue.\n"
            + "- [ ] I preserved uncommitted work.\n"
            + "- [ ] I avoided prohibited destructive operations.\n"
            + "- [ ] I used merge rather than rebase.\n"
        )
        self._write(".github/pull_request_template.md", pull_request_template)
        self._write("profile/README.md", SEMANTIC_POLICY_TEXT)
        self._write("agents/org-context.agent.md", SEMANTIC_POLICY_TEXT)
        self._write("README.md", "organization context\n")
        self._write(".github/workflows/org-context-integrity.yml", "name: integrity\n")
        self._write(
            ".github/workflows/reusable-organization-policy.yml",
            """name: reusable\non:\n  workflow_call:\npermissions:\n  contents: read\n  pull-requests: read\njobs:\n  verify:\n    steps:\n      - uses: actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1\n        with:\n          persist-credentials: false\n      - run: echo 'avoid git rebase in favor of git merge and Linear'\n""",
        )
        self._write("SECURITY.md", "Do not open a public issue. Use a private report, create a restricted Linear issue, and never expose credentials.\n")
        self._write("SUPPORT.md", "Follow SECURITY.md. Never post credentials. Accepted work requires Linear tracking.\n")
        self._write("CODE_OF_CONDUCT.md", "Be respectful and report concerns privately.\n")
        self._write(".github/ISSUE_TEMPLATE/bug_report.yml", "name: Bug\nbody:\n  - type: input\n    validations:\n      required: true\n")
        self._write(".github/ISSUE_TEMPLATE/feature_request.yml", "name: Feature\nbody:\n  - type: input\n    validations:\n      required: true\n")
        self._write(".github/ISSUE_TEMPLATE/config.yml", "blank_issues_enabled: false\ncontact_links: []\n")

        context = {
            "git_conflict_resolution": {
                "mode": "semantic_conceptual_merge",
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
                    "pull_requests_issues_architecture_decisions_tests_and_docs",
                ],
                "forbidden_shortcuts": [
                    "wholesale_ours",
                    "wholesale_theirs",
                    "wholesale_current",
                    "wholesale_incoming",
                    "discarding_one_side_without_conceptual_analysis",
                ],
                "required_outcome": "preserve compatible intent from every relevant side",
            }
        }
        self._write("project-context.yaml", json.dumps(context, indent=2) + "\n")
        organization_policy = {
            "schema_version": 1,
            "work_tracking": {
                "provider": "Linear",
                "search_before_create": True,
                "require_issue_before_implementation": True,
                "require_pull_request_reference": True,
                "require_status_and_validation_sync": True,
                "tracked_categories": sorted(validator.TRACKED_CATEGORIES),
                "on_unmapped_or_ambiguous": "stop_and_report",
                "untracked_drive_by_changes": "forbidden",
            },
            "safe_change_policy": {
                "integration_strategy": "merge",
                "directive": "avoid git rebase in favor of git merge",
                "inspect_worktree_before_mutation_and_publish": True,
                "preserve_uncommitted_and_untracked_work": True,
                "on_unexpected_worktree_changes": "stop_and_report",
                "force_push": "forbidden",
                "bypass_required_checks": "forbidden",
                "disable_security_controls": "forbidden",
                "prohibited_git_commands": list(validator.PROHIBITED_GIT_COMMANDS),
                "prohibited_filesystem_commands": list(validator.PROHIBITED_FILESYSTEM_COMMANDS),
            },
        }
        self._write("organization-policy.json", json.dumps(organization_policy, indent=2) + "\n")

        managed = [
            "README.md",
            ".github/workflows/org-context-integrity.yml",
            "agents/org-context.agent.md",
            "profile/README.md",
            "project-context.yaml",
        ]
        manifest = {
            "files": {
                path: hashlib.sha256((self.root / path).read_bytes()).hexdigest()
                for path in managed
            }
        }
        self._write("org-context-manifest.json", json.dumps(manifest, indent=2) + "\n")

    def assertFailureContains(self, expected: str) -> None:  # noqa: N802
        errors = validator.validate_repository(self.root)
        self.assertTrue(
            any(expected in error for error in errors),
            f"expected {expected!r} in {errors!r}",
        )

    def test_accepts_complete_policy_bundle(self) -> None:
        self.assertEqual(validator.validate_repository(self.root), [])

    def test_rejects_missing_primary_agent_instructions(self) -> None:
        (self.root / "AGENTS.md").unlink()
        self.assertFailureContains("missing required file: AGENTS.md")

    def test_rejects_weakened_history_window(self) -> None:
        path = self.root / "project-context.yaml"
        payload = json.loads(path.read_text(encoding="utf-8"))
        payload["git_conflict_resolution"]["history_lookback_commits"]["minimum"] = 1
        path.write_text(json.dumps(payload), encoding="utf-8")
        self.assertFailureContains("exact 3–10 commit history contract")

    def test_rejects_missing_external_repository_scope(self) -> None:
        path = self.root / "project-context.yaml"
        payload = json.loads(path.read_text(encoding="utf-8"))
        payload["git_conflict_resolution"]["context_scope"].remove(
            "relevant_external_github_organization_repositories"
        )
        path.write_text(json.dumps(payload), encoding="utf-8")
        self.assertFailureContains("relevant_external_github_organization_repositories")

    def test_rejects_wholesale_side_selection_shortcut(self) -> None:
        path = self.root / "project-context.yaml"
        payload = json.loads(path.read_text(encoding="utf-8"))
        payload["git_conflict_resolution"]["forbidden_shortcuts"].remove("wholesale_theirs")
        path.write_text(json.dumps(payload), encoding="utf-8")
        self.assertFailureContains("wholesale_theirs")

    def test_rejects_manifest_drift(self) -> None:
        path = self.root / "profile" / "README.md"
        path.write_text(path.read_text(encoding="utf-8") + "drift\n", encoding="utf-8")
        self.assertFailureContains("manifest hash mismatch: profile/README.md")

    def test_rejects_unresolved_conflict_marker(self) -> None:
        path = self.root / "CONTRIBUTING.md"
        path.write_text("<<<<<<< HEAD\n" + CONTROL_POLICY_TEXT, encoding="utf-8")
        self.assertFailureContains("unresolved Git conflict marker")

    def test_rejects_incomplete_pull_request_checklist(self) -> None:
        self._write(".github/pull_request_template.md", CONTROL_POLICY_TEXT + "\n- [ ] one\n")
        self.assertFailureContains("at least ten checklist items")

    def test_rejects_symlinked_required_file(self) -> None:
        agents = self.root / "AGENTS.md"
        agents.unlink()
        agents.symlink_to(self.root / "CONTRIBUTING.md")
        self.assertFailureContains("must be a regular file: AGENTS.md")

    def test_rejects_missing_exact_merge_directive(self) -> None:
        path = self.root / "AGENTS.md"
        path.write_text(path.read_text(encoding="utf-8").replace(
            "avoid git rebase in favor of git merge", "prefer merging"
        ), encoding="utf-8")
        self.assertFailureContains("avoid git rebase in favor of git merge")

    def test_rejects_removed_destructive_command_ban(self) -> None:
        path = self.root / "organization-policy.json"
        payload = json.loads(path.read_text(encoding="utf-8"))
        payload["safe_change_policy"]["prohibited_git_commands"].remove("git clean")
        path.write_text(json.dumps(payload), encoding="utf-8")
        self.assertFailureContains("git clean")

    def test_rejects_untracked_drive_by_changes(self) -> None:
        path = self.root / "organization-policy.json"
        payload = json.loads(path.read_text(encoding="utf-8"))
        payload["work_tracking"]["untracked_drive_by_changes"] = "allowed"
        path.write_text(json.dumps(payload), encoding="utf-8")
        self.assertFailureContains("untracked_drive_by_changes")

    def test_rejects_missing_linear_tracking_language(self) -> None:
        path = self.root / "CONTRIBUTING.md"
        path.write_text(path.read_text(encoding="utf-8").replace("Linear", "tracker"), encoding="utf-8")
        self.assertFailureContains("linear")

    def test_rejects_unpinned_checkout_in_reusable_workflow(self) -> None:
        path = self.root / ".github/workflows/reusable-organization-policy.yml"
        path.write_text(path.read_text(encoding="utf-8").replace(
            "actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1",
            "actions/checkout@main",
        ), encoding="utf-8")
        self.assertFailureContains("full commit SHA")

    def test_rejects_write_all_permissions(self) -> None:
        path = self.root / ".github/workflows/reusable-organization-policy.yml"
        path.write_text(path.read_text(encoding="utf-8") + "\npermissions: write-all\n", encoding="utf-8")
        self.assertFailureContains("write-all")

    def test_rejects_missing_security_fallback(self) -> None:
        (self.root / "SECURITY.md").unlink()
        self.assertFailureContains("missing required file: SECURITY.md")


if __name__ == "__main__":
    unittest.main()
