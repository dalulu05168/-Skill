"""Tests for local image composition, trade-ledger linkage, and stock lookup."""
import json
import sys
import tempfile
import threading
import unittest
from http.server import ThreadingHTTPServer
from pathlib import Path
from urllib.request import urlopen
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import finance_skill_api
from finance_skill_api import make_handler
from image_editor_ui import PAGE


class ImageEditorModuleTests(unittest.TestCase):
    def test_local_editor_uses_centered_fields_and_same_origin_trade_ledger(self):
        self.assertIn('id="templateFile"', PAGE)
        self.assertIn("/api/trading/sim/state", PAGE)
        self.assertIn("buyTime", PAGE)
        self.assertIn("sellTime", PAGE)
        self.assertIn("pointermove", PAGE)
        self.assertIn("toDataURL('image/png')", PAGE)
        self.assertIn("Europe/Bucharest", PAGE)
        self.assertIn("仅供内部教学记录", PAGE)
        self.assertNotIn("<iframe", PAGE)
        self.assertNotIn("https://trade.sasakic.cc", PAGE)
        self.assertIn("x:50,y:20", PAGE)
        self.assertIn("align:'center'", PAGE)

    def test_internal_routes_allow_local_image_editor_and_query_prefill(self):
        with tempfile.TemporaryDirectory() as temp:
            folder = Path(temp)
            with ThreadingHTTPServer(("127.0.0.1", 0), make_handler(folder)) as server:
                th = threading.Thread(target=server.serve_forever, daemon=True)
                th.start()
                base = f"http://127.0.0.1:{server.server_port}"
                try:
                    for route in ("/", "/trading", "/skill", "/image-editor", "/image-editor?holding_id=hd-example"):
                        with self.subTest(route=route), urlopen(base + route) as resp:
                            self.assertEqual(resp.status, 200)
                            page = resp.read().decode("utf-8")
                            self.assertIn('href="/image-editor"', page)
                            if route.startswith("/image-editor"):
                                self.assertIn('id="templateFile"', page)
                    with urlopen(base + "/image-editor") as resp:
                        csp = resp.headers.get("Content-Security-Policy", "")
                        self.assertIn("script-src 'unsafe-inline'", csp)
                        self.assertIn("img-src 'self' data: blob:", csp)
                        self.assertIn("connect-src 'self'", csp)
                        self.assertNotIn("frame-src", csp)
                        self.assertEqual(resp.headers.get("Referrer-Policy"), "no-referrer")
                        self.assertEqual(resp.headers.get("Cache-Control"), "no-store")
                    with urlopen(base + "/trade-platform") as resp:
                        self.assertEqual(resp.status, 200)
                        self.assertEqual(resp.url, base + "/image-editor")
                    with urlopen(base + "/api/trading/people") as resp:
                        self.assertEqual(json.load(resp)["count"], 65)
                    self.assertEqual(list(folder.iterdir()), [])
                finally:
                    server.shutdown()
                    th.join(timeout=5)

    def test_symbol_lookup_route_is_read_only_and_passes_query_code(self):
        expected = {
            "symbol": "AAPL", "name": "Apple Inc.", "market": "NasdaqGS",
            "currency": "USD", "provider": "Yahoo Finance", "price_is_reference_only": True,
        }
        with tempfile.TemporaryDirectory() as temp:
            with ThreadingHTTPServer(("127.0.0.1", 0), make_handler(Path(temp))) as server:
                th = threading.Thread(target=server.serve_forever, daemon=True)
                th.start()
                try:
                    with patch.object(finance_skill_api, "lookup_symbol", return_value=expected) as lookup:
                        with urlopen(f"http://127.0.0.1:{server.server_port}/api/trading/symbol-lookup?symbol=AAPL") as resp:
                            self.assertEqual(json.load(resp), expected)
                        lookup.assert_called_once_with("AAPL")
                finally:
                    server.shutdown()
                    th.join(timeout=5)


if __name__ == "__main__":
    unittest.main()
