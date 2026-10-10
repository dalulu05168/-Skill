"""Contract tests for selected 16:9 light finance UI and authoritative 65 roster.

No mock market data, external network calls, publication or financial orders.
"""
import json
import sys
import tempfile
import threading
import unittest
from http.server import ThreadingHTTPServer
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import urlopen

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"tools"))

import finance_skill_api as api
from chennan_writing import empty_state, write_state
from workspace_overview import dashboard_summary
from workspace_layout import wrap_page


class UIContractTests(unittest.TestCase):
    def test_real_metrics_from_official_65_roster_and_empty_local_state(self):
        with tempfile.TemporaryDirectory() as folder:
            data=Path(folder)
            value=dashboard_summary(data)
            self.assertEqual(value["roster_count"],65)
            self.assertEqual(value["roster_source"],"finance-director-65-v4.1")
            self.assertEqual(value["adopted_sessions"],0)
            self.assertEqual(value["documents"],0)
            self.assertIsNone(value["last_news_review"])
            self.assertEqual(list(data.iterdir()),[],"Read-only overview cannot create data")

    def test_metrics_are_saved_actual_review_and_formal_sessions_not_examples(self):
        with tempfile.TemporaryDirectory() as folder:
            data=Path(folder)
            state=empty_state()
            state["sessions"]=[{"id":"test-session"}]
            state["docs"]=[{"id":"doc","title":"draft"}]
            write_state(data/"chennan-writing-65.json",state)
            (data/"latest-internal-review.json").write_text(json.dumps({
                "runner":"unified-finance-skill-hub","generated_at":"2026-10-10T10:00:00+00:00",
                "news":{"pending_count":3},"review":{"status":"NEEDS_REVIEW"}
            }),encoding="utf-8")
            value=dashboard_summary(data)
            self.assertEqual(value["adopted_sessions"],1)
            self.assertEqual(value["documents"],1)
            self.assertEqual(value["last_news_review"]["pending_count"],3)
            self.assertEqual(value["last_news_review"]["status"],"NEEDS_REVIEW")

    def test_reject_nonofficial_news_metrics_and_non65_state(self):
        with tempfile.TemporaryDirectory() as folder:
            data=Path(folder)
            (data/"latest-internal-review.json").write_text(json.dumps({
                "runner":"third-party-trading","news":{"pending_count":999},
            }),encoding="utf-8")
            with self.assertRaises(ValueError):
                dashboard_summary(data)
            (data/"latest-internal-review.json").unlink()
            write_state(data/"chennan-writing-65.json",{
                "roster_source":"legacy-70","drafts":{},"docs":[],"sessions":[]
            })
            with self.assertRaises(ValueError):
                dashboard_summary(data)

    def test_shell_has_no_external_tracking_or_broken_navigation(self):
        rendered=wrap_page("<html><head><style></style></head><body><main class='app'>ok</main></body></html>","external")
        self.assertIn('href="/trading#tc-profile"',rendered)
        self.assertIn('href="/trade-platform"',rendered)
        self.assertIn('name="member"',rendered)
        self.assertIn('aria-label="主模块"',rendered)
        for unsafe in ("https://fonts.googleapis.com","example.com/price","iframe","localStorage"):
            self.assertNotIn(unsafe,rendered)

    def test_all_three_routes_use_approved_dashboard_chrome_and_real_roster(self):
        with tempfile.TemporaryDirectory() as folder:
            data=Path(folder)
            with ThreadingHTTPServer(("127.0.0.1",0),api.make_handler(data)) as server:
                t=threading.Thread(target=server.serve_forever,daemon=True);t.start()
                base=f"http://127.0.0.1:{server.server_port}"
                try:
                    for route in ("/","/?member=01","/trading","/trade-platform"):
                        with self.subTest(route=route),urlopen(base+route) as r:
                            self.assertEqual(r.status,200)
                            html=r.read().decode("utf-8")
                            self.assertIn('class="ws-frame"',html)
                            self.assertIn('class="ws-rail"',html)
                            self.assertIn('class="ws-top"',html)
                            self.assertIn('href="/trade-platform"',html)
                            self.assertIn('href="/trading"',html)
                            self.assertIn('href="/"',html)
                            self.assertIn("65人",html)
                    with urlopen(base+"/") as r:
                        html=r.read().decode("utf-8")
                        self.assertIn('id="ws-members-body"',html)
                        self.assertIn("ws-unknown",html)
                        self.assertIn("fetchApi",html,"Original news workflow must stay available")
                        self.assertIn('id="generate"',html,"Original optional Ollama feature retained")
                    with urlopen(base+"/api/dashboard/summary") as r:
                        state=json.load(r)
                        self.assertEqual(state["roster_count"],65)
                        self.assertIsNone(state["last_news_review"])
                    with urlopen(base+"/api/trading/people") as r:
                        p=json.load(r)
                        self.assertEqual(p["count"],65)
                        self.assertEqual(len(p["people"]),65)
                        self.assertEqual(set(x["character_id"] for x in p["people"]),{
                            f"{i:02d}" for i in range(1,66)})
                    with urlopen(base+"/trade-platform") as r:
                        html=r.read().decode("utf-8")
                        self.assertIn("https://trade.sasakic.cc/",html)
                        self.assertIn("script-src 'none'",r.headers["Content-Security-Policy"])
                    self.assertEqual(list(data.iterdir()),[])
                finally:
                    server.shutdown();t.join(timeout=5)


if __name__=="__main__":
    unittest.main()
