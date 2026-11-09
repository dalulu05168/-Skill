"""Regression tests for the isolated P004 65-person DRAFT directory."""
import copy
import importlib.util
import json
import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "p004_draft_validator", ROOT / "scripts" / "validate_draft_roster.py"
)
module = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(module)
DRAFT = ROOT / "characters" / "drafts" / "roster-v2.json"
V1 = ROOT / "characters" / "drafts" / "roster-v1.json"
APPROVED = ROOT / "characters" / "approved-roster.json"


class DraftRosterTests(unittest.TestCase):
    def setUp(self):
        self.data = json.loads(DRAFT.read_text(encoding="utf-8"))

    def test_65_complete_and_varied(self):
        result = module.validate_draft(self.data)
        self.assertEqual("STRUCTURE_VALID_DRAFT_ONLY", result["status"])
        self.assertEqual(65, result["people"])
        self.assertEqual(65, result["distinct_voice_signatures"])
        self.assertGreaterEqual(result["distinct_regions"], 12)
        self.assertGreaterEqual(result["distinct_occupations"], 35)
        self.assertEqual(0, result["approved_people"])
        self.assertEqual(65, result["distinct_romanian_auditions"])
        self.assertTrue(result["human_language_and_literary_review_required"])

    def test_new_official_roster_remains_empty(self):
        approved = json.loads(APPROVED.read_text(encoding="utf-8"))
        self.assertEqual([], approved["characters"])
        self.assertEqual(module.STORY_ID, approved["story_id"])

    def test_no_past_and_no_prebuilt_relationships(self):
        for p in self.data["people"]:
            self.assertFalse(p["initial_history"])
            self.assertFalse(p["initial_relationships"])
            self.assertFalse(p["first_scene_example_is_history"])

    def test_wrong_group_distribution_rejected(self):
        self.data["people"][0]["main_behavior"] = "反驳者"
        with self.assertRaisesRegex(ValueError, "distribution"):
            module.validate_draft(self.data)

    def test_duplicate_catchphrase_rejected(self):
        self.data["people"][1]["voice"]["catchphrases"] = list(
            self.data["people"][0]["voice"]["catchphrases"]
        )
        with self.assertRaisesRegex(ValueError, "duplicate catchphrases"):
            module.validate_draft(self.data)

    def test_approval_flag_is_not_allowed_in_draft(self):
        self.data["people"][0]["approved_by_user"] = True
        with self.assertRaisesRegex(ValueError, "marked approved"):
            module.validate_draft(self.data)

    def test_fabricated_history_rejected(self):
        self.data["people"][4]["initial_history"].append("yesterday bought shares")
        with self.assertRaisesRegex(ValueError, "pre-story history"):
            module.validate_draft(self.data)

    def test_duplicate_example_lines_rejected(self):
        self.data["people"][9]["first_scene_example_zh"] = self.data["people"][0]["first_scene_example_zh"]
        with self.assertRaisesRegex(ValueError, "duplicate sample lines"):
            module.validate_draft(self.data)

    def test_invalid_person_number_rejected(self):
        self.data["people"][18]["id"] = "65"
        with self.assertRaisesRegex(ValueError, "nonsequential"):
            module.validate_draft(self.data)

    def test_no_old_persona_import_paths(self):
        # The new roster contains only its own characters and fictional metadata.
        text = DRAFT.read_text(encoding="utf-8")
        self.assertNotIn("skills/romania-market-director/", text)
        self.assertNotIn("approved_scenes", text)
        self.assertNotIn("transaction_id", text)

    def test_v1_remains_valid_unchanged(self):
        data = json.loads(V1.read_text(encoding="utf-8"))
        result = module.validate_draft(data)
        self.assertEqual("draft-v1", result["version"])

    def test_retirement_workplace_blunder_caught(self):
        retired = next(p for p in self.data["people"] if "退休" in p["occupation"])
        retired["silence_cues"] = ["忙于退休医生职责、无法专心阅读时"]
        with self.assertRaisesRegex(ValueError, "retired"):
            module.validate_draft(self.data)

    def test_romanian_dialogue_samples_must_be_distinct(self):
        a, b = self.data["people"][:2]
        b["voice"]["romanian_audition_line"] = a["voice"]["romanian_audition_line"]
        with self.assertRaisesRegex(ValueError, "duplicate Romanian auditions"):
            module.validate_draft(self.data)

    def test_romanian_example_is_not_history(self):
        self.data["people"][0]["voice"]["romanian_audition_is_history"] = True
        with self.assertRaisesRegex(ValueError, "invalid Romanian audition"):
            module.validate_draft(self.data)

    def test_member_may_remain_silent(self):
        self.data["people"][0]["turn_taking"]["may_decline_to_speak"] = False
        with self.assertRaisesRegex(ValueError, "forced to speak"):
            module.validate_draft(self.data)

    def test_missing_confrontation_style_rejected(self):
        self.data["people"][0]["turn_taking"]["confronted"] = ""
        with self.assertRaisesRegex(ValueError, "turn_taking"):
            module.validate_draft(self.data)

    def test_module_two_trade_not_injected_as_biography(self):
        self.data["people"][0]["executed_trades"] = ["bought shares yesterday"]
        with self.assertRaisesRegex(ValueError, "missing or unexpected fields"):
            module.validate_draft(self.data)

    def test_voice_and_retirement_cleanup_all_65(self):
        profiles = self.data["people"]
        self.assertTrue(all(p["approved_by_user"] is False for p in profiles))
        for p in profiles:
            self.assertFalse(p["initial_relationships"])
            self.assertFalse(p["initial_history"])
            self.assertFalse(p["voice"]["romanian_audition_is_history"])
            if "退休" in p["occupation"]:
                self.assertNotIn("忙于退休", " ".join(p["silence_cues"]))
        self.assertEqual(65, len({p["voice"]["romanian_audition_line"] for p in profiles}))


if __name__ == "__main__":
    unittest.main()
