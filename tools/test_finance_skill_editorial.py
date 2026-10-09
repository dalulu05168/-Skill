"""Synthetic editorial regressions; no claims or remote calls."""
import copy
import unittest
from datetime import datetime, timezone
from finance_skill_editorial import audit_editorial
from finance_skill_hub import run_pipeline


def packet():
    return {
        "date": "2026-10-09", "node_id": "RO-10", "theme": "假设课堂",
        "learning_goal": "识别错误", "handoff": "承接前一栏目",
        "owners": dict.fromkeys(("evidence", "editor", "assistant", "homework_reviewer"), "待人工核证的测试人"),
        "course_chain": dict.fromkeys(("previous_record_or_unknown", "problem", "prerequisites",
                                      "example", "homework", "rubric", "next_lesson"), "假设教学测试"),
        "reply_plan": dict.fromkeys(("assistant_scope", "professor_pending", "follow_up_node"), "RO-11助理回收"),
        "hotspots": [], "credentials": [], "real_experiences": [],
    }


class EditorialTests(unittest.TestCase):
    def test_missing_is_honest_and_complete_is_never_approved(self):
        self.assertEqual(audit_editorial(None, [])["status"], "not_run")
        out = audit_editorial(packet(), [])
        self.assertEqual(out["status"], "needs_human_review")
        self.assertFalse(out["facts_verified"])
        self.assertTrue(out["human_review_required"])

    def test_each_required_section_fails_closed(self):
        for key in packet():
            p = packet()
            del p[key]
            with self.subTest(key=key):
                self.assertEqual(audit_editorial(p, [])["status"], "fail")
        for field in ("hotspots", "credentials", "real_experiences"):
            p = packet()
            p[field] = [{}]
            self.assertEqual(audit_editorial(p, [])["status"], "fail")

    def test_simulation_chorus_experiences_and_reply_references(self):
        member = {"message_id": "m1", "character_id": "01", "single_focus": True,
                  "simulation_only": True, "text": "【虚构教学模拟】【假设】如何判断？",
                  "experience_kind": "hypothetical", "intent": "discussion"}
        self.assertEqual(audit_editorial(packet(), [member])["status"], "needs_human_review")
        for changes in ({"simulation_only": False}, {"text": "我的亏损"},
                        {"experience_kind": "real"}, {"single_focus": False},
                        {"intent": "question", "reply_to": "future"}):
            with self.subTest(changes=changes):
                self.assertEqual(audit_editorial(packet(), [{**member, **changes}])["status"], "fail")
        praise = {**member, "intent": "praise"}
        self.assertEqual(audit_editorial(packet(), [praise, {**praise, "message_id": "m2"}])["status"], "fail")
        answer = {"message_id": "a1", "speaker": "助理", "text": "先检查条件",
                  "single_focus": True, "intent": "answer", "reply_to": "m1"}
        self.assertEqual(audit_editorial(packet(), [member, answer])["status"], "needs_human_review")

    def test_hub_blocks_wrong_date_and_retains_internal_status(self):
        at = datetime(2026, 10, 9, 12, tzinfo=timezone.utc)
        out = run_pipeline({"editorial_packet": packet()}, at=at, node_id="RO-10")
        self.assertEqual(out["review"]["status"], "NEEDS_REVIEW")
        p = copy.deepcopy(packet())
        p["date"] = "2026-10-08"
        out = run_pipeline({"editorial_packet": p}, at=at, node_id="RO-10")
        self.assertEqual(out["review"]["status"], "BLOCKED")
        self.assertEqual(out["characters"]["roster_count"], 65)


if __name__ == "__main__":
    unittest.main()
