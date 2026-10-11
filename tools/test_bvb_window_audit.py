"""Deterministic and fully offline tests for time-window BVB brief."""
from datetime import datetime, timezone
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parent))
from bvb_window_audit import audit_news, build_brief, market_analysis, schedule, window_for

NOW = datetime(2026, 10, 9, 5, 50, tzinfo=timezone.utc)  # Fri 08:50 Bucharest

def story(title, stamp, *, host="www.bvb.ro", source="bvb-market", description=""):
    return {
        "title": title, "dateRaw": stamp, "url": f"https://{host}/news/article-123",
        "guid": title, "sourceId": source, "source": "BVB", "description": description,
    }

class BVBWindowTests(unittest.TestCase):
    def test_canonical_node_times_and_recent_window_only(self):
        self.assertEqual(len(schedule()), 16)
        w = window_for(NOW)
        self.assertEqual(w["id"], "RO-04")
        self.assertEqual(w["start"], "2026-10-09T08:15:00+03:00")
        self.assertEqual(w["end"], "2026-10-09T08:50:00+03:00")
        self.assertEqual(w["execution"], "on_demand_only_not_scheduled")
        old = window_for(NOW, "RO-03")
        self.assertEqual(old["end"], "2026-10-09T08:45:00+03:00")
        with self.assertRaises(ValueError):
            window_for(NOW, "RO-08")
        with self.assertRaises(ValueError):
            window_for(datetime(2026, 10, 9, 5, 50))

    def test_weekend_dst_uses_bucharest_and_does_not_change_schedule(self):
        sunday = window_for(datetime(2026, 10, 25, 7, 5, tzinfo=timezone.utc))
        self.assertEqual(sunday["id"], "RO-15")
        self.assertEqual(sunday["timezone"], "Europe/Bucharest")
        self.assertTrue(sunday["end"].endswith("+02:00"))

    def test_hot_news_window_origin_fact_check_not_falsely_verified(self):
        w=window_for(NOW)
        rows,held=audit_news([
            story("Routine market commentary", "Fri, 09 Oct 2026 05:20:00 GMT"),
            story("Dividend declared", "Fri, 09 Oct 2026 05:45:00 GMT"),
            story("suspendarea tranzacționării", "Fri, 09 Oct 2026 05:40:00 GMT"),
            story("Too early", "Fri, 09 Oct 2026 05:10:00 GMT"),
            story("Tomorrow headline", "Sat, 10 Oct 2026 05:15:00 GMT"),
            story("Fake source", "Fri, 09 Oct 2026 05:40:00 GMT", host="evil.example"),
            story("No timestamp", ""),
            story("HTTP spoof", "Fri, 09 Oct 2026 05:40:00 GMT",host="evil.bvb.ro")
        ],w,checked_at=NOW)
        self.assertEqual([x["priority_candidate"] for x in rows],["P0","P1","P2"])
        self.assertEqual(len(held),3)
        self.assertTrue(all(not x["facts_verified"] for x in rows))
        self.assertTrue(all(not x["original_article_checked"] for x in rows))
        self.assertTrue(all(not x["independent_corroboration_checked"] for x in rows))
        self.assertTrue(all("evidence_gaps" in x for x in rows))

    def test_no_index_price_means_no_claim_of_market_direction(self):
        unavailable=market_analysis({"state":"unavailable","value":None},[])
        self.assertEqual(unavailable["status"],"insufficient_market_data")
        self.assertEqual(unavailable["bet_direction"],"unknown")
        self.assertFalse(unavailable["numerical_claims_verified"])
        self.assertEqual(market_analysis({"state":"ok","value":"nan","change":4,"marketTime":"08:45"},[])["bet_direction"],"unknown")
        delayed=market_analysis({"state":"ok","value":23000.2,"change":-0.72,"marketTime":"08:40",
                                 "url":"https://ws.bvb.ro/"},[])
        self.assertEqual(delayed["bet_direction"],"down")
        self.assertEqual(delayed["status"],"provisional_delayed_observation")
        self.assertFalse(delayed["numerical_claims_verified"])
        self.assertIn("delayed",delayed["quote_type"])

    def test_market_report_keeps_feed_failures_and_pending_evidence(self):
        snapshot={"fetchedAt":NOW.isoformat(),
                  "articles":[story("Dividend declared", "Fri, 09 Oct 2026 05:40:00 GMT")],
                  "sources":[{"id":"bvb-market","state":"ok"},{"id":"bursa","state":"failed","message":"HTTP 500"}],
                  "quote":{"state":"unavailable","value":None}}
        output=build_brief(snapshot,at=NOW)
        self.assertEqual(output["news"]["count"],1)
        self.assertEqual(len(output["news"]["priority_candidates"]),1)
        self.assertEqual(output["news"]["source_failures"][0]["message"],"HTTP 500")
        self.assertFalse(output["news"]["autofactcheck_success"])
        self.assertEqual(output["market"]["status"],"insufficient_market_data")
        with self.assertRaises(ValueError):
            build_brief({"articles":None},at=NOW)

if __name__=="__main__":
    unittest.main()
