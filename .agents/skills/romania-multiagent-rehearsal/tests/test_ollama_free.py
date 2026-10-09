"""Keyless tests for local CPU-only open-model simulation safety."""
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

SRC=Path(__file__).resolve().parents[1]/"scripts"/"ollama_free_rehearsal.py"
sp=importlib.util.spec_from_file_location("ro_ollama_trial",SRC)
m=importlib.util.module_from_spec(sp)
sp.loader.exec_module(m)

class OllamaFreeTests(unittest.TestCase):
    def test_no_model_dry_run(self):
        with tempfile.TemporaryDirectory() as td:
            def forbidden(**kw):
                raise AssertionError("No model calls allowed")
            report=m.run("gestionarea riscului","qwen2.5:1.5b",Path(td)/"dry.json",
                         dry_run=True,llm=forbidden)
            self.assertEqual(report["model_calls_attempted"],0)
            self.assertFalse(report["publication_allowed"])
            self.assertFalse(report["real_model_used"])
            self.assertEqual(len(report["rounds"]),3)
            self.assertEqual(sum(len(q["participants"]) for q in report["rounds"]),15)

    def test_15_simulated_calls_and_no_send(self):
        with tempfile.TemporaryDirectory() as td:
            seen=[]
            def stub(**kw):
                seen.append(kw["prompt"])
                return "Prefer să înţeleg riscul înainte să aleg."
            report=m.run("diversificarea", "qwen2.5:1.5b",
                         Path(td)/"test.json", llm=stub)
            self.assertEqual(report["model_calls_attempted"],15)
            self.assertEqual(len(seen),15)
            self.assertFalse(report["publication_allowed"])
            self.assertEqual(report["whatsapp_messages_sent"],0)
            ids=[p["simulated_persona_id"] for r in report["rounds"] for p in r["participants"]]
            self.assertEqual(len(ids),len(set(ids)))
            self.assertEqual(json.loads((Path(td)/"test.json").read_text())["role_count"],67)
            self.assertTrue(all(x["quality_status"]=="SIMULATION_ONLY_HUMAN_REVIEW_REQUIRED"
                                for r in report["rounds"] for x in r["participants"]))

    def test_prevent_banned_promise(self):
        self.assertIn("financial_guarantee",m.safety_flags("Profit garantat azi."))
        self.assertIn("directional_trade_instruction",m.safety_flags("Cumpără acum!"))
        self.assertIn("suspicious_link",m.safety_flags("https://test.example"))
        self.assertNotIn("financial_guarantee",m.safety_flags("Nu ştiu ce se va întâmpla."))

    def test_invalid_model(self):
        with tempfile.TemporaryDirectory() as td:
            with self.assertRaises(ValueError):
                m.run("test","cloud-provider-without-budget",Path(td)/"unsafe.json",dry_run=True)

    def test_no_overwrite(self):
        with tempfile.TemporaryDirectory() as td:
            path=Path(td)/"out.json"
            path.write_text("KEEP",encoding="utf-8")
            with self.assertRaises(FileExistsError):
                m.run("topic","qwen2.5:0.5b",path,dry_run=True)
            self.assertEqual(path.read_text(encoding="utf-8"),"KEEP")

    def test_model_failure_flagged(self):
        with tempfile.TemporaryDirectory() as td:
            def reject(**kw):raise RuntimeError("internal AI unavailable")
            report=m.run("risk","qwen2.5:0.5b",Path(td)/"failed.json",llm=reject)
            self.assertEqual(report["model_calls_attempted"],0)
            self.assertTrue(all(t["quality_status"]=="MODEL_CALL_FAILED"
                                for r in report["rounds"] for t in r["participants"]))
            self.assertFalse(report["publication_allowed"])

if __name__=="__main__":unittest.main()
