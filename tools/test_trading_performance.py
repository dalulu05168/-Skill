import unittest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from trading_performance import summarize_performance


class TradingPerformanceTests(unittest.TestCase):
    def test_daily_return_is_weighted_and_daily_rates_are_summed_not_compounded(self):
        state = {
            "holdings": [
                {"id": "h1", "person_id": "01", "symbol": "AAA", "name": "Alpha",
                 "currency": "USD", "quantity": 10, "buy_price": 10, "sold_price": 11,
                 "buy_at": "2026-10-10T10:00:00+03:00", "sold_at": "2026-10-12T10:00:00+03:00", "status": "sold"},
                {"id": "h2", "person_id": "02", "symbol": "BBB", "name": "Beta",
                 "currency": "USD", "quantity": 10, "buy_price": 10, "sold_price": 9.5,
                 "buy_at": "2026-10-10T10:00:00+03:00", "sold_at": "2026-10-12T12:00:00+03:00", "status": "sold"},
                {"id": "h3", "person_id": "03", "symbol": "CCC", "name": "Gamma",
                 "currency": "USD", "quantity": 10, "buy_price": 10, "sold_price": 11,
                 "buy_at": "2026-10-11T10:00:00+03:00", "sold_at": "2026-10-13T10:00:00+03:00", "status": "sold"},
                {"id": "h4", "person_id": "04", "symbol": "DDD", "name": "Delta",
                 "currency": "USD", "quantity": 10, "buy_price": 10, "status": "holding"},
            ],
            "transactions": [],
        }
        result = summarize_performance(state)
        self.assertEqual(len(result["daily_returns"]), 2)
        self.assertAlmostEqual(result["daily_returns"][0]["return_pct"], 2.5)
        self.assertAlmostEqual(result["daily_returns"][1]["return_pct"], 10.0)
        self.assertAlmostEqual(result["total_percent"], 12.5)
        open_record = next(r for r in result["records"] if r["symbol"] == "DDD")
        self.assertEqual(open_record["status"], "holding")
        self.assertIsNone(open_record["roi_pct"])
        self.assertFalse(result["unrealized_pnl_included"])

    def test_uses_transaction_values_when_holding_fields_are_missing(self):
        state = {
            "holdings": [{"id": "h1", "person_id": "01", "symbol": "AAA", "quantity": 2,
                          "status": "sold", "currency": "USD"}],
            "transactions": [
                {"holding_id": "h1", "type": "buy", "unit_price": 4, "created_at": "2026-10-10T10:00:00+03:00"},
                {"holding_id": "h1", "type": "sell", "unit_price": 5, "created_at": "2026-10-11T10:00:00+03:00"},
            ],
        }
        result = summarize_performance(state)
        self.assertEqual(result["records"][0]["buy_price"], 4)
        self.assertEqual(result["records"][0]["sell_price"], 5)
        self.assertAlmostEqual(result["total_percent"], 25)

    def test_daily_returns_are_separated_by_currency(self):
        state = {"holdings": [
            {"id": "usd", "person_id": "01", "symbol": "AAA", "quantity": 1,
             "buy_price": 100, "sold_price": 110, "currency": "USD", "status": "sold",
             "sold_at": "2026-10-12T10:00:00+03:00"},
            {"id": "ron", "person_id": "02", "symbol": "BBB", "quantity": 1,
             "buy_price": 100, "sold_price": 90, "currency": "RON", "status": "sold",
             "sold_at": "2026-10-12T12:00:00+03:00"},
        ], "transactions": []}
        result = summarize_performance(state)
        self.assertEqual({(x["date"], x["currency"]) for x in result["daily_returns"]},
                         {("2026-10-12", "USD"), ("2026-10-12", "RON")})
        self.assertAlmostEqual(result["total_percent"], 0)


if __name__ == "__main__":
    unittest.main()
