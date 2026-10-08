"""Offline interface and safety tests; no network, no secrets."""
import importlib.util
import tempfile
import unittest
from pathlib import Path

SRC = Path(__file__).resolve().parents[1] / "scripts" / "engine.py"
SPEC = importlib.util.spec_from_file_location("ro_engine", SRC)
e = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(e)


class IntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.bank = e.registry()

    def test_exact_65(self):
        self.assertEqual(len(self.bank), 65)
        self.assertEqual(sorted(self.bank), [f"{i:02d}" for i in range(1,66)])

    def test_source_profiles_untouched(self):
        self.assertTrue(all("source_profile" in p and "language_dna" in p for p in self.bank.values()))

    def test_panel_and_67_slots(self):
        p = e.panel("Riscuri și educație", size=5)
        self.assertFalse(p["publication_allowed"])
        self.assertEqual(p["total_role_slots"],67)
        self.assertEqual(len(set(x["id"] for x in p["participants"])), 5)

    def test_all_65_over_13_batches(self):
        ids = [p["id"] for i in range(13) for p in e.panel("Test",i,5)["participants"]]
        self.assertEqual(len(set(ids)), 65)

    def test_determinism(self):
        self.assertEqual(e.panel("Test",2,5), e.panel("Test",2,5))

    def test_invalid_role_and_size(self):
        for bad in ("66", "real_customer", "+40123456789", "", "0", None):
            with self.subTest(bad=bad), self.assertRaises(ValueError):e.namespace(bad)
        with self.assertRaises(ValueError):e.panel("",0,5)
        with self.assertRaises(ValueError):e.panel("anything",0,9)

    def test_memory_isolation(self):
        with tempfile.TemporaryDirectory() as td:
            m = e.LocalMemory(Path(td)/"scratch.db")
            m.add("01", "A is cautious")
            m.add("02", "B likes bonds")
            self.assertEqual(m.search("01"),["A is cautious"])
            self.assertEqual(m.search("02"),["B likes bonds"])
            m.close()

    def test_mem0_v3_filters(self):
        class Stub:
            def add(self, *a, **kw): return kw
            def search(self, *a, **kw):
                self.last = kw
                return {"results": [{"user_id":"simulation_ro_persona_01", "metadata":{"source":"internal_simulation"}},
                                    {"user_id":"simulation_ro_persona_02", "metadata":{"source":"internal_simulation"}}]}
        s=Stub();m=e.Mem0ScopedMemory(s)
        self.assertEqual(len(m.search("01", "idea")),1)
        self.assertEqual(s.last["filters"],{"user_id":"simulation_ro_persona_01"})

    def test_course_weekdays(self):
        expected=["technical","investment_philosophy","technical","investment_philosophy","technical","no_regular_class","no_regular_class"]
        for d,name in zip(range(12,19),expected):
            res=e.course_for_date(f"2026-10-{d:02d}")
            self.assertEqual(res["course"],name)
            self.assertFalse(res["professor_morning"])
            self.assertFalse(res["course_afternoon"])

    def test_dst_malaysia_conversion(self):
        summer = e.course_for_date("2026-10-23")
        winter = e.course_for_date("2026-10-26")
        self.assertEqual(summer["malaysia_start"][11:16], "01:20")
        self.assertEqual(winter["malaysia_start"][11:16], "02:20")

    def test_no_live_without_ack(self):
        with self.assertRaises(PermissionError):e.run_tinytroupe(e.panel("Safety"))

    def test_crewai_requires_approval(self):
        with self.assertRaises(RuntimeError):e.review_with_crewai("Some report")

if __name__ == "__main__":unittest.main()
