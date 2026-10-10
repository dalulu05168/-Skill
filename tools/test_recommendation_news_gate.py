"""Regression: one-click role cards and high-impact news candidate gates.

Synthetic fixture tests do NOT constitute verification of live BVB news.
"""
import json
import sys
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent))
import finance_skill_hub as hub
from news_materiality import assess_news
from trading_65 import fresh_state, summary, apply
from trading_65_ui import SECTION, SCRIPT

NOW = datetime(2026, 10, 9, 11, 15, tzinfo=timezone.utc)

def candidate(title, published=None, ident="candidate"):
    return {"item_id": ident, "digest": "digest-" + ident,
            "url": "https://www.bvb.ro/notice/" + ident,
            "title": title, "published_at": published or NOW.isoformat(),
            "urgency_hint": "priority_review_candidate", "change_state": "new"}

def roster():
    return {f"{i:02d}": {
       "character_id": f"{i:02d}",
       "identity_extension": {"姓名": f"角色{i}", "居住城市": "布加勒斯特"},
       "source_profile": {"性别": "女" if i%2 else "男", "年龄": 45,
                          "学员资历": "新女" if i%2 else "新男", "工作_职业": "医生"},
       "investment_profile": {"偏好行业": ["银行", "能源"], "单票仓位偏好": "低仓位"},
       "personality": {"核心标签": ["谨慎", "独立"]},
       "relationship_to_group": {"角色定位": "喜欢核对市场原始资料"},
    } for i in range(1, 66)}

class CardAndSignalTests(unittest.TestCase):
    def test_card_visual_and_65_person_profiles(self):
        self.assertIn('id="sim-recommend"', SECTION)
        self.assertIn("一键推荐交易人员", SECTION)
        self.assertIn("sim-candidate-grid", SECTION + SCRIPT)
        self.assertIn("sim-candidate-card", SECTION + SCRIPT)
        for key in ("p.age", "p.occupation", "p.city", "p.position_preference",
                    "p.traits", "p.investment_focus", "p.hold_count",
                    "data-sim-action=\"invite\"", "data-sim-action=\"buy\""):
            self.assertIn(key, SCRIPT)
        state = fresh_state()
        people = summary(state, roster())["people"]
        self.assertEqual(len(people), 65)
        self.assertEqual(people[0]["investment_focus"], ["银行", "能源"])
        self.assertEqual(people[0]["opened"], False)
        self.assertEqual(people[0]["hold_count"], 0)

    def test_recommend_still_persists_member_actions_and_never_invents_trades(self):
        state = fresh_state()
        p = roster()
        day = "2026-10-09"
        apply(state, p, "eligibility", {"person_id": "01", "opened": True,
              "currency": "RON", "funds": 500, "frequency": "HIGH"})
        offer = apply(state, p, "create_offer", {"symbol": "SIM", "name": "股票模拟",
              "market": "BVB", "currency": "RON", "unit_price": 10,
              "min_shares": 4, "hold_days": 1, "participant_count": 5})
        rec = apply(state,p,"recommend",{"offer_id":offer["id"],"date":day})
        self.assertEqual([x["person_id"] for x in rec["candidates"]], ["01"])
        self.assertEqual(state["transactions"], [])
        self.assertEqual(rec["id"], apply(state,p,"recommend",{"offer_id":offer["id"],"date":day})["id"])
        apply(state,p,"invite",{"offer_id":offer["id"],"date":day,"person_id":"01"})
        apply(state,p,"buy",{"offer_id":offer["id"],"date":day,"person_id":"01","quantity":4})
        self.assertEqual(len(state["transactions"]), 1)
        self.assertEqual(state["transactions"][0]["type"], "buy")

    def test_material_story_triage_is_not_fact_verification(self):
        critical = assess_news(candidate("BVB trading suspension for issuer"), NOW)
        self.assertEqual(critical["tier_candidate"], "P0")
        self.assertEqual(critical["headline_review_priority"], "review_soon")
        self.assertFalse(critical["facts_verified"])
        self.assertFalse(critical["publishable"])
        important = assess_news(candidate("Central bank rate decision expected"), NOW)
        self.assertEqual(important["tier_candidate"], "P1")
        trivial = assess_news(candidate("Local innovation prize and corporate meeting"), NOW)
        self.assertEqual(trivial["tier_candidate"], "P2")
        self.assertEqual(trivial["headline_review_priority"], "routine_review")
        # RSS urgency is only a hint and cannot turn generic PR into P0.
        self.assertFalse(trivial["metadata_holds_highlight"])

    def test_real_bvb_feed_shape_issuer_title_and_three_source_versions(self):
        issuer = "OMV PETROM S.A. (SNP)"
        with_detail = candidate(issuer, ident="a")
        with_detail["summary"] = "Trading Update T3/26"
        self.assertEqual(assess_news(with_detail, NOW)["tier_candidate"], "P1")
        # Three versions (PDF Romanian, PDF English, canonical HTML) represent
        # one issuer event and must not appear as three talking points.
        versions = []
        for n, source in enumerate(("ro.pdf", "en.pdf",
                                    "/FinancialInstruments/SelectedData/NewsItem/SNP-trading-update/X")):
            item = {**with_detail, "item_id": str(n), "digest": "v"+str(n),
                    "url": ("https://www.bvb.ro"+source if source.startswith("/")
                            else "https://bvb.ro/infocont/"+source)}
            versions.append(item)
        result = hub.run_pipeline({"news_queue": {"items": versions}}, at=NOW)
        self.assertEqual(result["news"]["raw_pending_versions"], 3)
        self.assertEqual(result["news"]["pending_count"], 1)
        self.assertEqual(result["news"]["duplicate_source_versions"], 2)
        self.assertEqual(result["news"]["high_impact_review_candidates"], 1)
        self.assertEqual(len(result["news"]["items"][0]["source_variants"]), 3)
        self.assertIn("/FinancialInstruments/SelectedData/NewsItem/",
                      result["news"]["items"][0]["url"])
        self.assertIn("Trading Update", result["news"]["items"][0]["display_title"])
        self.assertEqual(result["news"]["push_delivery"]["sent_count"], 0)

    def test_unreliable_dates_and_numbers_are_flagged(self):
        future = candidate("BVB trading suspension", (NOW + timedelta(days=3)).isoformat())
        future_gate = assess_news(future, NOW)
        self.assertTrue(future_gate["metadata_holds_highlight"])
        self.assertEqual(future_gate["headline_review_priority"], "hold_metadata_review")
        old = candidate("Central bank rate decision", (NOW - timedelta(days=45)).isoformat())
        self.assertTrue(assess_news(old, NOW)["metadata_holds_highlight"])
        missing = candidate("Bank earnings report", " ")
        self.assertTrue(assess_news(missing, NOW)["metadata_holds_highlight"])
        numbers = candidate("Dividend increases 15%")
        self.assertTrue(assess_news(numbers, NOW)["numerical_source_check_required"])
        self.assertFalse(assess_news(numbers, NOW)["publishable"])

    def test_end_to_end_candidate_queue_never_calls_publisher(self):
        items = [candidate("BVB trading suspension", ident="halt"),
                 candidate("Dividend 15% proposed", ident="dividend"),
                 candidate("Corporate awards update", ident="pr")]
        result = hub.run_pipeline({"news_queue": {"items": items}}, at=NOW)
        self.assertEqual(result["news"]["pending_count"], 3)
        self.assertEqual(result["news"]["high_impact_review_candidates"], 2)
        self.assertEqual(len(result["news"]["editorial_shortlist"]), 2)
        self.assertEqual(result["news"]["push_delivery"]["sent_count"], 0)
        self.assertEqual(result["news"]["push_delivery"]["status"], "NOT_CONFIGURED_NO_WHATSAPP_SEND")
        self.assertEqual(result["review"]["publish_status"], "BLOCKED_NO_AUTOMATIC_PUBLICATION")
        self.assertTrue(all(x["evidence_status"] == "UNVERIFIED" for x in result["news"]["items"]))

    def test_failed_rss_fetch_has_no_false_empty_news_and_no_state_mutation(self):
        with tempfile.TemporaryDirectory() as tmp:
            state = Path(tmp) / "rss.json"
            with patch.object(hub.rss_intake, "official_fetch", side_effect=OSError("RSS offline")):
                with self.assertRaises(OSError):
                    hub.run_pipeline({}, at=NOW, fetch_rss=True, state_file=state)
            self.assertFalse(state.exists())

    def test_actual_fetch_routing_with_mock_official_rss_and_idempotent_versions(self):
        item = candidate("Dividend proposed for next fiscal year", ident="real-structure")
        with tempfile.TemporaryDirectory() as tmp:
            state = Path(tmp) / "rss.json"
            with patch.object(hub.rss_intake,"official_fetch",return_value=b"<rss></rss>"), \
                 patch.object(hub.rss_intake,"parse_feed",return_value=[item]):
                first = hub.run_pipeline({}, at=NOW, fetch_rss=True, state_file=state)
                again = hub.run_pipeline({}, at=NOW, fetch_rss=True, state_file=state)
            self.assertEqual(first["news"]["pending_count"],1)
            self.assertEqual(again["news"]["pending_count"],1)
            persisted = json.loads(state.read_text())
            self.assertEqual(persisted["version"],2)
            self.assertEqual(len(persisted["pending"]),1)
            self.assertFalse(first["news"]["items"][0]["materiality"]["facts_verified"])


if __name__ == "__main__":
    unittest.main()
