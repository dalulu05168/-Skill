"""Real HTTP checks for five isolated P004 skills embedded in four-in-one /skill."""
import json
import sys
import tempfile
import threading
import unittest
from pathlib import Path
from http.server import ThreadingHTTPServer
from urllib.error import HTTPError
from urllib.request import urlopen, Request

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import finance_skill_api as api
import p004_five_skill_bridge as bridge


class FiveSkillIntegrationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.directory = Path(self.temp.name)
        self.server = ThreadingHTTPServer(("127.0.0.1",0), api.make_handler(self.directory))
        self.thread = threading.Thread(target=self.server.serve_forever,daemon=True)
        self.thread.start()
        self.base = "http://127.0.0.1:" + str(self.server.server_port)

    def tearDown(self):
        self.server.shutdown()
        self.thread.join(timeout=4)
        self.server.server_close()
        self.temp.cleanup()

    def post(self, endpoint, payload, headers=None):
        req = Request(self.base+endpoint, data=json.dumps(payload).encode("utf-8"),
                      method="POST", headers={"Content-Type":"application/json",
                                            "Origin":self.base,**(headers or {})})
        try:
            with urlopen(req,timeout=6) as r:
                return r.status,json.loads(r.read().decode("utf-8"))
        except HTTPError as exc:
            return exc.code,json.loads(exc.read().decode("utf-8"))

    def get(self, endpoint):
        with urlopen(self.base+endpoint,timeout=6) as r:
            return r.status,r.read().decode("utf-8")

    def begin(self,scene="scene-five-skill-test",daypart="afternoon"):
        return self.post("/api/p004/plan",{
            "scene_id":scene,
            "story_date":"2026-10-14",
            "daypart":daypart,
            "topic_keywords":["能源","交通"],
            "max_members":8,
            "simulation_only":True,
            "source_status":"HYPOTHETICAL"})

    def manuscript(self,task):
        cast = task["cast"]
        self.assertGreater(len(cast),0)
        messages=[
            {"message_id":"m01","speaker_id":"assistant",
             "text":"Discutăm o situație ipotetică legată de energie."},
            {"message_id":"m02","speaker_id":cast[0]["speaker_id"],
             "reply_to":"m01","text":"Eu aș verifica și costurile."},
            {"message_id":"m03","speaker_id":cast[-1]["speaker_id"],
             "reply_to":"m02","text":"Nu sunt sigur, riscăm să simplificăm."}]
        if task["daypart"]=="evening":
            messages.append({"message_id":"m04","speaker_id":"professor",
                             "text":"Verificați ipoteza. Învățați să explicați riscul familiei."})
        return {"story_id":task["story_id"],"scene_id":task["scene_id"],
                "story_date":task["story_date"],"daypart":task["daypart"],
                "lesson_type":task["lesson_type"],
                "simulation_only":True,"fictional_case_only":True,
                "status":"DRAFT_NOT_ADOPTED","approved_by_user":False,
                "publishable":False,"messages":messages}

    def test_five_separate_skill_specs_and_empty_formal_roster(self):
        self.assertEqual(len(bridge.ROLES),5)
        for role in bridge.ROLES:
            with self.subTest(role=role):
                path = bridge.ROOT / "roles" / role / "SKILL.md"
                self.assertTrue(path.is_file(),str(path))
                self.assertIn("story_id: p004-fiction-director-independent",
                              path.read_text(encoding="utf-8"))
        self.assertEqual(len(bridge.read_json(bridge.DRAFT)["people"]),65)
        self.assertEqual(bridge.read_json(bridge.APPROVED)["characters"],[])

    def test_skill_page_is_the_real_four_in_one_route(self):
        status,page=self.get("/skill")
        self.assertEqual(status,200)
        self.assertIn("id=\"p004-five-skills\"",page)
        self.assertIn("总导演",page)
        self.assertIn("编剧",page)
        self.assertIn("65人成员",page)
        self.assertIn("/api/p004/",page)
        self.assertIn('href="/trading"',page)

    def test_status_reports_truth_not_old_personas(self):
        code,s = self.post("/api/p004/plan", {"source_status":"HYPOTHETICAL"})
        self.assertEqual(code,400)
        with urlopen(self.base+"/api/p004/status") as response:
            live=json.loads(response.read())
        self.assertEqual(live["candidate_count"],65)
        self.assertEqual(live["approved_count"],0)
        self.assertEqual(live["skills"],list(bridge.ROLES))
        self.assertFalse(live["autonomous_writer_connected"])
        self.assertFalse(live["module_two_transaction_linked"])
        self.assertFalse(live["publishes_to_whatsapp"])

    def test_live_plan_review_and_mandatory_approval_gate(self):
        code,out=self.begin()
        self.assertEqual(code,200)
        self.assertEqual(out["stage"],"AWAITING_WRITER_SKILL")
        self.assertEqual(out["next_skill"],"p004-writer")
        self.assertFalse(out["model_invoked"])
        self.assertEqual(out["task"]["approved_history"],[])
        self.assertIn("只写罗马尼亚语",out["prompt"])
        self.assertTrue(out["task"]["cast"])
        token=out["token"]
        self.assertEqual(self.post("/api/p004/restore",{"token":token})[0],200)
        draft=self.manuscript(out["task"])
        code,good=self.post("/api/p004/review",{"token":token,"manuscript":draft})
        self.assertEqual(code,200)
        self.assertEqual(good["report"]["status"],"EDITORIAL_REVIEW_REQUIRED")
        self.assertFalse(good["official_history_written"])
        code,blocked=self.post("/api/p004/adopt",{
            "token":token,"editorial_confirmed":True,"operator_confirmed":True})
        self.assertEqual(code,400)
        self.assertIn("not formally approved",blocked["error"])
        self.assertFalse((self.directory/"p004-five-skills"/"adopted-history.sqlite3").exists())
        self.assertFalse((self.directory/"chennan-writing-65.json").exists())

    def test_real_one_by_one_character_approval_and_persistence(self):
        with urlopen(self.base+"/api/p004/characters") as response:
            data=json.loads(response.read())
        self.assertEqual(data["candidate_count"],65)
        self.assertEqual(data["approved_count"],0)
        first=data["people"][0]
        self.assertEqual(first["id"],"01")
        self.assertFalse(first["approved"])
        code,blocked=self.post("/api/p004/approve-character",{
            "id":"01","confirmed_name":first["name"],"reviewed":False,
            "confirmed":True})
        self.assertEqual(code,400)
        self.assertIn("individually",blocked["error"])
        code,blocked=self.post("/api/p004/approve-character",{
            "id":"01","confirmed_name":"wrong name",
            "reviewed":True,"confirmed":True})
        self.assertEqual(code,400)
        self.assertIn("Confirm",blocked["error"])
        code,done=self.post("/api/p004/approve-character",{
            "id":"01","confirmed_name":first["name"],
            "reviewed":True,"confirmed":True})
        self.assertEqual(code,200)
        self.assertEqual(done["approved_count"],1)
        _,same=self.post("/api/p004/approve-character",{
            "id":"01","confirmed_name":first["name"],
            "reviewed":True,"confirmed":True})
        self.assertEqual(same["status"],"already_approved")
        approved_path=self.directory/"p004-five-skills"/"approved-roster.json"
        self.assertTrue(approved_path.is_file())
        self.assertEqual(len(json.loads(approved_path.read_text())["characters"]),1)
        with urlopen(self.base+"/api/p004/status") as response:
            current=json.loads(response.read())
        self.assertEqual(current["approved_count"],1)
        self.assertEqual(bridge.read_json(bridge.APPROVED)["characters"],[])
        with urlopen(self.base+"/api/p004/characters") as response:
            again=json.loads(response.read())
        self.assertTrue(again["people"][0]["approved"])
        self.assertFalse(again["people"][1]["approved"])

    def test_five_first_class_skill_metadata_is_real_not_an_ai_program(self):
        self.assertEqual(set(bridge.SKILL_FILES), set(bridge.ROLES))
        metadata=bridge.skill_registry()
        self.assertEqual(len(metadata),5)
        for item in metadata:
            with self.subTest(role=item["role"]):
                self.assertTrue(item["defined"])
                self.assertFalse(item["installed_in_chatgpt"])
                self.assertTrue(item["file"].startswith("skills/p004-"))
                self.assertTrue(bridge.SKILL_FILES[item["role"]].is_file())
        with urlopen(self.base+"/api/p004/status") as response:
            state=json.loads(response.read())
        self.assertTrue(state["skill_only_mode"])
        self.assertTrue(state["writer_skill_defined"])
        self.assertFalse(state["writer_skill_automatically_invoked"])
        self.assertEqual(state["skill_definitions"],metadata)
        _,page=self.get("/skill")
        self.assertIn("编剧 Skill",page)
        self.assertNotIn("自动AI编剧",page)

    def test_adopted_story_history_reaches_next_director_and_writer_skill(self):
        """Synthetic approvals exist ONLY inside a temp test workspace."""
        draft=bridge.read_json(bridge.DRAFT)
        approvals=bridge.read_json(bridge.APPROVED)
        approvals["characters"]=[{
            "id":p["id"],"name":p["name"],
            "approved_by_user":True,
            "profile_fingerprint":bridge.fingerprint(p)}
            for p in draft["people"]]
        tmp_roster=self.directory/"p004-five-skills"/"approved-roster.json"
        bridge.save_json(tmp_roster,approvals)
        code,first=self.begin(scene="first-synthetic-scene")
        self.assertEqual(code,200)
        manuscript=self.manuscript(first["task"])
        code,result=self.post("/api/p004/review",{
            "token":first["token"],"manuscript":manuscript})
        self.assertEqual(code,200)
        self.assertFalse(result["report"]["blocking_issues"])
        code,adopted=self.post("/api/p004/adopt",{
            "token":first["token"],"editorial_confirmed":True,"operator_confirmed":True})
        self.assertEqual(code,200)
        self.assertTrue(adopted["adoption"]["official_story_memory_written"])
        code,next_scene=self.begin(scene="second-synthetic-scene",daypart="evening")
        self.assertEqual(code,200)
        previous=next_scene["task"]["approved_history"]
        self.assertGreater(len(previous),0)
        self.assertTrue(any(
            row["scene_id"]=="first-synthetic-scene"
            and row["message_id"]=="m01"
            and row["speaker_id"]=="assistant"
            for row in previous))
        self.assertIn("first-synthetic-scene",next_scene["prompt"])
        valid=self.manuscript(next_scene["task"])
        valid["messages"][1]["history_reference"]={
            "scene_id":"first-synthetic-scene",
            "message_id":"m01",
            "speaker_id":"assistant"}
        code,reviewed=self.post("/api/p004/review",{
            "token":next_scene["token"],"manuscript":valid})
        self.assertEqual(code,200)
        self.assertEqual(reviewed["report"]["status"],"EDITORIAL_REVIEW_REQUIRED")
        self.assertFalse((self.directory/"chennan-writing-65.json").exists())

    def test_invalid_speaker_refused_and_no_memory(self):
        _,p=self.begin(scene="p004-unknown-speaker")
        draft=self.manuscript(p["task"])
        draft["messages"][1]["speaker_id"]="99"
        code,result=self.post("/api/p004/review",{
            "token":p["token"],"manuscript":draft})
        self.assertEqual(code,200)
        self.assertEqual(result["report"]["status"],"BLOCKED_REWRITE_REQUIRED")
        code,denied=self.post("/api/p004/adopt",{
            "token":p["token"],"editorial_confirmed":True,"operator_confirmed":True})
        self.assertEqual(code,400)
        self.assertFalse((self.directory/"p004-five-skills"/"adopted-history.sqlite3").exists())

    def test_professor_daytime_block_and_evening_rule(self):
        _,morning=self.begin(scene="p004-no-daytime-professor",daypart="morning")
        bad=self.manuscript(morning["task"])
        bad["messages"].append({"message_id":"m04","speaker_id":"professor",
                                  "text":"Azi țin o lecție."})
        _,res=self.post("/api/p004/review",{
            "token":morning["token"],"manuscript":bad})
        self.assertEqual(res["report"]["status"],"BLOCKED_REWRITE_REQUIRED")
        _,evening=self.begin(scene="p004-evening-professor",daypart="evening")
        self.assertEqual(evening["task"]["lesson_type"],"technical")

    def test_reject_cross_origin(self):
        code,result=self.post("/api/p004/plan",{},{
            "Origin":"http://evil.example"})
        self.assertEqual(code,403)
        self.assertIn("Cross-origin",result["error"])

if __name__ == "__main__":
    unittest.main()
