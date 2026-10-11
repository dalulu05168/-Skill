"""P004 continuity-memory acceptance: local disk, real SQLite, no models/network.

Approved rosters in tests are synthetic and isolated under TemporaryDirectory.
Production candidate roster remains 0 approved; no real fiction is adopted here.
"""
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import p004_five_skill_bridge as bridge
from scene_memory import person_history, scene_message_exists, adopt_scene


class ContinuityMemoryAcceptanceTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.data_dir = Path(self.tmp.name)
        self.story_data = self.data_dir / "p004-five-skills"
        self.db = self.story_data / "adopted-history.sqlite3"
        candidates = bridge.read_json(bridge.DRAFT)["people"]
        roster = bridge.read_json(bridge.APPROVED)
        # Fixture only; never mutate GitHub or real user-approved identities.
        roster["characters"] = [{
            "id": p["id"], "name": p["name"], "approved_by_user": True,
            "profile_fingerprint": bridge.fingerprint(p)
        } for p in candidates]
        self.roster = self.story_data / "approved-roster.json"
        bridge.save_json(self.roster, roster)

    def tearDown(self):
        self.tmp.cleanup()

    def plan(self, scene, date="2026-10-14", slot="morning"):
        return bridge.plan({
            "scene_id": scene, "story_date": date, "daypart": slot,
            "topic_keywords": ["能源", "交通"], "max_members": 8,
            "simulation_only": True, "source_status": "HYPOTHETICAL"
        }, self.data_dir)

    def manuscript(self, task, *, history_ref=None):
        members = task["cast"]
        self.assertTrue(members)
        lines = [
            {"message_id": "m01", "speaker_id": "assistant",
             "text": "Este un exercițiu ipotetic, fără cotații reale."},
            {"message_id": "m02", "speaker_id": members[0]["speaker_id"],
             "reply_to": "m01", "text": "Verific mai întâi cheltuielile."}
        ]
        if history_ref:
            lines[1]["history_reference"] = history_ref
        if task["lesson_type"] is not None:
            lines.append({"message_id": "m03", "speaker_id": "professor",
                          "text": "Înainte de toate, analizăm riscul familiei."})
        return {
            "story_id": task["story_id"], "scene_id": task["scene_id"],
            "story_date": task["story_date"], "daypart": task["daypart"],
            "lesson_type": task["lesson_type"], "simulation_only": True,
            "fictional_case_only": True, "status": "DRAFT_NOT_ADOPTED",
            "approved_by_user": False, "publishable": False, "messages": lines
        }

    def adopt(self, package):
        draft = self.manuscript(package["task"])
        reviewed = bridge.check({"token": package["token"], "manuscript": draft},
                                self.data_dir)
        self.assertEqual(reviewed["report"]["status"], "EDITORIAL_REVIEW_REQUIRED")
        result = bridge.adopt({
            "token": package["token"], "editorial_confirmed": True,
            "operator_confirmed": True
        }, self.data_dir)
        self.assertTrue(result["adoption"]["official_story_memory_written"])
        return draft

    def test_first_scene_is_empty_and_unreviewed_drafts_do_not_persist(self):
        p = self.plan("first-empty")
        self.assertEqual(p["task"]["approved_history"], [])
        self.assertFalse(self.db.exists())
        draft = self.manuscript(p["task"])
        report = bridge.check({"token": p["token"], "manuscript": draft},self.data_dir)
        self.assertEqual(report["report"]["status"], "EDITORIAL_REVIEW_REQUIRED")
        self.assertFalse(self.db.exists())
        another = self.plan("second-unadopted", slot="afternoon")
        self.assertEqual(another["task"]["approved_history"], [])

    def test_afternoon_sees_morning_and_evening_sees_both_in_order(self):
        morning = self.plan("accepted-am")
        self.adopt(morning)
        afternoon = self.plan("accepted-pm", slot="afternoon")
        prior = afternoon["task"]["approved_history"]
        self.assertTrue(prior)
        self.assertEqual({m["scene_id"] for m in prior}, {"accepted-am"})
        self.assertEqual([(m["message_id"],m["ordinal"]) for m in prior
                          if m["speaker_id"] == "assistant"], [("m01",0)])
        self.adopt(afternoon)
        evening = self.plan("after-pm", slot="evening")
        prior = evening["task"]["approved_history"]
        self.assertTrue(any(m["scene_id"] == "accepted-am" for m in prior))
        self.assertTrue(any(m["scene_id"] == "accepted-pm" for m in prior))
        dates = [(x["story_date"], {"morning":0,"afternoon":1,"evening":2}[x["slot"]],
                  x["scene_id"], x["ordinal"]) for x in prior]
        self.assertEqual(dates,sorted(dates))

    def test_future_and_same_slot_are_never_quoted_as_past(self):
        morning = self.plan("accepted-morning")
        self.adopt(morning)
        evening = self.plan("accepted-evening", slot="evening")
        self.adopt(evening)
        same_morning = self.plan("other-morning")
        self.assertEqual(same_morning["task"]["approved_history"], [])
        backdated = self.plan("yesterday", date="2026-10-13",slot="evening")
        self.assertEqual(backdated["task"]["approved_history"], [])
        afternoon = self.plan("middle-day",slot="afternoon")
        included={m["scene_id"] for m in afternoon["task"]["approved_history"]}
        self.assertIn("accepted-morning",included)
        self.assertNotIn("accepted-evening",included)
        later=person_history(self.db,self.roster,"assistant",before_story_date="2026-10-14",
                             before_slot="afternoon")
        self.assertTrue(all(r["scene_id"]=="accepted-morning" for r in later))
        self.assertFalse(scene_message_exists(self.db,self.roster,
                         scene_id="accepted-evening",message_id="m01",
                         speaker_id="assistant",before_story_date="2026-10-14",
                         before_slot="afternoon"))

    def test_snapshot_prevents_later_adoption_becoming_retroactive_memory(self):
        prepared=self.plan("planned-before-adoption",slot="afternoon")
        self.assertEqual(prepared["task"]["approved_history"],[])
        first=self.plan("adopted-after-planning")
        self.adopt(first)
        ref={"scene_id":"adopted-after-planning","message_id":"m01",
             "speaker_id":"assistant"}
        bad=self.manuscript(prepared["task"],history_ref=ref)
        answer=bridge.check({"token":prepared["token"],"manuscript":bad},self.data_dir)
        self.assertEqual(answer["report"]["status"],"BLOCKED_REWRITE_REQUIRED")
        self.assertTrue(any("snapshot" in issue for issue in
                            answer["report"]["blocking_issues"]))
        fresh=self.plan("planned-after-adoption",slot="afternoon")
        self.assertTrue(fresh["task"]["approved_history"])
        valid=self.manuscript(fresh["task"],history_ref=ref)
        reviewed=bridge.check({"token":fresh["token"],"manuscript":valid},self.data_dir)
        self.assertEqual(reviewed["report"]["status"],"EDITORIAL_REVIEW_REQUIRED")

    def test_real_disk_is_readable_by_a_new_python_process(self):
        old=self.plan("persisted-scene")
        self.adopt(old)
        # This subprocess does not share runtime state, proving persistence.
        code = (
            "import json,sys;"
            "sys.path.insert(0, 'tools');"
            "import p004_five_skill_bridge as b;"
            "r=b.plan({'scene_id':'after-process-restart',"
            "'story_date':'2026-10-15','daypart':'morning',"
            "'topic_keywords':['能源'],'max_members':8,"
            "'simulation_only':True,'source_status':'HYPOTHETICAL'},sys.argv[1]);"
            "print(json.dumps(r['task']['approved_history']))"
        )
        result=subprocess.run([sys.executable,"-c",code,str(self.data_dir)],cwd=ROOT,
                              text=True,capture_output=True,timeout=15,check=True)
        previous=json.loads(result.stdout)
        self.assertTrue(previous)
        self.assertTrue(any(p["scene_id"]=="persisted-scene" for p in previous))
        self.assertTrue(self.db.exists())

    def test_other_story_unapproved_speakers_and_unconfirmed_scene_rejected(self):
        data={
            "story_id":"p004-fiction-director-independent","scene_id":"candidate-only",
            "story_date":"2026-10-14","slot":"morning",
            "simulation_only":True,"approved_by_user":True,
            "messages":[{"message_id":"m1","speaker_id":"01","text":"Test"}]
        }
        with self.assertRaisesRegex(ValueError,"operator_confirmed"):
            adopt_scene(self.db,self.roster,data)
        wrong=dict(data,story_id="another-story")
        with self.assertRaisesRegex(ValueError,"another story"):
            adopt_scene(self.db,self.roster,wrong,operator_confirmed=True)
        extra=dict(data,messages=[{"message_id":"m1","speaker_id":"99","text":"Test"}])
        with self.assertRaisesRegex(ValueError,"unknown/unapproved"):
            adopt_scene(self.db,self.roster,extra,operator_confirmed=True)
        self.assertFalse(self.db.exists())

    def test_duplicate_scene_cannot_overwrite_adopted_history(self):
        package=self.plan("immutable-scene")
        self.adopt(package)
        new_plan=self.plan("immutable-scene",slot="afternoon")
        new_draft=self.manuscript(new_plan["task"])
        bridge.check({"token":new_plan["token"],"manuscript":new_draft},self.data_dir)
        with self.assertRaisesRegex(ValueError,"already adopted"):
            bridge.adopt({"token":new_plan["token"],
                          "editorial_confirmed":True,
                          "operator_confirmed":True},self.data_dir)
        history=person_history(self.db,self.roster,"assistant")
        self.assertEqual(len(history),1)
        self.assertEqual(history[0]["scene_id"],"immutable-scene")


if __name__=="__main__":
    unittest.main()
