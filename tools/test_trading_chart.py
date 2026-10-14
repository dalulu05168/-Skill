import unittest
import sys
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent))
import trading_chart
from trading_chart import ChartDataError, get_history


class TradingChartTests(unittest.TestCase):
    def setUp(self):
        with trading_chart._lock:
            trading_chart._cache.clear()
        self.instrument = {
            "symbol": "AAPL", "name": "Apple Inc.", "market": "NASDAQ",
            "currency": "USD", "provider": "Yahoo Finance",
        }
        self.payload = {
            "chart": {"result": [{
                "meta": {
                    "symbol": "AAPL", "longName": "Apple Inc.",
                    "fullExchangeName": "NasdaqGS", "currency": "USD",
                    "exchangeTimezoneName": "America/New_York",
                },
                "timestamp": [1791921600, 1792008000, 1792094400],
                "indicators": {"quote": [{
                    "open": [100, None, 102], "high": [105, None, 106],
                    "low": [99, None, 101], "close": [104, None, 105],
                }]},
            }], "error": None}
        }

    def test_parses_closing_prices_and_filters_missing_rows(self):
        with patch("trading_chart.lookup_symbol", return_value=self.instrument), patch(
            "trading_chart._json", return_value=self.payload
        ):
            result = get_history("AAPL", "1y")
        self.assertEqual(result["provider"], "Yahoo Finance")
        self.assertEqual(result["interval"], "1d")
        self.assertEqual(len(result["points"]), 2)
        self.assertEqual(result["points"][0]["value"], 104.0)
        self.assertIn("time", result["points"][0])

    def test_rejects_unapproved_range_before_network_lookup(self):
        with patch("trading_chart.lookup_symbol") as lookup:
            with self.assertRaises(ValueError):
                get_history("AAPL", "1m")
        lookup.assert_not_called()

    def test_refuses_a_mismatched_security_response(self):
        payload = {"chart": {"result": [{
            "meta": {"symbol": "MSFT", "exchangeTimezoneName": "UTC"},
            "timestamp": [1791921600],
            "indicators": {"quote": [{"close": [10]}]},
        }], "error": None}}
        with patch("trading_chart.lookup_symbol", return_value=self.instrument), patch(
            "trading_chart._json", return_value=payload
        ):
            with self.assertRaises(ChartDataError):
                get_history("AAPL", "6mo")

    def test_reports_empty_history(self):
        payload = {"chart": {"result": [{
            "meta": {"symbol": "AAPL", "exchangeTimezoneName": "UTC"},
            "timestamp": [1791921600],
            "indicators": {"quote": [{"close": [None]}]},
        }], "error": None}}
        with patch("trading_chart.lookup_symbol", return_value=self.instrument), patch(
            "trading_chart._json", return_value=payload
        ):
            with self.assertRaises(ChartDataError):
                get_history("AAPL", "5y")


if __name__ == "__main__":
    unittest.main()
