"""Boundary tests: formal memory, persona media, course weekdays, and news/assistant/professor gates."""
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from skill_execution_contract import (audit_member_voice, audit_publication_packet,
                                      lesson_for, load_official_memory)
from chennan_writing import load_profiles


def record(**update):
    val = {"assistant": {"event": "verified market story", "evidence_url": "https://www.bvb.ro/",
                         "observed_at": "2026-10-12T10:00+03:00", "market_link": "possible",
                         "causal_path": "rate -> credit cost", "counter_factors": "regulation",
                         "uncertainty": "unconfirmed market price", "next_check": "read issuer report"},
           "news": [{"original_url": "https://www.bvb.ro/", "published_at": "time",
                     "event_at": "time", "why_relevant": "BVB issuer", "source_status": "unverified"}],
           "node": "RO-07"}
    val.update(update)
    return val


class MandatorySkillContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.profiles = load_profiles()

    def test_memory_state_is_true_empty_history_not_fake_past(self):
        state = load_official_memory(["01", "07"])
        self.assertEqual(state["source"], "skills/romania-market-director/memory/state.json")
        self.assertEqual(state["state"], "empty_no_official_history")
        self.assertEqual(state["approved_scene_count"], 0)
        self.assertEqual(state["selected_persona_memory"], {"01": {}, "07": {}})

    def test_weekday_135_24_and_weekend_prohibition(self):
        days = [("2026-10-12", "technical"), ("2026-10-13", "philosophy"),
                ("2026-10-14", "technical"), ("2026-10-15", "philosophy"),
                ("2026-10-16", "technical")]
        for day, course in days:
            self.assertEqual(lesson_for(day, "RO-10")["mode"], course)
            self.assertTrue(lesson_for(day, "RO-10")["can_speak"])
        self.assertFalse(lesson_for("2026-10-17", "RO-10")["can_speak"])
        self.assertFalse(lesson_for("2026-10-12", "RO-08")["can_speak"])
        self.assertEqual(lesson_for("2026-10-12", "RO-10")["technical_source_status"],
                         "original_user_technical_course_not_in_repository")

    def test_persona_01_forbids_gif_and_persona_emoji_soft_limit(self):
        blocked = audit_member_voice([{"character_id": "01", "text": "【虚构教学模拟】我再看看。",
                                       "media_type": "GIF", "asset_id": "G01", "asset_verified": True}], self.profiles)
        self.assertTrue(any("GIF is forbidden" in x for x in blocked["issues"]))
        emoji = audit_member_voice([{"character_id": "01", "text": "【虚构教学模拟】我再看看。🤔"}], self.profiles)
        self.assertEqual(emoji["issues"], [])
        self.assertTrue(emoji["human_review_required"])
        self.assertFalse(emoji["naturalness_verified"])

    def test_news_and_assistant_evidence_gates(self):
        self.assertEqual(audit_publication_packet(record())["status"], "NEEDS_HUMAN_REVIEW")
        self.assertFalse(audit_publication_packet(record())["publication_allowed"])
        p = record()
        del p["assistant"]["counter_factors"]
        self.assertEqual(audit_publication_packet(p)["status"], "BLOCKED")
        self.assertEqual(audit_publication_packet({})["status"], "BLOCKED")

    def test_professor_wrong_weekday_mode_blocks(self):
        prof = {"date": "2026-10-13", "course_type": "technical",
                "learning_objective": "understand uncertainty", "principle": "concept",
                "example": "hypothetical", "mistake": "hindsight",
                "practice": "ask one question", "next_link": "continue on Thursday",
                "source_status": "reference exists"}
        p = record(node="RO-10", professor=prof)
        self.assertEqual(audit_publication_packet(p)["status"], "BLOCKED")
        prof["course_type"] = "philosophy"
        self.assertEqual(audit_publication_packet(p)["status"], "NEEDS_HUMAN_REVIEW")
        prof["date"] = "2026-10-17"
        self.assertEqual(audit_publication_packet(p)["status"], "BLOCKED")

    def test_fictional_character_claims_require_checked_memory_and_identity(self):
        p = record(fictional_characters_used=True)
        self.assertEqual(audit_publication_packet(p)["status"], "BLOCKED")
        p.update(simulation_notice=True, memory_checked=True, roster_checked=True)
        self.assertEqual(audit_publication_packet(p)["status"], "NEEDS_HUMAN_REVIEW")


if __name__ == "__main__":
    unittest.main()
