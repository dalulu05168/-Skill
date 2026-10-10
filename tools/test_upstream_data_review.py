"""Synthetic upstream-feed validation: checking evidence metadata is NOT source verification."""
import sys
import unittest
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from skill_execution_contract import audit_upstream_news_data, lesson_for
from finance_skill_hub import run_pipeline

NEWS = {"headline": "Synthetic test only", "original_url": "https://example.org/original",
        "publisher": "Synthetic test publisher", "published_at": "2026-10-09T12:00+03:00",
        "event_at": "2026-10-09T11:00+03:00", "verified": True}
MARKET = {"instrument": "TEST", "market": "TEST", "value": 100, "unit": "points",
          "baseline": "prior session", "observed_at": "2026-10-09T12:00+03:00",
          "source_url": "https://example.org/data", "delay_status": "unknown", "verified": True}


class UpstreamReviewTests(unittest.TestCase):
    def test_absent_data_does_not_claim_received(self):
        r = audit_upstream_news_data(None)
        self.assertEqual(r["status"], "NOT_RECEIVED")
        self.assertFalse(r["facts_verified"])

    def test_upstream_verified_is_never_inherited(self):
        r = audit_upstream_news_data({"news": [NEWS], "market": [MARKET]})
        self.assertEqual(r["status"], "AWAITING_INDEPENDENT_VERIFICATION")
        self.assertEqual([x["status"] for x in r["items"]], ["UNVERIFIED", "UNVERIFIED"])
        self.assertTrue(all(x["upstream_verified_claim_ignored"] for x in r["items"]))
        self.assertFalse(r["facts_verified"])

    def test_missing_source_and_time_are_rejected(self):
        invalid = dict(MARKET, source_url="", observed_at="2026-10-09T12:00")
        r = audit_upstream_news_data({"news": [dict(NEWS, original_url="file:///secret")],
                                      "market": [invalid]})
        self.assertEqual(r["status"], "REJECTED")
        self.assertTrue(r["issues"])

    def test_extra_fields_and_empty_lists_are_supported(self):
        r = audit_upstream_news_data({"news": [], "market": [], "source": "external"})
        self.assertEqual(r["status"], "AWAITING_INDEPENDENT_VERIFICATION")

    def test_review_in_hub_never_authorizes_publication(self):
        dt = datetime(2026, 10, 9, 12, tzinfo=timezone.utc)
        r = run_pipeline({"upstream_packet": {"news": [NEWS], "market": [MARKET]}},
                         at=dt, node_id="RO-08")
        self.assertEqual(r["upstream_fact_review"]["status"], "AWAITING_INDEPENDENT_VERIFICATION")
        self.assertEqual(r["review"]["publish_status"], "BLOCKED_NO_AUTOMATIC_PUBLICATION")

    def test_course_routing_is_preserved(self):
        self.assertEqual(lesson_for("2026-10-12", "RO-10")["mode"], "technical")
        self.assertEqual(lesson_for("2026-10-13", "RO-10")["mode"], "philosophy")
        root = Path(__file__).resolve().parents[1]
        for sub in ("professor-core", "technical-course", "investment-philosophy"):
            self.assertTrue((root / "skills" / sub / "SKILL.md").is_file())


if __name__ == "__main__":
    unittest.main()
