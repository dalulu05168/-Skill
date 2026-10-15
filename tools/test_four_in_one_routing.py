"""Four-in-one workbench regression checks; isolated from external trading systems.

No network access outside the local test server; no real accounts or database.
"""
import base64
import json
import sys
import tempfile
import threading
import unittest
from http.server import ThreadingHTTPServer
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import finance_skill_api as api


class FourInOneRoutesTests(unittest.TestCase):
    def _serve(self, folder, *, hosted=False):
        return ThreadingHTTPServer(
            ("127.0.0.1", 0),
            api.make_handler(
                Path(folder), public_mode=hosted,
                auth_username="test-reviewer" if hosted else None,
                auth_password="test-secret-password" if hosted else None,
            ),
        )

    def test_every_module_accepts_filtered_urls_without_changing_saved_data(self):
        with tempfile.TemporaryDirectory() as folder:
            with self._serve(folder) as server:
                thread = threading.Thread(target=server.serve_forever, daemon=True)
                thread.start()
                base = f"http://127.0.0.1:{server.server_port}"
                try:
                    routes = ("/", "/trading", "/skill", "/writing", "/trade-platform")
                    for route in routes:
                        with self.subTest(route=route), urlopen(base + route + "?member=01") as response:
                            self.assertEqual(response.status, 200)
                            self.assertIn("text/html", response.headers["Content-Type"])
                            self.assertEqual(response.headers.get("Cache-Control"), "no-store")
                            self.assertEqual(response.headers.get("Referrer-Policy"), "no-referrer")
                            html = response.read().decode("utf-8")
                            for link in ('href="/"', 'href="/trading"', 'href="/skill"', 'href="/trade-platform"'):
                                self.assertIn(link, html)
                            if route == "/trade-platform":
                                self.assertIn("script-src 'none'", response.headers["Content-Security-Policy"])
                                self.assertIn("https://trade.sasakic.cc/", html)
                    for route in ("/api/dashboard/summary?tab=overview", "/api/trading/people?tab=members",
                                  "/api/trading/sim/state?tab=positions"):
                        with self.subTest(api=route), urlopen(base + route) as response:
                            self.assertEqual(response.status, 200)
                            self.assertIsInstance(json.load(response), dict)
                    with urlopen(base + "/api/trading/profile?character_id=01") as response:
                        self.assertEqual(json.load(response)["character_id"], "01")
                    with self.assertRaises(HTTPError) as bad_profile:
                        urlopen(base + "/api/trading/profile")
                    self.assertEqual(bad_profile.exception.code, 400)
                    with urlopen(base + "/healthz?probe=yes") as response:
                        self.assertEqual(json.load(response)["status"], "ok")
                    self.assertEqual(list(Path(folder).iterdir()), [],
                                     "Read-only module navigation must not write news, person or trade state")
                finally:
                    server.shutdown()
                    thread.join(timeout=5)

    def test_hosted_mode_requires_real_basic_auth_even_with_query_strings(self):
        with tempfile.TemporaryDirectory() as folder:
            with self._serve(folder, hosted=True) as server:
                thread = threading.Thread(target=server.serve_forever, daemon=True)
                thread.start()
                base = f"http://127.0.0.1:{server.server_port}"
                token = base64.b64encode(b"test-reviewer:test-secret-password").decode("ascii")
                try:
                    for route in ("/?member=01", "/trading?member=01",
                                  "/skill?tab=people", "/trade-platform?from=news",
                                  "/api/trading/people?query=x"):
                        with self.subTest(route=route):
                            with self.assertRaises(HTTPError) as unauth:
                                urlopen(base + route)
                            self.assertEqual(unauth.exception.code, 401)
                            with urlopen(Request(base + route, headers={
                                "Authorization": "Basic " + token,
                            })) as response:
                                self.assertEqual(response.status, 200)
                    with urlopen(base + "/healthz?probe=yes") as response:
                        self.assertEqual(json.load(response)["status"], "ok")
                finally:
                    server.shutdown()
                    thread.join(timeout=5)


if __name__ == "__main__":
    unittest.main()
