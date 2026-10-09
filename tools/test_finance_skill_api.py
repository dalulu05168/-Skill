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
from unittest.mock import patch

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

    def test_opt_in_ai_routes_and_rejects_provider_failures(self):
        fake_draft = {
            "kind": "INTERNAL_FICTIONAL_EDUCATION_DRAFT",
            "model_request_completed": True, "status": "HOLD_FOR_HUMAN_REVIEW",
            "text": "只谈风险和情景假设。",
            "publication_allowed": False, "messages_sent": 0,
        }
        with tempfile.TemporaryDirectory() as folder:
            with ThreadingHTTPServer(("127.0.0.1", 0), api.make_handler(Path(folder))) as srv:
                thread = threading.Thread(target=srv.serve_forever, daemon=True)
                thread.start()
                base = f"http://127.0.0.1:{srv.server_port}"
                body = json.dumps({
                    "role": "assistant", "topic": "如何理解短线不确定性？",
                    "node": "RO-08", "model": "qwen2.5:1.5b",
                }).encode("utf-8")
                try:
                    with patch.object(api, "model_status",
                                      return_value={"can_generate": False,
                                                    "connected": False}):
                        with urlopen(base + "/api/model/status") as response:
                            self.assertFalse(json.load(response)["can_generate"])
                    with patch.object(api, "generate_draft", return_value=fake_draft) as mock:
                        req = Request(base + "/api/generate", data=body,
                                      headers={"Content-Type": "application/json"},
                                      method="POST")
                        with urlopen(req) as response:
                            packet = json.load(response)
                        self.assertEqual(packet["status"], "HOLD_FOR_HUMAN_REVIEW")
                        self.assertFalse(packet["publication_allowed"])
                        self.assertTrue(mock.called)
                        saved = Path(folder) / "latest-ai-draft-internal.json"
                        self.assertTrue(saved.exists())
                    with patch.object(api, "generate_draft", side_effect=RuntimeError("offline")):
                        req = Request(base + "/api/generate", data=body,
                                      headers={"Content-Type": "application/json"},
                                      method="POST")
                        with self.assertRaises(HTTPError) as exc:
                            urlopen(req)
                        self.assertEqual(exc.exception.code, 400)
                finally:
                    srv.shutdown()
                    thread.join(timeout=5)



if __name__ == "__main__":
    unittest.main()
