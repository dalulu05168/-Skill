"""Regression guard: canonical sources and obsolete bundle snapshots.

This intentionally avoids touching any persisted user or trading state.
"""
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class CanonicalSourceTests(unittest.TestCase):
    def test_old_distributed_zip_snapshots_are_not_tracked_in_source_tree(self):
        old = (
            ROOT / "dist" / "romania-finance-bundle.zip",
            ROOT / "dist" / "romania-market-director-skill.zip",
        )
        for path in old:
            with self.subTest(path=path.name):
                self.assertFalse(path.exists(), "Use validated workflow artifacts, not an outdated ZIP")
        ignore = (ROOT / ".gitignore").read_text(encoding="utf-8")
        self.assertIn("/dist/*.zip", ignore)

    def test_production_package_is_built_from_current_sources(self):
        workflow = (ROOT / ".github/workflows/skill-quality.yml").read_text(encoding="utf-8")
        packaging = (ROOT / "tools/assemble_bundle.py").read_text(encoding="utf-8")
        self.assertIn("python tools/assemble_bundle.py --out-dir build/skill-bundles", workflow)
        self.assertIn("name: romania-skill-bundles", workflow)
        self.assertIn("bundle-manifest.json", packaging)

    def test_exactly_65_persona_profiles_are_authoritative_here(self):
        directory = ROOT / "skills/romania-market-director/characters/profiles"
        self.assertEqual(len(list(directory.glob("*_AI_Profile.json"))), 65)
        self.assertTrue((ROOT / "skills/romania-market-director/characters/index.json").exists())

    def test_old_005_js_is_archived_and_not_loaded_by_active_workspace(self):
        old = ROOT / "legacy/005-trading"
        self.assertTrue((old / "trading-simulator.js").exists())
        self.assertTrue((old / "trade-dashboard.js").exists())
        # Active services must not import or serve the unadapted legacy 70-person JS.
        for relative in (
            "tools/finance_skill_api.py",
            "tools/trading_center_ui.py",
            "tools/trading_65.py",
            "tools/trading_65_ui.py",
        ):
            with self.subTest(file=relative):
                current = (ROOT / relative).read_text(encoding="utf-8")
                self.assertNotIn("legacy/005-trading", current)
                self.assertNotIn("france70-v6.1.json", current)


if __name__ == "__main__":
    unittest.main()
