"""Three-day 65-person workflow stress, with a test-double author (not an AI)."""
import json
import pathlib
import sys
import unittest

ROOT=pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
from director_storyflow import prepare,STATUS,STORY
from director_session import SandboxSession

ROSTER=json.loads((ROOT/"characters/drafts/roster-v2.json").read_text(encoding="utf8"))


class StressTests(unittest.TestCase):
    def test_65_distinct_characters_in_three_day_staged_rehearsal(self):
        dates=["2026-10-12","2026-10-13","2026-10-14"]
        plans=[]
        for idx,person in enumerate(ROSTER["people"]):
            for slot in ("morning","afternoon","evening"):
                request={"scene_id":"stress-"+person["id"],
                         "story_date":dates[idx//22],"daypart":slot,
                         "topic":"Independent fictional discussion",
                         "topic_keywords":[person["interest_triggers"][0]],
                         "source_status":"HYPOTHETICAL","simulation_only":True,
                         "max_members":15}
                pl=prepare(ROSTER,request)
                if any(c["id"]==person["id"] for c in pl["cast"]):
                    plans.append((request,person))
                    break
            else:self.fail("not castable: "+person["id"])
        rank={"morning":0,"afternoon":1,"evening":2}
        plans.sort(key=lambda row:(row[0]["story_date"],rank[row[0]["daypart"]]))
        session=SandboxSession(ROSTER)
        all_speakers=set()
        date_counts={}
        for request,person in plans:
            planned=prepare(ROSTER,request)
            def make_stub(prompt):
                return {"story_id":STORY,"status":STATUS,
                        "scene_id":request["scene_id"],"story_date":request["story_date"],
                        "daypart":request["daypart"],"simulation_only":True,
                        "source_status":"HYPOTHETICAL","messages":[
                            {"message_id":"a","speaker_id":"assistant",
                             "text":"O situație ipotetică, nu știri de pe bursă.",
                             "director_note":"exercise introduction"},
                            {"message_id":"b","speaker_id":person["id"],
                             "text":person["voice"]["romanian_audition_line"]+" Este doar un exercițiu.",
                             "director_note":"specific interest from the character profile",
                             "reply_to":"a"}]}
            out=session.make(request,model_fn=make_stub)
            self.assertEqual("EDITORIAL_REVIEW_REQUIRED",out["state"],person["id"])
            self.assertFalse(out["publishable"])
            all_speakers.add(person["id"])
            date_counts[request["story_date"]]=date_counts.get(request["story_date"],0)+1
        self.assertEqual(65,len(all_speakers))
        self.assertEqual(65,session.staged_summary()["scenes"])
        self.assertEqual(130,session.staged_count())
        self.assertEqual(set(dates),set(date_counts))
        self.assertFalse(session.staged_summary()["formal_memory_written"])
        self.assertEqual([],
            json.loads((ROOT/"characters/approved-roster.json").read_text())["characters"])


if __name__=="__main__":unittest.main()
