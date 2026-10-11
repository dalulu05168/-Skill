"""Confirmed screenplay-to-memory bridge. All tests use temporary local files."""
import json
import pathlib
import sys
import tempfile
import unittest

ROOT=pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
import director_workflow as wf
import approve_scene as gate
import scene_memory as memory

DRAFT=json.loads((ROOT/"characters"/"drafts"/"roster-v2.json").read_text(encoding="utf-8"))


class ApprovalTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        root=pathlib.Path(self.tmp.name)
        self.db=root/"story.sqlite3"
        self.official=root/"approved.json"
        self.official.write_text(json.dumps({"story_id":wf.STORY,"characters":[]}),encoding="utf-8")
        self.p=wf.prepare(DRAFT,{"simulation_only":True,"source_status":"HYPOTHETICAL",
           "scene_id":"sceneA","story_date":"2026-10-12","daypart":"morning",
           "topic_keywords":["能源"],"max_members":4})
        sid=self.p["task"]["cast"][0]["speaker_id"]
        self.member=sid
        self.draft={"story_id":wf.STORY,"scene_id":"sceneA","story_date":"2026-10-12",
          "daypart":"morning","lesson_type":None,"simulation_only":True,
          "fictional_case_only":True,"status":"DRAFT_NOT_ADOPTED",
          "approved_by_user":False,"publishable":False,
          "messages":[
           {"message_id":"m1","speaker_id":"assistant","text":"Un exemplu imaginar despre costuri."},
           {"message_id":"m2","speaker_id":sid,"reply_to":"m1","text":"Dar cine plătește facturile?"},
          ]}
    def commit(self,**kwargs):
        return gate.finalize(self.p,self.draft,db_path=self.db,
                             approved_roster_path=self.official,**kwargs)
    def test_never_write_without_both_confirmations(self):
        for kwargs in ({},{"operator_confirmed":True},{"editorial_confirmed":True}):
            with self.assertRaisesRegex(ValueError,"both explicit"):
                self.commit(**kwargs)
        self.assertEqual([],memory.person_history(self.db,self.official,"assistant"))
    def test_cannot_adopt_member_still_not_approved(self):
        with self.assertRaisesRegex(ValueError,"unapproved"):
            self.commit(operator_confirmed=True,editorial_confirmed=True)
        self.assertEqual([],memory.person_history(self.db,self.official,"assistant"))
    def test_reviewed_approved_fiction_writes_once_without_publishing(self):
        self.official.write_text(json.dumps({"story_id":wf.STORY,
          "characters":[{"id":self.member,"approved_by_user":True}]}),encoding="utf-8")
        a=self.commit(operator_confirmed=True,editorial_confirmed=True)
        self.assertEqual("adopted",a["status"])
        self.assertFalse(a["published_to_whatsapp"])
        self.assertFalse(a["real_trade_executed"])
        self.assertTrue(a["official_story_memory_written"])
        self.assertEqual("m2",memory.person_history(self.db,self.official,self.member)[0]["message_id"])
        again=self.commit(operator_confirmed=True,editorial_confirmed=True)
        self.assertEqual("already_adopted",again["status"])
        self.assertFalse(again["official_story_memory_written"])
    def test_invalid_backstory_blocks_even_when_confirmed(self):
        self.official.write_text(json.dumps({"story_id":wf.STORY,
          "characters":[{"id":self.member,"approved_by_user":True}]}),encoding="utf-8")
        self.draft["messages"][1]["history_reference"]={
           "scene_id":"never","message_id":"ghost","speaker_id":self.member}
        with self.assertRaisesRegex(ValueError,"QA blocked"):
            self.commit(operator_confirmed=True,editorial_confirmed=True)
        self.assertEqual([],memory.person_history(self.db,self.official,self.member))
    def test_change_to_approved_scene_is_rejected_not_overwritten(self):
        self.official.write_text(json.dumps({"story_id":wf.STORY,
          "characters":[{"id":self.member,"approved_by_user":True}]}),encoding="utf-8")
        self.commit(operator_confirmed=True,editorial_confirmed=True)
        self.draft["messages"][1]["text"]="Complet diferit."
        with self.assertRaisesRegex(ValueError,"cannot overwrite"):
            self.commit(operator_confirmed=True,editorial_confirmed=True)


if __name__=="__main__":
    unittest.main()
