"""Offline parser tests: synthetic fixture strings never claimed as market data."""
import datetime as dt
import importlib.util
from pathlib import Path
import unittest
from unittest.mock import patch
from zoneinfo import ZoneInfo

p = Path(__file__).with_name("bvb_index_probe.py")
spec = importlib.util.spec_from_file_location("bvb_index_probe", p)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

def fixture(symbol):
    # Mixed BVB namespace variants and a foreign symbol must be handled safely.
    rows = "".join(
        f'<TypeIndicesSeries><Code>{symbol}</Code><LastUpdateTime>'
        f'2026-10-23T13:0{n}:00</LastUpdateTime><CurrentValue>'
        f'{100+n/10}</CurrentValue></TypeIndicesSeries>'
        for n in range(3))
    return ('<ArrayOfTypeIndicesSeries xmlns="www.bvb.ro">' + rows +
            '<TypeIndicesSeries><Code>OTHER</Code><LastUpdateTime>2026-10-23T13:05:00'
            '</LastUpdateTime><CurrentValue>9999</CurrentValue></TypeIndicesSeries>'
            '</ArrayOfTypeIndicesSeries>').encode()


def quote_fixture(symbol):
    return ('<ArrayOfTypeIndices><TypeIndices>'
            f'<Code>{symbol}</Code><LastUpdateTime>2026-10-23T13:02:00</LastUpdateTime>'
            '<CurrentValue>100.2</CurrentValue><NetChange>0.2</NetChange>'
            '<PrcChange>0.2</PrcChange></TypeIndices></ArrayOfTypeIndices>').encode()

class Parser(unittest.TestCase):
    def test_all_three_codes_separate_and_sorted(self):
        for symbol in m.SYMBOLS:
            rows = m.parse_series(fixture(symbol), symbol)
            self.assertEqual(len(rows), 3)
            self.assertEqual([x["price"] for x in rows], [100, 100.1, 100.2])

    def test_never_mislabel_a_foreign_series(self):
        self.assertEqual(m.parse_series(fixture("BET"), "BET-NG"), [])
        with self.assertRaises(ValueError):
            m.parse_series(fixture("BET"), "QQQ")

    def test_soap_fault_blocks(self):
        with self.assertRaisesRegex(ValueError, "soap_fault"):
            m.parse_series(b'<Envelope><Fault>denied</Fault></Envelope>', "BET")

    def test_no_invented_points_from_getindex_quote(self):
        sample = b'<TypeIndices><Code>BET</Code><LastUpdateTime>2026-10-23T13:00:00</LastUpdateTime><CurrentValue>100</CurrentValue></TypeIndices>'
        self.assertEqual(len(m.parse_series(sample, "BET")), 1)
        with patch.object(m, "request_service", return_value=sample):
            x = m.check("BET", now=dt.datetime(2026,10,23,13,2,tzinfo=ZoneInfo("Europe/Bucharest")))
        self.assertEqual(x["status"], "NOT_VERIFIED")
        self.assertEqual(x["error"], "insufficient_matching_points")

    def test_history_is_not_claimed_real_time(self):
        with patch.object(m, "request_service", side_effect=lambda symbol, operation="IndicesDataSeries": quote_fixture(symbol) if operation=="GetIndex" else fixture(symbol)):
            x = m.check("BET", now=dt.datetime(2026,10,25,12,0,tzinfo=ZoneInfo("Europe/Bucharest")))
        self.assertEqual(x["status"], "HISTORICAL_SERIES_OK")

    def test_3_of_3_gate_cannot_pass_with_two(self):
        good = fixture("BET")
        def response(symbol, operation="IndicesDataSeries"):
            if operation == "GetIndex":
                return quote_fixture(symbol)
            return fixture(symbol) if symbol != "BET-FI" else b'<message>Access denied</message>'
        with patch.object(m, "request_service", side_effect=response):
            outcomes = [m.check(s) for s in m.SYMBOLS]
        self.assertEqual(len([x for x in outcomes if x["status"] in
                              ("HISTORICAL_SERIES_OK","RECENT_SERIES_AVAILABLE")]), 2)

if __name__=="__main__":
    unittest.main()
