"""Smoke tests for internal module-four route with no outbound domain link.

The independent trading service and 65-person data flows are not altered.
"""
import json
import sys
import tempfile
import threading
import unittest
from http.server import ThreadingHTTPServer
from pathlib import Path
from urllib.request import urlopen

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import finance_skill_api as api
from external_trade_ui import EXTERNAL_TRADE_URL, PAGE


class ExternalTradeModuleTests(unittest.TestCase):
    def test_module_four_has_no_outbound_domain_or_clickthrough(self):
        self.assertEqual(EXTERNAL_TRADE_URL, "")
        self.assertIn("外部域名链接已取消", PAGE)
        self.assertNotIn("brantone-veyor-trading.onrender.com", PAGE)
        self.assertNotIn("trade.sasakic.cc", PAGE)
        self.assertNotIn('target="_blank"', PAGE)
        self.assertNotIn("打开交易平台 ↗", PAGE)
        self.assertIn('href="/trading"', PAGE)
        self.assertIn('href="/"', PAGE)
        for unsafe in ("<iframe", "<form", "localStorage", "document.cookie",
                       "window.location=", "fetch(", "XMLHttpRequest", "<script"):
            self.assertNotIn(unsafe, PAGE)

    def test_all_three_pages_link_each_other_and_keep_existing_business_routes(self):
        with tempfile.TemporaryDirectory() as folder:
            data_dir = Path(folder)
            with ThreadingHTTPServer(("127.0.0.1", 0), api.make_handler(data_dir)) as server:
                t = threading.Thread(target=server.serve_forever, daemon=True)
                t.start()
                base = f"http://127.0.0.1:{server.server_port}"
                try:
                    for route in ("/", "/news", "/trading", "/skill", "/trade-platform"):
                        with self.subTest(route=route), urlopen(base+route) as response:
                            self.assertEqual(response.status, 200)
                            self.assertIn("text/html", response.headers.get("Content-Type"))
                            html = response.read().decode("utf-8")
                            if route == "/":
                                self.assertIn("四合一管理工作台", html)
                                for item in ('href="/news"', 'href="/trading"',
                                             'href="/skill"', 'href="/trade-platform"'):
                                    self.assertIn(item, html)
                            else:
                                for item in ('href="/"', 'href="/trading"', 'href="/trade-platform"'):
                                    self.assertIn(item, html)
                            self.assertNotIn("fake equity", html)
                    with urlopen(base+"/trade-platform") as response:
                        policy=response.headers.get("Content-Security-Policy", "")
                        self.assertIn("frame-src 'none'", policy)
                        self.assertIn("script-src 'none'", policy)
                        self.assertIn("no-store", response.headers.get("Cache-Control", ""))
                        text=response.read().decode("utf-8")
                        self.assertIn("外部域名链接已取消", text)
                        self.assertNotIn("brantone-veyor-trading.onrender.com", text)
                    with urlopen(base + "/api/trading/people") as response:
                        self.assertEqual(json.load(response)["count"], 65)
                    with urlopen(base + "/healthz") as response:
                        self.assertEqual(json.load(response)["status"], "ok")
                    self.assertEqual(list(data_dir.iterdir()), [], "GET pages must not persist or modify trading/news data")
                finally:
                    server.shutdown()
                    t.join(timeout=5)


if __name__ == "__main__":
    unittest.main()
