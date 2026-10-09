#!/usr/bin/env python3
"""Offline structural smoke test; never claim live-market verification."""
from pathlib import Path
import unittest
ROOT = Path(__file__).resolve().parents[1]
NAMES = ["bvb-fact-check","news-priority","character-consistency","script-qa"]
REFERENCES = ["16-prompt-engineering/instructor/SKILL.md","16-prompt-engineering/instructor/references/validation.md","20-ml-paper-writing/ml-paper-writing/references/citation-workflow.md","15-rag/sentence-transformers/SKILL.md","15-rag/sentence-transformers/references/models.md","17-observability/phoenix/SKILL.md"]
VENDOR = ROOT / "third_party/orchestra-research/AI-Research-SKILLs/"
class AccuracyTests(unittest.TestCase):
    def test_skills(self):
        for name in NAMES:
            with self.subTest(name=name):
                path = ROOT / "skills" / name / "SKILL.md"
                body = path.read_text(encoding="utf-8")
                self.assertEqual(body.splitlines()[1], "name: " + name)
                self.assertTrue(body.startswith("---\n"))
                self.assertGreater(len(body), 500)
    def test_upstream_license(self):
        self.assertIn("MIT License", (VENDOR/"LICENSE").read_text(encoding="utf-8"))
        for p in REFERENCES:
            with self.subTest(path=p):
                self.assertGreater((VENDOR / p).stat().st_size, 100)
    def test_existing_modules(self):
        for path in ["skills/romania-market-director/SKILL.md", ".agents/skills/romania-stock-intelligence/SKILL.md", "skills/romania-market-director/characters/index.json"]:
            self.assertTrue((ROOT/path).is_file())
if __name__ == "__main__":
    unittest.main()
