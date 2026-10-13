"""Offline tests for the read-only Yahoo Finance symbol metadata adapter."""
import json
import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import trading_symbol_lookup as lookup


def response_for(payload):
    response = MagicMock()
    response.__enter__.return_value.read.return_value = json.dumps(payload).encode()
    return response


def search_payload(items):
    return {"quotes": items}


def chart_payload(symbol, name, exchange, currency, price=123.45):
    return {"chart": {"result": [{"meta": {
        "symbol": symbol, "longName": name, "fullExchangeName": exchange,
        "currency": currency, "instrumentType": "EQUITY",
        "regularMarketPrice": price, "regularMarketTime": 1_790_000_000,
    }}], "error": None}}


class TradingSymbolLookupTests(unittest.TestCase):
    def setUp(self):
        with lookup._lock:
            lookup._cache.clear()

    def test_returns_exact_matched_metadata_and_reference_quote(self):
        search = search_payload([{"symbol": "AAPL", "quoteType": "EQUITY", "exchDisp": "NASDAQ"}])
        chart = chart_payload("AAPL", "Apple Inc.", "NasdaqGS", "USD")
        with patch.object(lookup, "urlopen", side_effect=[response_for(search), response_for(chart)]) as mocked:
            result = lookup.lookup_symbol(" aapl ")
        self.assertEqual(result["symbol"], "AAPL")
        self.assertEqual(result["name"], "Apple Inc.")
        self.assertEqual(result["market"], "NasdaqGS")
        self.assertEqual(result["currency"], "USD")
        self.assertEqual(result["reference_price"], 123.45)
        self.assertEqual(result["provider"], "Yahoo Finance")
        self.assertTrue(result["price_is_reference_only"])
        self.assertEqual(mocked.call_count, 2)
        self.assertIn("query1.finance.yahoo.com/v8/finance/chart/AAPL", mocked.call_args.args[0].full_url)

    def test_maps_unique_unsuffixed_bvb_code_to_ro_listing(self):
        search = search_payload([
            {"symbol": "SNPS", "quoteType": "EQUITY", "exchDisp": "NASDAQ"},
            {"symbol": "SNP.RO", "quoteType": "EQUITY", "exchDisp": "BVB"},
        ])
        chart = chart_payload("SNP.RO", "OMV Petrom S.A.", "BVB", "RON", 1.24)
        with patch.object(lookup, "urlopen", side_effect=[response_for(search), response_for(chart)]) as mocked:
            result = lookup.lookup_symbol("SNP")
        self.assertEqual(result["symbol"], "SNP.RO")
        self.assertEqual(result["name"], "OMV Petrom S.A.")
        self.assertEqual(result["market"], "BVB")
        self.assertEqual(result["currency"], "RON")
        self.assertIn("/chart/SNP.RO?", mocked.call_args.args[0].full_url)

    def test_rejects_unsafe_symbol_before_network_access(self):
        with patch.object(lookup, "urlopen") as mocked:
            with self.assertRaises(ValueError):
                lookup.lookup_symbol("https://example.com")
            mocked.assert_not_called()

    def test_rejects_mismatched_symbol_response(self):
        search = search_payload([{"symbol": "AAPL", "quoteType": "EQUITY"}])
        chart = chart_payload("MSFT", "Microsoft Corporation", "NasdaqGS", "USD")
        with patch.object(lookup, "urlopen", side_effect=[response_for(search), response_for(chart)]):
            with self.assertRaises(lookup.SymbolLookupError):
                lookup.lookup_symbol("AAPL")

    def test_caches_successful_metadata(self):
        search = search_payload([{"symbol": "AAPL", "quoteType": "EQUITY"}])
        chart = chart_payload("AAPL", "Apple Inc.", "NasdaqGS", "USD")
        with patch.object(lookup, "urlopen", side_effect=[response_for(search), response_for(chart)]) as mocked:
            first = lookup.lookup_symbol("AAPL")
            second = lookup.lookup_symbol("AAPL")
        self.assertEqual(first, second)
        self.assertEqual(mocked.call_count, 2)


if __name__ == "__main__":
    unittest.main()
