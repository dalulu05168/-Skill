"""Offline director/author/review tests: writer is a fake callback, not an AI."""
import json
import pathlib
import sys
import unittest

ROOT=pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
from director_storyflow import prepare,roster_coverage,STATUS,STORY
from director_storygate import review,execute,OK

ROSTER=json.loads((ROOT/"characters/drafts/roster-v2.json").read_text(encoding="utf8"))


def request(person,slot="morning",name="test-one"):
    return {"scene_id":name,"story_date":"2026-10-14","daypart":slot,
            "topic":"Example financial education question","topic_keywords":[person["interest_triggers"][0]],
            "source_status":"HYPOTHETICAL","simulation_only":True,"max_members":15}


def draft(plan,speaker):
    return {"story_id":STORY,"scene_id":plan["scene_id"],"story_date":plan["story_date"],
            "daypart":plan["daypart"],"status":STATUS,"source_status":"HYPOTHETICAL",
            "simulation_only":True,"messages":[
                {"message_id":"a","speaker_id":"assistant","text":"Discutăm un exemplu ipotetic.",
                 "director_note":"opening"},
                {"message_id":"b","speaker_id":speaker,"text":"Mai trebuie verificate condițiile.",
                 "director_note":"personal question","reply_to":"a"}]}


class StoryflowTests(unittest.TestCase):
    def setUp(self):
        self.p=ROSTER["people"][3]
        self.req=request(self.p)
        self.plan=prepare(ROSTER,self.req)

    def test_prompt_without_paid_model(self):
        o=execute(ROSTER,self.req)
        self.assertEqual("AWAITING_AUTHOR",o["state"])
        self.assertFalse(o["publishable"])
        self.assertIn("Director context",o["prompt"])

    def test_accepted_structure_is_still_not_published(self):
        o=execute(ROSTER,self.req,model_fn=lambda prompt:draft(self.plan,self.p["id"]))
        self.assertEqual("EDITORIAL_REVIEW_REQUIRED",o["state"])
        self.assertEqual(OK,o["qa"]["status"])
        self.assertFalse(o["memory_written"])

    def test_repair_loop_rejects_then_returns_for_review(self):
        calls=[]
        def callback(prompt):
            calls.append(prompt)
            o=draft(self.plan,self.p["id"])
            if len(calls)==1:o["messages"][1]["speaker_id"]="66"
            return o
        out=execute(ROSTER,self.req,model_fn=callback)
        self.assertEqual(2,len(calls))
        self.assertEqual("REJECTED",out["attempts"][0]["result"])
        self.assertIn("speaker not selected",calls[1])

    def test_perpetual_error_is_not_delivered(self):
        result=execute(ROSTER,self.req,model_fn=lambda prompt:"not JSON")
        self.assertEqual("REJECTED_MAX_RETRIES",result["state"])
        self.assertEqual(3,len(result["attempts"]))

    def test_wrong_person_history_or_time_is_rejected(self):
        o=draft(self.plan,self.p["id"])
        o["messages"][1]["reply_to"]="future"
        self.assertEqual("REJECTED",review(o,self.plan)["status"])
        o=draft(self.plan,self.p["id"])
        o["messages"][1]["text"]="Ieri am vorbit despre asta."
        self.assertEqual("REJECTED",review(o,self.plan)["status"])
        o=draft(self.plan,"professor")
        self.assertEqual("REJECTED",review(o,self.plan)["status"])

    def test_all_65_can_be_cast_and_pass_synthetic_structure_gate(self):
        coverage=roster_coverage(ROSTER)
        self.assertEqual([],coverage["missing"])
        self.assertFalse(coverage["ai_dialogue_tested"])
        for p in ROSTER["people"]:
            for slot in ("morning","afternoon","evening"):
                req=request(p,slot,name="s-"+p["id"]+"-"+slot)
                plan=prepare(ROSTER,req)
                if any(c["id"]==p["id"] for c in plan["cast"]):
                    self.assertEqual(OK,review(draft(plan,p["id"]),plan)["status"],p["id"])
                    break
            else:self.fail("not castable: "+p["id"])
        self.assertEqual([],
            json.loads((ROOT/"characters/approved-roster.json").read_text())["characters"])


if __name__=="__main__":unittest.main()
