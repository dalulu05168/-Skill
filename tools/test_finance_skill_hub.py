"""Hub integration tests: no network or market claims; use synthetic candidates."""
import json
import sys
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import finance_skill_hub as hub

FRIDAY = datetime(2026, 10, 9, 11, 15, tzinfo=timezone.utc)
FAKE_NEWS = {
    "item_id": "synthetic-test-id", "digest": "synthetic-test-digest",
    "title": "Synthetic dividend candidate", "url": "https://www.bvb.ro/notice/sample",
    "published_at": "2026-10-09T11:00:00+00:00",
    "urgency_hint": "priority_review_candidate", "change_state": "new",
}


class HubTests(unittest.TestCase):
    def test_single_call_chains_real_roster_news_and_qa(self):
        result = hub.run_pipeline({"news_queue": {"items": [FAKE_NEWS]}}, at=FRIDAY)
        self.assertEqual(result["characters"]["roster_count"], 65)
        self.assertEqual(len(result["routing"]["skill_sequence"]), 5)
        self.assertEqual(result["news"]["items"][0]["evidence_status"], "UNVERIFIED")
        self.assertEqual(result["news"]["items"][0]["review_priority"], "review_soon")
        self.assertEqual(result["review"]["status"], "NEEDS_REVIEW")
        self.assertEqual(result["review"]["publish_status"], "BLOCKED_NO_AUTOMATIC_PUBLICATION")

    def test_romanian_weekend_and_dst(self):
        saturday = datetime(2026, 10, 10, 5, 0, tzinfo=timezone.utc)
        info = hub.slot_for(saturday)
        self.assertEqual(info["id"], "RO-13")
        self.assertEqual(info["publication"], "09:30")
        autumn = hub.slot_for(datetime(2026, 10, 25, 7, 0, tzinfo=timezone.utc))
        self.assertEqual(autumn["timezone"], "Europe/Bucharest")
        self.assertEqual(autumn["id"], "RO-15")

    def test_professor_only_evening_and_roster_four_way_match(self):
        roster = hub.personas.validate()
        any_id, person = sorted(roster.items())[0]
        member = {"character_id": any_id, "name": person["name"],
                  "gender": person["gender"], "role": person["role"],
                  "text": "This is a fictional teaching sample."}
        ok = hub.run_pipeline({"messages": [
            {"speaker": "教授", "text": "Fictional concept lesson"}, member],
            "fictional_simulation_notice": True}, at=FRIDAY, node_id="RO-10")
        self.assertEqual(ok["review"]["status"], "NEEDS_REVIEW")
        disallowed = hub.run_pipeline({"messages": [
            {"speaker": "教授", "text": "Outside class"}]},
            at=FRIDAY, node_id="RO-08")
        self.assertEqual(disallowed["review"]["status"], "BLOCKED")
        self.assertTrue(any("professor" in x.lower() for x in disallowed["review"]["issues"]))
        member["gender"] = "错误"
        invalid = hub.run_pipeline({"messages": [member],
                                    "fictional_simulation_notice": True},
                                   at=FRIDAY, node_id="RO-10")
        self.assertEqual(invalid["review"]["status"], "BLOCKED")

    def test_audit_is_metadata_only_and_no_quote_claim(self):
        result = hub.run_pipeline({"observations": {"observations": []}}, at=FRIDAY)
        self.assertEqual(result["review"]["status"], "BLOCKED")
        self.assertEqual(result["market_metadata_audit"]["gate"], "fail")
        result = hub.run_pipeline({}, at=FRIDAY)
        self.assertEqual(result["market_metadata_audit"]["gate"], "not_run")

    def test_malformed_queue_and_untrusted_url_rejected(self):
        with self.assertRaises(ValueError):
            hub.run_pipeline({"news_queue": {"wrong_key": []}}, at=FRIDAY)
        item = {**FAKE_NEWS, "url": "https://evil.example/articles/1"}
        output = hub.run_pipeline({"news_queue": {"items": [item]}}, at=FRIDAY)
        self.assertEqual(output["review"]["status"], "BLOCKED")
        self.assertEqual(output["news"]["pending_count"], 0)

    def test_cli_writes_review_file_without_fetch(self):
        with tempfile.TemporaryDirectory() as d:
            inp, out = Path(d) / "input.json", Path(d) / "output.json"
            inp.write_text(json.dumps({"news_queue": {"items": [FAKE_NEWS]}}),
                           encoding="utf-8")
            code = hub.main(["--input", str(inp), "--at", FRIDAY.isoformat(),
                             "--node", "RO-08", "--out", str(out)])
            self.assertEqual(code, 0)
            data = json.loads(out.read_text(encoding="utf-8"))
            self.assertEqual(data["slot"]["id"], "RO-08")
            self.assertEqual(data["review"]["publish_status"], "BLOCKED_NO_AUTOMATIC_PUBLICATION")

    def test_fetch_cannot_run_without_durable_state(self):
        with self.assertRaises(ValueError):
            hub.run_pipeline({}, fetch_rss=True, at=FRIDAY)


if __name__ == "__main__":
    unittest.main()
