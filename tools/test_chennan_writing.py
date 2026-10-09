"""Trading Center merged 65-person tests; no network, no external account changes."""
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

import chennan_writing as writing
import finance_skill_api as api


class TradingCenter65Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.profiles = writing.load_profiles()
        cls.p = cls.profiles["01"]
        cls.name = cls.p["identity_extension"]["姓名"]
        cls.gender = cls.p["source_profile"]["性别"]
        cls.role = cls.p["source_profile"]["学员资历"]

    def request(self):
        return {"date": "2026-10-10", "node": "RO-08", "source_kind": "assistant",
                "source_text": "本次演练观察风险管理，不使用虚构行情。",
                "selected_ids": ["01"], "topic": "假设场景"}

    def member(self):
        return {"character_id": "01", "name": self.name, "gender": self.gender,
                "role": self.role, "text": "需要更多数据再下判断。"}

    def test_only_official_65_profiles_with_complete_fields(self):
        self.assertEqual(len(self.profiles), 65)
        self.assertEqual(set(self.profiles), {f"{i:02d}" for i in range(1, 66)})
        self.assertTrue(self.p.get("language_dna"))
        self.assertTrue(self.p.get("investment_profile"))
        self.assertTrue(self.p.get("identity_extension"))
        self.assertNotIn("70", self.profiles)

    def test_prompt_validation_adoption_and_memory_gate(self):
        state = writing.empty_state()
        prompt, state = writing.make_prompt(self.request(), self.profiles, state)
        self.assertEqual(prompt["roster_source"], writing.ROSTER_SOURCE)
        self.assertEqual(prompt["selected_characters"][0]["character_id"], "01")
        self.assertEqual(prompt["selected_characters"][0]["identity_extension"]["姓名"], self.name)
        self.assertEqual(state["sessions"], [])
        draft = state["drafts"][prompt["draft_id"]]
        checked = writing.validate_messages({"messages": [self.member()]}, draft, self.profiles, state["sessions"])
        self.assertTrue(checked["valid"], checked["errors"])
        self.assertEqual(state["sessions"], [])
        with self.assertRaises(ValueError):
            writing.adopt({"messages": [self.member()]}, prompt["draft_id"], state, self.profiles)
        session, new_state = writing.adopt({"messages": [self.member()], "confirmed": True},
                                           prompt["draft_id"], state, self.profiles)
        self.assertEqual(len(new_state["sessions"]), 1)
        self.assertEqual(session["status"], "adopted")
        self.assertEqual(session["roster_source"], writing.ROSTER_SOURCE)
        self.assertFalse(new_state["drafts"])
        with self.assertRaises(ValueError):
            writing.adopt({"messages": [self.member()], "confirmed": True},
                          prompt["draft_id"], new_state, self.profiles)

    def test_cross_project_72_member_or_identity_mismatch_is_rejected(self):
        state = writing.empty_state()
        with self.assertRaises(ValueError):
            writing.make_prompt({**self.request(), "selected_ids": ["70"]}, self.profiles, state)
        prompt, state = writing.make_prompt(self.request(), self.profiles, state)
        draft = state["drafts"][prompt["draft_id"]]
        fake = {**self.member(), "name": "A person from another project"}
        report = writing.validate_messages({"messages": [fake]}, draft, self.profiles, [])
        self.assertFalse(report["valid"])
        self.assertTrue(any("mismatch" in issue for issue in report["errors"]))
        other = {**self.member(), "character_id": "70"}
        report = writing.validate_messages({"messages": [other]}, draft, self.profiles, [])
        self.assertFalse(report["valid"])

    def test_professor_only_on_scheduled_node(self):
        with self.assertRaises(ValueError):
            writing.make_prompt({**self.request(), "source_kind": "professor"}, self.profiles,
                                writing.empty_state())
        prompt, _ = writing.make_prompt({**self.request(), "node": "RO-10",
                                         "source_kind": "professor"}, self.profiles,
                                        writing.empty_state())
        self.assertEqual(prompt["node"], "RO-10")

    def test_documents_and_atomic_local_backup_boundary(self):
        state = writing.empty_state()
        doc, state = writing.save_doc({"title": "第一章", "content": "文字草稿"}, state)
        self.assertEqual(len(state["docs"]), 1)
        _, state = writing.save_doc({"id": doc["id"], "title": "第一章 修订",
                                      "content": "修改后的正文"}, state)
        self.assertEqual(len(state["docs"]), 1)
        with tempfile.TemporaryDirectory() as folder:
            p = Path(folder) / "writing-65.json"
            writing.write_state(p, state)
            loaded = writing.read_state(p)
            self.assertEqual(loaded["docs"][0]["content"], "修改后的正文")
            bad = {**loaded, "roster_source": "old-72-people"}
            writing.write_state(p, bad)
            with self.assertRaises(ValueError):
                writing.read_state(p)


class TradingCenterApiTests(unittest.TestCase):
    def test_module_route_and_real_local_endpoints(self):
        with tempfile.TemporaryDirectory() as folder:
            with ThreadingHTTPServer(("127.0.0.1", 0), api.make_handler(Path(folder))) as srv:
                t = threading.Thread(target=srv.serve_forever, daemon=True)
                t.start()
                url = f"http://127.0.0.1:{srv.server_port}"
                def post(path, data):
                    body = json.dumps(data).encode("utf-8")
                    request = Request(url + path, data=body, method="POST",
                                      headers={"Content-Type": "application/json"})
                    with urlopen(request) as result:
                        return json.load(result)
                try:
                    with urlopen(url + "/") as r:
                        self.assertIn('href="/trading"', r.read().decode("utf-8"))
                    with urlopen(url + "/trading") as r:
                        page = r.read().decode("utf-8")
                        self.assertIn("交易中心", page)
                        self.assertIn('id="peoplelist"', page)
                    with urlopen(url + "/api/trading/people") as r:
                        roster = json.load(r)
                        self.assertEqual(roster["count"], 65)
                    p = roster["people"][0]
                    with urlopen(url + "/api/trading/profile?character_id=" + p["character_id"]) as r:
                        full = json.load(r)
                        self.assertTrue(full["profile"]["simulation_only"])
                    generated = post("/api/trading/prompt", {
                        "date": "2026-10-10", "node": "RO-08",
                        "source_kind": "assistant", "source_text": "用于测试的虚构讨论",
                        "selected_ids": [p["character_id"]], "topic": "短句验证"
                    })
                    did = generated["prompt"]["draft_id"]
                    msg = {"character_id": p["character_id"], "name": p["name"],
                           "gender": p["gender"], "role": p["role"], "text": "我还需要确认一下。"}
                    result = post("/api/trading/validate", {"draft_id": did, "response": {"messages": [msg]}})
                    self.assertTrue(result["valid"], result["errors"])
                    with urlopen(url + "/api/trading/state") as r:
                        self.assertEqual(json.load(r)["sessions"], [])
                    with self.assertRaises(HTTPError) as err:
                        post("/api/trading/adopt", {"draft_id": did, "response": {"messages": [msg]}})
                    self.assertEqual(err.exception.code, 400)
                    saved = post("/api/trading/adopt", {"draft_id": did,
                                                        "response": {"messages": [msg]},
                                                        "confirmed": True})
                    self.assertEqual(len(saved["session"]["messages"]), 1)
                    document = post("/api/trading/docs", {"title": "大纲", "content": "草稿"})
                    with urlopen(url + "/api/trading/state") as r:
                        current = json.load(r)
                        self.assertEqual(len(current["sessions"]), 1)
                        self.assertEqual(current["docs"][0]["id"], document["doc"]["id"])
                    request = Request(url + "/api/trading/docs",
                                      data=json.dumps({"title": "x", "content": "y"}).encode(),
                                      headers={"Origin": "https://evil.example",
                                               "Content-Type": "application/json"})
                    with self.assertRaises(HTTPError) as err:
                        urlopen(request)
                    self.assertEqual(err.exception.code, 403)
                finally:
                    srv.shutdown()
                    t.join(timeout=5)


if __name__ == "__main__":
    unittest.main()
