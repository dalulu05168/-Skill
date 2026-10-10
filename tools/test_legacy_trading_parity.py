"""Do not retire 005 trading source until every legacy feature is reviewed.

Functional parity needs actual end-to-end tests; this is a conservative
static deletion gate, not proof that all features have been implemented.
"""
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class LegacyTradingParityGate(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.matrix = json.loads((ROOT / "docs/legacy-trading-parity.json").read_text(encoding="utf-8"))

    def test_matrix_has_expected_identity_and_traceable_legacy_areas(self):
        self.assertEqual(self.matrix["legacy_persona_count"], 70)
        self.assertEqual(self.matrix["canonical_persona_count"], 65)
        self.assertFalse(self.matrix["mapped_data"])
        self.assertEqual(len(self.matrix["open_gaps"]), 6)
        self.assertEqual(len({x["id"] for x in self.matrix["open_gaps"]}), 6)
        for gap in self.matrix["open_gaps"]:
            with self.subTest(gap=gap["id"]):
                self.assertIn(gap["status"], {"unverified", "implemented", "waived"})
                self.assertTrue(gap["legacy"].startswith("legacy/005-trading/"))
                self.assertTrue(gap["condition"].strip())

    def test_unresolved_gaps_require_recoverable_legacy_source(self):
        if any(x["status"] == "unverified" for x in self.matrix["open_gaps"]):
            for file in ("trading-simulator.js", "trade-dashboard.js", "README.md"):
                with self.subTest(file=file):
                    self.assertTrue((ROOT / "legacy/005-trading" / file).is_file())

    def test_supported_trading_actions_stay_available(self):
        backend = (ROOT / "tools/trading_65.py").read_text(encoding="utf-8")
        expected = set(self.matrix["workflow_actions_verified"])
        for action in expected:
            with self.subTest(action=action):
                self.assertIn('"' + action + '"', backend)
        self.assertEqual(len(expected), 7)

    def test_legacy_and_new_identity_sources_do_not_get_merged(self):
        script = (ROOT / "tools/trading_65_ui.py").read_text(encoding="utf-8")
        backend = (ROOT / "tools/trading_65.py").read_text(encoding="utf-8")
        self.assertNotIn("growth-workspace-db", script + backend)
        self.assertNotIn("france70-v6.1.json", script + backend)
        self.assertTrue((ROOT / "skills/romania-market-director/characters/index.json").is_file())


if __name__ == "__main__":
    unittest.main()
