"""End-to-end loopback API tests: only local review, no external calls."""
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


class APIHarnessTests(unittest.TestCase):
    def test_dashboard_health_and_prepare(self):
        with tempfile.TemporaryDirectory() as folder:
            with ThreadingHTTPServer(("127.0.0.1", 0), api.make_handler(Path(folder))) as srv:
                thread = threading.Thread(target=srv.serve_forever, daemon=True)
                thread.start()
                base = f"http://127.0.0.1:{srv.server_port}"
                try:
                    with urlopen(base + "/") as r:
                        html = r.read().decode("utf-8")
                        self.assertIn("统一 SKILL 工作台", html)
                        self.assertIn("fetchApi", html)
                    with urlopen(base + "/healthz") as r:
                        self.assertEqual(json.load(r)["mode"], "loopback_internal_review_only")
                    payload = json.dumps({"spec": {}, "node": "RO-08",
                                          "fetch_rss": False}).encode("utf-8")
                    req = Request(base + "/api/prepare", data=payload, method="POST",
                                  headers={"Content-Type": "application/json"})
                    with urlopen(req) as response:
                        packet = json.load(response)
                    self.assertEqual(packet["slot"]["id"], "RO-08")
                    self.assertEqual(packet["characters"]["roster_count"], 65)
                    self.assertEqual(packet["review"]["publish_status"],
                                     "BLOCKED_NO_AUTOMATIC_PUBLICATION")
                    self.assertTrue((Path(folder)/"latest-internal-review.json").exists())
                    cross = Request(base + "/api/prepare", data=payload, method="POST",
                                    headers={"Content-Type": "application/json",
                                             "Origin": "https://evil.example"})
                    with self.assertRaises(HTTPError) as context:
                        urlopen(cross)
                    self.assertEqual(context.exception.code, 403)
                finally:
                    srv.shutdown()
                    thread.join(timeout=5)


if __name__ == "__main__":
    unittest.main()
