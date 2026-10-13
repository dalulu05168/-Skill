"""Deletion guard: only the authoritative 65-person trading simulation may ship."""
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class CanonicalTradingOnly(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.matrix = json.loads((ROOT / "docs/legacy-trading-parity.json").read_text(encoding="utf-8"))

    def test_no_70_person_legacy_source_is_packaged(self):
        self.assertTrue(self.matrix["legacy_removed"])
        self.assertFalse((ROOT / "legacy" / "005-trading").exists(),
                         "Old 70-person JS source must not be repackaged")
        self.assertEqual(self.matrix["canonical_persona_count"], 65)
        self.assertFalse(self.matrix["mapped_data"])
        self.assertTrue(self.matrix["archived_source_url"].startswith("https://github.com/"))

    def test_simulation_workflow_actions_present(self):
        backend = (ROOT / "tools/trading_65.py").read_text(encoding="utf-8")
        for action in self.matrix["workflow_actions_verified_in_source"]:
            with self.subTest(action=action):
                self.assertIn('"' + action + '"', backend)

    def test_retired_features_are_explicit_not_fake(self):
        self.assertEqual({x["id"] for x in self.matrix["intentionally_retired"]},
                         {"manual_holding_input", "standalone_daily_buy_list"})
        self.assertEqual({x["id"] for x in self.matrix["enhancements"]},
                         {"edit_existing_offer", "chart_unique_holders_by_stock",
                          "batch_holdings_and_sale", "next_sale_countdown"})

    def test_canonical_roster_remains_separate(self):
        backend = (ROOT / "tools/trading_65.py").read_text(encoding="utf-8")
        ui = (ROOT / "tools/trading_65_ui.py").read_text(encoding="utf-8")
        self.assertNotIn("growth-workspace-db", backend + ui)
        self.assertNotIn("france70-v6.1.json", backend + ui)
        self.assertIn("stock_groups", backend)
        self.assertIn("sim-stock-chart", ui)
        self.assertTrue((ROOT / "skills/romania-market-director/characters/index.json").is_file())


if __name__ == "__main__":
    unittest.main()
