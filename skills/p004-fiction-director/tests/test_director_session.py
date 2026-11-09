"""Proof sandbox continuity is isolated from formally adopted SQLite history."""
import json
import pathlib
import sys
import tempfile
import unittest

ROOT=pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
from director_storyflow import prepare,STORY,STATUS
from director_session import SandboxSession,approved_sqlite_history
from scene_memory import adopt_scene

ROSTER=json.loads((ROOT/"characters/drafts/roster-v2.json").read_text(encoding="utf8"))


def req(scene_id,date):
    return {"scene_id":scene_id,"story_date":date,"daypart":"afternoon",
            "topic":"Hypothetical company cash-flow classroom example",
            "topic_keywords":["企业现金流"],"source_status":"HYPOTHETICAL",
            "simulation_only":True,"max_members":15}


def fake_draft(plan,continuity=None):
    messages=[{"message_id":"a","speaker_id":"assistant","director_note":"fictional question",
               "text":"Acesta este un exemplu, nu o veste din piață."}]
    if continuity:
        messages.append({"message_id":"b","speaker_id":"04",
                         "text":"Data trecută am rămas cu o întrebare.",
                         "director_note":"responding to prior staged scene",
                         "continuity_ref":continuity,"reply_to":"a"})
    else:
        messages.append({"message_id":"b","speaker_id":"04",
                         "text":"Mă interesează banii pe care firma îi încasează.",
                         "director_note":"printer cashflow question","reply_to":"a"})
    return {"story_id":STORY,"scene_id":plan["scene_id"],
            "story_date":plan["story_date"],"daypart":plan["daypart"],
            "status":STATUS,"source_status":"HYPOTHETICAL",
            "simulation_only":True,"messages":messages}


class SessionTests(unittest.TestCase):
    def test_two_day_staged_memory_can_be_referenced_but_never_adopted(self):
        session=SandboxSession(ROSTER)
        first=req("test-day1","2026-10-14")
        p1=prepare(ROSTER,first)
        a=session.make(first,model_fn=lambda prompt:fake_draft(p1))
        self.assertEqual("EDITORIAL_REVIEW_REQUIRED",a["state"])
        second=req("test-day2","2026-10-15")
        continuity={"scene_id":"test-day1","message_id":"b","speaker_id":"04"}
        p2=prepare(ROSTER,second,history=[
            {"scene_id":"test-day1","message_id":"a","speaker_id":"assistant",
             "text":"Acesta este un exemplu, nu o veste din piață.",
             "provenance":"SAME_RUN_SANDBOX"},
            {"scene_id":"test-day1","message_id":"b","speaker_id":"04",
             "text":"Mă interesează banii pe care firma îi încasează.",
             "provenance":"SAME_RUN_SANDBOX"}])
        b=session.make(second,model_fn=lambda prompt:fake_draft(p2,continuity))
        self.assertEqual("EDITORIAL_REVIEW_REQUIRED",b["state"])
        self.assertEqual(4,session.staged_count())
        self.assertFalse(session.staged_summary()["formal_memory_written"])
        with self.assertRaisesRegex(ValueError,"already been staged"):
            session.make(first)

    def test_sqlite_requires_new_story_approval(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=pathlib.Path(tmp); db=root/"approved.sqlite3"
            roster=root/"approved-roster.json"
            roster.write_text(json.dumps({"story_id":STORY,"characters":[
                {"id":"04","approved_by_user":True}]}))
            scene={"story_id":STORY,"scene_id":"official-1","story_date":"2026-10-13",
                   "slot":"afternoon","simulation_only":True,"approved_by_user":True,
                   "messages":[{"message_id":"m1","speaker_id":"04",
                                "text":"Only a user-approved fictional scene."}]}
            adopt_scene(db,roster,scene,operator_confirmed=True)
            h=approved_sqlite_history(db,roster,["04"])
            self.assertEqual("ADOPTED_SQLITE",h[0]["provenance"])
            with self.assertRaisesRegex(ValueError,"unapproved"):
                approved_sqlite_history(db,roster,["05"])


if __name__=="__main__":unittest.main()
