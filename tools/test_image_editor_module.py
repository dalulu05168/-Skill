"""Tests for local template composition, chart history and simulated-ledger linkage."""
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

IMAGE_EDITOR_SCRIPT = (ROOT / "tools" / "static" / "app" / "image-editor.js").read_text(encoding="utf-8")


class ImageEditorModuleTests(unittest.TestCase):
    def test_page_uses_local_templates_chart_library_and_performance_data(self):
        self.assertIn('id="templateMode"', PAGE)
        self.assertIn('id="templateFile"', PAGE)
        self.assertIn('id="saleDate"', PAGE)
        self.assertIn('id="sellReason"', PAGE)
        self.assertIn('/static/vendor/lightweight-charts-5.2.0.js', PAGE)
        self.assertIn('/static/app/image-editor.js', PAGE)
        self.assertIn("/api/trading/sim/performance", IMAGE_EDITOR_SCRIPT)
        self.assertIn('Yahoo Finance', PAGE)
        self.assertIn('TradingView Lightweight Charts', PAGE)
        self.assertNotIn('<iframe', PAGE)
        self.assertNotIn('https://trade.sasakic.cc', PAGE)

    def test_pages_static_assets_and_performance_route(self):
        with tempfile.TemporaryDirectory() as temp:
            folder = Path(temp)
            server = ThreadingHTTPServer(("127.0.0.1", 0), make_handler(folder))
            th = threading.Thread(target=server.serve_forever, daemon=True)
            th.start()
            base = f"http://127.0.0.1:{server.server_port}"
            try:
                for route in ("/", "/trading", "/skill", "/image-editor", "/image-editor?holding_id=hd-example&event=buy"):
                    with self.subTest(route=route), urlopen(base + route) as resp:
                        self.assertEqual(resp.status, 200)
                        page = resp.read().decode("utf-8")
                        self.assertIn('href="/image-editor"', page)
                        if route.startswith("/image-editor"):
                            self.assertIn('id="templateMode"', page)
                            self.assertIn('/static/app/image-editor.js', page)
                for route in (
                    "/static/vendor/lightweight-charts-5.2.0.js",
                    "/static/vendor/html2canvas-1.4.1.js",
                    "/static/app/image-editor.js",
                    "/static/templates/performance-background.jpeg",
                    "/static/templates/recommendation-background.jpg",
                ):
                    with self.subTest(asset=route), urlopen(base + route) as resp:
                        body = resp.read()
                        self.assertEqual(resp.status, 200)
                        self.assertGreater(len(body), 500)
                        self.assertIn("nosniff", resp.headers.get("X-Content-Type-Options", ""))
                with self.assertRaises(Exception):
                    urlopen(base + "/static/%2e%2e/finance_skill_api.py")
                with urlopen(base + "/image-editor") as resp:
                    csp = resp.headers.get("Content-Security-Policy", "")
                    self.assertIn("script-src 'self' 'unsafe-inline'", csp)
                    self.assertIn("img-src 'self' data: blob:", csp)
                    self.assertIn("connect-src 'self'", csp)
                    self.assertNotIn("frame-src", csp)
                    self.assertEqual(resp.headers.get("Referrer-Policy"), "no-referrer")
                    self.assertEqual(resp.headers.get("Cache-Control"), "no-store")
                with urlopen(base + "/api/trading/sim/performance") as resp:
                    summary = json.load(resp)
                    self.assertEqual(summary["records"], [])
                    self.assertEqual(summary["total_percent"], 0)
                    self.assertTrue(summary["simulation_only"])
                with urlopen(base + "/trade-platform") as resp:
                    self.assertEqual(resp.status, 200)
                    self.assertEqual(resp.url, base + "/image-editor")
                self.assertEqual(list(folder.iterdir()), [])
            finally:
                server.shutdown()
                server.server_close()
                th.join(timeout=5)

    def test_chart_route_passes_symbol_and_allowed_range_to_readonly_provider(self):
        expected = {"symbol": "AAPL", "provider": "Yahoo Finance", "points": [{"time": "2026-10-14", "value": 250.0}]}
        with tempfile.TemporaryDirectory() as temp:
            server = ThreadingHTTPServer(("127.0.0.1", 0), make_handler(Path(temp)))
            th = threading.Thread(target=server.serve_forever, daemon=True)
            th.start()
            try:
                url = f"http://127.0.0.1:{server.server_port}/api/trading/chart?symbol=AAPL&range=1y"
                with patch.object(finance_skill_api, "get_history", return_value=expected) as history:
                    with urlopen(url) as resp:
                        self.assertEqual(json.load(resp), expected)
                    history.assert_called_once_with("AAPL", "1y")
            finally:
                server.shutdown()
                server.server_close()
                th.join(timeout=5)

    def test_symbol_lookup_route_remains_read_only(self):
        expected = {
            "symbol": "AAPL", "name": "Apple Inc.", "market": "NasdaqGS",
            "currency": "USD", "provider": "Yahoo Finance", "price_is_reference_only": True,
        }
        with tempfile.TemporaryDirectory() as temp:
            server = ThreadingHTTPServer(("127.0.0.1", 0), make_handler(Path(temp)))
            th = threading.Thread(target=server.serve_forever, daemon=True)
            th.start()
            try:
                with patch.object(finance_skill_api, "lookup_symbol", return_value=expected) as lookup:
                    with urlopen(f"http://127.0.0.1:{server.server_port}/api/trading/symbol-lookup?symbol=AAPL") as resp:
                        self.assertEqual(json.load(resp), expected)
                    lookup.assert_called_once_with("AAPL")
            finally:
                server.shutdown()
                server.server_close()
                th.join(timeout=5)


if __name__ == "__main__":
    unittest.main()
