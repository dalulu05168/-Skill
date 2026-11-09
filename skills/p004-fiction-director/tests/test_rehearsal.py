"""Regression tests for fictional three-day P004 group screenplay.

Run locally: python -m unittest discover -s skills/p004-fiction-director/tests -p 'test_*.py' -v
"""
import copy
import importlib.util
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("new_story_rehearsal_validator",
    ROOT / "scripts" / "validate_rehearsal.py")
auditor = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(auditor)


class RehearsalTests(unittest.TestCase):
    def setUp(self):
        self.story = json.loads((ROOT / "examples" / "three-day-sandbox.json").read_text(encoding="utf-8"))
        self.roster = json.loads((ROOT / "characters" / "drafts" / "roster-v2.json").read_text(encoding="utf-8"))

    def run_audit(self):
        return auditor.validate(self.story, self.roster)

    def test_baseline_has_crossday_story_and_distinct_members(self):
        r = self.run_audit()
        self.assertEqual("STRUCTURAL_REHEARSAL_PASS_NOT_LITERARY_CERTIFICATION", r["status"])
        self.assertEqual(7, r["scenes"])
        self.assertEqual(37, r["messages"])
        self.assertGreaterEqual(r["member_speakers"], 8)
        self.assertGreaterEqual(r["cross_scene_callbacks"], 2)
        self.assertGreaterEqual(r["member_to_member_replies"], 2)
        self.assertEqual(3, r["evening_professor_lessons"])
        self.assertFalse(r["wrote_memory"])

    def test_no_old_or_unknown_person_speaks(self):
        self.story["scenes"][0]["messages"][1]["speaker_id"] = "66"
        with self.assertRaisesRegex(ValueError, "unknown"):
            self.run_audit()

    def test_professor_daytime_is_rejected(self):
        self.story["scenes"][0]["messages"][0]["speaker_id"] = "professor"
        with self.assertRaisesRegex(ValueError, "evening only"):
            self.run_audit()

    def test_weekday_lesson_type_cannot_change(self):
        self.story["scenes"][1]["lesson_type"] = "philosophy"
        with self.assertRaisesRegex(ValueError, "wrong weekday"):
            self.run_audit()

    def test_duplicate_message_ids_detected(self):
        self.story["scenes"][1]["messages"][0]["message_id"] = "m01"
        with self.assertRaisesRegex(ValueError, "duplicate"):
            self.run_audit()

    def test_a_nonexistent_past_message_is_not_memory(self):
        self.story["scenes"][2]["messages"][1]["reply_to"] = "m9999"
        with self.assertRaisesRegex(ValueError, "previously authored"):
            self.run_audit()

    def test_a_future_message_cannot_be_referenced(self):
        self.story["scenes"][0]["messages"][1]["reply_to"] = "m34"
        with self.assertRaisesRegex(ValueError, "previously authored"):
            self.run_audit()

    def test_sandbox_cannot_claim_user_approval(self):
        self.story["status"] = "ADOPTED"
        with self.assertRaisesRegex(ValueError, "unadopted"):
            self.run_audit()

    def test_new_story_roster_cannot_use_old_story_id(self):
        self.roster["story_id"] = "romania-market-director"
        with self.assertRaisesRegex(ValueError, "isolated draft"):
            self.run_audit()

    def test_rehearsal_cannot_mark_candidate_as_approved(self):
        self.roster["people"][0]["approved_by_user"] = True
        with self.assertRaisesRegex(ValueError, "not imply characters are approved"):
            self.run_audit()

    def test_member_reply_narrative_is_required(self):
        for s in self.story["scenes"]:
            for msg in s["messages"]:
                if msg["speaker_id"] in {p["id"] for p in self.roster["people"]}:
                    msg.pop("reply_to", None)
        with self.assertRaisesRegex(ValueError, "never reply"):
            self.run_audit()

    def test_crossday_story_continuity_is_required(self):
        for s in self.story["scenes"]:
            ids = {m["message_id"] for m in s["messages"]}
            for m in s["messages"]:
                if "reply_to" in m and m["reply_to"] not in ids:
                    m.pop("reply_to")
        with self.assertRaisesRegex(ValueError, "cross-day"):
            self.run_audit()

    def test_a_member_dialogue_cannot_be_empty(self):
        self.story["scenes"][0]["messages"][1]["text"] = "  "
        with self.assertRaisesRegex(ValueError, "empty message"):
            self.run_audit()

    def test_dates_must_remain_chronological(self):
        self.story["scenes"][2]["date"] = "2026-10-11"
        with self.assertRaisesRegex(ValueError, "chronological"):
            self.run_audit()


if __name__ == "__main__":
    unittest.main()
