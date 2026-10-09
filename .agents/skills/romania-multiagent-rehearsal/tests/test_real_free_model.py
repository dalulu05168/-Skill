"""Offline tests: original full persona fields, continuity and no official memory change."""
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

HERE=Path(__file__).resolve().parents[1]/"scripts"
p=importlib.util.spec_from_file_location("ro_fullsource_rehearsal",HERE/"real_free_model_3rounds.py")
m=importlib.util.module_from_spec(p)
p.loader.exec_module(m)

class RealFreeHarnessTests(unittest.TestCase):
    def test_full_profiles_have_distinct_styles_and_languages(self):
        bank=m.registry()
        self.assertEqual(len(bank),65)
        a=m.info_for_model(bank["01"])
        b=m.info_for_model(bank["15"])
        self.assertNotEqual(a["personality"],b["personality"])
        self.assertFalse(a["gif_permitted"])
        self.assertTrue(b["gif_permitted"])
        self.assertEqual(m.info_for_model(bank["05"])["language"],"fr-FR")
        self.assertEqual(m.info_for_model(bank["30"])["language"],"fr-FR")
        self.assertEqual(m.info_for_model(bank["37"])["language"],"fr-FR")

    def test_same_five_people_remember_prior_lines(self):
        observed=[]
        def fake_llm(*,prompt,model):
            observed.append(prompt)
            return "Aş vrea mai întâi să verific dacă riscurile sunt legate."
        with tempfile.TemporaryDirectory() as td:
            report=m.produce("qwen2.5:1.5b",Path(td)/"result.json",llm=fake_llm)
            self.assertEqual(report["character_count_loaded"],65)
            self.assertEqual(report["real_model_calls_succeeded"],15)
            self.assertTrue(report["same_five_roles_across_rounds"])
            self.assertFalse(report["publish_allowed"])
            self.assertFalse(report["user_adopted_memory_changed"])
            self.assertEqual([m["id"] for m in report["rounds"][0]["messages"]],
                             [m["id"] for m in report["rounds"][1]["messages"]])
            self.assertIn("Aş vrea mai întâi",observed[5])
            self.assertIn("previous lines",observed[5])
            # This is a stub test, never interpreted as a real model result.
            self.assertEqual(json.loads((Path(td)/"result.json").read_text())["whatsapp_sent"],False)

    def test_review_flag_for_chinese_and_duplicate(self):
        bank=m.registry()
        c=m.info_for_model(bank["01"])
        flags=m.text_issues("你好，这个百分百赚钱",[],c)
        self.assertIn("contains_chinese_not_romanian",flags)
        dup=m.text_issues("Asta e riscant.",["Asta e riscant."],c)
        self.assertIn("duplicate_message",dup)

    def test_french_primary_language_not_forced_to_romanian(self):
        bank=m.registry()
        c=m.info_for_model(bank["05"])
        with self.assertRaises(ValueError):
            m.instruction(c,"topic",1,[],[])

if __name__=="__main__":unittest.main()
