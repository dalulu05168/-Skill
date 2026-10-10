"""Synthetic data only. Never use these demo quotes as real market or investor records."""
import copy
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from multiday_rehearsal import inspect_three_day_rehearsal
from chennan_writing import load_profiles

def member(profiles, cid, mid, text, reply_to=None):
    p = profiles[cid]
    return {
        "character_id": cid, "message_id": mid,
        "name": p["identity_extension"]["姓名"],
        "gender": p["source_profile"]["性别"],
        "role": p["source_profile"]["学员资历"],
        "text": "【虚构教学模拟】" + text,
        "simulation_only": True,
        "reply_to": reply_to
    }

def sample(profiles):
    news = {
        "item_id": "synthetic-2026-10-12-1",
        "headline": "Synthetic input not a real news story",
        "original_url": "https://example.org/synthetic-test",
        "publisher": "synthetic-only",
        "published_at": "2026-10-12T10:00:00+03:00",
        "event_at": "2026-10-12T09:00:00+03:00",
        "verified": True,
    }
    assistant = {
        "event": "Synthetic demo story", "evidence_url": "https://example.org/synthetic-test",
        "observed_at": "2026-10-12T10:00:00+03:00", "market_link": "Only hypothetical",
        "causal_path": "Hypothetical credit cost to issuer funding",
        "counter_factors": "Other macro conditions could reverse inference",
        "uncertainty": "Real facts are unverified", "next_check": "Check actual original disclosure",
    }
    course = {
        "course_type": "technical", "learning_objective": "Explain confirmation vs invalidation",
        "principle": "Signals do not guarantee a future return",
        "example": "【假设】Volume increase without confirmation",
        "mistake": "Retrospective cherry-picking",
        "practice": "Find a falsifying condition",
        "next_link": "Review one example later", "source_status": "Reconstructed outline only",
    }
    return {
        "upstream_packet": {"news": [news], "market": []},
        "days": [
            {"date": "2026-10-12", "scenes": [{
                "scene_id": "d1", "node": "RO-08", "host_kind": "assistant",
                "news_item_ids": ["synthetic-2026-10-12-1"], "assistant_analysis": assistant,
                "messages": [
                    member(profiles, "01", "m1", "这条消息的时间需要先确认。"),
                    member(profiles, "02", "m2", "是啊，我觉得前提还没说清楚。", "m1"),
                ],
            }]},
            {"date": "2026-10-13", "scenes": [{
                "scene_id": "d2", "node": "RO-08", "host_kind": "assistant",
                "news_item_ids": [], "continuity_refs": [
                    {"scene_id": "d1", "scope": "sandbox_rehearsal"}],
                "messages": [
                    member(profiles, "02", "m3", "昨天那个时间问题还没回答呢。"),
                    member(profiles, "01", "m4", "我也没找到源头，再查一下。", "m3"),
                ],
            }]},
            {"date": "2026-10-14", "scenes": [{
                "scene_id": "d3", "node": "RO-10", "host_kind": "professor",
                "professor_course": course,
                "continuity_refs": [{"scene_id": "d2", "scope": "sandbox_rehearsal"}],
                "messages": [member(profiles, "01", "m5", "假设这个量并不是真突破，怎么检验？")],
            }]},
        ],
    }


class ThreeDayRehearsalTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.profiles = load_profiles()

    def test_three_day_demo_has_sandbox_continuity_but_no_factual_certification(self):
        p = sample(self.profiles)
        before = copy.deepcopy(p)
        result = inspect_three_day_rehearsal(p, self.profiles)
        self.assertEqual(result["status"], "NEEDS_HUMAN_EDITION", result["issues"])
        self.assertEqual(result["day_count"], 3)
        self.assertEqual(result["metrics"]["supported_continuity_references"], 2)
        self.assertEqual(result["metrics"]["peer_reply_turns"], 2)
        self.assertEqual(result["source_review"]["items"][0]["status"], "UNVERIFIED")
        self.assertFalse(result["market_facts_verified"])
        self.assertFalse(result["character_naturalness_verified"])
        self.assertFalse(result["publication_allowed"])
        self.assertFalse(result["approved_memory_mutated"])
        self.assertEqual(p, before)

    def test_unapproved_or_future_callbacks_are_blocked(self):
        p = sample(self.profiles)
        p["days"][0]["scenes"][0]["continuity_refs"] = [
            {"scene_id": "d3", "scope": "sandbox_rehearsal"}]
        self.assertEqual(inspect_three_day_rehearsal(p, self.profiles)["status"],
                         "STRUCTURAL_BLOCKED")
        p = sample(self.profiles)
        p["days"][1]["scenes"][0]["continuity_refs"] = [
            {"scene_id": "unapproved-past", "scope": "approved_history"}]
        self.assertEqual(inspect_three_day_rehearsal(p, self.profiles)["status"],
                         "STRUCTURAL_BLOCKED")

    def test_approved_history_never_accepts_draft(self):
        p = sample(self.profiles)
        p["days"][1]["scenes"][0]["continuity_refs"] = [
            {"scene_id": "historic-1", "scope": "approved_history"}]
        draft = {"id": "historic-1", "status": "draft", "messages": []}
        self.assertEqual(inspect_three_day_rehearsal(
            p, self.profiles, adopted_scenes=[draft])["status"], "STRUCTURAL_BLOCKED")
        draft["status"] = "adopted"
        self.assertEqual(inspect_three_day_rehearsal(
            p, self.profiles, adopted_scenes=[draft])["status"], "NEEDS_HUMAN_EDITION")

    def test_persona_identity_disclosure_and_unlabeled_trades_fail(self):
        p = sample(self.profiles)
        msg = p["days"][0]["scenes"][0]["messages"][0]
        msg["name"] = "Not this person"
        msg["text"] = "我今天买了100股"
        msg["simulation_only"] = False
        result = inspect_three_day_rehearsal(p, self.profiles)
        self.assertEqual(result["status"], "STRUCTURAL_BLOCKED")
        self.assertTrue(any("identity" in x for x in result["issues"]))
        self.assertTrue(any("fiction" in x for x in result["issues"]))

    def test_bad_professor_schedule_and_wrong_course_type_blocked(self):
        p = sample(self.profiles)
        p["days"][2]["scenes"][0]["professor_course"]["course_type"] = "philosophy"
        self.assertEqual(inspect_three_day_rehearsal(
            p, self.profiles)["status"], "STRUCTURAL_BLOCKED")
        p = sample(self.profiles)
        p["days"][2]["scenes"][0]["node"] = "RO-08"
        self.assertEqual(inspect_three_day_rehearsal(
            p, self.profiles)["status"], "STRUCTURAL_BLOCKED")

    def test_news_requires_article_input_and_complete_assistant_analysis(self):
        p = sample(self.profiles)
        p["days"][0]["scenes"][0]["news_item_ids"] = ["unsubmitted"]
        self.assertEqual(inspect_three_day_rehearsal(
            p, self.profiles)["status"], "STRUCTURAL_BLOCKED")
        p = sample(self.profiles)
        del p["days"][0]["scenes"][0]["assistant_analysis"]["counter_factors"]
        self.assertEqual(inspect_three_day_rehearsal(
            p, self.profiles)["status"], "STRUCTURAL_BLOCKED")

    def test_missing_real_news_does_not_fabricate_data(self):
        p = sample(self.profiles)
        del p["upstream_packet"]
        p["days"][0]["scenes"][0]["news_item_ids"] = []
        report = inspect_three_day_rehearsal(p, self.profiles)
        self.assertEqual(report["status"], "NEEDS_HUMAN_EDITION")
        self.assertEqual(report["source_review"]["status"], "NOT_RECEIVED")
        self.assertTrue(any("no incoming source data" in w for w in report["warnings"]))
        self.assertFalse(report["publication_allowed"])

    def test_same_phrase_each_day_produces_naturalness_warning(self):
        p = sample(self.profiles)
        p["days"][1]["scenes"][0]["messages"][0]["text"] = (
            p["days"][0]["scenes"][0]["messages"][0]["text"])
        report = inspect_three_day_rehearsal(p, self.profiles)
        self.assertTrue(any("identical member phrase repeated" in w
                            for w in report["warnings"]))

    def test_three_calendar_days_must_be_ordered_and_consecutive(self):
        p = sample(self.profiles)
        p["days"][2]["date"] = "2026-10-17"
        self.assertEqual(inspect_three_day_rehearsal(
            p, self.profiles)["status"], "STRUCTURAL_BLOCKED")


if __name__ == "__main__":
    unittest.main()
