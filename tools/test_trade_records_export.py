"""Acceptance of actual manual participant-record writes and CSV attachment export.

No market feeds, brokerage execution, invented rows or production data are used.
"""
import csv
import io
import json
import sys
import tempfile
import threading
import unittest
from http.server import ThreadingHTTPServer
from pathlib import Path
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent))
import finance_skill_api as api
from trading_65 import fresh_state, read_state, write_state
from trade_records import add_record, csv_export, FIELDS

PROFILES = {
    f"{i:02d}": {
        "character_id": f"{i:02d}",
        "identity_extension": {"姓名": f"参与成员{i}"},
        "source_profile": {"性别": "男", "年龄": 45, "学员资历": "新", "工作_职业": "测试"},
    } for i in range(1, 66)
}


def record(pid="01", date="2026-10-11", symbol="TLV", direction="buy", note="已登记"):
    return {
        "person_id": pid, "trade_type": direction, "trade_date": date,
        "symbol": symbol, "name": "股票教学记录", "market": "BVB",
        "quantity": 12, "unit_price": 20.5, "currency": "RON",
        "note": note, "reference": "external-ref-001",
    }


def rows(data):
    self_bom = data.decode("utf-8-sig")
    return list(csv.DictReader(io.StringIO(self_bom)))


class ManualTradeRecordTests(unittest.TestCase):
    def test_record_appends_without_changing_holdings_or_inventing_executions(self):
        state = fresh_state()
        result = add_record(state, PROFILES, record())
        self.assertEqual(state["revision"], 1)
        self.assertEqual(state["holdings"], [])
        self.assertEqual(state["recommendations"], [])
        self.assertEqual(len(state["transactions"]), 1)
        self.assertEqual(result["record"]["type"], "buy")
        self.assertEqual(result["record"]["record_origin"], "manual-entry")
        self.assertFalse(result["record"]["execution_verified"])
        self.assertTrue(result["record"]["simulation_only"])
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "trading-65.json"
            write_state(path, state)
            self.assertEqual(read_state(path)["transactions"], state["transactions"])

    def test_csv_filters_person_direction_and_date_and_has_no_fake_rows(self):
        state = fresh_state()
        x = record()
        add_record(state, PROFILES, x)
        other = record(pid="02", date="2026-10-10", direction="sell")
        add_record(state, PROFILES, other)
        one = csv_export(state, PROFILES, person_id="01", start_date="2026-10-11",
                         end_date="2026-10-11", trade_type="buy")
        values = rows(one.encode("utf-8"))
        self.assertEqual(len(values), 1)
        self.assertEqual(values[0]["参与人员编号"], "01")
        self.assertEqual(values[0]["参与人员姓名"], "参与成员1")
        self.assertEqual(values[0]["股票代码"], "TLV")
        self.assertEqual(values[0]["交易日期"], "2026-10-11")
        self.assertEqual(values[0]["记录金额"], "246.0")
        self.assertEqual(values[0]["执行已核验"], "否")
        self.assertEqual(values[0]["教学模拟"], "是")
        self.assertEqual(len(rows(csv_export(state, PROFILES, person_id="03").encode())), 0)
        self.assertEqual(len(rows(csv_export(fresh_state(), PROFILES).encode())), 0)
        with self.assertRaises(ValueError):
            csv_export(state, PROFILES, start_date="2026-10-12", end_date="2026-10-11")
        with self.assertRaises(ValueError):
            csv_export(state, PROFILES, person_id="70")

    def test_invalid_records_do_not_mutate_state(self):
        cases = [
            {"person_id": "70"}, {"trade_date": "yesterday"},
            {"trade_type": "order_submit"}, {"quantity": -1},
            {"unit_price": "NaN"}, {"currency": "BTC"},
            {"symbol": ""}, {"note": "x" * 501},
        ]
        for override in cases:
            with self.subTest(override=override):
                state = fresh_state()
                with self.assertRaises(ValueError):
                    add_record(state, PROFILES, {**record(), **override})
                self.assertEqual(state["transactions"], [])
                self.assertEqual(state["revision"], 0)

    def test_spreadsheet_formula_payload_is_not_executable(self):
        state = fresh_state()
        add_record(state, PROFILES, record(symbol="=cmd()", note="@SUM(1,2)"))
        row = rows(csv_export(state, PROFILES).encode())[0]
        self.assertEqual(row["股票代码"], "'=CMD()")
        self.assertEqual(row["备注"], "'@SUM(1,2)")

    def test_existing_legacy_buy_record_included_in_export_without_rewriting(self):
        state = fresh_state()
        state["offers"].append({"id":"of-legacy","symbol":"SNP","name":"旧计划",
                                "market":"BVB","currency":"RON"})
        state["holdings"].append({"id":"hd-legacy","person_id":"01","offer_id":"of-legacy",
                                  "symbol":"SNP","name":"旧计划","market":"BVB","currency":"RON",
                                  "status":"holding","quantity":3,"buy_price":10})
        state["transactions"].append({
            "id":"tx-legacy","type":"buy","person_id":"01","offer_id":"of-legacy",
            "holding_id":"hd-legacy","created_at":"2026-10-11T10:00:00+00:00",
            "quantity":3,"unit_price":10,"currency":"RON","simulation_only":True})
        before=json.dumps(state, sort_keys=True)
        row=rows(csv_export(state,PROFILES).encode())[0]
        self.assertEqual(row["股票代码"],"SNP")
        self.assertEqual(row["记录金额"],"30")
        self.assertEqual(row["录入来源"],"既有模拟交易流程")
        self.assertEqual(json.dumps(state,sort_keys=True),before)

    def test_real_http_save_download_auth_scope_and_validation(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder)
            with patch.object(api, "load_profiles", return_value=PROFILES):
                with ThreadingHTTPServer(("127.0.0.1",0),api.make_handler(path)) as server:
                    t = threading.Thread(target=server.serve_forever,daemon=True)
                    t.start()
                    base=f"http://127.0.0.1:{server.server_port}"
                    def post(payload, origin=None):
                        req=Request(base+"/api/trading/records/add",method="POST",
                            data=json.dumps(payload).encode("utf-8"),
                            headers={"Content-Type":"application/json",
                                     "Origin":origin or base})
                        try:
                            with urlopen(req,timeout=6) as res:
                                return res.status, json.loads(res.read())
                        except HTTPError as e:
                            return e.code, json.loads(e.read())
                    try:
                        with urlopen(base+"/trading") as res:
                            page=res.read().decode("utf-8")
                        self.assertIn('id="trade-record-save"',page)
                        self.assertIn('id="trade-export-csv"',page)
                        self.assertFalse((path/"trading-65.json").exists())
                        url=base+"/api/trading/records/export.csv"
                        with urlopen(url) as res:
                            self.assertEqual(res.status,200)
                            self.assertIn("attachment",res.headers["Content-Disposition"])
                            self.assertEqual(rows(res.read()),[])
                        self.assertFalse((path/"trading-65.json").exists())
                        status,denied=post(record(),origin="http://example.org")
                        self.assertEqual(status,403)
                        self.assertFalse((path/"trading-65.json").exists())
                        status,fail=post({**record(),"quantity":0})
                        self.assertEqual(status,400)
                        self.assertFalse((path/"trading-65.json").exists())
                        status,created=post(record())
                        self.assertEqual(status,200)
                        self.assertFalse(created["actual_execution_verified"])
                        self.assertEqual(created["revision"],1)
                        saved=json.loads((path/"trading-65.json").read_text(encoding="utf-8"))
                        self.assertEqual(len(saved["transactions"]),1)
                        self.assertEqual(saved["holdings"],[])
                        uri=url+"?"+urlencode({"person_id":"01","start_date":"2026-10-11",
                                               "end_date":"2026-10-11","trade_type":"buy"})
                        with urlopen(uri) as response:
                            csv_body=response.read()
                            self.assertEqual(response.status,200)
                            self.assertEqual(response.headers["Cache-Control"],"no-store")
                        values=rows(csv_body)
                        self.assertEqual(len(values),1)
                        self.assertEqual(values[0]["参与人员编号"],"01")
                        self.assertEqual(values[0]["记录编号"],created["result"]["record"]["id"])
                        with self.assertRaises(HTTPError) as invalid:
                            urlopen(url+"?"+urlencode({"person_id":"99"}))
                        self.assertEqual(invalid.exception.code,400)
                    finally:
                        server.shutdown()
                        t.join(timeout=4)


if __name__ == "__main__":
    unittest.main()
