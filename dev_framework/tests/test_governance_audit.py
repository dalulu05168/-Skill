import unittest
from dev_framework.governance_audit import audit_branch

REPO = "owner/project"

class GovernanceAuditTests(unittest.TestCase):
    def complete(self):
        return {
            "name": "main", "protected": True,
            "protection": {"enabled": True, "required_status_checks": {
                "enforcement_level": "everyone",
                "checks": [{"context":"real-tests"}], "contexts": []
            }}
        }

    def test_missing_snapshot_is_blocked(self):
        self.assertEqual(audit_branch(None, REPO)["decision"], "BLOCK")

    def test_unprotected_main_is_blocked(self):
        s = self.complete()
        s["protected"] = False
        self.assertEqual(audit_branch(s, REPO)["decision"], "BLOCK")

    def test_disabled_rules_are_blocked(self):
        s = self.complete()
        s["protection"]["enabled"] = False
        self.assertEqual(audit_branch(s, REPO)["decision"], "BLOCK")

    def test_checks_are_required(self):
        s = self.complete()
        s["protection"]["required_status_checks"]["checks"] = []
        self.assertEqual(audit_branch(s, REPO)["decision"], "BLOCK")

    def test_non_enforced_checks_are_blocked(self):
        s = self.complete()
        s["protection"]["required_status_checks"]["enforcement_level"] = "off"
        self.assertEqual(audit_branch(s, REPO)["decision"], "BLOCK")

    def test_mismatched_branch_is_blocked(self):
        s = self.complete()
        s["name"] = "feature"
        self.assertEqual(audit_branch(s, REPO)["decision"], "BLOCK")

    def test_good_snapshot_only_passes_branch_checks(self):
        result = audit_branch(self.complete(), REPO)
        self.assertEqual(result["decision"], "PASS_BRANCH_CHECKS_ONLY")
        self.assertEqual(result["required_check_names"], ["real-tests"])
        self.assertIn("不能代替", result["limitations"])

if __name__ == "__main__":
    unittest.main()
