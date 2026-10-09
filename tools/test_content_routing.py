"""No-live-market regression tests for four-category BVB read-only contract."""
import copy
import json
import sys
import tempfile
import threading
import unittest
from pathlib import Path
from http.server import ThreadingHTTPServer
from urllib.request import urlopen

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import content_routing
import finance_skill_api as api
from finance_skill_hub import run_pipeline


class CategoryContractTests(unittest.TestCase):
    def test_exact_16_nodes_with_original_times_and_4_categories(self):
        before = json.loads((content_routing.INTEL_CONFIG / "schedule.json").read_text(encoding="utf-8"))
        snapshot = content_routing.routing_snapshot()
        after = json.loads((content_routing.INTEL_CONFIG / "schedule.json").read_text(encoding="utf-8"))
        self.assertEqual(before, after)  # categorization never writes schedule
        self.assertEqual(len(snapshot["nodes"]), 16)
        self.assertEqual(set(x["id"] for x in snapshot["categories"]),
                         {"news", "market", "course", "interaction"})
        for a, b in zip(snapshot["nodes"], before["runs"]):
            self.assertEqual(a["id"], b["id"])
            self.assertEqual(a["publication"], b["publication"])
            self.assertEqual(a["preparation"], b["preparation"])
        self.assertTrue(snapshot["read_only"])
        self.assertEqual(snapshot["source_schedule_status"], "specification_only_not_scheduled")

    def test_current_morning_afternoon_evening_goals_and_no_hard_quota(self):
        snap = content_routing.routing_snapshot()
        for period, target in (("weekday_morning", 35), ("weekday_afternoon", 35),
                               ("weekday_evening", 30)):
            self.assertEqual(snap["daily_targets"][period]["target"], target)
            self.assertEqual(snap["daily_targets"][period]["guidance_range"], [target-3, target+3])
            for actual in (target-3, target, target+3):
                result = content_routing.period_guidance(period, actual)
                self.assertTrue(result["within_guidance"])
                self.assertTrue(result["advisory_only"])
            self.assertFalse(content_routing.period_guidance(period, target+4)["within_guidance"])
        self.assertTrue(snap["counting_rules"]["quality_over_count"])
        self.assertTrue(snap["counting_rules"]["guidance_not_quota"])
        self.assertEqual(snap["counting_rules"]["not_counted"], ["RO-01"])
        self.assertIn("No fixed weekday quotas", snap["counting_rules"]["weekends"])

    def test_incomplete_mapping_or_duplicate_daypart_nodes_fails_closed(self):
        original = content_routing.INTEL_CONFIG
        config = json.loads((original / "content-classification.json").read_text(encoding="utf-8"))
        schedule = (original / "schedule.json").read_text(encoding="utf-8")
        try:
            with tempfile.TemporaryDirectory() as t:
                p = Path(t)
                (p / "schedule.json").write_text(schedule, encoding="utf-8")
                content_routing.INTEL_CONFIG = p
                broken = copy.deepcopy(config)
                broken["nodes"].pop()
                (p / "content-classification.json").write_text(json.dumps(broken), encoding="utf-8")
                with self.assertRaises(ValueError):
                    content_routing.routing_snapshot()
                broken = copy.deepcopy(config)
                broken["daily_targets"]["weekday_afternoon"]["counted_nodes"].append("RO-03")
                (p / "content-classification.json").write_text(json.dumps(broken), encoding="utf-8")
                with self.assertRaises(ValueError):
                    content_routing.routing_snapshot()
        finally:
            content_routing.INTEL_CONFIG = original

    def test_review_packet_exposes_advisory_metadata_not_publication(self):
        result = run_pipeline({}, node_id="RO-10")
        self.assertEqual(result["content_classification"]["category"], "course")
        self.assertEqual(result["content_classification"]["message_targets"]["weekday_evening"]["target"], 30)
        self.assertEqual(result["review"]["publish_status"], "BLOCKED_NO_AUTOMATIC_PUBLICATION")

    def test_http_category_endpoint_without_existing_ui_changes(self):
        with tempfile.TemporaryDirectory() as folder:
            with ThreadingHTTPServer(("127.0.0.1", 0), api.make_handler(Path(folder))) as srv:
                thread = threading.Thread(target=srv.serve_forever, daemon=True)
                thread.start()
                try:
                    base = f"http://127.0.0.1:{srv.server_port}"
                    with urlopen(base + "/api/content/categories") as response:
                        obj = json.load(response)
                    self.assertEqual(len(obj["nodes"]), 16)
                    self.assertTrue(obj["read_only"])
                    with urlopen(base + "/") as response:
                        self.assertEqual(response.status, 200)
                finally:
                    srv.shutdown()
                    thread.join(timeout=5)


if __name__ == "__main__":
    unittest.main()
