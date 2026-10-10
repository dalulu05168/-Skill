"""Regression: course/chat memory belong to Skill; /trading only handles 65-person simulation."""
import json
import sys
import tempfile
import threading
import unittest
from pathlib import Path
from http.server import ThreadingHTTPServer
from urllib.request import urlopen

sys.path.insert(0, str(Path(__file__).resolve().parent))
import finance_skill_api as api
from trading_center_ui import PAGE as TRADING_PAGE
from workspace_layout import SHELL_CSS


class TradingSkillUiSeparation(unittest.TestCase):
    def test_routes_keep_separate_visual_workspaces(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            with ThreadingHTTPServer(("127.0.0.1", 0), api.make_handler(root)) as server:
                thread = threading.Thread(target=server.serve_forever, daemon=True)
                thread.start()
                base = f"http://127.0.0.1:{server.server_port}"
                try:
                    with urlopen(base + "/trading") as response:
                        trading = response.read().decode("utf-8")
                    with urlopen(base + "/skill") as response:
                        skill = response.read().decode("utf-8")
                    with urlopen(base + "/writing") as response:
                        old_alias = response.read().decode("utf-8")
                    with urlopen(base + "/") as response:
                        home = response.read().decode("utf-8")
                    for page in (trading, skill, old_alias, home):
                        self.assertIn("class=\"ws-frame\"", page)
                        self.assertIn('href="/skill"', page)
                        self.assertIn('href="/trading"', page)
                    self.assertIn('id="sim-people-table"', trading)
                    self.assertIn('id="tc-profile-select"', trading)
                    self.assertIn('data-tab="sim"', trading)
                    for blocked in ('id="tab-script"', 'id="tab-docs"', 'id="tab-history"'):
                        self.assertNotIn(blocked, trading)
                    for moved in ('id="tab-script"', 'id="tab-docs"', 'id="tab-history"'):
                        self.assertIn(moved, skill)
                    self.assertIn('data-tab="docs">课程资料与文档', skill)
                    self.assertIn('data-tab="history">正式会话与人物记忆', skill)
                    self.assertNotIn('data-tab="sim"', skill)
                    self.assertIn('id="tab-script"', old_alias)
                    self.assertIn('background:#ffffff', trading)
                    self.assertIn('hover:hover', SHELL_CSS)
                    self.assertEqual(list(root.iterdir()), [], "Viewing pages must not create fake trades or sessions")
                finally:
                    server.shutdown()
                    thread.join(timeout=3)

    def test_trading_only_loads_authoritative_65_people(self):
        with tempfile.TemporaryDirectory() as folder:
            with ThreadingHTTPServer(("127.0.0.1", 0), api.make_handler(Path(folder))) as server:
                thread = threading.Thread(target=server.serve_forever, daemon=True)
                thread.start()
                try:
                    base = f"http://127.0.0.1:{server.server_port}"
                    with urlopen(base + "/api/trading/people") as response:
                        people = json.load(response)
                    self.assertEqual(people["count"], 65)
                    self.assertEqual({p["character_id"] for p in people["people"]},
                                     {f"{n:02d}" for n in range(1, 66)})
                finally:
                    server.shutdown()
                    thread.join(timeout=3)


if __name__ == "__main__":
    unittest.main()
