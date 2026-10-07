"""V2 deterministic unit/integration tests; all numbers are synthetic."""
import copy
import json
import subprocess
import sys
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from rsi_core.common import DataError, timestamp, web_url
from rsi_core.quality import audit_observations
from rsi_core.bet import analyze_bet
from rsi_core.events import radar
from rsi_core.professor import generate_lesson
from rsi_core.storage import History

FIX = ROOT / "examples/v2"
REGISTRY = json.loads((ROOT / "config/source-registry.json").read_text())
CLOCK = datetime(2026, 9, 8, 13, 0, tzinfo=timezone.utc)


def load(name):
    return json.loads((FIX / name).read_text(encoding="utf-8"))


class QualityTest(unittest.TestCase):
    def setUp(self): self.input = load("observations.synthetic.json")
    def audit(self): return audit_observations(self.input, REGISTRY, now=CLOCK)
    def test_valid_metadata(self): self.assertEqual(self.audit()["gate"], "pass")
    def test_empty_fails(self):
        self.input["observations"] = []
        self.assertEqual(self.audit()["gate"], "fail")
    def test_bvb_bare_alias(self):
        self.input["observations"][0]["source_url"] = "https://bvb.ro/FinancialInstruments/Indices/Overview"
        self.assertEqual(self.audit()["gate"], "pass")
    def test_unlisted_subdomain_fails(self):
        self.input["observations"][0]["source_url"] = "https://fake.www.bvb.ro/x"
        self.assertEqual(self.audit()["gate"], "fail")
    def test_missing_url(self):
        del self.input["observations"][0]["source_url"]
        self.assertEqual(self.audit()["gate"], "fail")
    def test_unregistered_source(self):
        self.input["observations"][0]["source_id"] = "FAKE"
        self.assertEqual(self.audit()["gate"], "fail")
    def test_domain_mismatch(self):
        self.input["observations"][0]["source_url"] = "https://www.ecb.europa.eu/x"
        self.assertEqual(self.audit()["gate"], "fail")
    def test_future_time(self):
        self.input["observations"][0]["observed_at"] = "2026-10-08T12:30:00+03:00"
        self.assertEqual(self.audit()["gate"], "fail")
    def test_wrong_dst(self):
        self.input["observations"][0]["observed_at"] = "2026-09-08T12:30:00+02:00"
        self.assertEqual(self.audit()["gate"], "fail")
    def test_conflict(self):
        x = copy.deepcopy(self.input["observations"][0]);x.update({"value":104,"source_id":"ECB_FX","source_url":"https://www.ecb.europa.eu/stats/"})
        self.input["observations"].append(x)
        self.assertIn("SOURCE_CONFLICT",[f["code"] for f in self.audit()["findings"]])
    def test_same_source_internal_conflict(self):
        x = copy.deepcopy(self.input["observations"][0]);x["value"] = 110
        self.input["observations"].append(x)
        self.assertIn("INTERNAL_SOURCE_CONFLICT",[f["code"] for f in self.audit()["findings"]])
    def test_stale_warning(self):
        self.assertEqual(audit_observations(self.input, REGISTRY, now=datetime(2026,10,2,tzinfo=timezone.utc))["gate"], "pass_with_warnings")
    def test_realtime_flag_warning(self):
        self.input["observations"][0]["delay_status"] = "realtime"
        self.assertIn("REALTIME_UNATTESTED",[f["code"] for f in self.audit()["findings"]])
    def test_boolean_value_rejected(self):
        self.input["observations"][0]["value"] = True
        self.assertEqual(self.audit()["gate"], "fail")
    def test_local_url_rejected(self):
        with self.assertRaises(DataError): web_url("https://127.0.0.1/x")
    def test_non_public_cidr_rejected(self):
        with self.assertRaises(DataError): web_url("https://192.168.1.2/x")
    def test_dst_winter_valid(self):
        self.assertEqual(timestamp("2026-12-08T08:00:00+02:00").hour,8)


class BETTest(unittest.TestCase):
    def setUp(self):self.input=load("bet.synthetic.json")
    def test_attribution(self):
        x=analyze_bet(self.input)
        self.assertAlmostEqual(x["estimated_total_return_pct"], .9)
        self.assertEqual((x["advancers"],x["decliners"],x["unchanged"]),(1,1,1))
        self.assertEqual(x["top_positive"][0]["ticker"],"A")
        self.assertTrue(x["qualified_full_index_attribution"])
    def test_stale_weights_rejected(self):
        self.input["weights_as_of"]="2025-01-02T17:00:00+02:00"
        with self.assertRaises(DataError): analyze_bet(self.input)
    def test_missing_session_unqualified(self):
        del self.input["previous_trading_close_at"]
        self.assertFalse(analyze_bet(self.input)["qualified_full_index_attribution"])
    def test_wrong_return_baseline_rejected(self):
        self.input["returns_baseline_at"]="2026-09-04T17:50:00+03:00"
        with self.assertRaises(DataError): analyze_bet(self.input)
    def test_missing_roster_unqualified(self):
        del self.input["official_roster"]
        self.assertFalse(analyze_bet(self.input)["qualified_full_index_attribution"])
    def test_wrong_roster_rejected(self):
        self.input["official_roster"]=["A","B","D"]
        with self.assertRaises(DataError): analyze_bet(self.input)
    def test_missing_member_partial(self):
        self.input["complete_roster"]=False
        self.input["constituents"].pop()
        x=analyze_bet(self.input)
        self.assertIsNone(x["estimated_total_return_pct"])
        self.assertFalse(x["complete"])
    def test_false_complete_rejected(self):
        self.input["constituents"].pop()
        with self.assertRaises(DataError):analyze_bet(self.input)
    def test_double_ticker_rejected(self):
        self.input["constituents"].append(copy.deepcopy(self.input["constituents"][0]))
        with self.assertRaises(DataError):analyze_bet(self.input)
    def test_bettr_rejected(self):
        self.input["index"]="BET-TR"
        with self.assertRaises(DataError):analyze_bet(self.input)
    def test_other_weights_approx(self):
        self.input["weights_basis"]="other"
        self.assertFalse(analyze_bet(self.input)["qualified_full_index_attribution"])
    def test_conflicting_weights_rejected(self):
        self.input["constituents"][0]["weight_pct"]=99
        with self.assertRaises(DataError):analyze_bet(self.input)
    def test_no_positive(self):
        self.input["constituents"][0]["return_pct"]=-2
        x=analyze_bet(self.input)
        self.assertIsNone(x["top_3_share_of_positive_contribution_pct"])


class EventTest(unittest.TestCase):
    def setUp(self):self.input=load("events.synthetic.json")
    def test_plain_scoring(self):
        self.assertEqual(radar(self.input,as_of=CLOCK)["events"][0]["change_state"],"not_tracked")
    def test_future_publication_rejected(self):
        self.input["events"][0]["published_at"]="2027-09-08T11:00:00+03:00"
        with self.assertRaises(DataError):radar(self.input,as_of=CLOCK)
    def test_invalid_category(self):
        self.input["events"][0]["category"]="buy_now"
        with self.assertRaises(DataError):radar(self.input,as_of=CLOCK)
    def test_duplicate_id(self):
        self.input["events"].append(copy.deepcopy(self.input["events"][0]))
        with self.assertRaises(DataError):radar(self.input,as_of=CLOCK)
    def test_invalid_batch_does_not_write(self):
        with tempfile.TemporaryDirectory() as t, History(Path(t)/"hist.db") as db:
            invalid=copy.deepcopy(self.input["events"][0])
            invalid["event_id"]="DEMO-INVALID"
            invalid["category"]="INVALID"
            self.input["events"].append(invalid)
            with self.assertRaises(DataError):radar(self.input,db,CLOCK)
            self.input["events"].pop()
            self.assertEqual(radar(self.input,db,CLOCK)["events"][0]["change_state"],"new")
    def test_dedup_lifecycle(self):
        with tempfile.TemporaryDirectory() as t, History(Path(t)/"hist.db") as db:
            self.assertEqual(radar(self.input,db,CLOCK)["events"][0]["change_state"],"new")
            self.assertEqual(radar(self.input,db,CLOCK)["events"][0]["change_state"],"unchanged")
            self.input["events"][0]["title"]="修订：假设政策调整"
            self.assertEqual(radar(self.input,db,CLOCK)["events"][0]["change_state"],"revised")


class ProfessorTest(unittest.TestCase):
    def setUp(self): self.input=load("professor.synthetic.json")
    def test_generate(self):
        memo=generate_lesson(self.input)
        self.assertIn("反面",memo) if False else self.assertIn("不成立",memo)
        self.assertIn("来源",memo)
        self.assertIn("有利情景",memo)
        self.assertIn("条件",memo)
    def test_no_facts(self):
        self.input["facts"]=[]
        with self.assertRaises(DataError):generate_lesson(self.input)
    def test_no_counterargument(self):
        self.input["counterarguments"]=[]
        with self.assertRaises(DataError):generate_lesson(self.input)
    def test_no_risk_scenario(self):
        del self.input["scenarios"]["adverse"]
        with self.assertRaises(DataError):generate_lesson(self.input)


class PersistenceTest(unittest.TestCase):
    def setUp(self): self.base=json.loads((ROOT/"tests/minimal_valid.json").read_text())
    def test_idempotent_and_immutable(self):
        with tempfile.TemporaryDirectory() as d, History(Path(d)/"history.sqlite") as h:
            self.assertEqual(h.save_report(self.base)["status"],"saved")
            self.assertEqual(h.save_report(self.base)["status"],"unchanged")
            other=copy.deepcopy(self.base);other["coverage_gaps"][0]["reason"]="UPDATED"
            with self.assertRaises(DataError):h.save_report(other)
    def test_previous_date(self):
        with tempfile.TemporaryDirectory() as d, History(Path(d)/"history.sqlite") as h:
            h.save_report(self.base)
            nxt=copy.deepcopy(self.base);nxt.update({"report_id":"RSI-20261008-1300","kind":"midday_1300","produced_at":"2026-10-08T13:00:00+03:00"})
            self.assertEqual(h.comparison(nxt)["previous_report_id"],self.base["report_id"])
    def test_dst_utc_history_sort(self):
        with tempfile.TemporaryDirectory() as d, History(Path(d)/"history.sqlite") as h:
            old=copy.deepcopy(self.base);old.update({"report_id":"RSI-20261024-1800","kind":"close_1800","produced_at":"2026-10-24T18:00:00+03:00"})
            new=copy.deepcopy(self.base);new.update({"report_id":"RSI-20261025-0800","kind":"morning_0800","produced_at":"2026-10-25T08:00:00+02:00"})
            h.save_report(old);h.save_report(new)
            self.assertEqual(h.previous()["report_id"],new["report_id"])


class CliTest(unittest.TestCase):
    def cmd(self,*a):
        return subprocess.run([sys.executable,str(ROOT/"scripts/rsi_v2.py"),*a],capture_output=True,text=True)
    def test_empty_audit_command(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/"empty.json";p.write_text('{"observations": []}')
            x=self.cmd("audit",str(p))
            self.assertEqual(x.returncode,1,x.stderr)
            self.assertEqual(json.loads(x.stdout)["gate"],"fail")
    def test_bet_command(self):
        x=self.cmd("bet",str(FIX/"bet.synthetic.json"))
        self.assertEqual(x.returncode,0,x.stderr)
        self.assertAlmostEqual(json.loads(x.stdout)["estimated_total_return_pct"],.9)
    def test_professor_command(self):
        x=self.cmd("professor",str(FIX/"professor.synthetic.json"))
        self.assertEqual(x.returncode,0,x.stderr)
    def test_audit_command(self):
        x=self.cmd("audit",str(FIX/"observations.synthetic.json"))
        self.assertEqual(x.returncode,0,x.stderr)
    def test_store_and_compare_commands(self):
        with tempfile.TemporaryDirectory() as d:
            f=str(ROOT/"tests/minimal_valid.json"); db=str(Path(d)/"a.sqlite")
            x=self.cmd("store",f,"--db",db)
            self.assertEqual(x.returncode,0,x.stderr)
            # A previous report isn't available for the same timestamp.
            y=self.cmd("compare",f,"--db",db)
            self.assertEqual(json.loads(y.stdout)["status"],"no_previous_report")


if __name__ == "__main__":unittest.main()
