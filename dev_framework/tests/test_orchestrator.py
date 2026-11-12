import json
import tempfile
import unittest
from pathlib import Path
from dev_framework.orchestrator import RELEASE_POLICY, acceptance, new_task, validate_task

class FrameworkContractTests(unittest.TestCase):
    def setUp(self):
        self.task = new_task("owner/project", "修复登录及手机排版", "feat/login", "web")

    def test_new_task_not_claimed_as_completed(self):
        self.assertEqual(validate_task(self.task), [])
        self.assertTrue(all(x["state"] == "pending" for x in self.task["phases"]))
        self.assertFalse(self.task["release_policy"]["auto_deploy"])
        self.assertTrue(self.task["release_policy"]["requires_explicit_merge_approval"])

    def test_reject_direct_main_branch(self):
        with self.assertRaises(ValueError):
            new_task("owner/project", "demo", "main", "web")

    def test_reject_invalid_repository_and_profile(self):
        with self.assertRaises(ValueError):
            new_task("project", "demo", "feat/x", "web")
        with self.assertRaises(ValueError):
            new_task("owner/project", "demo", "feat/x", "invalid")

    def test_reject_disabled_approvals(self):
        self.task["release_policy"] = dict(RELEASE_POLICY, auto_deploy=True)
        self.assertTrue(validate_task(self.task))

    def test_reject_unverified_pass_status(self):
        self.task["phases"][0]["state"] = "pass"
        self.assertTrue(validate_task(self.task))

    def test_reject_ready_without_evidence(self):
        self.task["phases"][0]["state"] = "ready_for_review"
        self.assertTrue(validate_task(self.task))

    def test_missing_report_blocks(self):
        with tempfile.TemporaryDirectory() as root:
            result = acceptance(self.task, Path(root)/"missing.json", Path(root), "a"*40)
        self.assertEqual(result["decision"], "BLOCK")

    def test_mismatched_repository_blocks(self):
        with tempfile.TemporaryDirectory() as root:
            file = Path(root)/"report.json"
            file.write_text(json.dumps({"project_id":"other/repo","schema_version":1}),encoding="utf-8")
            result = acceptance(self.task, file, Path(root), "a"*40)
        self.assertEqual(result["decision"], "BLOCK")

    def test_existing_evidence_gate_enforces_missing_checks(self):
        with tempfile.TemporaryDirectory() as root:
            file = Path(root)/"report.json"
            file.write_text(json.dumps({"project_id":"owner/project",
                                        "schema_version":1,
                                        "target_sha":"a"*40,
                                        "checks":{}}),encoding="utf-8")
            result = acceptance(self.task, file, Path(root), "a"*40)
        self.assertEqual(result["decision"], "BLOCK")
        self.assertIn("build", " ".join(result["issues"]))

if __name__ == "__main__":
    unittest.main()
