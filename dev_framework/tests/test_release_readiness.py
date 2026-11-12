import copy
import unittest
from dev_framework.release_readiness import evaluate_pr

SHA = "a"*40
REPO = "owner/project"
CHECKS = ["nuvexa-source-preflight-only", "nuvexa-branch-governance"]

class ReleaseReadinessTests(unittest.TestCase):
    def setUp(self):
        self.pr = {
            "number": 12, "state": "open", "merged": False, "draft": False,
            "head": {"sha": SHA, "repo": {"full_name": REPO}},
            "base": {"ref": "main"}, "user": {"login": "author", "type": "User"}
        }
        self.branch = {
            "name": "main", "protected": True,
            "protection": {"enabled": True, "required_status_checks": {
                "enforcement_level": "everyone", "checks": [
                    {"context": name} for name in CHECKS]
            }}
        }
        self.checks = {"check_runs": [
            {"name": name, "head_sha": SHA, "status": "completed", "conclusion": "success"}
            for name in CHECKS
        ]}
        self.reviews = [{"user": {"login": "reviewer", "type": "User"},
                         "state": "APPROVED", "commit_id": SHA,
                         "submitted_at": "2026-10-11T01:00:00Z"}]

    def eval(self):
        return evaluate_pr(REPO, self.pr, self.checks, self.reviews, self.branch, CHECKS)

    def test_valid_metadata_only_ready_for_human(self):
        self.assertEqual(self.eval()["decision"], "READY_FOR_HUMAN_AUTHORIZATION")

    def test_draft_stays_blocked(self):
        self.pr["draft"] = True
        self.assertEqual(self.eval()["decision"], "BLOCK")

    def test_unprotected_branch_stays_blocked(self):
        self.branch["protected"] = False
        self.assertEqual(self.eval()["decision"], "BLOCK")

    def test_non_enforced_ci_blocks(self):
        self.branch["protection"]["required_status_checks"]["checks"] = []
        self.assertEqual(self.eval()["decision"], "BLOCK")

    def test_no_mandatory_list_blocks(self):
        self.assertEqual(evaluate_pr(REPO, self.pr, self.checks, self.reviews,
                                     self.branch, [])["decision"], "BLOCK")

    def test_failed_or_skipped_or_stale_ci_blocks(self):
        for field, value in [("conclusion", "failure"), ("conclusion", "skipped"),
                             ("status", "in_progress"), ("head_sha", "b"*40)]:
            with self.subTest(field=field, value=value):
                copied = copy.deepcopy(self.checks)
                copied["check_runs"][0][field] = value
                result = evaluate_pr(REPO, self.pr, copied, self.reviews,
                                     self.branch, CHECKS)
                self.assertEqual(result["decision"], "BLOCK")

    def test_no_review_blocks(self):
        self.reviews = []
        self.assertEqual(self.eval()["decision"], "BLOCK")

    def test_author_self_approval_blocks(self):
        self.reviews[0]["user"]["login"] = "author"
        self.assertEqual(self.eval()["decision"], "BLOCK")

    def test_review_at_stale_commit_blocks(self):
        self.reviews[0]["commit_id"] = "b"*40
        self.assertEqual(self.eval()["decision"], "BLOCK")

    def test_latest_change_request_overrides_old_approval(self):
        self.reviews.append({
            "user": {"login": "reviewer", "type": "User"},
            "state": "CHANGES_REQUESTED", "commit_id": SHA,
            "submitted_at": "2026-10-11T02:00:00Z"
        })
        self.assertEqual(self.eval()["decision"], "BLOCK")

    def test_bot_approval_cannot_replace_human(self):
        self.reviews[0]["user"] = {"login": "helper[bot]", "type": "Bot"}
        self.assertEqual(self.eval()["decision"], "BLOCK")

    def test_pr_head_mismatch_blocks(self):
        self.pr["head"]["sha"] = "b"*40
        self.assertEqual(self.eval()["decision"], "BLOCK")

    def test_missing_repo_info_blocks(self):
        self.pr["head"]["repo"] = None
        self.assertEqual(self.eval()["decision"], "BLOCK")

    def test_duplicate_required_check_blocks(self):
        self.checks["check_runs"].append(copy.deepcopy(self.checks["check_runs"][0]))
        self.assertEqual(self.eval()["decision"], "BLOCK")

if __name__ == "__main__":
    unittest.main()
