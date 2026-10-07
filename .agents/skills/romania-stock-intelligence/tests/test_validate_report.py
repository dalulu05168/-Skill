import copy
import json
import unittest
from pathlib import Path
from sys import path

ROOT = Path(__file__).resolve().parents[1]
path.insert(0, str(ROOT / "scripts"))
from validate_report import validate  # noqa: E402
from show_schedule import schedule_for  # noqa: E402
from datetime import date  # noqa: E402


class TestRSI(unittest.TestCase):
    def setUp(self):
        self.base = json.loads((ROOT / "tests/minimal_valid.json").read_text(encoding="utf-8"))

    def metric(self):
        return {
            "series": "BET",
            "value": 100.0, "unit": "points",
            "baseline": {"description": "prior trading close", "status": "compared", "value": 98.0, "observed_at": "2026-10-07T17:50:00+03:00"},
            "observed_at": "2026-10-08T07:50:00+03:00",
            "timezone": "Europe/Bucharest",
            "source_url": "https://www.bvb.ro/FinancialInstruments/Indices/Overview",
            "delay_status": "end_of_day", "vs_previous_brief": {"status": "not_available", "reason": "prior briefing missing"}, "quality": "verified"
        }

    def test_minimal_missing_source_is_honest(self):
        self.assertEqual(validate(self.base), [])

    def test_compliant_metric(self):
        self.base["metrics"] = [self.metric()]
        self.assertEqual(validate(self.base), [])

    def test_missing_provenance_rejected(self):
        m = self.metric()
        del m["source_url"]
        self.base["metrics"].append(m)
        self.assertTrue(any("source_url" in x for x in validate(self.base)))

    def test_inconsistent_time_zone_rejected(self):
        self.base["produced_at"] = "2026-10-08T08:00:00+02:00"
        self.assertTrue(any("conflicts" in x for x in validate(self.base)))

    def test_confirmed_close_requires_proof_flag(self):
        self.base["market_status"] = "confirmed_close"
        self.assertTrue(any("official_close_confirmed" in x for x in validate(self.base)))

    def test_fake_previous_delta_rejected(self):
        m = self.metric()
        self.base["previous_report_id"] = "RSI-20261007-1800"
        m["vs_previous_brief"] = {"status": "compared", "previous_report_id": "RSI-20261007-1800", "previous_value": 95, "change_value": 3, "change_unit": "points"}
        self.base["metrics"] = [m]
        self.assertTrue(any("numeric change" in x for x in validate(self.base)))

    def test_dst_summer_and_winter(self):
        s = schedule_for(date(2026, 10, 8))
        w = schedule_for(date(2026, 12, 8))
        self.assertEqual([x[2].strftime("%H:%M") for x in s], ["13:00", "18:00", "23:00"])
        self.assertEqual([x[2].strftime("%H:%M") for x in w], ["14:00", "19:00", "00:00"])
        self.assertEqual(w[2][2].date(), date(2026, 12, 9))


if __name__ == "__main__":
    unittest.main()
