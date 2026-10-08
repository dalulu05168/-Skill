"""Offline tests for three-round launcher. Uses injected fake model; no LLM calls."""
import importlib.util
import json
import tempfile
import unittest
import sys
from pathlib import Path

PATH = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(PATH))
spec = importlib.util.spec_from_file_location("ro_live_batch", PATH / "live_batch.py")
batch = importlib.util.module_from_spec(spec)
spec.loader.exec_module(batch)


def fake_success(plan, *, acknowledged, steps):
    assert acknowledged is True
    assert len(plan["participants"]) == 5
    return {"status":"internal_only", "publication_allowed":False, "trace":[]}


class ThreeRoundsTests(unittest.TestCase):
    def test_must_acknowledge(self):
        with tempfile.TemporaryDirectory() as td:
            with self.assertRaises(PermissionError):
                batch.run_three("riscul",Path(td)/"run",readiness=lambda:{"real_llm_test_possible":True})

    def test_absent_credentials_fail_closed(self):
        with tempfile.TemporaryDirectory() as td:
            with self.assertRaises(RuntimeError):
                batch.run_three("riscul",Path(td)/"run",consent=True,
                                readiness=lambda:{"real_llm_test_possible":False},generate=fake_success)
            self.assertFalse((Path(td)/"run").exists())

    def test_three_fake_model_runs(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td)/"run"
            result=batch.run_three("diversificarea",path,consent=True,
                readiness=lambda:{"real_llm_test_possible":True},generate=fake_success)
            self.assertTrue(result["all_three_completed"])
            self.assertEqual(result["actual_runs_completed"],3)
            self.assertEqual(len(list(path.glob("rehearsal_round_*.json"))),3)
            selections=[]
            for n in (1,2,3):
                j=json.loads((path/f"rehearsal_round_{n}.json").read_text(encoding="utf-8"))
                self.assertFalse(j["publication_allowed"])
                selections.extend(j["selected_persona_ids"])
            self.assertEqual(len(set(selections)),15)
            self.assertEqual(json.loads((path/"run_summary.json").read_text())["review_status"],
                             "HOLD_FOR_HUMAN_REVIEW")

    def test_prevent_existing_files_from_overwrite(self):
        with tempfile.TemporaryDirectory() as td:
            path=Path(td)/"run";path.mkdir()
            (path/"old.txt").write_text("preserve")
            with self.assertRaises(FileExistsError):
                batch.run_three("test",path,consent=True,
                    readiness=lambda:{"real_llm_test_possible":True},generate=fake_success)
            self.assertEqual((path/"old.txt").read_text(),"preserve")

    def test_reject_unsafe_response(self):
        with tempfile.TemporaryDirectory() as td:
            def unsafe(*args,**kwargs):
                return {"status":"ready_to_send","publication_allowed":True}
            path=Path(td)/"run"
            report=batch.run_three("test",path,consent=True,
                readiness=lambda:{"real_llm_test_possible":True},generate=unsafe)
            self.assertEqual(report["actual_runs_completed"],0)
            self.assertFalse(report["all_three_completed"])
            self.assertEqual(report["review_status"],"INCOMPLETE_DO_NOT_USE")
            self.assertEqual(report["rounds"][0]["error_type"],"ValueError")
            self.assertFalse(list(path.glob("rehearsal_round_*.json")))

    def test_reject_invalid_size(self):
        with tempfile.TemporaryDirectory() as td:
            with self.assertRaises(ValueError):
                batch.run_three("test",Path(td)/"run",consent=True,size=65,
                    readiness=lambda:{"real_llm_test_possible":True},generate=fake_success)


if __name__ == "__main__":
    unittest.main()
