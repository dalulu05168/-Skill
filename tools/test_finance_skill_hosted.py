"""Hosted-mode smoke tests: protected workbench, never a public data API."""
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


def auth(username="admin", password="correct-horse-battery-staple"):
    token = base64.b64encode(f"{username}:{password}".encode()).decode("ascii")
    return {"Authorization": "Basic " + token}


class HostedModeTests(unittest.TestCase):
    def test_hosted_workspace_auth_and_origin(self):
        with tempfile.TemporaryDirectory() as folder:
            handler = api.make_handler(
                Path(folder), public_mode=True, auth_username="admin",
                auth_password="correct-horse-battery-staple")
            with ThreadingHTTPServer(("127.0.0.1", 0), handler) as server:
                thread = threading.Thread(target=server.serve_forever, daemon=True)
                thread.start()
                base = f"http://127.0.0.1:{server.server_port}"
                try:
                    with urlopen(base + "/healthz") as response:
                        self.assertEqual(json.load(response)["mode"],
                                         "password_protected_hosted_review")
                    for endpoint in ("/", "/trading", "/api/trading/people",
                                     "/api/trading/state"):
                        with self.assertRaises(HTTPError) as denied:
                            urlopen(base + endpoint)
                        self.assertEqual(denied.exception.code, 401)
                    with self.assertRaises(HTTPError) as wrong_password:
                        urlopen(Request(base + "/", headers=auth(password="incorrect")))
                    self.assertEqual(wrong_password.exception.code, 401)
                    with urlopen(Request(base + "/", headers=auth())) as response:
                        self.assertIn("统一 SKILL 工作台", response.read().decode("utf-8"))
                    with urlopen(Request(base + "/api/trading/people", headers=auth())) as response:
                        self.assertEqual(json.load(response)["count"], 65)
                    body = json.dumps({"spec": {}, "fetch_rss": False, "node": "RO-08"}).encode()
                    post_headers = {**auth(), "Content-Type": "application/json"}
                    with self.assertRaises(HTTPError) as denied:
                        urlopen(Request(base + "/api/prepare", data=body, method="POST",
                                        headers={"Content-Type": "application/json"}))
                    self.assertEqual(denied.exception.code, 401)
                    with self.assertRaises(HTTPError) as cross_origin:
                        urlopen(Request(base + "/api/prepare", data=body, method="POST",
                                        headers={**post_headers, "Origin": "https://evil.example"}))
                    self.assertEqual(cross_origin.exception.code, 403)
                    with self.assertRaises(HTTPError) as insecure_origin:
                        urlopen(Request(base + "/api/prepare", data=body, method="POST",
                                        headers={**post_headers, "Origin": base}))
                    self.assertEqual(insecure_origin.exception.code, 403)
                    # Simulate a Render TLS-terminating proxy while keeping test HTTP local.
                    host = f"127.0.0.1:{server.server_port}"
                    with urlopen(Request(base + "/api/prepare", data=body, method="POST",
                                         headers={**post_headers, "Origin": "https://" + host})) as response:
                        result = json.load(response)
                    self.assertEqual(result["characters"]["roster_count"], 65)
                    self.assertEqual(result["review"]["publish_status"],
                                     "BLOCKED_NO_AUTOMATIC_PUBLICATION")
                    self.assertTrue((Path(folder) / "latest-internal-review.json").exists())
                finally:
                    server.shutdown()
                    thread.join(timeout=3)

    def test_public_mode_fails_closed_without_credentials(self):
        with tempfile.TemporaryDirectory() as folder:
            with self.assertRaises(ValueError):
                api.make_handler(Path(folder), public_mode=True)
            with self.assertRaises(ValueError):
                api.make_handler(Path(folder), public_mode=True, auth_username="admin")


if __name__ == "__main__":
    unittest.main()
