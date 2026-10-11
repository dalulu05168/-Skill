"""Audition is an isolated *unapproved fiction*; never official story history."""
import json
import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
AUDITION = ROOT / "examples" / "65-person-multiscene-audition-v2.json"
ROSTER = ROOT / "characters" / "drafts" / "roster-v2.json"
OFFICIAL = ROOT / "characters" / "approved-roster.json"


class AuditionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.script = json.loads(AUDITION.read_text(encoding="utf-8"))
        cls.roster = json.loads(ROSTER.read_text(encoding="utf-8"))
        cls.official = json.loads(OFFICIAL.read_text(encoding="utf-8"))

    def test_samples_remain_simulated_not_official_memory(self):
        self.assertTrue(self.script["simulation_only"])
        self.assertFalse(self.script["approved_by_user"])
        self.assertTrue(self.script["not_official_memory"])
        self.assertEqual("HYPOTHETICAL_EDUCATIONAL_SCENARIO", self.script["fact_status"])
        self.assertEqual([], self.official["characters"])

    def test_same_story_and_approved_roster_not_assumed(self):
        self.assertEqual(self.script["story_id"], self.roster["story_id"])
        self.assertEqual(self.script["story_id"], self.official["story_id"])
        self.assertTrue(all(x["approved_by_user"] is False for x in self.roster["people"]))

    def test_three_stages_and_scheduled_professor(self):
        self.assertEqual(["morning", "afternoon", "evening"], [s["slot"] for s in self.script["scenes"]])
        self.assertEqual("Wednesday", self.script["weekday"])
        professor_count = 0
        for scene in self.script["scenes"]:
            for msg in scene["messages"]:
                if msg["speaker_id"] == "professor":
                    self.assertEqual("evening", scene["slot"])
                    professor_count += 1
        self.assertGreaterEqual(professor_count, 2)

    def test_speakers_and_reply_references_exist_in_prior_messages(self):
        ids = {p["id"] for p in self.roster["people"]} | {"professor", "assistant"}
        seen = set()
        for scene in self.script["scenes"]:
            for msg in scene["messages"]:
                self.assertIn(msg["speaker_id"], ids)
                self.assertNotIn(msg["message_id"], seen)
                self.assertTrue(msg["text"].strip())
                if "reply_to" in msg:
                    self.assertIn(msg["reply_to"], seen)
                seen.add(msg["message_id"])

    def test_member_to_member_discussion_not_only_assistant_responses(self):
        speakers = {}
        member_replies = 0
        for s in self.script["scenes"]:
            for msg in s["messages"]:
                if msg.get("reply_to") and msg["speaker_id"] not in ("assistant", "professor"):
                    if speakers[msg["reply_to"]] not in ("assistant", "professor"):
                        member_replies += 1
                speakers[msg["message_id"]] = msg["speaker_id"]
        self.assertGreaterEqual(member_replies, 5)

    def test_afternoon_refers_to_actually_written_morning_message(self):
        morning_ids = {m["message_id"] for m in self.script["scenes"][0]["messages"]}
        afternoon = self.script["scenes"][1]["messages"]
        self.assertTrue(any(m.get("reply_to") in morning_ids for m in afternoon))

    def test_no_unverified_real_transactions_or_automatic_adoption(self):
        self.assertEqual([], [p for p in self.roster["people"] if p["initial_history"]])
        self.assertNotIn("CONFIRMED_LIVE_DATA", self.script["fact_status"])
        self.assertTrue(all("transaction_id" not in m for s in self.script["scenes"] for m in s["messages"]))


if __name__ == "__main__":
    unittest.main()
