"""Independent memory tests: no paid models, network, or legacy roster."""
import importlib.util
import json
import pathlib
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("p004_scene_memory", ROOT / "scripts" / "scene_memory.py")
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


def scene():
    return {"story_id": m.STORY_ID, "scene_id": "day1-am", "story_date": "2026-10-11",
            "slot": "morning", "simulation_only": True, "approved_by_user": True,
            "messages": [
                {"message_id": "a", "speaker_id": "assistant", "text": "新闻主题讨论。"},
                {"message_id": "b", "speaker_id": "01", "text": "我还想再看看具体报告。"},
                {"message_id": "c", "speaker_id": "02", "text": "那成本怎么办？"},
            ]}


class MemoryTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.db = pathlib.Path(self.tmp.name) / "independent.sqlite3"
        self.roster = pathlib.Path(self.tmp.name) / "approved-roster.json"
        self.roster.write_text(json.dumps({"story_id":m.STORY_ID,"characters":[
            {"id":"01","approved_by_user":True},
            {"id":"02","approved_by_user":True}
        ]}), encoding="utf-8")

    def adopt(self, s=None):
        return m.adopt_scene(self.db, self.roster, s or scene(), operator_confirmed=True)

    def test_zero_history_does_not_fake_past(self):
        self.assertEqual([], m.person_history(self.db, self.roster, "01"))
        self.assertFalse(m.scene_message_exists(self.db, self.roster,
                         scene_id="day1-am", message_id="b", speaker_id="01"))

    def test_requires_user_and_operator_confirmation(self):
        with self.assertRaisesRegex(ValueError,"operator_confirmed"):
            m.adopt_scene(self.db, self.roster, scene())
        s=scene();s["approved_by_user"]=False
        with self.assertRaisesRegex(ValueError,"approved"):
            self.adopt(s)
        s=scene();s["simulation_only"]=False
        with self.assertRaisesRegex(ValueError,"approved fictional"):
            self.adopt(s)
        self.assertEqual([],m.person_history(self.db, self.roster,"01"))

    def test_strict_isolation_person_history_and_literal_search(self):
        self.assertEqual("adopted",self.adopt()["status"])
        rows=m.person_history(self.db,self.roster,"01")
        self.assertEqual(1,len(rows))
        self.assertEqual("b",rows[0]["message_id"])
        self.assertTrue(m.scene_message_exists(self.db,self.roster,scene_id="day1-am",message_id="b",speaker_id="01"))
        self.assertFalse(m.scene_message_exists(self.db,self.roster,scene_id="day1-am",message_id="c",speaker_id="01"))
        self.assertEqual([],m.person_history(self.db,self.roster,"01",keyword="成本"))
        self.assertEqual(1,len(m.person_history(self.db,self.roster,"02",keyword="成本")))
        self.assertEqual([],m.person_history(self.db,self.roster,"02",keyword="%"))

    def test_duplicate_is_idempotent_and_modified_conflicts(self):
        self.adopt()
        self.assertEqual("already_adopted",self.adopt()["status"])
        changed=scene();changed["messages"][1]["text"]="new text"
        with self.assertRaisesRegex(ValueError,"cannot overwrite"):
            self.adopt(changed)
        self.assertEqual("我还想再看看具体报告。",m.person_history(self.db,self.roster,"01")[0]["text"])

    def test_transaction_rolls_back_entire_invalid_scene(self):
        bad=scene();bad["messages"][2]["speaker_id"]="65"
        with self.assertRaisesRegex(ValueError,"unapproved"):
            self.adopt(bad)
        self.assertEqual([],m.person_history(self.db,self.roster,"01"))
        bad=scene();bad["messages"][2]["message_id"]="a"
        with self.assertRaisesRegex(ValueError,"duplicate"):
            self.adopt(bad)
        self.assertEqual([],m.person_history(self.db,self.roster,"01"))

    def test_reject_legacy_story_and_unapproved_roster(self):
        s=scene();s["story_id"]="romania-market-director"
        with self.assertRaisesRegex(ValueError,"another story"):
            self.adopt(s)
        self.roster.write_text(json.dumps({"story_id":m.STORY_ID,"characters":[
            {"id":"01","approved_by_user":False}]}),encoding="utf-8")
        with self.assertRaisesRegex(ValueError,"explicitly approved"):
            self.adopt()

    def test_time_order_does_not_depend_on_import_order(self):
        late=scene();late["scene_id"]="day2";late["story_date"]="2026-10-12"
        late["messages"]=[{"message_id":"z","speaker_id":"01","text":"第二天"}]
        self.adopt(late)
        self.adopt()
        got=m.person_history(self.db,self.roster,"01")
        self.assertEqual(["day1-am","day2"],[x["scene_id"] for x in got])

    def test_roles_separate_and_sql_escaping(self):
        self.adopt()
        self.assertEqual([],m.person_history(self.db,self.roster,"professor"))
        self.assertEqual("a",m.person_history(self.db,self.roster,"assistant")[0]["message_id"])
        self.assertEqual([],m.person_history(self.db,self.roster,"01",keyword="' OR 1=1 --"))
        with self.assertRaises(ValueError):m.person_history(self.db,self.roster,"03")


if __name__=="__main__":unittest.main()
